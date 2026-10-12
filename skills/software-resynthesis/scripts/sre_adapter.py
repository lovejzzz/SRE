"""Bounded, explicit adapter execution. This is a runner, not a sandbox."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from sre_common import require, read, write_new, digest, text, object_v1, difference


def stop_owned(process):
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, check=False)
    if process.poll() is None:
        process.kill()
    process.wait(timeout=10)


def run_adapter(manifest_path, request_path, output_dir, timeout=30):
    manifest_path, request_path = Path(manifest_path).resolve(), Path(request_path).resolve()
    manifest, request = read(manifest_path), read(request_path)
    object_v1(manifest)
    object_v1(request)
    require(manifest.get("kind") in ("source-runtime", "successor-runtime", "synthetic"), "Invalid adapter kind")
    for key in ("id", "build"):
        require(text(manifest.get(key)), f"Adapter missing {key}")
    argv = manifest.get("argv")
    require(isinstance(argv, list) and argv and all(text(x) for x in argv), "argv must be a nonempty string list")
    require(type(timeout) in (int, float) and 0 < timeout <= 3600, "Timeout must be >0 and <=3600 seconds")
    require(text(request.get("scenario")) and isinstance(request.get("fixture"), dict), "Invalid scenario/fixture")
    actions = request.get("actions")
    require(isinstance(actions, list) and actions and all(isinstance(a, dict) and a for a in actions), "Invalid actions")
    files = manifest.get("build_files")
    require(isinstance(files, list) and files and all(text(p) for p in files), "Explicit build_files required")
    for name in files:
        require((manifest_path.parent / name).resolve().is_file(),
                f"Missing build file: {name} (resolved relative to {manifest_path.parent})")
    pinned = {p: digest((manifest_path.parent / p).resolve()) for p in files}
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / "manifest.json", manifest)
    write_new(output / "request.json", request)
    command = [part.replace("{python}", sys.executable).replace("{adapter_dir}", str(manifest_path.parent))
               .replace("{run_dir}", str(output)) for part in argv]
    report = {"schema_version": 1, "adapter": manifest["id"], "status": "running", "passed": False,
              "argv": command, "manifest_sha256": digest(output / "manifest.json"),
              "request_sha256": digest(output / "request.json"), "build_files": pinned}
    write_new(output / "started.json", report)
    started = time.monotonic()
    process = None
    try:
        # Logs go to disk, not unbounded in-memory communicate buffers. Only selected
        # inputs are sent; original installations are not copied or modified by this runner.
        with (output / "request.json").open("rb") as stdin, (output / "stdout.json").open("wb") as stdout, (output / "stderr.log").open("wb") as stderr:
            process = subprocess.Popen(command, cwd=output, stdin=stdin, stdout=stdout, stderr=stderr,
                                       shell=False, start_new_session=(os.name == "posix"),
                                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            report["owned_pid"] = process.pid
            write_new(output / "process.json", {"pid": process.pid, "argv": command,
                                                "note": "PID alone is not safe identity for later cleanup; verify ownership/start time."})
            try:
                report["exit_code"] = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                stop_owned(process)
                report["status"] = "timeout"
                raise ValueError("Adapter timed out; owned process terminated; diagnostics retained")
        require(report["exit_code"] == 0, "Adapter exited unsuccessfully")
        require((output / "stdout.json").stat().st_size <= 16 * 1024 * 1024, "Adapter response exceeds 16 MiB")
        response = read(output / "stdout.json")
        object_v1(response)
        require(response.get("scenario") == request["scenario"], "Adapter scenario mismatch")
        lifecycle = response.get("lifecycle")
        require(isinstance(lifecycle, dict) and lifecycle.get("reset") is True and lifecycle.get("finalize") is True,
                "Adapter must acknowledge reset and finalize")
        steps = response.get("steps")
        require(isinstance(steps, list) and len(steps) == len(actions), "Adapter omitted/added actions")
        for action, step in zip(actions, steps):
            require(isinstance(step, dict) and difference(action, step.get("action")) is None, "Adapter changed action")
            for field in ("result", "state"):
                require(isinstance(step.get(field), dict) and step[field], f"Missing adapter {field}")
        require(all(digest((manifest_path.parent / p).resolve()) == h for p, h in pinned.items()),
                "Pinned build file changed during execution")
        captured = {"schema_version": 1, "scenario": request["scenario"], "steps": steps,
                    "provenance": {"kind": manifest["kind"], "build": manifest["build"],
                                   "adapter": manifest["id"], "build_files": pinned,
                                   "request_sha256": report["request_sha256"]}}
        write_new(output / "trace.json", captured)
        report.update({"status": "completed", "passed": True, "trace_sha256": digest(output / "trace.json")})
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        if process is not None and process.poll() is None:
            stop_owned(process)
        if report["status"] == "running":
            report["status"] = "failed"
        report["error"] = str(exc)
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 6)
        write_new(output / "run.json", report)
    return report
