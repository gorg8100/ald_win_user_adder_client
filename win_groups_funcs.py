from typing import Literal, Union, Iterator, Any
import subprocess
import re
import tempfile
import os
import unittest


def do_command(command: list[str], inp: str = None, check_code: bool = True, ret_code: bool = False) \
        -> Union[str, tuple[int, str]]:
    print(command)
    result = subprocess.run(command, text=True, input=inp, capture_output=True, shell=False)
    if check_code and result.returncode != 0:
        raise RuntimeError(f"Command {" ".join(command)} failed, with exit code {result.returncode} and msg:"
                           f"\n{result.stderr}")
    if ret_code:
        return result.returncode, result.stdout
    else:
        return result.stdout


def escape_powershell_argument_script(s: str) -> str:
    if not s:
        raise ValueError("Empty strings are not supported")
    if any(ord(c) < 32 for c in s):
        raise ValueError("ASCII control codes are not supported")
    return "'" + s.replace("'", "''") + "'"


def get_name_prefix(g_type: Literal["user", "group"]):
    if g_type == "user":
        return "ALD-User-"
    return "ALD-Group-"


def get_fullname(g_type: Literal["user", "group"], name: str) -> str:
    return get_name_prefix(g_type) + name


def check_win_group(fullname: str) -> bool:
    code, _ = do_command(["net", "localgroup", fullname], check_code=False, ret_code=True)
    if code != 0:
        return False
    return True


def get_win_groups() -> Iterator[str]:
    win_groups = do_command(["net", "localgroup"]).split("\n")
    win_groups = filter(lambda x: bool(x) and x[0] == "*", win_groups)
    win_groups = map(lambda x: x[1:], win_groups)
    return win_groups


def difference_win_groups(g_type: Literal["user", "group"], names: set[str]) -> set[str]:
    prefix = get_name_prefix(g_type)
    filtered_win_groups = set(filter(lambda x: x.startswith(prefix), get_win_groups()))
    return filtered_win_groups - names


def del_win_groups(names: set[str]):
    for name in names:
        do_command(["net", "localgroup", name, "/delete"])


def del_extraneous_ald_objects(g_type: Literal["user", "group"], objects: list[dict[str, Any]]):
    objects_names = set(map(lambda x: get_fullname(g_type, x["name"]), objects))
    extra_groups = difference_win_groups(g_type, objects_names)
    del_win_groups(extra_groups)
    return


def check_sid(sid: str):
    if not bool(re.fullmatch(r'[A-Za-z0-9-]+', sid)):
        raise ValueError("Invalid sid format")


def get_sid_win_group(fullname: str) -> str:
    escaped_fullname = escape_powershell_argument_script(fullname)
    # pwsh_c = f'powershell.exe -Command (Get-LocalGroup -Name {escaped_fullname}).SID.Value'
    # gr_sid = do_command(["runas", "/trustlevel:0x20000", pwsh_c])
    gr_sid = do_command(["powershell.exe", "-Command", f"(Get-LocalGroup -Name {escaped_fullname}).SID.Value"])
    return gr_sid.split("\n")[0]


def get_win_group_members(gr_sid: str) -> set[str]:
    print("{")
    # data = do_command(["powershell.exe", "-Command", f'(Get-LocalGroupMember -SID "{gr_sid}").SID.Value'])
    pwsh_script = (f'$groupSID="{gr_sid}";'
                   '$group=Get-WmiObject -Class Win32_Group|Where-Object{$_.SID -eq $groupSID};'
                   'if($group){$groupName=$group.Name;([ADSI]"WinNT://./$groupName,group").Members()'
                   '|ForEach-Object{$sidBytes=$_.GetType().InvokeMember("objectSid","GetProperty",$null,$_,$null);'
                   'if($sidBytes){[System.Security.Principal.SecurityIdentifier]::new($sidBytes,0).Value}}}'
                   'else{throw "Группа с SID $groupSID не найдена."}')
    data = do_command(["powershell.exe", "-Command", pwsh_script])
    print(data)
    members = set(filter(lambda x: bool(x), data.split("\n")))
    print(members)
    print("}")
    return members


def add_user_win_group(fullname: str, sec_id: str, existence_check: bool, gr_sid: str = None):
    if gr_sid is None:
        gr_sid = get_sid_win_group(fullname)
    check_sid(sec_id)
    if existence_check:
        members = get_win_group_members(gr_sid)
        if sec_id in members:
            return
    do_command(["powershell.exe", "-Command",
                f'Add-LocalGroupMember -SID "{gr_sid}" -Member "{sec_id}"'])
    return


def add_ald_object(g_type: Literal["user", "group"], name: str, sec_id: str = None):
    fullname = get_fullname(g_type, name)
    # print(fullname, check_win_group(fullname))
    if not check_win_group(fullname):
        do_command(["net", "localgroup", fullname, "/add", f'/comment: "Domain {g_type}"'])
        if g_type == "user":
            add_user_win_group(fullname, sec_id, False)
    return


def set_up_ald_users(users: list[dict[str, Any]]):
    del_extraneous_ald_objects("user", users)
    for user in users:
        add_ald_object("user", user["name"], user["sec_id"])
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


def set_up_ald_groups(groups: list[dict[str, Any]], group_members: dict[str, set[str]]):
    del_extraneous_ald_objects("group", groups)
    for group in groups:
        add_ald_object("group", group["name"])
    for group in group_members:
        set_up_ald_group_members(group, group_members[group])
    return


def del_user_win_group(sid: str, gr_sid: str):
    check_sid(sid)
    do_command(["powershell.exe", "-Command", f'Remove-LocalGroupMember -SID "{gr_sid}" -Member "{sid}"'])
    return


