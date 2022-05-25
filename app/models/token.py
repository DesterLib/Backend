from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Token:
    access_token: str
    token_expiry: Optional[str] = None

    @classmethod
    def from_json(cls, json: Dict[str, Any]) -> "Token":
        return cls(**json)
