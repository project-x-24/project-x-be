"""
Utility class to define properties of video, fullbleed, and product assets 
for asset fitting
"""
import json

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterable, List, Optional, Set, TypeVar, Union
from uuid import uuid4

if TYPE_CHECKING is True:
    from src.asset_selection.common.classes.asset_trace import TraceAbstractClass

from src.asset_selection.common.constants import DBAssetType, InputAssetType, ASSET_EMBEDDING_VERSION
from src.common.classes.json_serializable_abc import JSONSerializableAbstractClass
from src.common.logger.logger import get_logger


logger = get_logger(__name__)


T = TypeVar("T", bound="BaseAsset")


class BaseAssetException(Exception):
    def __init__(self, failure_message: str, asset_id: Optional[int] = None) -> None:
        super().__init__(failure_message)
        self.failure_message = failure_message
        self.asset_id = asset_id


class UnprocessedVideoAssetException(BaseAssetException):
    def __init__(
        self, failure_message: str, asset_id: Optional[int] = None, unconverted: Optional[bool] = False
    ) -> None:
        super().__init__(failure_message, asset_id)
        self.unconverted = unconverted


class BaseAsset(ABC):
    _asset_type = None

    @abstractmethod
    def __init__(
        self,
        name: str,
        width: Optional[int],
        height: Optional[int],
        asset_id: int,
        uri: Optional[str],
        gs_uri: Optional[str],
        ad_hoc: Optional[bool] = False,
        db_asset_type_id: Optional[int] = None,
        embedding_versions: Optional[List[str]] = None,
        asset_description: Optional[str] = None,
    ):
        self.__width = width
        self.__height = height

        self.__asset_id = asset_id
        self.__uri = uri
        self.__gs_uri = gs_uri

        self.__name = name

        self.__ad_hoc = ad_hoc
        self.__db_asset_type_id = db_asset_type_id

        self.__embedding_versions = None
        self.embedding_versions = embedding_versions  # use setter to set

        self.__asset_description = asset_description

        assert self._asset_type is not None, "asset_type is None"

        if self._asset_type in [InputAssetType.FULLBLEED, InputAssetType.VIDEO, InputAssetType.PRODUCT]:
            assert self.__width is not None and self.__width > 0, "Invalid width"
            assert self.__height is not None and self.__height > 0, "Invalid height"

        if self.__ad_hoc is True:
            assert isinstance(self.__asset_id, str), "asset_id should be str for ad-hoc assets"

        assert self.__asset_id is not None, "asset_id is None"
        assert self.__uri is not None, "uri is None"

    @property
    def asset_type(self) -> InputAssetType:
        return self._asset_type

    @property
    def name(self) -> str:
        return self.__name

    @property
    def uri(self) -> str:
        return self.__uri

    @property
    def gs_uri(self) -> str:
        return self.__gs_uri

    @property
    def width(self) -> int:
        return self.__width

    @property
    def height(self) -> int:
        return self.__height

    @property
    def asset_id(self) -> int:
        return self.__asset_id

    @property
    def ad_hoc(self) -> bool:
        return self.__ad_hoc

    @property
    def db_asset_type_id(self) -> int:
        return self.__db_asset_type_id

    @property
    def has_embedding(self) -> bool:
        return ASSET_EMBEDDING_VERSION in self.__embedding_versions

    @property
    def embedding_versions(self) -> Set[str]:
        if self.__embedding_versions is None:
            return set()

        else:
            return self.__embedding_versions

    @embedding_versions.setter
    def embedding_versions(self, _embedding_versions: List[str]):
        if _embedding_versions is None:
            self.__embedding_versions = set()

        else:
            assert not isinstance(_embedding_versions, str) and isinstance(
                _embedding_versions, Iterable
            ), "_embedding_versions must be iterable of str"

            if self.__embedding_versions is None:
                self.__embedding_versions = set()

            self.__embedding_versions.update(set(_embedding_versions))

    @property
    def asset_description(self) -> Optional[dict]:
        return self.__asset_description
    
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"{self.asset_type.name} - " f"asset_id={self.__asset_id}, name={self.__name}"

    def __eq__(self, other: "BaseAsset") -> bool:
        return type(self) == type(other) and self.asset_id == other.asset_id

    def __hash__(self):
        return hash(self.asset_id)


