from typing import Literal, Any
from os_commands_worker import OsCommands


def get_name_prefix(g_type: Literal["user", "group"]):
    if g_type == "user":
        return "ALD-User-"
    return "ALD-Group-"


def get_fullname(g_type: Literal["user", "group"], name: str) -> str:
    return get_name_prefix(g_type) + name


def difference_win_groups(g_type: Literal["user", "group"], names: set[str], current_local_groups: set[str]) \
        -> set[str]:
    prefix = get_name_prefix(g_type)
    filtered_win_groups = set(filter(lambda x: x.startswith(prefix), current_local_groups))
    return filtered_win_groups - names


def del_extraneous_ald_objects(g_type: Literal["user", "group"], objects: list[dict[str, Any]],
                               current_local_groups: set[str], os_commands: OsCommands):
    objects_names = set(map(lambda x: get_fullname(g_type, x["name"]), objects))
    extra_groups = difference_win_groups(g_type, objects_names, current_local_groups)
    os_commands.del_local_groups(extra_groups)
    return


def set_up_ald_users(users: list[dict[str, Any]], os_commands: OsCommands):
    current_local_groups = os_commands.get_local_groups()
    del_extraneous_ald_objects("user", users, current_local_groups, os_commands)
    for user in users:
        fullname = get_fullname("user", user["name"])
        if fullname not in current_local_groups:
            os_commands.add_local_group(fullname, "Domain user")
            os_commands.add_local_group_member(fullname, user["sec_id"])
    return


def get_group_members(groups: list[dict[str, Any]], users: list[dict[str, Any]]) -> dict[str, set[str]]:
    groups_names = set(map(lambda x: x["name"], groups))
    group_members: dict[str, set[str]] = {}
    for user in users:
        for user_group in user["groups"]:
            if user_group in groups_names:
                if user_group in group_members:
                    group_members[user_group].add(user["sec_id"])
                else:
                    group_members[user_group] = {user["sec_id"]}
    return group_members


def set_up_ald_groups(groups: list[dict[str, Any]], group_members: dict[str, set[str]], os_commands: OsCommands):
    current_local_groups = os_commands.get_local_groups()
    del_extraneous_ald_objects("group", groups, current_local_groups, os_commands)
    for group in groups:
        fullname = get_fullname("group", group["name"])
        if fullname not in current_local_groups:
            os_commands.add_local_group(fullname, "Domain group")
    for group in group_members:
        set_up_ald_group_members(group, group_members[group], os_commands)
    return


def set_up_ald_group_members(group_name: str, members: set[str], os_commands: OsCommands):
    group_fullname = get_fullname("group", group_name)
    current_members = os_commands.get_local_group_members(group_fullname)
    extra_members = current_members - members
    os_commands.del_local_group_members(group_fullname, extra_members)
    for member in members:
        if member not in current_members:
            os_commands.add_local_group_member(group_fullname, member)
    return


def get_sid_prefix(sid: str) -> str:
    return sid[:sid.rfind("-")]


def get_all_sid_prefix(users: list[dict[str, Any]]) -> set[str]:
    return set(map(lambda usr: get_sid_prefix(usr["sec_id"]), users))


def check_sid_prefix(sid: str, sid_prefixes: set[str]) -> bool:
    for prefix in sid_prefixes:
        if sid.startswith(prefix):
            return True
    return False


def set_up_local_groups_members(group_members: dict[str, set[str]], users: list[dict[str, Any]],
                                os_commands: OsCommands):
    win_groups = os_commands.get_local_groups()
    ald_sid_prefixes = get_all_sid_prefix(users)
    for win_group in win_groups:
        if win_group.startswith(get_name_prefix("group")) or win_group.startswith(get_name_prefix("user")):
            continue
        if win_group in group_members:
            set_up_local_group_members(win_group, group_members[win_group], ald_sid_prefixes, os_commands)
        else:
            del_ald_users_local_group(win_group, ald_sid_prefixes, os_commands)
    return


def set_up_local_group_members(win_group: str, relevant_members: set[str], ald_sid_prefixes: set[str],
                               os_commands: OsCommands):
    current_members = os_commands.get_local_group_members(win_group)
    for member in current_members:
        if check_sid_prefix(member, ald_sid_prefixes):
            if member not in relevant_members:
                os_commands.del_local_group_member(win_group, member)
    for member in relevant_members:
        if member not in current_members:
            os_commands.add_local_group_member(win_group, member)
    return


def del_ald_users_local_group(win_group: str, ald_sid_prefixes: set[str], os_commands: OsCommands):
    all_members = os_commands.get_local_group_members(win_group)
    for member in all_members:
        if check_sid_prefix(member, ald_sid_prefixes):
            os_commands.del_local_group_member(win_group, member)
    return
