import os
import re
import yaml
import hashlib
from typing import Any, List

class FileManager:

    def __init__(self):
        super().__init__()

    def find(self, path:str, regex:str='.*') -> List[str]:
        for root, dirs, files in sorted(os.walk(path), reverse=False):
            for name in sorted(files):
                full_path = os.path.join(root, name)
                if re.match(regex, full_path):
                    yield full_path

    def read(self, path:str) -> str:
        data = ""
        with open(path, 'r') as read_file:
            for line in read_file:
                data += str(line)

            return data

    def read_yaml(self, path: str) -> Any:
        with open(path, 'r') as read_file:
            return yaml.safe_load(read_file)


    def sha256(self, path: str) -> str:
        bytes = ""
        with open(path, 'rb') as read_file:
            bytes = read_file.read()
            readable_hash = hashlib.sha256(bytes).hexdigest();

            return readable_hash

    def create(self, path:str, content:str=""):
        output_file = open(path, "w")
        if (len(content) > 0):
            n = output_file.write(content)
        output_file.close()

    def append(self, path:str, content:str=""):
        output_file = open(path, "a")
        if (len(content) > 0):
            n = output_file.write(content)
        output_file.close()
