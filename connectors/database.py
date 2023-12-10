import os
import json
from base64 import b64decode, b64encode

"""
Because the main `tig.py` deals with bytes instead of strings, this file is responsible for the encoding/decoding schemes. 
"""

class JsonDatabase():
    def __init__(self, main):
        self.main = main
    
    def get(self, path):
        path = [component for component in path.split("/") if component]
        with open(self.main, "r") as f:
            data = json.load(f)
            for i, component in enumerate(path): 
                try:
                    data = self._get(component, data)
                except KeyError:
                    raise KeyError(f"Search stopped at {component} in {path[:i+1]}")
                
        return self._deserialize_data(data) if not isinstance(data, dict) else data

    def _get(self, key: str, store: dict):
        try:
            return store[key]
        except KeyError:
            raise KeyError(f"Key {key} not found in database")
    
    def set(self, path, value, overwrite=False, no_encoding=False):
        path = [component for component in path.split("/") if component]
        with open(self.main, "r") as f:
            full_data = json.load(f)
            data = full_data
            for i, component in enumerate(path[:-1]):
                data = self._get(component, data)

            if not overwrite:
                if path[-1] in data:
                    return
                
            if value is None:
                data[path[-1]] = {}
            else:
                data[path[-1]] = self._serialize_data(value) if not no_encoding else value
        
        with open(self.main, "w") as f:
            json.dump(full_data, f)
        return full_data
    
    def _serialize_data(self, data):
        return b64encode(data).decode()
    
    def _deserialize_data(self, data):
        return b64decode(data.encode())
                
    
    def show(self):
        with open(self.main, "r") as f:
            return json.load(f)
        
    def is_folder(self, path):
        data = self.get(path)
        return isinstance(data, dict)
        
    def is_file(self, path):
        return not self.is_folder(path)
    
    def get_type(self, path):
        return "folder" if self.is_folder(path) else "file"
    
    def clear(self):
        with open(self.main, "w") as f:
            json.dump({}, f)

class FileDatabase():
    def __init__(self, main):
        self.main = main

    def get(self, path):
        raise NotImplementedError
    
    def set(self, path, value, overwrite=False):
        raise NotImplementedError