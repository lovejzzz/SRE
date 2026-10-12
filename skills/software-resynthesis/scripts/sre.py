#!/usr/bin/env python3
"""SRE workspace and evidence helpers. Python 3.10+, standard library only."""
import argparse
import json
import os
from pathlib import Path
import sys
from sre_common import require, read, write_new, digest, text, object_v1, difference
import sre_research
import sre_domains
from sre_adapter import run_adapter


def trace(path):
    data = read(path)
    object_v1(data)
    require(text(data.get("scenario")), "Missing trace scenario")
    provenance = data.get("provenance")
    require(isinstance(provenance, dict), "Missing trace provenance")
    require(text(provenance.get("kind")) and provenance["kind"] in {"source-runtime", "successor-runtime", "synthetic"},
            "Invalid provenance kind")
    for key in ("build", "adapter"):
        require(text(provenance.get(key)), f"Missing provenance {key}")
    require(isinstance(data.get("steps"), list) and data["steps"], "Empty or invalid steps")
    for i, step in enumerate(data["steps"]):
        require(isinstance(step, dict), f"Invalid step {i}")
        for key in ("action", "result", "state"):
            require(isinstance(step.get(key), dict) and step[key], f"Empty or invalid {key} in step {i}")
    return data


def compare(left, right, report_path):
    left, right, report_path = Path(left).resolve(), Path(right).resolve(), Path(report_path).resolve()
    require(left != right, "Source and successor must be different trace files")
    a, b = trace(left), trace(right)
    delta = difference({"scenario": a["scenario"], "steps": a["steps"]},
                       {"scenario": b["scenario"], "steps": b["steps"]})
    def entry(path, data):
        return {"path": os.path.relpath(path, report_path.parent), "sha256": digest(path),
                "provenance": data["provenance"]}
    return {"schema_version": 1, "kind": "comparison", "passed": delta is None,
            "scenario": a["scenario"], "source": entry(left, a), "successor": entry(right, b),
            "first_difference": delta}


def inside(root, base, relative):
    require(text(relative) and not Path(relative).is_absolute(), "Artifact must use a relative path")
    path = (base / relative).resolve()
    require(path.is_relative_to(root), "Artifact escapes workspace (including symlinks)")
    require(path.is_file(), f"Missing artifact: {relative}")
    return path


def indexed(items, label):
    require(isinstance(items, list), f"Invalid {label} list")
    result = {}
    for item in items:
        require(isinstance(item, dict) and text(item.get("id")), f"Invalid {label} record")
        require(item["id"] not in result, f"Duplicate {label} ID: {item['id']}")
        result[item["id"]] = item
    return result


def check(workspace):
    root = Path(workspace).resolve()
    project = read(root / "project.json")
    object_v1(project)
    for key in ("request", "source", "target"):
        require(text(project.get(key)), f"Missing project {key}")
    features = indexed(project.get("features"), "feature")
    validations = indexed(project.get("validations"), "validation")
    require(features, "No features recorded")
    unknowns = indexed(project.get("unknowns"), "unknown")
    problems = []
    for item in unknowns.values():
        require(type(item.get("blocking")) is bool and text(item.get("description")), "Invalid unknown")
        if item["blocking"]:
            problems.append(f"Blocking unknown: {item['id']}")
    decisions = project.get("decisions")
    require(isinstance(decisions, list), "Invalid decisions")
    accepted = {}
    for vid, validation in validations.items():
        require(text(validation.get("kind")) and validation["kind"] in {"differential", "target", "domain", "synthetic"}, f"Invalid kind: {vid}")
        require(text(validation.get("status")) and validation["status"] in {"passed", "failed", "pending"}, f"Invalid status: {vid}")
        links = validation.get("features")
        require(isinstance(links, list) and links and all(text(x) and x in features for x in links),
                f"Invalid feature links: {vid}")
        if validation["status"] != "passed":
            continue
        try:
            path = inside(root, root, validation.get("artifact"))
            if validation["kind"] == "differential":
                report = read(path)
                object_v1(report)
                require(report.get("kind") == "comparison", "Not a comparison report")
                require(isinstance(report.get("source"), dict) and isinstance(report.get("successor"), dict),
                        "Invalid report inputs")
                source = inside(root, path.parent, report["source"].get("path"))
                successor = inside(root, path.parent, report["successor"].get("path"))
                actual = compare(source, successor, path)
                require(difference(report, actual) is None, "Stale or modified comparison report")
                require(actual["passed"], "Differential mismatch")
                require(actual["source"]["provenance"]["kind"] == "source-runtime" and
                        actual["successor"]["provenance"]["kind"] == "successor-runtime",
                        "Synthetic/wrong provenance cannot establish fidelity")
                require(actual["scenario"] == vid, "Scenario does not match validation ID")
            elif validation["kind"] == "domain":
                recorded = read(path)
                object_v1(recorded)
                manifest = inside(root, path.parent, recorded.get("manifest"))
                require(manifest == inside(root, root, validation.get("policy")), "Domain report does not match pinned policy")
                sre_domains.verify_report(path)
            elif validation["kind"] == "target":
                result = read(path)
                object_v1(result)
                require(result.get("passed") is True, "Target test did not pass")
                for key in ("command", "environment"):
                    require(text(result.get(key)), f"Missing target {key}")
                require(isinstance(result.get("assertions"), list) and result["assertions"] and
                        all(text(x) for x in result["assertions"]), "Missing target assertions")
            accepted[vid] = validation
        except (ValueError, OSError) as exc:
            problems.append(f"{vid}: {exc}")
    for fid, feature in features.items():
        mode = feature.get("mode")
        require(text(mode) and mode in {"preserve", "adapt", "extend"}, f"Invalid feature mode: {fid}")
        require(text(feature.get("description")), f"Missing description: {fid}")
        require(text(feature.get("status")) and feature["status"] in {"planned", "researching", "implementing", "blocked", "verified"},
                f"Invalid feature status: {fid}")
        if feature["status"] != "verified":
            problems.append(f"Feature not verified: {fid}")
        required = feature.get("acceptance")
        require(isinstance(required, list) and required and all(text(x) for x in required),
                f"Missing acceptance scenarios: {fid}")
        kinds = set()
        for vid in required:
            v = accepted.get(vid)
            if not v or fid not in v["features"]:
                problems.append(f"{fid}: missing passed acceptance {vid}")
            else:
                kinds.add(v["kind"])
        if not kinds.intersection({"target", "domain"}):
            problems.append(f"{fid}: missing target evidence")
        if mode == "preserve" and "differential" not in kinds:
            problems.append(f"{fid}: missing source-runtime differential evidence")
        if mode != "preserve" and not any(isinstance(d, dict) and d.get("feature") == fid and
                                          text(d.get("rationale")) and text(d.get("acceptance")) for d in decisions):
            problems.append(f"{fid}: missing designed-change decision")
    behavior_ready = not problems
    try:
        research = sre_research.audit(root)
        problems.extend(research["problems"])
    except (ValueError, OSError) as exc:
        research = {"research_ready": False, "claim": "unestablished"}
        problems.append(f"Research audit: {exc}")
    return {"schema_version": 1, "recorded_acceptance": not problems, "behavior_ready": behavior_ready,
            "research_ready": research["research_ready"], "claim": research["claim"], "problems": problems,
            "limitation": "Acceptance within sealed discovery scope only; not proof of undiscovered-feature absence or authentic captures."}


