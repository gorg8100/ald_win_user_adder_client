from typing import Literal
from typing import Any
import re
from unittest import case


def and_condition(obj_type: Literal["user", "group"], obj: dict, condition: dict, local_data: dict) -> bool:
    conditions: list[dict] = condition["conditions"]
    for condition in conditions:
        if not process_condition(obj_type, obj, condition, local_data):
            return False
    return True


def or_condition(obj_type: Literal["user", "group"], obj: dict, condition: dict, local_data: dict) -> bool:
    conditions: list[dict] = condition["conditions"]
    for condition in conditions:
        if process_condition(obj_type, obj, condition, local_data):
            return True
    return False


def not_condition(obj_type: Literal["user", "group"], obj: dict, condition: dict, local_data: dict) -> bool:
    return not process_condition(obj_type, obj, condition["condition"], local_data)


def is_user_condition(obj_type: Literal["user", "group"], obj: dict, condition: dict, local_data: dict) -> bool:
    if obj_type == "user":
        return True
    return False


def is_group_condition(obj_type: Literal["user", "group"], obj: dict, condition: dict, local_data: dict) -> bool:
    if obj_type == "group":
        return True
    return False


class FieldMissing:
    pass


def calc_fields_op_val(obj: dict, descr_val: dict, local_data: dict) -> Any:
    match descr_val["source"]:
        case "const":
            return descr_val["value"]
        case "object":
            if descr_val["field"] in obj:
                return obj[descr_val["field"]]
            return FieldMissing
        case "computer":
            if descr_val["field"] in local_data:
                return local_data[descr_val["field"]]
            return FieldMissing
        case _:
            raise RuntimeError


def calc_fields_do_op(l_v, r_v, condition: dict) -> bool:
    if l_v is FieldMissing or r_v is FieldMissing:
        return False
    match condition["op"]:
        case "<":
            return l_v < r_v
        case ">":
            return l_v > r_v
        case "<=":
            return l_v <= r_v
        case ">=":
            return l_v >= r_v
        case "==":
            return l_v == r_v
        case "!=":
            return l_v != r_v
        case "in":
            return l_v in r_v
        case _:
            raise RuntimeError


def fields_op_condition(obj_type: Literal["user", "group"], obj: dict, condition: dict, local_data: dict) -> bool:
    l_v = calc_fields_op_val(obj, condition["l_v"], local_data)
    r_v = calc_fields_op_val(obj, condition["r_v"], local_data)
    return calc_fields_do_op(l_v, r_v, condition)


def regexp_condition(obj_type: Literal["user", "group"], obj: dict, condition: dict, local_data: dict) -> bool:
    if condition["field"] not in obj:
        return False
    return bool(re.fullmatch(condition["value"], obj[condition["field"]]))


def process_condition(obj_type: Literal["user", "group"], obj: dict | bool, condition: dict, local_data: dict) -> bool:
    if isinstance(obj, dict):
        resolver_dict = {"or": or_condition, "and": and_condition, "not": not_condition, "is_user": is_user_condition,
                         "is_group": is_group_condition, "fields_op": fields_op_condition, "regexp": regexp_condition}
        condition_type: str = condition["cond_type"]
        return resolver_dict[condition_type](obj_type, obj, condition, local_data)
    return obj
