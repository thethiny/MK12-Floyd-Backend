# Generated by https://quicktype.io
from typing import Any
from src.models.common import (
    from_int,
    from_str,
    to_class,
)

class Body:
    pass

    def __init__(self, ) -> None:
        pass

    @staticmethod
    def from_dict(obj: Any) -> 'Body':
        assert isinstance(obj, dict)
        return Body()

    def to_dict(self) -> dict:
        result: dict = {}
        return result


class HydraError:
    code: int
    msg: str
    hydra_error: int
    relying_party_error: int
    body: Body

    def __init__(self, code: int, msg: str, hydra_error: int, relying_party_error: int, body: Body) -> None:
        self.code = code
        self.msg = msg
        self.hydra_error = hydra_error
        self.relying_party_error = relying_party_error
        self.body = body

    @staticmethod
    def from_dict(obj: Any) -> 'HydraError':
        assert isinstance(obj, dict)
        code = from_int(obj.get("code"))
        msg = from_str(obj.get("msg"))
        hydra_error = from_int(obj.get("hydra_error"))
        relying_party_error = from_int(obj.get("relying_party_error"))
        body = Body.from_dict(obj.get("body"))
        return HydraError(code, msg, hydra_error, relying_party_error, body)

    def to_dict(self) -> dict:
        result: dict = {}
        result["code"] = from_int(self.code)
        result["msg"] = from_str(self.msg)
        result["hydra_error"] = from_int(self.hydra_error)
        result["relying_party_error"] = from_int(self.relying_party_error)
        result["body"] = to_class(Body, self.body)
        return result


def hydra_error_from_dict(s: Any) -> HydraError:
    return HydraError.from_dict(s)


def hydra_error_to_dict(x: HydraError) -> Any:
    return to_class(HydraError, x)
