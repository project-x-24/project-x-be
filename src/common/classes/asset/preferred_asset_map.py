from collections import defaultdict
from typing import Dict, List, Optional, Set, Union

from src.asset_selection.common.constants import AssetState, InputAssetType
from src.common.classes.asset.asset import BaseAsset, VideoAsset
from src.common.logger.logger import get_logger


logger = get_logger(__name__)


class PreferredAssetMap(object):
    def __init__(
        self,
        scene_preferred_assets: Dict[
            int, Optional[Union[Dict[str, Union[AssetState, BaseAsset]], List[Union[AssetState, BaseAsset]]]]
        ],
    ):
        self.__preferred_assets_info = {}
        self.__num_assets = 0

        for iscene, iasset_info in scene_preferred_assets.items():
            __iasset_info = {}
            __iscene_assets, __iplaceholder_assets = set(), {}

            if isinstance(iasset_info, list) or isinstance(iasset_info, set):
                __iscene_assets.update(set(iasset_info))

            elif isinstance(iasset_info, dict):
                __iplaceholder_assets.update(iasset_info)

            else:
                logger.warning(f"Unexpected structure of iasset_info={iasset_info} for scene={iscene} - skipping!")

            if __iplaceholder_assets is not None:
                __iscene_assets_from_placeholder_assets = set()

                for __iph_asset in __iplaceholder_assets.values():
                    try:
                        assert __iph_asset is not None, "__iph_asset is None"
                        __iscene_assets_from_placeholder_assets.add(__iph_asset)

                    except Exception as e:
                        logger.debug(e, exc_info=True)

                __iscene_assets.update(__iscene_assets_from_placeholder_assets)

            __iscene_assets = list(__iscene_assets)
            self.__num_assets += len(__iscene_assets)

            if len(__iscene_assets) == 0:
                __iscene_assets = None

            if len(__iplaceholder_assets) == 0:
                __iplaceholder_assets = None

            __iasset_info = {"scene_assets": __iscene_assets, "placeholder_assets": __iplaceholder_assets}

            self.__preferred_assets_info.update({iscene: __iasset_info})

        logger.info(f"Initialized PreferredAssetMap() with {self.__num_assets} assets")

    def add_preferred_asset(self, asset: BaseAsset, scene: int, placeholder: Optional[str] = None):
        assert isinstance(scene, int), f"Invalid scene={scene}"

        try:
            __iscene_assets = self.__preferred_assets_info.get(scene, {}).get("scene_assets", None)
            __iplaceholder_assets = self.__preferred_assets_info.get(scene, {}).get("placeholder_assets", None)

        except Exception as e:
            logger.debug(e, exc_info=True)
            __iscene_assets, __iplaceholder_assets = None, None

        if __iscene_assets is None:
            __iscene_assets = set()

        else:
            __iscene_assets = set(__iscene_assets)

        if __iplaceholder_assets is None:
            __iplaceholder_assets = {}

        __iscene_assets.add(asset)

        if placeholder is not None:
            __iplaceholder_assets.update({placeholder: asset})

        __iasset_info = {"scene_assets": list(__iscene_assets), "placeholder_assets": __iplaceholder_assets}
        self.__preferred_assets_info.update({scene: __iasset_info})

        self.__num_assets += 1

        logger.info(
            f"PreferredAssetmap().add_preferred_asset() - Added asset={asset} to "
            f"scene={scene}, placeholder={placeholder}"
        )

    def add_update_video_segments(self, available_assets: List[VideoAsset]):
        """
        Adds video segments if any preferred assets are detected to be parent video - but instead of just adding all
        video segments from DB, this fn only adds those that are supplied in available_assets - this is to ensure we
        scope the assets properly in case we have any upstream filtering criteria imposed

        Call this fn when required - this is not fully developed e.g. add_preferred_asset() won't update this yet
        """
        available_assets_id_map = defaultdict(set)
        for iasset in available_assets:
            if iasset.is_parent_video is False:
                available_assets_id_map[iasset.parent_asset_id].add(iasset)

        available_assets_id_map = dict(available_assets_id_map)

        for iscene, iasset_info in self.__preferred_assets_info.items():
            __iplaceholder_assets: Dict[str, BaseAsset] = iasset_info.get("placeholder_assets", None)

            __iscene_assets: Optional[List[BaseAsset]] = iasset_info.get("scene_assets", None)
            __iscene_assets: Set[BaseAsset] = set(__iscene_assets) if __iscene_assets is not None else set()

            __iplaceholder_video_segments = iasset_info.get("placeholder_video_segments", None)
            if __iplaceholder_video_segments is None:
                __iplaceholder_video_segments: Optional[Dict[str, set[VideoAsset]]] = {}

            if __iplaceholder_assets is not None:
                for iph, iph_asset in __iplaceholder_assets.items():
                    if isinstance(iph_asset, BaseAsset) and iph_asset.asset_type == InputAssetType.VIDEO:
                        iph_asset: VideoAsset  # for type hinting
                        if iph_asset.is_parent_video is True:
                            ivideo_segment_assets = available_assets_id_map.get(iph_asset.asset_id, None)

                    else:
                        ivideo_segment_assets = None

                    if ivideo_segment_assets is not None:
                        if __iplaceholder_video_segments.get(iph, None) is None:
                            __iplaceholder_video_segments[iph] = list(ivideo_segment_assets)

                        else:
                            __iplaceholder_video_segments[iph] = list(
                                set(__iplaceholder_video_segments[iph]).update(ivideo_segment_assets)
                            )

                        __iscene_assets.update(ivideo_segment_assets)

            __iasset_info = {
                "scene_assets": list(__iscene_assets),
                "placeholder_video_segments": __iplaceholder_video_segments,
            }

            iasset_info: dict
            iasset_info.update(__iasset_info)

            self.__preferred_assets_info.update({iscene: iasset_info})

            logger.info(
                f"PreferredAssetmap().add_update_video_segments() - Added placeholder_video_segments="
                f"{iasset_info.get('placeholder_video_segments', None)} to scene={iscene}"
            )

    def get_preferred_asset_by_scene_and_placeholder(
        self, scene: int, placeholder: str, include_failures: Optional[bool] = False
    ) -> Optional[Union[BaseAsset, AssetState]]:
        placeholder_asset = None

        try:
            placeholder_asset = (
                self.__preferred_assets_info.get(scene, None).get("placeholder_assets", None).get(placeholder, None)
            )

            if include_failures is not True:
                assert isinstance(
                    placeholder_asset, BaseAsset
                ), f"placeholder_asset={placeholder_asset} not a BaseAsset"

        except Exception as e:
            logger.warning(f"Failed to get asset for scene={scene}, placeholder={placeholder}. E: {e}")

        logger.info(
            f"PreferredAssetMap().get_preferred_asset_by_scene_and_placeholder(): scene={scene}, "
            f"placeholder={placeholder} --> asset={placeholder_asset}"
        )

        return placeholder_asset

    def get_preferred_video_segments_by_scene_and_placeholder(
        self,
        scene: int,
        placeholder: str,
        include_failures: Optional[bool] = False,
    ) -> Optional[List[Union[VideoAsset, AssetState]]]:
        placeholder_video_segments = None

        try:
            placeholder_video_segments = (
                self.__preferred_assets_info.get(scene, None)
                .get("placeholder_video_segments", None)
                .get(placeholder, None)
            )

            if include_failures is not True:
                assert isinstance(
                    placeholder_video_segments, VideoAsset
                ), f"placeholder_video_segments={placeholder_video_segments} not a VideoAsset"

        except Exception as e:
            logger.warning(f"Failed to get video segments for scene={scene}, placeholder={placeholder}. E: {e}")

        logger.info(
            f"PreferredAssetMap().get_preferred_asset_by_scene_and_placeholder(): scene={scene}, "
            f"placeholder={placeholder} --> asset={placeholder_video_segments}"
        )

        return placeholder_video_segments

    def get_preferred_assets(self, asset_type: Optional[InputAssetType] = None) -> Optional[List[BaseAsset]]:
        preferred_assets = []

        for iasset_info in self.__preferred_assets_info.values():
            iassets: Optional[List[BaseAsset]] = iasset_info.get("scene_assets", None)

            if iassets is not None:
                iassets = [k for k in iassets if isinstance(k, BaseAsset)]

                if asset_type is not None:
                    iassets = [k for k in iassets if k.asset_type == asset_type]

                if len(iassets) > 0:
                    preferred_assets.extend(iassets)

        if len(preferred_assets) == 0:
            preferred_assets = None

        logger.info(f"PreferredAssetMap().preferred_assets(): returning {preferred_assets}")

        return preferred_assets

    def get_preferred_assets_by_scene(
        self,
        asset_type: Optional[InputAssetType] = None,
        include_failures: Optional[bool] = False,
    ) -> Optional[Dict[int, List[Union[AssetState, BaseAsset]]]]:
        """
        Returns a dict of {<scene_index>: <list of valid BaseAsset excluding AssetState items>} OR None
        """
        if asset_type is not None:
            assert include_failures is not True, "Cannot set asset_type when include_failures is True"

        preferred_assets_by_scene = {}

        for iscene, iasset_info in self.__preferred_assets_info.items():
            iassets: Optional[List[BaseAsset]] = iasset_info.get("scene_assets", None)

            if iassets is not None:
                if include_failures is not True:
                    iassets = [k for k in iassets if isinstance(k, BaseAsset)]

                if asset_type is not None:
                    iassets = [k for k in iassets if k.asset_type == asset_type]

                if len(iassets) > 0:
                    preferred_assets_by_scene.update({iscene: iassets})

        if len(preferred_assets_by_scene) == 0:
            preferred_assets_by_scene = None

        logger.info(f"PreferredAssetMap().get_preferred_assets_by_scene(): returning {preferred_assets_by_scene}")

        return preferred_assets_by_scene

    def get_preferred_asset_ids_by_scene(
        self, asset_type: Optional[InputAssetType] = None
    ) -> Optional[Dict[int, List[int]]]:
        preferred_assets_by_scene = self.get_preferred_assets_by_scene(asset_type=asset_type)

        if preferred_assets_by_scene is not None:
            preferred_asset_ids_by_scene = {
                k: [iv.asset_id for iv in v] for k, v in preferred_assets_by_scene.items() if v is not None
            }

        else:
            preferred_asset_ids_by_scene = None

        return preferred_asset_ids_by_scene

    def __len__(self) -> int:
        return self.__num_assets

    def __str__(self) -> str:
        __ostr = "PreferredAssetMap():"

        for iscene, iasset_info in self.__preferred_assets_info.items():
            __ostr += f"\n\tscene={iscene}"

            iscene_assets = iasset_info.get("scene_assets", None)
            __ostr += f"\n\t\tscene_assets:"

            if iscene_assets is not None:
                for iasset in iscene_assets:
                    __ostr += f"\n\t\t\t{iasset}"

            else:
                __ostr += f" {iscene_assets}"

            iplaceholder_assets = iasset_info.get("placeholder_assets", None)
            __ostr += f"\n\t\tplaceholder_assets:"

            if iplaceholder_assets is not None:
                for iph, iasset in iplaceholder_assets.items():
                    __ostr += f"\n\t\t\tplaceholder={iph}, asset={iasset}"

            else:
                __ostr += f" {iplaceholder_assets}"

            iplaceholder_video_segments = iasset_info.get("placeholder_video_segments", None)
            __ostr += f"\n\t\tplaceholder_video_segments:"

            if iplaceholder_video_segments is not None:
                for iph, iassets in iplaceholder_video_segments.items():
                    for iasset in iassets:
                        __ostr += f"\n\t\t\tplaceholder={iph}, asset={iasset}"

            else:
                __ostr += f" {iplaceholder_video_segments}"

        return __ostr

    def __repr__(self) -> str:
        return self.__str__()
