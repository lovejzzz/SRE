"""Helper contract tests. Fixture provenance labels are test data, not PZ evidence."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from research_fixture import prepare

SCRIPT = Path(__file__).resolve().parents[1] / "skills/software-resynthesis/scripts/sre.py"
sys.path.insert(0, str(SCRIPT.parent))
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
             "artifact": "runs/target.json", "sha256": sre.digest(self.root / "runs/target.json")}]
        prepare(self.root, self.project, sre.sre_research)

    def save(self, path, data):
        path.write_text(json.dumps(data), encoding="utf-8")

    def test_manual_ui_requires_raw_capture_and_rechecks_it(self):
        self.original['provenance']['observation_method'] = 'manual-ui'
        self.save(self.a, self.original)
        with self.assertRaisesRegex(ValueError, 'fingerprinted raw captures'):
            sre.trace(self.a)
        raw = self.a.parent / 'screen.bin'
        raw.write_bytes(b'fixture screenshot bytes, not source evidence')
        self.original['provenance']['raw_captures'] = [{'path':'screen.bin', 'description':'Fixture', 'sha256':sre.digest(raw)}]
        self.save(self.a, self.original)
        self.save(self.report, sre.compare(self.a, self.b, self.report))
        self.assertTrue(self.gate()['behavior_ready'])
        raw.write_bytes(b'changed screenshot')
        self.assertFalse(self.gate()['behavior_ready'])
        with self.assertRaisesRegex(ValueError, 'stale raw capture'):
            sre.compare(self.a, self.b, self.report)

    def test_raw_capture_escape_and_duplicate_rejected(self):
        raw = self.root / 'outside.bin'; raw.write_bytes(b'fixture')
        capture = {'path':'../outside.bin', 'description':'Fixture', 'sha256':sre.digest(raw)}
        self.original['provenance']['raw_captures'] = [capture]
        self.save(self.a, self.original)
        with self.assertRaisesRegex(ValueError, 'escapes'):
            sre.trace(self.a)
        raw = self.a.parent / 'inside.bin'; raw.write_bytes(b'fixture')
        capture['path'] = 'inside.bin'
        self.original['provenance']['raw_captures'] = [capture, capture]
        self.save(self.a, self.original)
        with self.assertRaisesRegex(ValueError, 'Duplicate raw capture'):
            sre.trace(self.a)

    def gate(self):
        self.save(self.root / "project.json", self.project)
        return sre.check(self.root)

    def test_complete_recorded_obligations(self):
        self.assertTrue(self.gate()["recorded_acceptance"])

    def test_component_comparison_cannot_establish_application_fidelity(self):
        for side, kind in ((self.a, 'source-component'), (self.b, 'successor-component')):
            with self.subTest(kind=kind):
                self.save(self.a, self.original)
                self.save(self.b, self.successor)
                data = sre.read(side)
                data['provenance']['kind'] = kind
                self.save(side, data)
                report = sre.compare(self.a, self.b, self.report)
                self.assertTrue(report['passed'], 'Equal component results remain useful evidence')
                self.save(self.report, report)
                self.assertFalse(self.gate()['behavior_ready'], 'Component equality is not a whole-app workflow')

    def test_target_metadata_mutation_rejected(self):
        path = self.root / "runs/target.json"
        data = sre.read(path)
        data["environment"] = "unmeasured device"
        self.save(path, data)
        self.assertFalse(self.gate()["recorded_acceptance"])

    def test_missing_target_hash_rejected(self):
        self.project["validations"][1].pop("sha256")
        self.assertFalse(self.gate()["recorded_acceptance"])

    def test_explicit_scenario_can_differ_from_validation_id(self):
        self.project["validations"][0].update(id="move-validation", scenario="move")
        self.project["features"][0]["acceptance"][0] = "move-validation"
        prepare(self.root, self.project, sre.sre_research, "scenario-baseline.json")
        self.assertTrue(self.gate()["recorded_acceptance"])

    def test_synthetic_artifact_must_be_valid_trace(self):
        self.project["validations"].append({"id": "fixture", "kind": "synthetic",
            "status": "passed", "features": ["inventory"], "artifact": "runs/fixture.json"})
        self.save(self.root / "runs/fixture.json", {})
        self.assertFalse(self.gate()["recorded_acceptance"])
        data = copy.deepcopy(self.original)
        data["scenario"] = "fixture"
        data["provenance"]["kind"] = "synthetic"
        self.save(self.root / "runs/fixture.json", data)
        self.assertTrue(self.gate()["recorded_acceptance"])

    def test_deep_json_has_actionable_error(self):
        for depth in (130, 5000):
            self.a.write_text("[" * depth + "0" + "]" * depth)
            with self.assertRaisesRegex(ValueError, "maximum depth 128"):
                sre.read(self.a)

    def test_plan_cli_works_before_source_build_is_known(self):
        self.project["features"] = []
        self.save(self.root / "project.json", self.project)
        self.save(self.root / "research.json", {"schema_version": 1,
            "scope": {"source_build": "unresolved"}, "surveys": [], "questions": []})
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = sre.main(["plan", str(self.root)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["next_experiments"], [])

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
        prepare(self.root, self.project, sre.sre_research, "enhancement-baseline.json")
        self.assertTrue(self.gate()["recorded_acceptance"])

    def test_behavior_pass_does_not_hide_missing_discovery(self):
        (self.root / "research-baseline.json").unlink()
        result = self.gate()
        self.assertTrue(result["behavior_ready"])
        self.assertFalse(result["recorded_acceptance"])

    def test_domain_policy_is_pinned_by_research_baseline(self):
        policy = self.root / "runs/policy.json"
        raster = {"schema_version": 1, "width": 1, "height": 1, "channels": 1,
                  "color_space": "linear-gray", "alpha_mode": "none", "samples": [0.5]}
        self.save(self.root / "runs/reference.json", raster)
        self.save(self.root / "runs/candidate.json", raster)
        data = {"schema_version": 1, "kind": "image", "rationale": "Exact identity operation",
                "reference": "reference.json", "candidate": "candidate.json", "limits": {"max_abs": 0, "rmse": 0}}
        self.save(policy, data)
        self.save(self.root / "runs/domain.json", sre.sre_domains.evaluate(policy))
        feature = self.project["features"][0]
        feature.update(mode="extend", acceptance=["image"])
        self.project["validations"] = [{"id": "image", "kind": "domain", "status": "passed",
            "features": ["inventory"], "artifact": "runs/domain.json", "policy": "runs/policy.json"}]
        self.project["decisions"] = [{"feature": "inventory", "rationale": "Test extension", "acceptance": "Exact pixels"}]
        prepare(self.root, self.project, sre.sre_research, "domain-baseline.json")
        self.assertTrue(self.gate()["recorded_acceptance"])
        data["limits"] = {"max_abs": 1, "rmse": 1}
        self.save(policy, data)
        self.save(self.root / "runs/domain.json", sre.sre_domains.evaluate(policy))
        self.assertFalse(self.gate()["recorded_acceptance"])

    def test_target_failure_not_accepted(self):
        result = sre.read(self.root / "runs/target.json")
        result["passed"] = False
        self.save(self.root / "runs/target.json", result)
        self.project["validations"][1]["sha256"] = sre.digest(self.root / "runs/target.json")
        outcome = self.gate()
        self.assertFalse(outcome["recorded_acceptance"])
        self.assertTrue(any("Target test did not pass" in p for p in outcome["problems"]))

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
