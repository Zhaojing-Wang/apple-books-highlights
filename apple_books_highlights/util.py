import os
import re
import pathlib

from typing import List, Dict, Optional, Union, Any, Callable
from jinja2 import Environment, FileSystemLoader

NS_TIME_INTERVAL_SINCE_1970 = 978307200


PATH = pathlib.Path(__file__).resolve().parent / "templates"
TEMPLATE_ENVIRONMENT = Environment(
    autoescape=False,
    loader=FileSystemLoader(str(PATH)),
    trim_blocks=True,
    lstrip_blocks=False,
)


def _parse_epubcfi_offsets(raw: str) -> List[int]:
    parts = raw[8:-1].split(",")
    cfistart = parts[0] + parts[1]

    parts = cfistart.split(":")
    path = parts[0]
    offsets = [int(x[1:]) for x in re.findall(r"(/\d+)", path)]
    if len(parts) > 1:
        try:
            offsets.append(int(parts[1]))
        except ValueError:
            pass
    return offsets


def parse_location(raw: str) -> List[int]:
    if raw is None:
        return []
    if raw.startswith("epubcfi(") and raw.endswith(")"):
        return _parse_epubcfi_offsets(raw)
    numbers = re.findall(r"\d+", raw)
    if numbers:
        return [int(n) for n in numbers]
    return []


def epubcfi_compare(x: List[int], y: List[int]) -> int:
    depth = min(len(x), len(y))
    for d in range(depth):
        if x[d] == y[d]:
            continue
        else:
            return x[d] - y[d]

    return len(x) - len(y)


def query_compare_no_asset_id(x: Dict[str, str], y: Dict[str, str]) -> int:
    return epubcfi_compare(parse_location(x["location"]), parse_location(y["location"]))


def cmp_to_key(mycmp: Callable) -> Any:
    "Convert a cmp= function into a key= function"

    class K:
        def __init__(self, obj: Any, *args: Any) -> None:
            self.obj = obj

        def __lt__(self, other: Any) -> Any:
            return mycmp(self.obj, other.obj) < 0

        def __gt__(self, other: Any) -> Any:
            return mycmp(self.obj, other.obj) > 0

        def __eq__(self, other: Any) -> Any:
            return mycmp(self.obj, other.obj) == 0

        def __le__(self, other: Any) -> Any:
            return mycmp(self.obj, other.obj) <= 0

        def __ge__(self, other: Any) -> Any:
            return mycmp(self.obj, other.obj) >= 0

        def __ne__(self, other: Any) -> Any:
            return mycmp(self.obj, other.obj) != 0

    return K
