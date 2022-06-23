from app.apis import mongo
from time import perf_counter


class DResponse:
    """A template response for the API"""

    __slots__ = [
        "code",
        "message",
        "ok",
        "result",
        "time_taken",
        "title",
        "description",
    ]

    def __json__(self):
        return {
            "code": self.code,
            "message": self.message,
            "ok": self.ok,
            "result": self.result,
            "time_taken": self.time_taken,
            "title": self.title,
            "description": self.description,
        }

    def __init__(
        self,
        code: int = 200,
        message: str = "Success.",
        ok: bool = True,
        result=None,
        init_time: float = 0,
        extra_title: str = "",
    ):
        self.code: int = code
        self.message: str = message
        self.ok: bool = ok
        self.result = result
        self.time_taken: float = perf_counter() - init_time
        title: str = mongo.config["app"].get("title", "Dester")
        if extra_title != "":
            title += " | " + extra_title
        self.title: str = title
        self.description: str = mongo.config["app"].get("description", "Dester")
