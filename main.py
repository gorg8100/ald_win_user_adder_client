from typing import Any
from configuration_getter import Configuration
from manifest_getter import JsonManifest, Command
from preprocess_condition import pre_process_condition
from condition_handler import process_condition
from win_groups_funcs import set_up_ald_users, set_up_ald_groups, set_up_local_groups_members, get_group_members


def get_local_group_members(commands: list[Command], local_data: dict, users: list[dict[str, Any]],
                            groups: list[dict[str, Any]], group_members: dict[str, set[str]]) -> dict[str, set[str]]:
    local_group_members: dict[str, set[str]] = {}
    for command in commands:
        if command.ctype != "add_to_local_group":
            continue
        command.condition = pre_process_condition(command.condition, local_data)
        users_sec_id = list(map(lambda usr: usr["sec_id"],
                                filter(lambda usr: process_condition("user", usr, command.condition, local_data), users)
                                ))
        f_groups = list(map(lambda group: group["name"],
                            filter(lambda group: process_condition("group", group, command.condition, local_data),
                                   groups)
                            ))
        for local_group in command.local_groups:
            if local_group not in local_group_members:
                local_group_members[local_group] = set()
            local_group_members[local_group].update(users_sec_id)
            for f_group in f_groups:
                if f_group in group_members:
                    local_group_members[local_group].update(group_members[f_group])
    return local_group_members


def main():
    settings = Configuration("settings.json")
    manifest = JsonManifest(settings.sources)
    manifest.obj_filter = pre_process_condition(manifest.obj_filter, settings.local_data)
    # print(manifest.obj_filter)
    users = list(
        filter(lambda usr: process_condition("user", usr, manifest.obj_filter, settings.local_data),
               manifest.users))
    groups = list(
        filter(lambda group: process_condition("group", group, manifest.obj_filter, settings.local_data),
               manifest.groups))
    # print(users)
    # print(groups)
    try:
        set_up_ald_users(users)
        # print("================")
        group_members = get_group_members(groups, users)
        # print(group_members)
        set_up_ald_groups(groups, group_members)
        local_group_members = get_local_group_members(manifest.commands, settings.local_data, users, groups, group_members)
        # print(local_group_members)
        set_up_local_groups_members(local_group_members, users)
    except Exception as err:
        print(type(err).__name__, err)
        input()
    return


if __name__ == '__main__':
    main()
