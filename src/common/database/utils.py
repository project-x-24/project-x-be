from peewee import *
from peewee import callable_
import numpy as np


_clone_set = lambda s: set(s) if s else set()


def model_to_dict(
    model,
    recurse=True,
    backrefs=False,
    only=None,
    exclude=None,
    seen=None,
    extra_attrs=None,
    fields_from_query=None,
    max_depth=None,
    manytomany=False,
):
    """
    Convert a model instance (and any related objects) to a dictionary.

    :param bool recurse: Whether foreign-keys should be recursed.
    :param bool backrefs: Whether lists of related objects should be recursed.
    :param only: A list (or set) of field instances indincating which fields
        should be included.
    :param exclude: A list (or set) of field instances that should be
        excluded from the dictionary.
    :param list extra_attrs: Names of model instance attributes or methods
        that should be included.
    :param SelectQuery fields_from_query: Query that was source of model. Take
        fields explicitly selected by the query and serialize them.
    :param int max_depth: Maximum depth to recurse, value <= 0 means no max.
    :param bool manytomany: Process many-to-many fields.
    """
    max_depth = -1 if max_depth is None else max_depth
    if max_depth == 0:
        recurse = False

    only = _clone_set(only)
    extra_attrs = _clone_set(extra_attrs)
    should_skip = lambda n: (n in exclude) or (only and (n not in only))

    if fields_from_query is not None:
        for item in fields_from_query._returning:
            if isinstance(item, Field):
                only.add(item)
            elif isinstance(item, Alias):
                extra_attrs.add(item._alias)

    data = {}
    exclude = _clone_set(exclude)
    seen = _clone_set(seen)
    exclude |= seen
    model_class = type(model)

    if manytomany:
        for name, m2m in model._meta.manytomany.items():
            if should_skip(name):
                continue

            exclude.update((m2m, m2m.rel_model._meta.manytomany[m2m.backref]))
            for fkf in m2m.through_model._meta.refs:
                exclude.add(fkf)

            accum = []
            for rel_obj in getattr(model, name):
                accum.append(
                    model_to_dict(
                        rel_obj,
                        recurse=recurse,
                        backrefs=backrefs,
                        only=only,
                        exclude=exclude,
                        max_depth=max_depth - 1,
                    )
                )
            data[name] = accum

    for field in model._meta.sorted_fields:
        if should_skip(field):
            continue

        field_data = model.__data__.get(field.name)
        if isinstance(field, ForeignKeyField) and recurse:
            if field_data is not None:
                seen.add(field)
                rel_obj = getattr(model, field.name)
                field_data = model_to_dict(
                    rel_obj,
                    recurse=recurse,
                    backrefs=backrefs,
                    only=only,
                    exclude=exclude,
                    seen=seen,
                    max_depth=max_depth - 1,
                )
            else:
                field_data = None

        data[field.name] = field_data

    if extra_attrs:
        for attr_name in extra_attrs:
            attr = getattr(model, attr_name)
            if callable_(attr):
                data[attr_name] = attr()
            else:
                data[attr_name] = attr

    if backrefs and recurse:
        for foreign_key, rel_model in model._meta.backrefs.items():
            if foreign_key.backref == "+":
                continue
            descriptor = getattr(model_class, foreign_key.backref)
            if descriptor in exclude or foreign_key in exclude:
                continue
            if only and (descriptor not in only) and (foreign_key not in only):
                continue

            accum = []
            exclude.add(foreign_key)
            related_query = getattr(model, foreign_key.backref)

            for rel_obj in related_query:
                accum.append(
                    model_to_dict(
                        rel_obj,
                        recurse=recurse,
                        backrefs=backrefs,
                        only=only,
                        exclude=exclude,
                        max_depth=max_depth - 1,
                    )
                )

            data[foreign_key.backref] = accum

    return data


def convert_object_to_dict(model_instance, exclude=None) -> dict:
    """
    Converts a peewee model instance to a dict of named col to values

    :param model_instance:
    :param exclude:
    :return:
    """
    model_dict = model_to_dict(
        model_instance, backrefs=False, recurse=False, manytomany=False, exclude=exclude
    )

    for k, v in model_dict.items():
        if isinstance(v, np.integer):
            model_dict[k] = int(v)

        elif isinstance(v, np.floating):
            model_dict[k] = float(v)

        elif isinstance(v, np.ndarray):
            model_dict[k] = v.tolist()

    return model_dict
