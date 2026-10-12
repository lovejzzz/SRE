"""Helper contract tests. Fixture provenance labels are test data, not PZ evidence."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/software-resynthesis/scripts/sre.py"
spec = importlib.util.spec_from_file_location("sre_helper", SCRIPT)
sre = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sre)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        sre.initialize(self.root, "test-only source", "test-only destination")
        self.a = self.root / "runs/source.json"
        self.b = self.root / "runs/successor.json"
        self.report = self.root / "runs/comparison.json"
        self.original = {"schema_version": 1, "scenario": "move",
                         "provenance": {"kind": "source-runtime", "build": "fixture-only", "adapter": "test-v1"},
                         "steps": [{"action": {"move": "water"}, "result": {"ok": True},
                                    "state": {"items": [{"id": "water", "parent": "bag"}]}}]}
        self.successor = copy.deepcopy(self.original)
        self.successor["provenance"]["kind"] = "successor-runtime"
        self.save(self.a, self.original)
        self.save(self.b, self.successor)
        self.save(self.report, sre.compare(self.a, self.b, self.report))
        self.save(self.root / "runs/target.json", {"schema_version": 1, "passed": True,
                  "environment": "fixture", "command": "fixture test", "assertions": ["one item remains"]})
        self.project = sre.read(self.root / "project.json")
        self.project["features"] = [{"id": "inventory", "mode": "preserve", "status": "verified",
                                     "description": "Item identity is conserved", "acceptance": ["move", "ui"]}]
        self.project["validations"] = [
            {"id": "move", "kind": "differential", "status": "passed", "features": ["inventory"],
             "artifact": "runs/comparison.json"},
            {"id": "ui", "kind": "target", "status": "passed", "features": ["inventory"],
             "artifact": "runs/target.json"}]

    def save(self, path, data):
        path.write_text(json.dumps(data), encoding="utf-8")

    def gate(self):
        self.save(self.root / "project.json", self.project)
        return sre.check(self.root)

    def test_complete_recorded_obligations(self):
        self.assertTrue(self.gate()["recorded_acceptance"])

    def test_mutant_loses_item(self):
        self.successor["steps"][0]["state"]["items"] = []
        self.save(self.b, self.successor)
        report = sre.compare(self.a, self.b, self.report)
        self.assertFalse(report["passed"])
        self.assertIn('"items"', report["first_difference"]["path"])
        self.assertFalse(self.gate()["recorded_acceptance"])

    def test_stale_report_detected_even_if_both_traces_changed_equally(self):
        self.original["steps"][0]["result"]["ticks"] = 2
        self.successor["steps"][0]["result"]["ticks"] = 2
        self.save(self.a, self.original)
        self.save(self.b, self.successor)
        self.assertTrue(sre.compare(self.a, self.b, self.report)["passed"])
        self.assertFalse(self.gate()["recorded_acceptance"])

    def test_forged_pass_recomputed(self):
        self.successor["steps"][0]["result"]["ok"] = False
        self.save(self.b, self.successor)
        report = sre.compare(self.a, self.b, self.report)
        report["passed"] = True
        report["first_difference"] = None
        self.save(self.report, report)
        self.assertFalse(self.gate()["recorded_acceptance"])

    def test_synthetic_not_fidelity(self):
        self.original["provenance"]["kind"] = "synthetic"
        self.save(self.a, self.original)
        self.save(self.report, sre.compare(self.a, self.b, self.report))
        self.assertFalse(self.gate()["recorded_acceptance"])

    def test_wrong_scenario(self):
        self.successor["scenario"] = "other"
        self.save(self.b, self.successor)
        self.assertFalse(sre.compare(self.a, self.b, self.report)["passed"])

    def test_extra_step(self):
        self.successor["steps"].append(copy.deepcopy(self.successor["steps"][0]))
        self.save(self.b, self.successor)
        self.assertFalse(sre.compare(self.a, self.b, self.report)["passed"])

    def test_boolean_not_number(self):
        self.assertIsNotNone(sre.difference(False, 0))
        self.assertIsNotNone(sre.difference(1, 1.0))

    def test_object_order_ignored_array_order_preserved(self):
        self.assertIsNone(sre.difference({"x": 1, "y": 2}, {"y": 2, "x": 1}))
        self.assertIsNotNone(sre.difference([1, 2], [2, 1]))

    def test_empty_trace_rejected(self):
        self.original["steps"] = []
        self.save(self.a, self.original)
        with self.assertRaises(ValueError):
            sre.compare(self.a, self.b, self.report)

    def test_empty_observation_rejected(self):
        self.original["steps"][0]["state"] = {}
        self.save(self.a, self.original)
        with self.assertRaises(ValueError):
            sre.trace(self.a)

    def test_ambiguous_json_rejected(self):
        for value in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'):
            self.a.write_text(value)
            with self.assertRaises(ValueError):
                sre.read(self.a)

    def test_init_does_not_overwrite(self):
        before = (self.root / "project.json").read_bytes()
        with self.assertRaises(FileExistsError):
            sre.initialize(self.root, "other", "other")
        self.assertEqual(before, (self.root / "project.json").read_bytes())

    def test_no_empty_project_acceptance(self):
        self.project["features"] = []
        with self.assertRaises(ValueError):
            self.gate()

    def test_unknown_blocks(self):
        self.project["unknowns"] = [{"id": "server", "description": "Remote dependency", "blocking": True}]
        self.assertFalse(self.gate()["recorded_acceptance"])

    def test_enhancement_requires_design_and_target_not_fidelity(self):
        f = self.project["features"][0]
        f["mode"] = "extend"
        f["acceptance"] = ["ui"]
        self.project["validations"] = self.project["validations"][1:]
        self.assertFalse(self.gate()["recorded_acceptance"])
        self.project["decisions"] = [{"feature": "inventory", "rationale": "Add couch co-op",
                                      "acceptance": "Two independent focus owners"}]
        self.assertTrue(self.gate()["recorded_acceptance"])

    def test_target_failure_not_accepted(self):
        result = sre.read(self.root / "runs/target.json")
        result["passed"] = False
        self.save(self.root / "runs/target.json", result)
        self.assertFalse(self.gate()["recorded_acceptance"])

    def test_evidence_must_link_required_feature(self):
        self.project["validations"][0]["features"] = ["nonexistent"]
        with self.assertRaises(ValueError):
            self.gate()

    def test_path_escape_and_symlink_rejected(self):
        outside = self.root.parent / "outside.json"
        self.save(outside, {"secret": "fixture"})
        (self.root / "runs/link.json").symlink_to(outside)
        for path in ("../outside.json", "runs/link.json", str(outside)):
            self.project["validations"][1]["artifact"] = path
            self.assertFalse(self.gate()["recorded_acceptance"])

    def test_duplicate_ids_rejected(self):
        self.project["features"].append(copy.deepcopy(self.project["features"][0]))
        with self.assertRaises(ValueError):
            self.gate()

    def test_malformed_enum_returns_validation_error(self):
        for key in ("mode", "status"):
            saved = self.project["features"][0][key]
            self.project["features"][0][key] = []
            with self.assertRaises(ValueError):
                self.gate()
            self.project["features"][0][key] = saved

    def test_report_cannot_compare_same_file(self):
        with self.assertRaises(ValueError):
            sre.compare(self.a, self.a, self.report)

    def test_cli_exit_codes_and_no_clobber(self):
        out = self.root / "runs/new-report.json"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(0, sre.main(["compare", str(self.a), str(self.b), "--out", str(out)]))
            self.assertEqual(2, sre.main(["compare", str(self.a), str(self.b), "--out", str(out)]))
            self.successor["steps"][0]["result"]["ok"] = False
            self.save(self.b, self.successor)
            self.assertEqual(1, sre.main(["compare", str(self.a), str(self.b), "--out", str(out.with_name("fail.json"))]))
            self.a.write_text("not JSON")
            self.assertEqual(2, sre.main(["compare", str(self.a), str(self.b), "--out", str(out.with_name("bad.json"))]))


if __name__ == "__main__":
    unittest.main()
