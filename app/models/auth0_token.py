from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class Token:
    access_token: str
    token_expiry: Optional[str] = None

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> "Token":
        return cls(**json)

    def to_json(self) -> Dict[str, Any]:
        return self.__dict__()

    def __dict__(self):
        return {"access_token": self.access_token, "token_expiry": self.token_expiry}