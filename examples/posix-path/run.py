#!/usr/bin/env python3
"""Real Python stdlib oracle vs JavaScript successor. No network or external installs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import posixpath
import random
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("sre", ROOT / "skills/software-resynthesis/scripts/sre.py")
sre = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sre)


def run(workspace):
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js 18+ is required for the JavaScript successor; no automatic installation")
    sre.initialize(workspace, "Python posixpath.normpath: Unicode string paths", "Portable JavaScript")
    workspace = Path(workspace)
    paths = ["", ".", "..", "/", "//", "///", "////", "//a/../b", "a/../../b", "/../../a",
             "a//b/./c/..", "../a/..", "文件/../背包", "a\\b/../c", "a/.../b", "a/", " /../x"]
    rng = random.Random(4217)
    pieces = ["a", "b", "..", ".", "", "文件", "x y", "..."]
    paths.extend('/'.join(rng.choice(pieces) for _ in range(rng.randrange(1, 15))) for _ in range(400))
    source_values = [posixpath.normpath(p) for p in paths]
    def successor(mutant=False):
        command = [node, str(HERE / "runner.mjs")] + (["--mutant"] if mutant else [])
        response = subprocess.run(command, input=json.dumps(paths), text=True, capture_output=True,
                                  timeout=30, check=True)
        values = json.loads(response.stdout)
        if not isinstance(values, list) or len(values) != len(paths) or not all(isinstance(v, str) for v in values):
            raise ValueError("Invalid successor output")
        return values
    values = successor()
    mutant_values = successor(True)
    build_hash = hashlib.sha256((HERE / "normalize.mjs").read_bytes() + (HERE / "runner.mjs").read_bytes()).hexdigest()
    def capture(kind, build, result):
        return {"schema_version": 1, "scenario": "posix-normalize", "provenance": {
            "kind": kind, "build": build, "adapter": "posix-path-example-v1"}, "steps": [
                {"action": {"normalize": path}, "result": {"value": value}, "state": {"stateless": True}}
                for path, value in zip(paths, result)]}
    source_path = workspace / "runs/source.json"
    successor_path = workspace / "runs/successor.json"
    mutant_path = workspace / "runs/mutant.json"
    sre.write_new(source_path, capture("source-runtime", f"CPython {platform.python_version()}", source_values))
    sre.write_new(successor_path, capture("successor-runtime", build_hash, values))
    sre.write_new(mutant_path, capture("successor-runtime", build_hash + ":--mutant", mutant_values))
    report_path = workspace / "runs/comparison.json"
    report = sre.compare(source_path, successor_path, report_path)
    sre.write_new(report_path, report)
    mutant_report_path = workspace / "runs/mutant-comparison.json"
    mutant_report = sre.compare(source_path, mutant_path, mutant_report_path)
    sre.write_new(mutant_report_path, mutant_report)
    node_version = subprocess.run([node, "--version"], text=True, capture_output=True, check=True, timeout=10).stdout.strip()
    target_pass = values == source_values and not mutant_report["passed"]
    sre.write_new(workspace / "runs/target.json", {
        "schema_version": 1, "passed": target_pass, "environment": f"{platform.system()} / Node {node_version}",
        "command": "node examples/posix-path/runner.mjs (JSON input on stdin)",
        "assertions": [f"{len(paths)} observed outputs match the running stdlib oracle",
                       "Deliberate double-leading-slash regression is detected"],
        "scope": "Node execution of portable module; browser and full-application acceptance not tested"})
    project_path = workspace / "project.json"
    project = sre.read(project_path)
    project.update({"request": "Validate a small lexical POSIX string-path operation across Python and JavaScript",
                    "features": [{"id": "normpath", "description": "Lexically normalize Unicode POSIX path strings",
                                  "mode": "preserve", "status": "verified" if target_pass else "implementing",
                                  "acceptance": ["posix-normalize", "node-execution"]}],
                    "validations": [
                        {"id": "posix-normalize", "kind": "differential", "status": "passed" if report["passed"] else "failed",
                         "features": ["normpath"], "artifact": "runs/comparison.json"},
                        {"id": "node-execution", "kind": "target", "status": "passed" if target_pass else "failed",
                         "features": ["normpath"], "artifact": "runs/target.json"}],
                    "stage": "validation", "next_action": "Review the limited scope; this is not PZ or a full application benchmark."})
    project_path.write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")
    result = sre.check(workspace)
    print(json.dumps({"cases": len(paths), "differential_passed": report["passed"],
                      "mutant_detected": not mutant_report["passed"], "acceptance": result}, indent=2))
    return 0 if result["recorded_acceptance"] and not mutant_report["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, help="New output directory; must not exist")
    args = parser.parse_args()
    try:
        sys.exit(run(args.workspace))
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
