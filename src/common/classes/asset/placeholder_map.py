from typing import Dict, List, Optional, Set, Tuple

from src.asset_selection.common.constants import InputAssetType, PlaceholderDimension
from src.common.classes.json_serializable_abc import JSONSerializableAbstractClass
from src.common.logger.logger import get_logger


logger = get_logger(__name__)


class ConceptPlaceholderMap(JSONSerializableAbstractClass):
    def __init__(
        self,
        input_asset_type: InputAssetType,
        placeholder_name: str,
        dimension: Optional[PlaceholderDimension] = PlaceholderDimension.SQUARE,
        placeholder_tag: Optional[str] = None,
    ):
        self.__input_asset_type: InputAssetType = input_asset_type
        self.__dimension_placeholder_mapping: Dict[PlaceholderDimension, str] = {dimension: placeholder_name}
        self.__placeholder_tag: Optional[str] = placeholder_tag

    @classmethod
    def from_serializable_dict(cls, serializable_dict: dict) -> "ConceptPlaceholderMap":
        # Get fixed attributes
        input_asset_type = InputAssetType[serializable_dict.get("input_asset_type", None)]
        placeholder_tag = serializable_dict.get("placeholder_tag", None)

        # Get dict of dim to ph mapping
        dimension_placeholder_mapping = serializable_dict.get("dimension_placeholder_mapping", None)
        assert dimension_placeholder_mapping is not None, "dimension_placeholder_mapping is None"

        # Make this an iter, get the first mapping to init the ConceptPlaceholderMap object
        dimension_placeholder_mapping = iter(dimension_placeholder_mapping.items())

        dimension, placeholder_name = next(dimension_placeholder_mapping)
        placeholder_dimension = PlaceholderDimension[dimension]

        # Init the ConceptPlaceholderMap object
        __cls = cls(input_asset_type, placeholder_name, placeholder_dimension, placeholder_tag)

        # Add the remaining dimensions
        for dimension, placeholder_name in dimension_placeholder_mapping:
            __cls.add_placeholder_dimension(placeholder_name, PlaceholderDimension[dimension])

        return __cls

    def to_serializable_dict(self) -> dict:
        serializable_dict = {
            "input_asset_type": self.__input_asset_type.name,
            "dimension_placeholder_mapping": {k.name: v for k, v in self.__dimension_placeholder_mapping},
            "placeholder_tag": self.__placeholder_tag,
        }

        return serializable_dict

    @property
    def asset_type(self) -> InputAssetType:
        return self.__input_asset_type

    @property
    def placeholder_name(self) -> str:
        """
        This attribute just retrieves a placeholder name - for now, we'll just assume if we request for one without
        specifying diemsnion, then we're always asking for SQUARE oreintation

        If we have no such oreintation set, then fallback to getting the first key we find

        This function should not be used for anything that requires accurate orientation definition
        """
        if PlaceholderDimension.SQUARE in self.__dimension_placeholder_mapping.keys():
            _placeholder_name = self.__dimension_placeholder_mapping.get(PlaceholderDimension.SQUARE, None)

        else:
            _placeholder_name = self.__dimension_placeholder_mapping.get(
                next(self.__dimension_placeholder_mapping.keys()), None
            )

        assert _placeholder_name is not None, "No placeholder_name set"

        return _placeholder_name

    @property
    def placeholder_tag(self) -> str:
        if self.__placeholder_tag is None:
            _placeholder_tag = self.placeholder_name

        else:
            _placeholder_tag = self.__placeholder_tag

        return _placeholder_tag

    @placeholder_tag.setter
    def placeholder_tag(self, _placeholder_tag: str):
        self.__placeholder_tag = _placeholder_tag

    @property
    def dimensions(self) -> Set[PlaceholderDimension]:
        return set(self.__dimension_placeholder_mapping.keys())

    @property
    def placeholders(self) -> List[str]:
        """
        Returns all the original placeholders associated with this object
        """
        return list(self.__dimension_placeholder_mapping.values())

    def add_placeholder_dimension(self, placeholder_name: str, dimension: PlaceholderDimension):
        if dimension in self.__dimension_placeholder_mapping:
            logger.warning(
                f"placeholder name {self.__dimension_placeholder_mapping.get(dimension, None)} "
                f"already exists with dimension {dimension} - will overwrite with {placeholder_name}"
            )

        self.__dimension_placeholder_mapping.update({dimension: placeholder_name})

    def get_placeholder_name_for_dimension(
        self, dimension: PlaceholderDimension, allow_missing: Optional[bool] = False
    ) -> str:
        if dimension not in self.__dimension_placeholder_mapping.keys() and allow_missing is True:
            _placeholder_name = self.placeholder_name

        else:
            _placeholder_name = self.__dimension_placeholder_mapping.get(dimension, None)

        assert _placeholder_name is not None, f"No placeholder_name with dimension={dimension}"

        return _placeholder_name

    def __str__(self) -> str:
        return (
            f"ConceptMapPlaceholder() - {self.asset_type.name} --> tag={self.placeholder_tag}, "
            f"placeholders={self.__dimension_placeholder_mapping}"
        )

    def __repr__(self) -> str:
        return self.__str__()


