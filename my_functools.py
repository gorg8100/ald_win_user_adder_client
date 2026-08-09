import subprocess
from typing import Union


def powershell_command(command: str, inp: str = None, check_code: bool = True,
                       ret_code: bool = False, capture_output: bool = True) -> Union[str, tuple[int, str], None]:
    result = subprocess.run("powershell.exe " + command, text=True, shell=True, input=inp,
                            capture_output=capture_output)
    if check_code and result.returncode != 0:
        raise RuntimeError(f"Command {command} failed, with exit code {result.returncode} and msg:"
                           f"\n{result.stderr}")
    if capture_output:
        if ret_code:
            return result.returncode, result.stdout
        else:
            return result.stdout
    return None
