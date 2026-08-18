import subprocess
from typing import Union, Iterable
from hashlib import blake2s
import tempfile
import os


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


def split_filter(data: str) -> Iterable[str]:
    return filter(lambda x: bool(x), data.split("\n"))


class PowershellScript:
    tmp_file_path: str
    tmp_file = None
    script_hash: str
    hash_salt: bytes

    def __init__(self, script: str):
        enc_script = script.encode()
        self.tmp_file = tempfile.NamedTemporaryFile(suffix='.ps1', delete=False)
        self.tmp_file.write(enc_script)
        self.tmp_file_path = self.tmp_file.name
        self.tmp_file.close()
        self.hash_salt = os.urandom(blake2s.SALT_SIZE)
        self.script_hash = blake2s(enc_script, salt=self.hash_salt).hexdigest()

    def check_hash(self):
        with open(self.tmp_file_path, 'rb') as f:
            text: bytes = f.read()
        text_hash = blake2s(text, salt=self.hash_salt).hexdigest()
        if text_hash != self.script_hash:
            raise ValueError("the script hash did not match")

    def do(self, **kwargs: str) -> str:
        self.check_hash()
        command = ["powershell",
                   "-NoProfile",
                   "-ExecutionPolicy", "Bypass",
                   "-WindowStyle", "Hidden",
                   "-File", self.tmp_file_path]
        for key, value in kwargs.items():
            command.append(f"-{key}")
            command.append(value)
        return do_command(command)

    def as_iterable(self, **kwargs: str) -> Iterable[str]:
        return split_filter(self.do(**kwargs))

    def as_list(self, **kwargs: str) -> list[str]:
        return list(self.as_iterable(**kwargs))

    def as_set(self, **kwargs: str) -> set[str]:
        return set(self.as_iterable(**kwargs))

    def close(self):
        if os.path.exists(self.tmp_file_path):
            os.remove(self.tmp_file_path)

    def __del__(self):
        self.close()


class OsCommands:
    powershell_scripts = {
        "get_group_users": PowershellScript(
            'param($groupName) ([ADSI]"WinNT://./$groupName,group").Members() | '
            'ForEach-Object { $sidBytes = $_.GetType().InvokeMember("objectSid", "GetProperty", $null, $_, $null); '
            'if ($sidBytes) { [System.Security.Principal.SecurityIdentifier]::new($sidBytes, 0).Value } }'
        ),
        "add_local_group": PowershellScript(
            'param($groupName, $description) New-LocalGroup -Name $groupName -Description $description'
        ),
        "add_local_group_member": PowershellScript(
            'param($groupName, $member) Add-LocalGroupMember -Group $groupName -Member $member'
        ),
        "del_local_group": PowershellScript(
            'param($groupName) Remove-LocalGroup -Name $groupName'
        ),
        "del_local_group_member": PowershellScript(
            'param($groupName, $member) Remove-LocalGroupMember -Group $groupName -Member $member'
        )
    }

    def __enter__(self) -> OsCommands:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for script in self.powershell_scripts.values():
            script.close()

    @staticmethod
    def get_local_groups() -> set[str]:
        return set(split_filter(do_command(["powershell", "-Command", "(Get-LocalGroup).Name"])))

    def get_group_members(self, group_name: str) -> set[str]:
        return self.powershell_scripts["get_group_users"].as_set(groupName=group_name)

    def add_local_group(self, group_name: str, description: str):
        self.powershell_scripts["add_local_group"].do(groupName=group_name, description=description)

    def add_local_group_member(self, group_name: str, member: str):
        self.powershell_scripts["add_local_group_member"].do(groupName=group_name, member=member)

    def del_local_group(self, group_name: str):
        self.powershell_scripts["del_local_group"].do(groupName=group_name)

    def del_local_groups(self, names: Iterable[str]):
        for name in names:
            self.del_local_group(name)

    def del_local_group_member(self, group_name: str, member: str):
        self.powershell_scripts["del_local_group_member"].do(groupName=group_name, member=member)

    def del_local_group_members(self, group_name: str, members: Iterable[str]):
        for member in members:
            self.del_local_group_member(group_name, member)
