import subprocess
import os


def checking_folders(*args: str):
    for folder in args:
        os.makedirs(folder, exist_ok=True)
    return


def assembly(distpath: str, workpath: str, specpath: str, name: str):
    checking_folders(distpath, workpath, specpath)
    subprocess.run(["pyinstaller",
                    "--distpath", distpath,
                    "--workpath", workpath,
                    "--specpath", specpath,
                    "--name", name,
                    "--optimize", "2",
                    "--uac-admin",
                    "--onefile",
                    "--strip",
                    "main.py"])
    return


def main():
    assembly("./compilation_data/bin",
             "./compilation_data/tmp",
             "./compilation_data/spec",
             "ald_user_adder")
    return


if __name__ == "__main__":
    main()