class VideoAsset(BaseAsset, JSONSerializableAbstractClass):
    _asset_type = InputAssetType.VIDEO

    def __init__(
        self,
        name: str,
        width: int,
        height: int,
        asset_id: Union[int, str],
        parent_asset_id: int,
        uri: str,
        start_time_ms: int,
        end_time_ms: int,
        fps: float,
        ad_hoc: Optional[bool] = False,
        db_asset_type_id: Optional[int] = DBAssetType.VIDEO.value,
        is_ugc: Optional[bool] = False,
        embedding_versions: Optional[List[str]] = None,
        processed: Optional[bool] = True,
        gs_uri: Optional[str] = None,
        asset_description: Optional[str] = None,
        is_generated: Optional[bool] = False
    ):
        super().__init__(
            name,
            width,
            height,
            asset_id,
            uri,
            ad_hoc=ad_hoc,
            db_asset_type_id=db_asset_type_id,
            embedding_versions=embedding_versions,
            gs_uri=gs_uri,
            asset_description=asset_description
        )

        self.__parent_asset_id = parent_asset_id
        self.__is_generated = is_generated

        self.__start_time_ms = start_time_ms
        self.__end_time_ms = end_time_ms
        assert self.__end_time_ms > self.__start_time_ms, "end_time_ms  <= start_time_ms"

        self.__duration_ms = self.__end_time_ms - self.__start_time_ms

        self.__fps = fps
        assert self.__fps > 0, "fps <= 0"

        assert self.asset_id != self.parent_asset_id, f"asset_id cannot be the same as parent_asset_id"

        self.__is_parent_video = self.__parent_asset_id is None

        # UGC flag
        self.__is_ugc = is_ugc

        # This flag is to indicate whether or not VideoAsset has been fully processed by video processor. We can still
        # use an unprocessed videos but we'll not have any proper child asset or vectors.
        # Use setter as it has some logic checks
        self.processed = processed

    @property
    def start_time_ms(self):
        return self.__start_time_ms

    @property
    def end_time_ms(self):
        return self.__end_time_ms

    @property
    def duration_ms(self):
        return self.__duration_ms

    @property
    def fps(self):
        return self.__fps

    @property
    def asset_type(self) -> InputAssetType:
        return self._asset_type

    @property
    def parent_asset_id(self) -> int:
        return self.__parent_asset_id

    @property
    def is_parent_video(self) -> bool:
        return self.__is_parent_video
    
    @property
    def is_generated(self) -> bool:
        return self.__is_generated

    @property
    def is_ugc(self) -> bool:
        return self.__is_ugc

    @property
    def processed(self) -> bool:
        return self.__processed

    @processed.setter
    def processed(self, _processed: bool):
        _processed = bool(_processed)

        if self.__parent_asset_id is not None and _processed is False:
            logger.warning(
                "parent_asset_id exists - meaning this is a child asset - processed flag cannot be False "
                f"for a child asset - overriding to True"
            )
            _processed = True

        self.__processed = _processed

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return (
            f"{self.asset_type.name} - asset_id={self.asset_id}, "
            f"parent_asset_id={self.parent_asset_id}, "
            f"name={self.name}, start={self.__start_time_ms:.3f} ms, "
            f"end={self.__end_time_ms:.3f} ms, duration={self.__duration_ms:.3f} ms, "
            f"is_ugc={self.__is_ugc}, processed={self.__processed}, is_generated={self.__is_generated}"
        )

    def __eq__(self, other: "BaseAsset") -> bool:
        return type(self) == type(other) and self.asset_id == other.asset_id and hash(self) == hash(other)

    def __hash__(self):
        return hash(json.dumps(self.to_serializable_dict()))

    def create_ad_hoc_video_segment(
        self,
        start_time_ms: float,
        duration_ms: float,
        db_asset_type_id=DBAssetType.VIDEO_SEGMENT.value,
        clamp_timestamps: Optional[bool] = False,
    ) -> "VideoAsset":
        if clamp_timestamps is True and start_time_ms < self.__start_time_ms:
            logger.warning(f"Clamping start_time_ms {start_time_ms:.3f} ms --> {self.__start_time_ms:.3f} ms")
            start_time_ms = max(start_time_ms, self.__start_time_ms)

        assert start_time_ms >= self.__start_time_ms, (
            f"start_time ({start_time_ms} ms) < " f"asset start_time ({self.__start_time_ms} ms)"
        )

        end_time_ms = start_time_ms + duration_ms

        if clamp_timestamps is True and end_time_ms > self.__duration_ms:
            logger.warning(f"Clamping end_time_ms {end_time_ms:.3f} ms --> {self.__duration_ms:.3f} ms")
            end_time_ms = min(end_time_ms, self.__duration_ms)

        assert end_time_ms <= self.__duration_ms, (
            f"end_time ({end_time_ms:.3f} ms) > " f"duration ({self.__duration_ms:.3f} ms)"
        )

        # If we're creating an ad-hoc asset from a parent video
        # then we'll have to take transfer the asset ID of current asset
        # to parent_asset_id of the new instance as we're creating
        # a 'child asset' a.k.a. video segment out of the current asset
        if self.__is_parent_video is True:
            __parent_asset_id = self.asset_id

        else:
            __parent_asset_id = self.parent_asset_id

        __ad_hoc_key = str(uuid4())

        return VideoAsset(
            name=f"{self.name}_{__ad_hoc_key}",
            width=self.width,
            height=self.height,
            asset_id=__ad_hoc_key,
            parent_asset_id=__parent_asset_id,
            uri=self.uri,
            gs_uri=self.gs_uri,
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
            fps=self.__fps,
            ad_hoc=True,
            db_asset_type_id=db_asset_type_id,
            is_ugc=False,  # Can't create a UGC ad-hoc clip w/o proper sentence boundaries, so this is always False
            asset_description=self.asset_description,
            is_generated=self.__is_generated
        )

    def to_serializable_dict(self) -> dict:
        serializable_dict = {
            "asset_type": self.asset_type.name,
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "asset_id": self.asset_id,
            "parent_asset_id": self.parent_asset_id,
            "uri": self.uri,
            "gs_uri": self.gs_uri,
            "start_time_ms": self.start_time_ms,
            "end_time_ms": self.end_time_ms,
            "fps": self.fps,
            "ad_hoc": self.ad_hoc,
            "is_ugc": self.is_ugc,
            "embedding_versions": list(self.embedding_versions),
            "processed": self.processed,
            "asset_description": self.asset_description,
            "is_generated": self.is_generated
        }

        return serializable_dict

    @classmethod
    def from_serializable_dict(cls, serializable_dict: dict) -> "VideoAsset":
        # Assert correct asset type
        __asset_type = serializable_dict.get("asset_type", None)
        assert (
            InputAssetType[__asset_type] == cls._asset_type
        ), f"Wrong asset_type ({__asset_type}, expected {cls._asset_type.name})"

        # Load from dict - cast mandatory properties to type to check for invalid
        # values, leave optional properties as they are (e.g. those with possible None)
        return cls(
            name=str(serializable_dict.get("name", None)),
            width=int(serializable_dict.get("width", None)),
            height=int(serializable_dict.get("height", None)),
            asset_id=serializable_dict.get("asset_id", None),
            parent_asset_id=serializable_dict.get("parent_asset_id", None),
            uri=serializable_dict.get("uri", None),
            gs_uri=serializable_dict.get("gs_uri", None),
            start_time_ms=float(serializable_dict.get("start_time_ms", None)),
            end_time_ms=float(serializable_dict.get("end_time_ms", None)),
            fps=float(serializable_dict.get("fps", None)),
            ad_hoc=bool(serializable_dict.get("ad_hoc", None)),
            is_ugc=bool(serializable_dict.get("is_ugc", False)),
            embedding_versions=serializable_dict.get("embedding_versions", None),
            processed=serializable_dict.get("processed", True),
            asset_description=serializable_dict.get("asset_description", None),
            is_generated=serializable_dict.get("is_generated", False)
        )
    