def initialize(path, source, target):
    require(text(source) and text(target), "Source and target must be nonempty")
    root = Path(path)
    root.mkdir(parents=True, exist_ok=False)
    for name in ("evidence", "runs", "implementation", "checkpoints"):
        (root / name).mkdir()
    write_new(root / "project.json", {
        "schema_version": 1, "request": f"Rebuild {source} for {target}",
        "source": source, "target": target, "stage": "discovery", "features": [],
        "validations": [], "decisions": [], "unknowns": [],
        "next_action": "Preserve the user's full request; discover and pin the source and target."})
    write_new(root / "research.json", {"schema_version": 1,
        "scope": {"claim": "milestone", "description": source, "source_build": "unresolved",
                  "target": target, "features": []}, "surveys": [], "questions": []})
    (root / ".gitignore").write_text("evidence/\nruns/\ncheckpoints/\nproject.json\nresearch*.json\n", encoding="utf-8")
    return {"workspace": str(root.resolve()), "stage": "discovery"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Create a new private workspace without overwriting")
    init.add_argument("workspace")
    init.add_argument("--source", required=True)
    init.add_argument("--target", required=True)
    fp = sub.add_parser("fingerprint", help="SHA-256 fingerprint of an explicitly selected file")
    fp.add_argument("file")
    cmp = sub.add_parser("compare", help="Compare normalized traces; report must not already exist")
    cmp.add_argument("source")
    cmp.add_argument("successor")
    cmp.add_argument("--out", required=True)
    gate = sub.add_parser("check", help="Check recorded acceptance obligations")
    gate.add_argument("workspace")
    seal = sub.add_parser("seal", help="Freeze reviewed discovery scope; refuses overwrite")
    seal.add_argument("workspace")
    seal.add_argument("--out", default="research-baseline.json")
    audit = sub.add_parser("audit", help="Audit discovery coverage and experimental evidence")
    audit.add_argument("workspace")
    plan = sub.add_parser("plan", help="Rank discriminating experiments without executing them")
    plan.add_argument("workspace")
    adapter = sub.add_parser("run-adapter", help="Execute a reviewed adapter command in a new run directory")
    adapter.add_argument("manifest")
    adapter.add_argument("request")
    adapter.add_argument("--out", required=True)
    adapter.add_argument("--timeout", type=float, default=30)
    domain = sub.add_parser("domain-check", help="Evaluate images, semantic roundtrips, interactions, or performance")
    domain.add_argument("manifest")
    domain.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        code = 0
        if args.command == "init":
            result = initialize(args.workspace, args.source, args.target)
        elif args.command == "fingerprint":
            result = {"file": str(Path(args.file).resolve()), "sha256": digest(args.file)}
        elif args.command == "compare":
            result = compare(args.source, args.successor, args.out)
            write_new(args.out, result)
            code = 0 if result["passed"] else 1
        elif args.command == "seal":
            result = sre_research.seal(args.workspace, args.out)
        elif args.command == "audit":
            result = sre_research.audit(args.workspace)
            code = 0 if result["research_ready"] else 1
        elif args.command == "plan":
            root, project, research = sre_research.inputs(args.workspace)
            sre_research.inventory(root, project, research)
            result = sre_research.experiments(root, project, research)
        elif args.command == "run-adapter":
            result = run_adapter(args.manifest, args.request, args.out, args.timeout)
            code = 0 if result["passed"] else 1
        elif args.command == "domain-check":
            require(Path(args.out).resolve().parent == Path(args.manifest).resolve().parent,
                    "Domain report must share manifest directory")
            result = sre_domains.evaluate(args.manifest)
            write_new(args.out, result)
            code = 0 if result["passed"] else 1
        else:
            result = check(args.workspace)
            code = 0 if result["recorded_acceptance"] else 1
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return code
    except (ValueError, OSError, RecursionError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
