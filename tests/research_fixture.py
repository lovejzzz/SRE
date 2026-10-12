"""Synthetic discovery records for helper tests; not real source research."""
import json


def prepare(root, project, module, baseline="research-baseline.json"):
    research = {"schema_version": 1, "scope": {"claim": "milestone", "description": "test scope",
                "source_build": "fixture-only", "target": "fixture", "features": [f["id"] for f in project["features"]]},
                "surveys": [], "questions": []}
    for kind in ("docs", "runtime"):
        name = f"evidence/{kind}.json"
        (root / name).write_text(json.dumps({"schema_version": 1, "source_build": "fixture-only", "source": "synthetic test fixture",
            "scope_note": "unit test only", "items": [{"id": f["id"], "label": f["description"], "feature": f["id"]} for f in project["features"]]}), encoding="utf-8")
        research["surveys"].append({"id": kind, "kind": kind, "required": True, "status": "complete", "artifact": name})
    project["research_baseline"] = baseline
    (root / "project.json").write_text(json.dumps(project), encoding="utf-8")
    (root / "research.json").write_text(json.dumps(research), encoding="utf-8")
    module.seal(root, baseline)
    return research
