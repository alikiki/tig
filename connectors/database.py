import os
import json

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
                
        return data

    def _get(self, key: str, store: dict):
        try:
            return store[key]
        except KeyError:
            raise KeyError(f"Key {key} not found in database")
    
    def set(self, path, value, overwrite=False):
        path = [component for component in path.split("/") if component]
        with open(self.main, "r") as f:
            full_data = json.load(f)
            data = full_data
            for i, component in enumerate(path[:-1]):
                data = self._get(component, data)

            if not overwrite:
                if path[-1] in data:
                    return
            
            data[path[-1]] = {} if value is None else value
        
        with open(self.main, "w") as f:
            json.dump(full_data, f)
        return full_data
    
    def serialize_data(self, data):
        return data.decode('utf-8') 
    
    def deserialize_data(self, data):
        return data.encode('utf-8')
                
    
    def show(self):
        with open(self.main, "r") as f:
            return json.load(f)