import copy

from collections import Counter, defaultdict
from types import MappingProxyType
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple, Union

from src.common.classes.asset.placeholder_map import (
    ConceptPlaceholderMap,
    concept_map_to_concept_placeholder_dimension_map,
)


if TYPE_CHECKING is True:
    from src.common.classes.asset.asset import VideoAsset
    from src.common.classes.asset.preferred_asset_map import PreferredAssetMap

from src.asset_selection.common.constants import (
    ASSET_SELECTOR_ENFORCE_TOTAL_VIDEO_DURATION,
    DEFAULT_NON_VIDEO_SCENE_DURATION_MS,
    ENABLE_VIDEO_DURATION_FALLBACKS,
    AssetState,
    InputAssetType,
)
from src.common.classes.asset.asset import BaseAsset
from src.common.logger.logger import get_logger


logger = get_logger(__name__)


class Concept(object):
    """
    Object to store information from an input ad template that will be used by Asset Selector algos to generate ads
    """

    def __init__(
        self,
        scene_config: List[Dict[str, InputAssetType]],  # called chat_params.concept_map in creative.py
        scene_copies: List[Optional[str]],
        scene_preferred_assets: Optional["PreferredAssetMap"] = None,
        scene_placeholder_dimension_map: Optional[List[Dict[str, ConceptPlaceholderMap]]] = None,
    ):
        """
        Inputs:

        scene_config: A List of dicts in this form (called 'concept_map' in other places):
        [
            {
                "video_placeholder_1": InputAssetType.VIDEO,
                "fullbleed_placeholder_2": InputAssetType.FULLBLEED,
            },
            {
                "video_placeholder_1": InputAssetType.VIDEO,
                "fullbleed_placeholder_2": InputAssetType.FULLBLEED,
            }
        ]
        where each dict in the list corresponds to a particular scene in an ad template. Each dict is a mapping of
        template placeholder names to its input asset type. dicts can be empty if there aren't any relevant placeholders
        to be fitted with assets

        scene_copies: A list of strings or Nones - each string in the list corresponds to the copy story of that scene.
        If there's no copy associated with a particular scene, replace the string with None

        scene_preferred_assets: A PreferredAssetMap object
        """
        # Sanity checks
        assert len(scene_config) == len(
            scene_copies
        ), f"Num scenes in scene_config ({len(scene_config)}) != scene_copies ({len(scene_copies)})"

        if scene_placeholder_dimension_map is None:
            self.__scene_placeholder_dimension_map = concept_map_to_concept_placeholder_dimension_map(scene_config)

        else:
            assert len(scene_config) == len(
                scene_placeholder_dimension_map
            ), "len(scene_config) != len(scene_placeholder_dimension_map)"

            for iconcept_map, idimension_map in zip(scene_config, scene_placeholder_dimension_map):
                iconcept_map_placeholders = set(iconcept_map.keys())
                idimension_map_placeholders = set([iv for v in idimension_map.values() for iv in v.placeholders])

                iplaceholders_difference = iconcept_map_placeholders.difference(idimension_map_placeholders)

                assert len(iplaceholders_difference) == 0, (
                    f"placeholders mismatch between concept_map and placeholder_dimension_map - "
                    f"iplaceholders_difference={iplaceholders_difference}"
                )

            self.__scene_placeholder_dimension_map = scene_placeholder_dimension_map

        # Store scene_config as self.__scene_placeholder_types to keep track ot input types of each placeholder name
        self.__scene_placeholder_types = [
            {layer_name: concept_placeholder_map.asset_type for layer_name, concept_placeholder_map in d.items()}
            for d in self.__scene_placeholder_dimension_map
        ]
        self.__scene_copies = scene_copies
        self.__scene_preferred_assets = scene_preferred_assets

        self.__num_scenes = len(self.__scene_placeholder_types)

        # Store tallies of placeholder count by type and scene, and by type over all scenes
        self.__scene_placeholder_type_count = [Counter(s.values()) for s in self.__scene_placeholder_types]
        self.__total_placholder_type_count = sum(self.__scene_placeholder_type_count, Counter())

        self.__total_duration = None  # This attribute should be set after fitting

        # For now - restrict to 1 video placeholder per scene as we have not coded up case to handle multiple videos
        assert all(
            [k.get(InputAssetType.VIDEO, 0) <= 1 for k in self.__scene_placeholder_type_count]
        ), f">1 video placeholder detected in one or more scenes: {self.__scene_placeholder_type_count}"

        # Construct a dict to store mapping of each placeholder name to a fitted asset (which will be a derived
        # class of BaseAsset) and init this as None. These Nones will be replaced with actual assets post fitting.
        """
        Sample of self.__scene_placeholders:
        [
            {
                'fullbleed_placeholder_1': <FullbleedAsaset Object FULLBLEED - asset_id=312, name=f3>,
                'fullbleed_placeholder_2': None  # None only prior to fitting - should be populated post-fitting
            },  # Scene 0
            {
                'video_placeholder_2': <VideoAsset Object>
            },  # Scene 1
            {}, # Scene 2 (empty dict means no fittable placeholders)
            {...}  # Scene 3 etc.
        ]
        """
        self.__scene_placeholders = [{k: None for k in s.keys()} for s in self.__scene_placeholder_types]

        # Duplicate self.__scene_placeholders here - this set stores a copy of swappable asset (so the values will be
        # a list of Assets instead of a single asset for each placeholder)
        self.__scene_placeholders_swap_candidates = copy.deepcopy(self.__scene_placeholders)

    @property
    def num_scenes(self) -> int:
        return self.__num_scenes

    @property
    def scene_copies(self) -> List[Union[str, None]]:
        return self.__scene_copies

    @property
    def scene_preferred_assets(self) -> Optional["PreferredAssetMap"]:
        return self.__scene_preferred_assets

    @property
    def scene_preferred_assets_including_failures(self) -> Dict[int, Optional[List[Union[AssetState, BaseAsset]]]]:
        raise NotImplementedError

    @property
    def scene_placeholders(self) -> Tuple[MappingProxyType[Dict[str, dict]]]:
        """
        this will return placeholders of the 'grouped' type i.e. 'horizontal_product_4' and 'vertical_product_4' from
        original visual JSON will appear as 'product_4' as the placeholder name/key
        """
        # Make this immutable as we don't intend for anyone to directly modify the property
        return tuple([MappingProxyType(k) for k in self.__scene_placeholders])

    @property
    def scene_placeholders_by_dimension(self) -> Tuple[MappingProxyType[Dict[str, dict]]]:
        """
        Maps back scene placeholders that we grouped together based on dimension and name back to their original names.
        Each original placeholder will get the same asset as the asset that was assigned to the grouped placeholder
        """
        __scene_placeholders_by_dimension = []

        for scene_placeholders, scene_placeholder_dimension_map in zip(
            self.__scene_placeholders, self.__scene_placeholder_dimension_map
        ):
            __scene_placeholders = {}
            for layer_tag, asset_dict in scene_placeholders.items():
                __scene_placeholders.update(
                    {layer_name: asset_dict for layer_name in scene_placeholder_dimension_map[layer_tag].placeholders}
                )

            __scene_placeholders_by_dimension.append(__scene_placeholders)

        return tuple([MappingProxyType(k) for k in __scene_placeholders_by_dimension])

    @property
    def scene_placeholders_swap_candidates(self) -> Tuple[MappingProxyType[Dict[str, dict]]]:
        # Make this immutable as we don't intend for anyone to directly modify the property
        return tuple([MappingProxyType(k) for k in self.__scene_placeholders_swap_candidates])
    
    @property
    def scene_placeholders_swap_candidates_by_dimension(self) -> Tuple[MappingProxyType[Dict[str, dict]]]:
        """
        scene_placeholders_swap_candidates_by_dimension() is to scene_placeholders_by_dimension() as
        scene_placeholders_by_dimension() is to scene_placeholders()
        """
        __scene_placeholders_swap_candidates_by_dimension = []

        for scene_placeholders, scene_placeholder_dimension_map in zip(
            self.__scene_placeholders_swap_candidates, self.__scene_placeholder_dimension_map
        ):
            __scene_placeholders = {}
            for layer_tag, asset_dict in scene_placeholders.items():
                __scene_placeholders.update(
                    {layer_name: asset_dict for layer_name in scene_placeholder_dimension_map[layer_tag].placeholders}
                )

            __scene_placeholders_swap_candidates_by_dimension.append(__scene_placeholders)

        return tuple([MappingProxyType(k) for k in __scene_placeholders_swap_candidates_by_dimension])

    @property
    def total_duration_ms(self) -> float:
        assert self.__total_duration is not None, "total_duration has not been set"
        return self.__total_duration

    @total_duration_ms.setter
    def total_duration_ms(self, _total_duration_ms: float):
        assert _total_duration_ms >= 0, "total_duration_ms must be >= 0"
        self.__total_duration = _total_duration_ms

    @property
    def scene_durations_ms(self) -> List[float]:
        assert self.__total_duration is not None, "total_duration_ms has not been set"
        scene_durations = []

        # Iterate over each fitted scene to find video placeholders
        for iscene_placeholder in self.scene_placeholders:
            iscene_duration = 0
            ihas_video = False

            # For all placeholder types in the scene, inspect the durations of each video placeholder and pick the max
            for _, iasset in iscene_placeholder.items():
                assert iasset is not None, (
                    "Concept().scene_durations_ms - attempting to get scene duration w/o properly fitted "
                    f"assets (i.e. asset is None in placeholder) is not allowed!"
                )
                iasset: BaseAsset  # for type hinting

                if iasset is not None and iasset.asset_type == InputAssetType.VIDEO:
                    iasset: "VideoAsset"

                    # The duration of the scene placeholder is the max duration of all videos in that scene
                    iscene_duration = max(iscene_duration, iasset.duration_ms)
                    ihas_video = True

            if ihas_video is True:
                scene_durations.append(iscene_duration)

            else:
                scene_durations.append(None)

        # Calculate the scene durations for the remaining non-video scenes whose values are None at this point
        total_video_duration_ms = sum([k for k in scene_durations if k is not None])
        total_non_video_duration_ms = self.__total_duration - total_video_duration_ms
        total_non_video_scenes = sum([int(k is None) for k in scene_durations])

        duration_per_non_video_scene = DEFAULT_NON_VIDEO_SCENE_DURATION_MS  # set default first

        # Sanity check
        if total_non_video_scenes > 0:
            if total_non_video_duration_ms < 0:
                if ASSET_SELECTOR_ENFORCE_TOTAL_VIDEO_DURATION is True:
                    raise AssertionError(
                        f"total_non_video_duration_ms < 0 (total_video_duration_ms={total_video_duration_ms:.1f} ms, "
                        f"total_duration_ms={self.__total_duration:.1f} ms)"
                    )

                else:
                    logger.warning(
                        f"total_non_video_duration_ms < 0 (total_video_duration_ms={total_video_duration_ms:.1f} ms, "
                        f"total_duration_ms={self.__total_duration:.1f} ms) - possibly due to flag "
                        f"ASSET_SELECTOR_ENFORCE_TOTAL_VIDEO_DURATION={ASSET_SELECTOR_ENFORCE_TOTAL_VIDEO_DURATION}. "
                        f"Setting min duration per non-video scene to {duration_per_non_video_scene:.1f} ms"
                    )

            else:
                duration_per_non_video_scene = total_non_video_duration_ms / total_non_video_scenes

        else:
            duration_per_non_video_scene = 0

        logger.info(
            f"Concept().scene_durations: total_duration_ms={self.__total_duration:.1f} ms, "
            f"total_video_duration_ms={total_video_duration_ms:.1f} ms, "
            f"total_non_video_scenes={total_non_video_scenes} "
            f"--> duration_per_non_video_scene={duration_per_non_video_scene:.1f} ms"
        )

        scene_durations = [duration_per_non_video_scene if k is None else k for k in scene_durations]

        # Sanity check
        __sum_scene_durations = sum(scene_durations)
        if abs(__sum_scene_durations - self.__total_duration) > 1e-3:
            if ENABLE_VIDEO_DURATION_FALLBACKS is True or ASSET_SELECTOR_ENFORCE_TOTAL_VIDEO_DURATION is False:
                logger.warning(
                    f"sum(scene_durations) ({__sum_scene_durations:.1f} ms) != "
                    f"self.__total_duration ({self.__total_duration:.1f} ms) - "
                    f"will cheat and change self.__total_duration"
                )
                self.__total_duration = __sum_scene_durations

            else:
                raise AssertionError(
                    f"sum(scene_durations) ({__sum_scene_durations:.1f} ms) != "
                    f"self.__total_duration ({self.__total_duration:.1f} ms)"
                )

        return scene_durations

    def set_scene_placeholder(self, scene_index: int, placeholder_name: str, asset: BaseAsset):
        """
        Sets the asset for a specific scene_index x placeholder_name
        """
        try:
            assert (
                placeholder_name in self.__scene_placeholders[scene_index].keys()
            ), f"placeholder_name {placeholder_name} does not exist in scene_index {scene_index}"

        except Exception as e:
            logger.error(e, exc_info=True)
            raise ValueError(f"scene_index={scene_index}, placeholder_name={placeholder_name} does not exist")

        # Forbid setting wrong asset type into placeholder
        assert asset.asset_type == self.__scene_placeholder_types[scene_index][placeholder_name], (
            f"Asset type mismatch - scene {scene_index} placeholder {placeholder_name} has type "
            f"{self.__scene_placeholder_types[scene_index][placeholder_name]} but asset as type {asset.asset_type}"
        )
        self.__scene_placeholders[scene_index][placeholder_name] = asset
        logger.info(f"Set asset for scene_index={scene_index}, {placeholder_name} --> {asset}")

    def unset_scene_placeholder(self, scene_index: int, placeholder_name: str):
        """
        CLears the asset for a specific scene_index x placeholder_name (sets to None)
        """
        try:
            assert (
                placeholder_name in self.__scene_placeholders[scene_index].keys()
            ), f"placeholder_name {placeholder_name} does not exist in scene_index {scene_index}"

        except Exception as e:
            logger.error(e, exc_info=True)
            raise ValueError(f"scene_index={scene_index}, placeholder_name={placeholder_name} does not exist")

        self.__scene_placeholders[scene_index][placeholder_name] = None
        logger.info(f"Cleared asset for scene_index={scene_index}, {placeholder_name}")

    def get_scene_placeholder(self, scene_index: int, placeholder_name: str) -> BaseAsset:
        """
        Function name is a misnomer - this fn actually gets the asset assigned to a specific (
        (scene_index, placeholder_name)
        """
        asset = None

        try:
            asset = self.scene_placeholders[scene_index][placeholder_name]

        except Exception as e:
            logger.error(e, exc_info=True)
            raise ValueError(
                f"Failed to retrieve placaholder asset for scene_index={scene_index}, "
                f"placeholder_name={placeholder_name}"
            )

        return asset

    def get_scene_placeholder_type(self, scene_index: int, placeholder_name: str) -> InputAssetType:
        try:
            return self.__scene_placeholder_types[scene_index][placeholder_name]

        except Exception as e:
            logger.error(
                f"Failed to get scene placeholder type for scene_index={scene_index}, "
                f"placeholder_name={placeholder_name}. E: {e}",
                exc_info=True,
            )

    def get_scene_placeholder_swap_candidates(
        self, scene_index: int, placeholder_name: str
    ) -> Optional[List[BaseAsset]]:
        """
        Counterpart of get_scene_placeholder(). These are always the 'grouped' placeholder/layer names
        """
        swap_assets = None

        try:
            swap_assets = self.scene_placeholders_swap_candidates[scene_index][placeholder_name]

        except Exception as e:
            logger.error(e, exc_info=True)
            raise ValueError(
                f"Failed to retrieve placaholder asset for scene_index={scene_index}, "
                f"placeholder_name={placeholder_name}"
            )

        return swap_assets

    def set_scene_placeholder_swap_candidates(self, scene_index: int, placeholder_name: str, assets: List[BaseAsset]):
        """
        Counterpart of get_scene_placeholder_swap_candidates(). These are always the 'grouped' placeholder/layer names
        """
        try:
            self.__scene_placeholders_swap_candidates[scene_index][placeholder_name] = assets

        except Exception as e:
            logger.error(e, exc_info=True)
            raise ValueError(
                f"Failed to set placaholder swap candidate assets for scene_index={scene_index}, "
                f"placeholder_name={placeholder_name}"
            )

    def get_placeholders(
        self,
        scene_index: Optional[int] = None,
        asset_type: Optional[InputAssetType] = None,
    ) -> Dict[Tuple[int, InputAssetType], Set[str]]:
        """
        Get placeholders by scene_index and asset_type

        scene_index: Get placeholders from this scene index - if not given, will return placeholders for all scenes
        asset_type: Get placeholders of this InputAssetType - if not give, will return placeholders for all asset types

        Return value: A dict of this structure:
        {
            (<scene_index>, <InputAssetType>): [<placeholder_name_1>, <placeholder_name_2>, ...],
            (...): [...],
            ...
        }
        where each key of the dict is a tuple of (scene_index, input_asset_type) and value is a list of all placeholder
        names of that asset type. If scene_index and/or asset_type is given in input, dict will only contain tuples of
        of those contraints.
        """
        if scene_index is None:
            scene_iter = range(self.__num_scenes)

        else:
            scene_iter = [scene_index]

        if asset_type is None:
            asset_type_iter = InputAssetType

        else:
            asset_type_iter = [asset_type]

        # Return value here is an ordered dict of {(scene_index, InputAssetType): <list of placeholder names>}
        placeholders = defaultdict(list)
        for isc in scene_iter:
            for iasset_type in asset_type_iter:
                placeholders[(isc, iasset_type)].extend(
                    [iph_name for iph_name, iat in self.__scene_placeholder_types[isc].items() if iat == iasset_type]
                )

        return dict(placeholders)

    def get_placeholder_type_count(
        self, asset_type: Optional[InputAssetType] = None
    ) -> Union[int, Dict[InputAssetType, int]]:
        """
        Returns placeholder type count over all scenes for a given asset type. If asset type is None, returns a dict
        of counts of all asset types
        """
        if asset_type is None:
            return {iat: self.__total_placholder_type_count.get(iat, 0) for iat in InputAssetType}

        else:
            return self.__total_placholder_type_count.get(asset_type, 0)

    def get_placeholder_type_count_by_scene(self, scene_index: int) -> Dict[InputAssetType, int]:
        """
        Returns placeholder type count by scene for all InputAssetType enums, even if 0
        """
        assert scene_index >= 0 and scene_index <= self.__num_scenes, f"Invalid scene_index={scene_index}"
        return {iat: self.__scene_placeholder_type_count[scene_index].get(iat, 0) for iat in InputAssetType}

    def get_scene_placeholder_name(self, scene_index: int, asset_type: InputAssetType, placeholder_index: int) -> str:
        """
        This function just returns the placeholder name given a scene_index, asset_type, and placeholder_index
        It's used in graph selector as we did not track placeholders by name, but by incremental indices
        """
        assert scene_index >= 0 and scene_index < self.__num_scenes, f"Invalid scene_index {scene_index}"
        placeholder_names = self.get_placeholders(scene_index, asset_type)[(scene_index, asset_type)]

        assert 0 <= placeholder_index < len(placeholder_names), f"Invalid placeholder index {placeholder_index}"

        return placeholder_names[placeholder_index]

    def get_scene_placeholder_type(self, scene_index: int, placeholder_name: str) -> InputAssetType:
        assert self.__num_scenes == len(
            self.__scene_placeholder_types
        ), "Somehow self.__num_scenes != len(self.__scene_placeholder_types)"

        assert (
            scene_index >= 0 and scene_index < self.__num_scenes
        ), f"Invalid scene_index={scene_index} (valid option from 0 to num_scenes={self.__num_scenes})"

        assert placeholder_name in self.__scene_placeholder_types[scene_index].keys(), (
            f"Invalid placeholder_name={placeholder_name} "
            f"(valid options={self.__scene_placeholder_types[scene_index].keys()})"
        )

        return self.__scene_placeholder_types[scene_index][placeholder_name]

    def __str__(self):
        str_rep = f"{self.__class__.__name__}\n\tnum_scenes: {self.num_scenes}\n\tTotal placeholders by type & scene:"

        for isc in range(self.__num_scenes):
            str_pre = f"\n\t\tScene {isc:1d}: "

            for iasset_type, icount in self.get_placeholder_type_count_by_scene(isc).items():
                str_rep += f"{str_pre}{iasset_type.name}: {icount}"
                str_pre = "\n\t\t         "

        # for iinput_type in InputAssetType:
        #    str_rep += f"\n\t\t{iinput_type.name}:" f"{self.get_placeholder_type_count(iinput_type)}"

        return str_rep
