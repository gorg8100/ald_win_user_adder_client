import json


class Configuration:
    log_file_path: str
    sources: list[str]
    local_data: dict

    def __init__(self, file_path: str):
        self.parse_configuration(file_path)

    def parse_configuration(self, file_path: str):
        with open(file_path, encoding="utf-8") as file:
            json_settings = json.load(file)
        self.log_file_path = json_settings["log_file_path"]
        self.sources = json_settings["sources"]
        self.local_data = json_settings["local_data"]
