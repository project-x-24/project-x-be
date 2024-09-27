import inspect
import os
import sys

from src.config import TEST_MODE, USE_DB_POOL


def get_sub_classes(base_class):
    """
    To find all subclasses of a given base class.
    """
    sub_classes = []
    # Identify caller's module
    frame = inspect.currentframe()
    module = sys.modules[frame.f_back.f_globals["__name__"]]
    # Iterate over all members of the caller's module
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and issubclass(obj, base_class) and obj.__module__ == module.__name__:
            sub_classes.append(obj)
    return sub_classes


def is_test_environment():
    return TEST_MODE


def db_pool_enabled():
    return USE_DB_POOL
