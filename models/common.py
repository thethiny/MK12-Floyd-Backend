from datetime import datetime
from typing import Any, List, Dict, TypeVar, Callable, Type, cast
from enum import Enum
import dateutil.parser
T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_str(x: Any) -> str:
    return x


def from_datetime(x: Any) -> datetime:
    return dateutil.parser.parse(x)


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_bool(x: Any) -> bool:
    return x


def from_int(x: Any) -> int:
    return x


def from_none(x: Any) -> Any:
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    try:
        return x.value
    except Exception:
        return x


def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
    if isinstance(x, dict):
        return {k: f(v) for (k, v) in x.items()}
    return {}


def from_float(x: Any) -> float:
    return float(x)


def to_float(x: Any) -> float:
    return x
