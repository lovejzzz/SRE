import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from research_fixture import prepare

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/software-resynthesis/scripts"))
import sre_research as research


class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "evidence").mkdir()
        self.project = {"schema_version": 1, "features": [{"id": "layers", "description": "Layers",
                        "mode": "preserve", "acceptance": ["layers-test"]}], "validations": []}
        self.data = prepare(self.root, self.project, research)

    def save(self):
        (self.root / "research.json").write_text(json.dumps(self.data), encoding="utf-8")
        (self.root / "project.json").write_text(json.dumps(self.project), encoding="utf-8")

    def question(self):
        self.data["questions"] = [{"id": "q", "feature": "layers", "question": "Which behavior?",
            "blocking": True, "impact": 5, "hypotheses": [{"id": "a", "explanation": "A"}, {"id": "b", "explanation": "B"}],
            "experiments": [{"id": "useless", "cost": 1, "input": {"x": 0}, "predictions": {"a": 0, "b": 0}},
                            {"id": "probe", "cost": 1, "input": {"x": 2}, "predictions": {"a": 1, "b": 2}}]}]
        self.save()
        self.project["research_baseline"] = "questions-baseline.json"
        self.save()
        research.seal(self.root, self.project["research_baseline"])

    def observe(self, value, kind="source-runtime"):
        file = self.root / "evidence/observation.json"
        file.write_text(json.dumps({"schema_version": 1, "provenance": {"kind": kind, "build": "fixture-only"},
                                    "value": value}), encoding="utf-8")
        self.data["questions"][0]["experiments"][1]["observation"] = {"artifact": "evidence/observation.json", "pointer": "/value"}
        self.save()

    def test_complete_declared_surfaces(self):
        self.assertTrue(research.audit(self.root)["research_ready"])

    def test_unmapped_menu_item_blocks(self):
        path = self.root / "evidence/docs.json"
        data = json.loads(path.read_text())
        data["items"].append({"id": "hidden", "label": "Hidden feature"})
        path.write_text(json.dumps(data))
        result = research.audit(self.root)
        self.assertFalse(result["research_ready"])
        self.assertTrue(any("Unmapped" in p for p in result["problems"]))

    def test_scope_shrink_detected(self):
        self.data["scope"]["description"] = "Smaller scope"
        self.save()
        self.assertFalse(research.audit(self.root)["research_ready"])

    def test_original_request_change_requires_review(self):
        self.project["request"] = "Silently changed goal"
        self.save()
        self.assertFalse(research.audit(self.root)["research_ready"])

    def test_deleted_feature_detected(self):
        self.project["features"] = []
        self.save()
        with self.assertRaises(ValueError):
            research.audit(self.root)

    def test_missing_required_surface_blocks(self):
        self.data["surveys"][0].update(status="unavailable", reason="No access")
        self.save()
        self.assertFalse(research.audit(self.root)["research_ready"])

    def test_cannot_overwrite_baseline(self):
        with self.assertRaises(FileExistsError):
            research.seal(self.root, "research-baseline.json")

    def test_dependency_cycle_rejected(self):
        self.project["features"][0]["depends_on"] = ["layers"]
        self.save()
        with self.assertRaises(ValueError):
            research.audit(self.root)

    def test_full_claim_cannot_exclude_discovered_feature(self):
        self.data["scope"]["claim"] = "full"
        path = self.root / "evidence/docs.json"
        data = json.loads(path.read_text())
        data["items"].append({"id": "hidden", "label": "Hidden", "disposition": "excluded", "reason": "Too hard"})
        path.write_text(json.dumps(data))
        self.save()
        self.assertTrue(any("excludes" in p for p in research.audit(self.root)["problems"]))

    def test_plan_prefers_discriminating_experiment(self):
        self.question()
        result = research.audit(self.root)
        self.assertFalse(result["research_ready"])
        self.assertEqual(["probe"], [x["experiment"] for x in result["next_experiments"]])

    def test_observation_resolves_without_invalidating_plan_baseline(self):
        self.question()
        self.observe(2)
        result = research.audit(self.root)
        self.assertTrue(result["research_ready"])
        self.assertEqual(["b"], result["questions"][0]["surviving_hypotheses"])

    def test_contradiction_blocks(self):
        self.question()
        self.observe(99)
        self.assertEqual("contradiction", research.audit(self.root)["questions"][0]["status"])

    def test_synthetic_observation_not_source_evidence(self):
        self.question()
        self.observe(2, "synthetic")
        with self.assertRaises(ValueError):
            research.audit(self.root)

    def test_rewriting_prediction_after_observation_is_stale(self):
        self.question()
        self.observe(99)
        self.data["questions"][0]["experiments"][1]["predictions"]["b"] = 99
        self.save()
        self.assertFalse(research.audit(self.root)["research_ready"])

    def test_unresolved_version_cannot_be_sealed(self):
        self.data["scope"]["source_build"] = "unresolved"
        self.save()
        with self.assertRaises(ValueError):
            research.seal(self.root, "other.json")