class FullbleedAsset(BaseAsset, JSONSerializableAbstractClass):
    _asset_type = InputAssetType.FULLBLEED

    def __init__(
        self,
        name: str,
        width: int,
        height: int,
        asset_id: int,
        uri: str,
        embedding_versions: Optional[List[str]] = None,
        gs_uri: Optional[str] = None,
        asset_description: Optional[str] = None
    ):
        super().__init__(
            name,
            width,
            height,
            asset_id,
            uri,
            db_asset_type_id=DBAssetType.PRODUCT.value,
            embedding_versions=embedding_versions,
            gs_uri=gs_uri,
            asset_description=asset_description
        )

    def to_serializable_dict(self) -> dict:
        serializable_dict = {
            "asset_type": self.asset_type.name,
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "asset_id": self.asset_id,
            "uri": self.uri,
            "gs_uri": self.gs_uri,
            # "ad_hoc": self.ad_hoc,
            "embedding_versions": list(self.embedding_versions),
            "asset_description": self.asset_description
        }

        return serializable_dict

    @classmethod
    def from_serializable_dict(cls, serializable_dict: dict) -> "VideoAsset":
        # Assert correct asset type
        __asset_type = serializable_dict.get("asset_type", None)
        assert (
            InputAssetType[__asset_type] == cls._asset_type
        ), f"Wrong asset_type ({__asset_type}, expected {cls._asset_type.name})"

        # Load from dict - cast mandatory properties to type to check for invalid
        # values, leave optional properties as they are (e.g. those with possible None)
        return cls(
            name=str(serializable_dict.get("name", None)),
            width=int(serializable_dict.get("width", None)),
            height=int(serializable_dict.get("height", None)),
            asset_id=serializable_dict.get("asset_id", None),
            uri=serializable_dict.get("uri", None),
            gs_uri=serializable_dict.get("gs_uri", None),
            # ad_hoc=bool(serializable_dict.get("ad_hoc", None)),
            embedding_versions=serializable_dict.get("embedding_versions", None),
            asset_description=serializable_dict.get("asset_description", None)
        )


