import os
import ujson as json
from copy import deepcopy
from typing import Any, Dict, Optional

class Database:
    def __init__(self, file_path: str):
        self.path = file_path
        if not os.path.exists(file_path):
            self.data = {}
        else:
            try:
                self.data = json.load(open(self.path))
            except ValueError:
                os.remove(file_path)
                self.data = {}
        self.save()
    
    @property
    def frozen_data(self) -> Dict[str, Any]:
        return deepcopy(self.data)

    def get(self, key: str, default = None, pop: bool = False) -> Optional[Any]:
        if self.data.get(key):
            value = self.data.pop(key) if pop else self.data.get(key, default)
            self.save()
            return value
    
    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()

    def add_to_col(
        self, col_name: str, data: Dict[Any, Any]
    ) -> None:
        if not self.data.get(col_name):
            self.data[col_name] = {}
        self.data[col_name].update(data)
        self.save()

    def get_from_col(
        self, col_name: str, key: str, pop: bool = True
    ) -> Optional[Dict[Any, Any]]:
        if self.data.get(col_name) and self.data[col_name].get(key):
            if not pop:
                return self.data[col_name][key]
            value = self.data[col_name].pop(key)
            self.save()
            return value
        return None

    def save(self):
        with open(self.path, "w+") as _file:
            json.dump(self.data, _file, indent=4)
            _file.close()
    
    def __len__(self):
        return len(self.data)