def del_users_win_group(sids: set[str], gr_sid: str):
    for sid in sids:
        del_user_win_group(sid, gr_sid)
    return


def set_up_ald_group_members(group_name: str, members: set[str]):
    group_fullname = get_fullname("group", group_name)
    gr_sid = get_sid_win_group(group_fullname)
    print(">>", gr_sid, group_fullname)
    current_members = get_win_group_members(gr_sid)
    print(current_members)
    extra_members = current_members - members
    del_users_win_group(extra_members, gr_sid)
    for member in members:
        if member not in current_members:
            add_user_win_group(group_fullname, member, False, gr_sid)
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


def warning_msg(func_name: str, msg: str):
    print("!!!!!!!!!!!!!!!!")
    print(f"[{func_name}]: {msg}")
    print("^^^^^^^^^^^^^^^^")


def set_up_local_groups_members(group_members: dict[str, set[str]], users: list[dict[str, Any]]):
    win_groups = get_win_groups()
    ald_sid_prefixes = get_all_sid_prefix(users)
    for win_group in win_groups:
        if win_group.startswith(get_name_prefix("group")) or win_group.startswith(get_name_prefix("user")):
            continue
        try:
            gr_sid = get_sid_win_group(win_group)
        except Exception as err:
            warning_msg("set_up_local_groups_members", f"local group {win_group} skipped: {err}")
            continue
        if not gr_sid:
            warning_msg("set_up_local_groups_members", f"local group {win_group} skipped: null sid")
            continue
        if win_group in group_members:
            set_up_local_group_members(win_group, group_members[win_group], ald_sid_prefixes, gr_sid)
        else:
            del_ald_users_local_group(win_group, ald_sid_prefixes, gr_sid)
    return


def set_up_local_group_members(win_group: str, relevant_members: set[str], ald_sid_prefixes: set[str], gr_sid: str):
    try:
        current_members = get_win_group_members(gr_sid)
    except Exception as err:
        warning_msg("set_up_local_group_members", f"local group {win_group} skipped, error: {err}")
        return
    for member in current_members:
        if check_sid_prefix(member, ald_sid_prefixes):
            if member not in relevant_members:
                del_user_win_group(member, gr_sid)
    for member in relevant_members:
        if member not in current_members:
            add_user_win_group(win_group, member, False, gr_sid)
    return


def del_ald_users_local_group(win_group: str, ald_sid_prefixes: set[str], gr_sid: str):
    try:
        all_members = get_win_group_members(gr_sid)
    except Exception as err:
        warning_msg("del_ald_users_local_group", f"local group {win_group} skipped, error: {err}")
        return
    for member in all_members:
        if check_sid_prefix(member, ald_sid_prefixes):
            del_user_win_group(member, gr_sid)
    return


class TestGetGroupMembers:
    """Тесты для функции get_group_members."""

    def test_empty_inputs(self):
        """Пустые списки групп и пользователей."""
        assert get_group_members([], []) == {}

    def test_no_users(self):
        """Группы заданы, но нет пользователей — результат пуст."""
        groups = [{"name": "admin"}, {"name": "editor"}]
        assert get_group_members(groups, []) == {}

    def test_users_with_unknown_groups(self):
        """Все группы пользователей отсутствуют в списке groups."""
        groups = [{"name": "a"}]
        users = [
            {"sec_id": "1", "groups": ["x"]},
            {"sec_id": "2", "groups": ["y", "z"]},
        ]
        assert get_group_members(groups, users) == {}

    def test_mixed_groups(self):
        """Часть групп совпадает, часть — нет."""
        groups = [{"name": "g1"}, {"name": "g2"}]
        users = [
            {"sec_id": "u1", "groups": ["g1", "unknown"]},
            {"sec_id": "u2", "groups": ["g2"]},
            {"sec_id": "u3", "groups": ["unknown"]},
        ]
        expected = {
            "g1": {"u1"},
            "g2": {"u2"},
        }
        assert get_group_members(groups, users) == expected

    def test_duplicates_in_user_groups(self):
        """Дубликаты в списке групп пользователя не влияют на множество sec_id."""
        groups = [{"name": "g"}]
        users = [
            {"sec_id": "id1", "groups": ["g", "g", "g"]},
        ]
        assert get_group_members(groups, users) == {"g": {"id1"}}

    def test_multiple_users_with_overlap(self):
        """Несколько пользователей, некоторые состоят в нескольких группах."""
        groups = [{"name": "admins"}, {"name": "users"}, {"name": "guests"}]
        users = [
            {"sec_id": "1", "groups": ["admins", "users"]},
            {"sec_id": "2", "groups": ["users"]},
            {"sec_id": "3", "groups": ["admins", "guests"]},
            {"sec_id": "4", "groups": []},
            {"sec_id": "5", "groups": ["admins", "admins"]},
        ]
        expected = {
            "admins": {"1", "3", "5"},
            "users": {"1", "2"},
            "guests": {"3"},
        }
        assert get_group_members(groups, users) == expected

    def test_groups_without_users(self):
        """Группы, в которых нет ни одного пользователя, не попадают в результат."""
        groups = [{"name": "x"}, {"name": "y"}]
        users = [{"sec_id": "1", "groups": ["x"]}]
        assert get_group_members(groups, users) == {"x": {"1"}}

    def test_same_sec_id_in_different_groups(self):
        """Один пользователь (один sec_id) может входить в несколько групп."""
        groups = [{"name": "a"}, {"name": "b"}]
        users = [{"sec_id": "common", "groups": ["a", "b"]}]
        expected = {"a": {"common"}, "b": {"common"}}
        assert get_group_members(groups, users) == expected
