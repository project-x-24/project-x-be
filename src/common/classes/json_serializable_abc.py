from __future__ import annotations

import hashlib
import pprint
import simplejson

from abc import ABC, abstractmethod


class JSONSerializableAbstractClass(ABC):
    def __init__(self):
        super().__init__()
        self.__hash = None

    @classmethod
    @abstractmethod
    def from_serializable_dict(
        cls, serializable_dict: dict
    ) -> JSONSerializableAbstractClass:
        """
        Implement this so that we can instantiate as my_class_instance = MyClass.from_serializable_dict(some_dict)

        :param serializable_dict: JSON serializable dict (i.e. json.dumps(<dict>) won't break)
        :return: inited class instance from serializable_dict
        """
        pass

    @classmethod
    def from_serialized_json(
        cls, serialized_json: str
    ) -> JSONSerializableAbstractClass:
        """

        :param serialized_json: serialized JSON str
        :return: inited class instance from serialized JSON str
        """
        serializable_dict = simplejson.loads(serialized_json)

        return cls.from_serializable_dict(serializable_dict)

    @classmethod
    def from_json_file(cls, file_path: str) -> JSONSerializableAbstractClass:
        """

        Args:
            file_path (str): Serialized json file

        Returns:
            JSONSerializableAbstractClass: _description_
        """
        with open(file_path, "r") as fp:
            serializable_dict = simplejson.load(fp)

            return cls.from_serializable_dict(serializable_dict)

    @abstractmethod
    def to_serializable_dict(self) -> dict:
        """
        Implement this to convert class into a JSON serializable dict (i.e. json.dumps(<dict>) won't break)

        :return: JSON serializble dict
        """
        pass

    def to_serialized_json(self) -> str:
        """
        Expresses class instance as a serialized JSON str

        :return: serialized JSON str
        """
        serialized_json = simplejson.dumps(
            self.to_serializable_dict(), indent=2, sort_keys=True, ignore_nan=True
        )

        return serialized_json

    def is_hash_modified(self) -> bool:
        """
        Computes a signature based on the serialized dict & stores it as a mangled attribute. Compares current hash
        against what is stored and returns whether or not hash has changed (the 1st call to hash() will always return
        True as we started with nothing)

        :return: True of hash has changed, False otherwise
        """
        __hash = self.get_hash()

        is_new_hash = __hash != self.__hash
        self.__hash = __hash

        return is_new_hash

    def get_hash(self) -> str:
        """
        Can be overriden or modified by derived class if needed e.g. if we want hash to be defined only for a subset
        of attributes or if we want a diff hash method as long as it returns str

        :return: str hex md5 hash
        """
        return str(hashlib.md5(self.to_serialized_json().encode()).hexdigest())

    def __repr__(self):
        return pprint.pformat(self.__dict__)

    def __str__(self):
        return pprint.pformat(self.__dict__)
