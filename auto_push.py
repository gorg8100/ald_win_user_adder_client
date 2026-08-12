from build_project import assembly
import subprocess
import shutil
import os
import urllib.request
import json


def obtain_consent(msg: str) -> bool:
    while True:
        confirmation = input(f"{msg} (y/n):")
        while confirmation not in ["y", "n"]:
            confirmation = input("Значение ответа должно быть y/n:")
        if confirmation == "y":
            return True
        return False


def input_loop(msg: str) -> str:
    while True:
        data = input(msg)
        print(f"Вы ввели:{data}")
        confirmation = input("Вы уверены? (y/n):")
        while confirmation not in ["y", "n"]:
            confirmation = input("Значение ответа должно быть y/n:")
        if confirmation == "y":
            return data


def repository_push():
    subprocess.run("git add .")
    commit_text = input_loop("Введите текст коммита:")
    subprocess.run(['git', 'commit', '-m', commit_text])
    subprocess.run("git push -u origin main")
    return


def get_latest_data(repos: str) -> tuple[str, str]:
    req = urllib.request.Request(f"https://api.github.com/repos/{repos}/releases")
    response = urllib.request.urlopen(req)
    text = response.read().decode('utf-8')
    json_data = json.loads(text)
    latest_release = json_data[0]
    latest_tag = latest_release["tag_name"]
    latest_title = latest_release["name"]
    return latest_tag, latest_title


def make_release(distpath: str, workpath: str, specpath: str, name: str, repos: str):
    building_folder = distpath[:distpath.rfind("/")]
    if os.path.exists(building_folder):
        shutil.rmtree(building_folder)
    print("*****[Начало сборки]*****")
    assembly(distpath, workpath, specpath, name)
    print("*****[Сборка окончена]*****")
    latest_tag, latest_title = get_latest_data(repos)
    print(f"Последний тег: {latest_tag}")
    tag = input_loop("Введите тег релиза:")
    print(f"Последний загаловок: {latest_title}")
    title = input_loop("Введите заголовок релиза:")
    subprocess.run(["git", "release", "create", tag, f"{distpath}/{name}.zip",
                    "--generate-notes",
                    "--title", title])
    return


def main():
    if obtain_consent("Отправить коммит?"):
        repository_push()
    if obtain_consent("Отправить релиз?"):
        make_release("./compilation_data/bin",
                     "./compilation_data/tmp",
                     "./compilation_data/spec",
                     "ald_user_adder",
                     "gorg8100/ald_win_user_adder_client")
    return


if __name__ == "__main__":
    main()
