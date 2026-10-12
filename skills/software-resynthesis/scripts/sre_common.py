"""Shared strict JSON and file utilities."""
import hashlib
import json
import math
from pathlib import Path

def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def finite(value, depth=0):
    require(depth <= 128, "JSON nesting exceeds maximum depth 128")
    if isinstance(value, float):
        require(math.isfinite(value), "Non-finite JSON number")
    elif isinstance(value, dict):
        for item in value.values():
            finite(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            finite(item, depth + 1)


def read(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except RecursionError as exc:
        raise ValueError("JSON nesting exceeds maximum depth 128") from exc
    finite(data)
    return data


def write_new(path, data):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def text(value):
    return isinstance(value, str) and bool(value.strip())


def object_v1(data):
    require(isinstance(data, dict), "Expected JSON object")
    require(type(data.get("schema_version")) is int and data["schema_version"] == 1,
            "Unsupported schema_version; expected integer 1")


def difference(left, right, path="$"):
    """Strict JSON types: false != 0 and 1 != 1.0. Object key order is irrelevant."""
    if type(left) is not type(right):
        return {"path": path, "reason": "type", "expected": left, "actual": right}
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return {"path": path, "reason": "keys", "expected": sorted(left), "actual": sorted(right)}
        for key in sorted(left):
            found = difference(left[key], right[key], path + "[" + json.dumps(key) + "]")
            if found:
                return found
    elif isinstance(left, list):
        if len(left) != len(right):
            return {"path": path, "reason": "length", "expected": len(left), "actual": len(right)}
        for i, (a, b) in enumerate(zip(left, right)):
            found = difference(a, b, f"{path}[{i}]")
            if found:
                return found
    elif left != right:
        return {"path": path, "reason": "value", "expected": left, "actual": right}
    return None


