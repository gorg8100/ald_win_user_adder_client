import re
from condition_handler import calc_fields_do_op, calc_fields_op_val


def prep_and(condition: dict, local_data: dict) -> dict | bool:
    conditions: list[dict] = condition["conditions"]
    new_conditions: list[dict] = []
    for condition in conditions:
        new_condition = pre_process_condition(condition, local_data)
        if new_condition is False:
            return False
        if new_condition is True:
            continue
        new_conditions.append(new_condition)
    if not new_conditions:
        return True
    return {"cond_type": "and","conditions": new_conditions}


def prep_or(condition: dict, local_data: dict) -> dict | bool:
    conditions: list[dict] = condition["conditions"]
    new_conditions: list[dict] = []
    for condition in conditions:
        new_condition = pre_process_condition(condition, local_data)
        if new_condition is True:
            return True
        if new_condition is False:
            continue
        new_conditions.append(new_condition)
    if not new_conditions:
        return False
    return {"cond_type": "or","conditions": new_conditions}


def prep_not(condition: dict, local_data: dict) -> dict | bool:
    if isinstance(condition["condition"], bool):
        return not condition["condition"]
    return condition


def fields_op_descr_val_comp(descr_val: dict) -> bool:
    if descr_val["source"] == "computer":
        return True
    return False


def prep_fields_op(condition: dict, local_data: dict) -> dict | bool:
    if fields_op_descr_val_comp(condition["l_v"]) or fields_op_descr_val_comp(condition["r_v"]):
        l_v = calc_fields_op_val({}, condition["l_v"], local_data)
        r_v = calc_fields_op_val({}, condition["r_v"], local_data)
        return calc_fields_do_op(l_v, r_v, condition)
    return condition


def prep_regexp(condition: dict, local_data: dict) -> dict | bool:
    if condition["source"] == "computer":
        if condition["field"] not in local_data:
            return False
        return bool(re.fullmatch(condition["value"], local_data[condition["field"]]))
    return condition


def pre_process_condition(condition: dict, local_data: dict) -> dict | bool:
    resolver_dict = {"or": prep_or, "and": prep_and, "not": prep_not, "fields_op": prep_fields_op,
                     "regexp": prep_regexp}
    condition_type: str = condition["cond_type"]
    if condition_type not in resolver_dict:
        return condition
    return resolver_dict[condition_type](condition, local_data)
