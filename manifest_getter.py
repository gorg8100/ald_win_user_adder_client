import urllib.request
import json
import random
from typing import Any


class Command:
    condition: dict
    ctype: str
    local_groups: list[str]

    def __init__(self, command: dict):
        self.parse_command(command)

    def parse_command(self, command: dict):
        self.condition = command["condition"]
        self.ctype = command["ctype"]
        self.local_groups = command["local_groups"]


class JsonManifest:
    obj_filter: dict
    users: list[dict[str, Any]]
    groups: list[dict[str, Any]]
    commands: list[Command]

    def __init__(self, urls: list[str]):
        self.get_manifest(urls)

    def get_manifest(self, sources: list[str]):
        random.shuffle(sources)
        row_data = None
        for source in sources:
            if source.startswith("http"):
                row_data = try_get_json_from_url(source)
            else:
                row_data = try_get_json_from_file(source)
        if isinstance(row_data, Exception):
            raise ConnectionError(f"Unable to retrieve JSON manifest, error: {row_data}")
        json_data = json.loads(row_data)
        self.obj_filter = json_data["obj_filter"]
        self.users = json_data["users"]
        self.groups = json_data["groups"]
        self.commands = []
        for command in json_data["commands"]:
            self.commands.append(Command(command))


def try_get_json_from_url(url: str) -> str | Exception:
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
        text = response.read().decode('utf-8')
        return text
    except Exception as err:
        return err


def try_get_json_from_file(path: str) -> str | Exception:
    try:
        with open('file.txt', 'r', encoding='utf-8') as f:
            text = f.read()
        return text
    except Exception as err:
        return err
