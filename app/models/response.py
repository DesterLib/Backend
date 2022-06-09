from time import perf_counter

class DResponse:
    __slots__ = [
        "code",
        "message",
        "ok",
        "result",
        "time_taken",
    ]

    def __dict__(self):
        return {
            "code": self.code,
            "message": self.message,
            "ok": self.ok,
            "result": self.result,
            "time_taken": self.time_taken,
        }

    def __init__(self, code: int = 200, message: str = "Success.", ok: bool = True, result = None, init_time: float = 0):
        self.code: int = code
        self.message: str = message
        self.ok: bool = ok
        self.result = result
        self.time_taken: float = perf_counter() - init_time
