import os
import json
from base64 import b64decode, b64encode

"""
Because the main `tig.py` deals with bytes instead of strings, this file is responsible for the encoding/decoding schemes. 
"""

class JsonDatabase():
    def __init__(self, main):
        self.main = main
    
    def get(self, path, no_encoding=False):
        path = [component for component in path.split("/") if component]
        with open(self.main, "r") as f:
            data = json.load(f)
            for i, component in enumerate(path): 
                try:
                    data = self._get(component, data)
                except KeyError:
                    raise KeyError(f"Search stopped at {component} in {path[:i+1]}")
        
        if not isinstance(data, dict):
            return self._deserialize_data(data) if not no_encoding else data

        return data

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
        data = self.get(path, no_encoding=True)
        return isinstance(data, dict)
        
    def is_file(self, path):
        return not self.is_folder(path)
    
    def get_type(self, path):
        return "folder" if self.is_folder(path) else "file"
    
    def clear(self):
        with open(self.main, "w") as f:
            json.dump({}, f)

    def abspath(self, path):
        return os.path.abspath(path)
    
    def relpath(self, path, base):
        return os.path.relpath(path, base)
    
    def get_metadata(self, path):
        metadata_path = os.path.join(".metadata", path)
        return self.get(metadata_path)
    

class FileDatabase():
    def __init__(self, main):
        self.main = main

    def get(self, path, no_encoding=False):
        full_path = os.path.join(self.main, path)
        if self.is_folder(path):
            data = {}
            for filename in os.listdir(full_path):
                file_path = os.path.join(full_path, filename)
                with open(file_path, "rb") as f:
                    data[filename] = f.read()
            return data
        else:
            read_mode = "r" if no_encoding else "rb"
            with open(full_path, read_mode) as f:
                data = f.read()
                return self._deserialize_data(data)
    
    def set(self, path, value, overwrite=False, no_encoding=False):
        full_path = os.path.join(self.main, path)
        print(full_path)

        if os.path.exists(full_path) and not overwrite:
            return
        
        if value is None:
            os.mkdir(full_path)
            return
        
        write_mode = "w" if no_encoding else "wb"
        data_to_write = self._serialize_data(value) if not no_encoding else value
        with open(full_path, write_mode) as f:
            f.write(data_to_write)
    
    def _serialize_data(self, data):
        return data
    
    def _deserialize_data(self, data):
        return data
    
    def is_folder(self, path):
        return os.path.isdir(os.path.join(self.main, path))
    
    def is_file(self, path):
        return os.path.isfile(os.path.join(self.main, path))
    
    def get_type(self, path):
        return "folder" if self.is_folder(path) else "file"
    
    def abspath(self, path):
        return os.path.abspath(os.path.join(self.main, path))
    
    def relpath(self, path, base): 
        return os.path.relpath(path, base)
    
    def show(self):
        return
    
    def clear(self):
        for root, dirs, files in os.walk(os.path.join(self.main, ".git")):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))

    def get_metadata(self, path):
        metadata = os.stat(path)
        return {
            "ctime": (int(metadata.st_ctime), metadata.st_ctime_ns % 10**9),
            "mtime": (int(metadata.st_mtime), metadata.st_mtime_ns % 10**9),
            "dev": metadata.st_dev,
            "ino": metadata.st_ino,
            "mode_type": 0b1000,
            "mode_perms": 0o644,
            "uid": metadata.st_uid,
            "gid": metadata.st_gid,
            "fsize": metadata.st_size,
        }