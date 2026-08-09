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

    def get_manifest(self, urls: list[str]):
        random.shuffle(urls)
        json_data = None
        for url in urls:
            json_data = try_get_json_from_url(url)
        if isinstance(json_data, Exception):
            raise ConnectionError(f"Unable to retrieve JSON manifest, error: {json_data}")
        self.obj_filter = json_data["obj_filter"]
        self.users = json_data["users"]
        self.groups = json_data["groups"]
        self.commands = []
        for command in json_data["commands"]:
            self.commands.append(Command(command))


def try_get_json_from_url(url: str) -> dict | Exception:
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
        text = response.read().decode('utf-8')
        json_data = json.loads(text)
        return json_data
    except Exception as err:
        return err