class ProductAsset(BaseAsset, JSONSerializableAbstractClass):
    _asset_type = InputAssetType.PRODUCT

    def __init__(
        self,
        name: str,
        width: int,
        height: int,
        asset_id: int,
        uri: str,
        is_segmented: Optional[bool] = True,
        embedding_versions: Optional[List[str]] = None,
        gs_uri: Optional[str] = None,
        asset_description: Optional[str] = None
    ):
        super().__init__(
            name,
            width,
            height,
            asset_id,
            uri,
            db_asset_type_id=DBAssetType.PRODUCT.value,
            embedding_versions=embedding_versions,
            gs_uri=gs_uri,
            asset_description=asset_description
        )

        self.__is_segmented = is_segmented

    @property
    def is_segmented(self):
        return self.__is_segmented

    def to_serializable_dict(self) -> dict:
        serializable_dict = {
            "asset_type": self.asset_type.name,
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "asset_id": self.asset_id,
            "uri": self.uri,
            "gs_uri": self.gs_uri,
            "is_segmented": self.is_segmented,
            # "ad_hoc": self.ad_hoc,
            "embedding_versions": list(self.embedding_versions),
            "asset_description": self.asset_description
        }

        return serializable_dict

    @classmethod
    def from_serializable_dict(cls, serializable_dict: dict) -> "VideoAsset":
        # Assert correct asset type
        __asset_type = serializable_dict.get("asset_type", None)
        assert (
            InputAssetType[__asset_type] == cls._asset_type
        ), f"Wrong asset_type ({__asset_type}, expected {cls._asset_type.name})"

        # Load from dict - cast mandatory properties to type to check for invalid
        # values, leave optional properties as they are (e.g. those with possible None)
        return cls(
            name=str(serializable_dict.get("name", None)),
            width=int(serializable_dict.get("width", None)),
            height=int(serializable_dict.get("height", None)),
            asset_id=serializable_dict.get("asset_id", None),
            uri=serializable_dict.get("uri", None),
            gs_uri=serializable_dict.get("gs_uri", None),
            is_segmented=bool(serializable_dict.get("is_segmented", None)),
            # ad_hoc=bool(serializable_dict.get("ad_hoc", None)),
            embedding_versions=serializable_dict.get("embedding_versions", None),
            asset_description=serializable_dict.get("asset_description", None)
        )


class AudioAsset(BaseAsset):
    _asset_type = InputAssetType.AUDIO

    def __init__(self, name: str, asset_id: int, uri: str):
        super().__init__(name, None, None, asset_id, uri, db_asset_type_id=DBAssetType.AUDIO_TRACK.value)


class OtherAsset(BaseAsset):
    _asset_type = InputAssetType.OTHER

    def __init__(self, name: str, asset_id: int, db_asset_type_id: int):
        super().__init__(name, None, None, asset_id, None, db_asset_type_id=db_asset_type_id)


class SceneAssetNode(object):
    def __init__(
        self,
        scene_index: int,
        placeholder_index: int,
        asset: BaseAsset,
        trace: Optional["TraceAbstractClass"] = None,
    ):
        self.__scene_index = scene_index
        self.__placeholder_index = placeholder_index
        self.__asset = asset

        self.__placeholder_type = self.__asset.asset_type
        # Names will appear like this: scene_0_VIDEO_0_v1_1
        self.__name = (
            f"scene_{self.__scene_index}_{self.__placeholder_type.name}"
            f"_{self.__placeholder_index}_{self.__asset.name}"
        )

        self.__trace = None
        if trace is not None:
            self.__trace = trace
            self.__trace.add(self.__asset)
            self.__name = f"{self.__name}_{'_'.join([str(k) for k in self.__trace.trace])}"

    @property
    def name(self) -> str:
        return self.__name

    @property
    def placeholder_type(self) -> InputAssetType:
        return self.__placeholder_type

    @property
    def asset(self) -> BaseAsset:
        return self.__asset

    @property
    def trace(self) -> "TraceAbstractClass":
        return self.__trace

    @property
    def scene_index(self) -> int:
        return self.__scene_index

    @property
    def placeholder_index(self) -> int:
        return self.__placeholder_index

    def add_trace(self, asset: BaseAsset):
        self.__trace.add(asset)

    def add_weight_trace(self, weight: float):
        self.__trace.add_weight(weight)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} object: " f"scene_index={self.__scene_index}, name={self.__name}>"
