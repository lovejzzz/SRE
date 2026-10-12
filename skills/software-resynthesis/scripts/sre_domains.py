"""Domain checks on explicit normalized artifacts; never execute embedded commands."""
import math
from pathlib import Path
from sre_common import require, read, digest, text, object_v1, difference


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def raster(data):
    object_v1(data)
    for field in ("width", "height", "channels"):
        require(type(data.get(field)) is int and data[field] > 0, f"Invalid raster {field}")
    require(data["channels"] <= 4, "Raster supports 1..4 channels")
    for field in ("color_space", "alpha_mode"):
        require(text(data.get(field)), f"Raster requires {field}")
    pixels = data.get("samples")
    require(isinstance(pixels, list) and len(pixels) == data["width"] * data["height"] * data["channels"],
            "Raster sample count does not match dimensions")
    require(all(number(x) and 0 <= x <= 1 for x in pixels), "Samples must be finite normalized numbers in [0,1]")
    return pixels


def evaluate(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    manifest = read(manifest_path)
    object_v1(manifest)
    kind = manifest.get("kind")
    require(kind in ("image", "roundtrip", "interaction", "performance"), "Unknown domain validator")
    require(text(manifest.get("rationale")), "Acceptance policy needs a rationale fixed before testing")
    hashes = {}
    def load(field):
        value = manifest.get(field)
        require(text(value) and not Path(value).is_absolute(), f"Expected relative {field} path")
        path = (manifest_path.parent / value).resolve()
        require(path.is_relative_to(manifest_path.parent), "Domain input escapes manifest directory")
        data = read(path)
        hashes[field] = {"path": value, "sha256": digest(path)}
        return data
    details = {}
    if kind == "image":
        a, b = load("reference"), load("candidate")
        left, right = raster(a), raster(b)
        metadata = ("width", "height", "channels", "color_space", "alpha_mode")
        same_metadata = all(a[k] == b[k] for k in metadata)
        limits = manifest.get("limits")
        require(isinstance(limits, dict) and all(number(limits.get(k)) and 0 <= limits[k] <= 1
                                               for k in ("max_abs", "rmse")), "Invalid image thresholds")
        details["metadata_match"] = same_metadata
        passed = False
        if same_metadata:
            errors = [abs(x - y) for x, y in zip(left, right)]
            details.update({"max_abs": max(errors), "rmse": math.sqrt(sum(x*x for x in errors) / len(errors))})
            passed = details["max_abs"] <= limits["max_abs"] and details["rmse"] <= limits["rmse"]
    elif kind == "roundtrip":
        original, reopened = load("original"), load("reopened")
        for data in (original, reopened):
            object_v1(data)
            require(isinstance(data.get("document"), dict) and data["document"], "Empty semantic document snapshot")
        delta = difference(original["document"], reopened["document"])
        details["first_difference"] = delta
        passed = delta is None
    elif kind == "interaction":
        a, b = load("reference"), load("candidate")
        for data in (a, b):
            object_v1(data)
            require(text(data.get("scenario")) and isinstance(data.get("steps"), list) and data["steps"], "Invalid interaction trace")
            for step in data["steps"]:
                require(isinstance(step, dict) and all(isinstance(step.get(k), dict) and step[k]
                                                       for k in ("action", "result", "state")), "Invalid interaction step")
        delta = difference({"scenario": a["scenario"], "steps": a["steps"]},
                           {"scenario": b["scenario"], "steps": b["steps"]})
        details["first_difference"] = delta
        passed = delta is None
    else:
        measurements = load("measurements")
        object_v1(measurements)
        samples = measurements.get("latency_ms")
        require(isinstance(samples, list) and samples and all(number(x) and x >= 0 for x in samples), "Invalid latency samples")
        require(number(measurements.get("peak_memory_mb")) and measurements["peak_memory_mb"] >= 0, "Invalid memory measurement")
        limits = manifest.get("limits")
        require(isinstance(limits, dict) and all(number(limits.get(k)) and limits[k] > 0
                                               for k in ("p95_ms", "peak_memory_mb")), "Invalid performance budgets")
        require(type(limits.get("min_samples")) is int and limits["min_samples"] >= 2, "Set minimum samples >=2")
        require(text(manifest.get("device")) and text(measurements.get("device")), "Device identity required")
        require(text(manifest.get("workload")) and text(measurements.get("workload")), "Workload identity required")
        p95 = sorted(samples)[math.ceil(.95 * len(samples)) - 1]
        details = {"p95_ms": p95, "peak_memory_mb": measurements["peak_memory_mb"], "samples": len(samples),
                   "device_match": manifest["device"] == measurements["device"],
                   "workload_match": manifest["workload"] == measurements["workload"]}
        passed = (details["device_match"] and details["workload_match"] and len(samples) >= limits["min_samples"]
                  and p95 <= limits["p95_ms"] and measurements["peak_memory_mb"] <= limits["peak_memory_mb"])
    return {"schema_version": 1, "kind": "domain-report", "domain": kind, "passed": passed,
            "manifest": manifest_path.name, "manifest_sha256": digest(manifest_path),
            "inputs": hashes, "details": details,
            "limitation": "Checks supplied observations; capture authenticity and policy suitability require review."}


def verify_report(report_path):
    report_path = Path(report_path).resolve()
    recorded = read(report_path)
    object_v1(recorded)
    name = recorded.get("manifest")
    require(text(name) and Path(name).name == name, "Domain report/manifest must share a directory")
    manifest = (report_path.parent / name).resolve()
    require(manifest.is_relative_to(report_path.parent), "Domain manifest escapes report directory")
    actual = evaluate(manifest)
    require(difference(recorded, actual) is None, "Stale or modified domain report")
    require(actual["passed"], "Domain acceptance failed")
    return actual