def parse_placeholder_name(placeholder_name: str) -> Tuple[InputAssetType, int, Optional[PlaceholderDimension]]:
    """
    Given a placeholder name for product with orientation e.g. "horizontal_product_2", parses the name to obtain
    the orientation, asset type, and placeholder index --> InputAssetType.PRODUCT, PlaceholderDimension.HORIZONTAL, 2
    """
    components = [k for k in placeholder_name.split("_") if k != "placeholder"]

    if len(components) == 2:
        ph_type, ph_index = components
        ph_orientation = None

    elif len(components) == 3:
        ph_orientation, ph_type, ph_index = components

    else:
        raise ValueError(f"Invalid placeholder name structure: {placeholder_name}")

    ph_index = int(ph_index)
    try:
        ph_type = InputAssetType[ph_type.upper()]

    except Exception as e:
        logger.debug(f"Unknown placeholder type {ph_type} - setting to {InputAssetType.OTHER}")
        ph_type = InputAssetType.OTHER

    try:
        ph_orientation = (
            PlaceholderDimension[ph_orientation.upper()] if ph_orientation is not None else PlaceholderDimension.SQUARE
        )

    except Exception as e:
        ph_orientation = PlaceholderDimension.SQUARE

    return ph_type, ph_index, ph_orientation


def concept_map_to_concept_placeholder_dimension_map(
    concept_map: List[Dict[str, InputAssetType]]
) -> List[Dict[str, ConceptPlaceholderMap]]:
    """
    This block will check if any of the layers are actually orientation versions of a single
    placeholder - if so, then we must group them together and consider these as 1 single placeholder
    Input - concept_map - each index in list corresponds to the scene index: [
        {
            "fullbleed_0": InputAssetType.FULLBLEED,
            "horizontal_product_3": InputAssetType.PRODUCT,
            "square_product_3": InputAssetType.PRODUCT,
            "vertical_product_3": InputAssetType.PRODUCT,
            ...
        },
        {...},
        ...
    ]

    Output - list of dicts - each index in list corresponds to the scene index: [
        {
            "fullbleed_0": ConceptPlaceholderMap(input_asset_type=InputAssetType.FULLBLEED, ...),
            "product_3": ConceptPlaceholderMap(input_asset_type=InputAssetType.PRODUCT, ...)  # handles dimensiosn
        },
        {...},
        ...
    ]
    """
    concept_placeholder_dimension_map = [{} for _ in concept_map]

    for scene_index, layer_names in enumerate(concept_map):
        for layer_name, layer_type in layer_names.items():
            try:
                layer_type, layer_index, layer_orientation = parse_placeholder_name(layer_name)

                # This will convert "horizontal_product_placeholder_1" to just "product_placeholder_1" etc.
                layer_tag = f"{layer_type.name.lower()}_{layer_index}"

                # NOTE - this list of dicts has been inited
                if concept_placeholder_dimension_map[scene_index].get(layer_tag, None) is None:
                    concept_placeholder_dimension_map[scene_index][layer_tag] = ConceptPlaceholderMap(
                        layer_type, layer_name, layer_orientation, layer_tag
                    )

                else:
                    assert isinstance(
                        concept_placeholder_dimension_map[scene_index][layer_tag], ConceptPlaceholderMap
                    ), "Invalid type for self.concept_map item"

                    concept_placeholder_dimension_map[scene_index][layer_tag].add_placeholder_dimension(
                        layer_name, layer_orientation
                    )

            except Exception as e:
                logger.error(f"Error parsing placeholder {layer_name} - using original. E: {e}", exc_info=True)
                concept_placeholder_dimension_map[scene_index][layer_name] = ConceptPlaceholderMap(
                    layer_type, layer_name
                )

    # Pretty print some results
    __ostr = "\n"
    __indent_0 = ""
    for scene_index, placeholder_maps in enumerate(concept_placeholder_dimension_map):
        __ostr += f"{__indent_0}\tScene {scene_index:1d}:"
        __indent_0 = "\n"

        __indent_1 = " "
        for layer_tag, placeholder_map in placeholder_maps.items():

            __ostr += f"{__indent_1}{layer_tag:12s} -"
            __indent_1 = "\n\t         "

            placeholder_map: ConceptPlaceholderMap  # for type hinting

            __indent_2 = " "
            for dimension in placeholder_map.dimensions:
                __ostr += (
                    f"{__indent_2}{dimension.name} --> "
                    f"{placeholder_map.get_placeholder_name_for_dimension(dimension)}"
                )
                __indent_2 = "\n\t                        "

    logger.info(f"Mapped placeholders to dimensions: {__ostr}")

    return concept_placeholder_dimension_map
