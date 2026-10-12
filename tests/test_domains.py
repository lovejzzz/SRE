import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/software-resynthesis/scripts"))
import sre_domains as domain


class DomainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def save(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def policy(self, kind, **kwargs):
        return self.save("policy.json", {"schema_version": 1, "kind": kind, "rationale": "fixed test policy", **kwargs})

    def image(self, samples, **kwargs):
        return {"schema_version": 1, "width": 1, "height": 1, "channels": 4, "color_space": "linear-sRGB",
                "alpha_mode": "straight", "samples": samples, **kwargs}

    def test_image_threshold_and_metadata(self):
        self.save("a.json", self.image([0, 0, 0, 1]))
        self.save("b.json", self.image([0.01, 0, 0, 1]))
        policy = self.policy("image", reference="a.json", candidate="b.json", limits={"max_abs": 0.02, "rmse": .01})
        self.assertTrue(domain.evaluate(policy)["passed"])
        self.save("b.json", self.image([0.1, 0, 0, 1]))
        self.assertFalse(domain.evaluate(policy)["passed"])
        self.save("b.json", self.image([0, 0, 0, 1], color_space="sRGB"))
        self.assertFalse(domain.evaluate(policy)["passed"])

    def test_alpha_loss_detected(self):
        self.save("a.json", self.image([0, 0, 0, .5]))
        self.save("b.json", self.image([0, 0, 0, 1]))
        p = self.policy("image", reference="a.json", candidate="b.json", limits={"max_abs": 0, "rmse": 0})
        self.assertFalse(domain.evaluate(p)["passed"])

    def test_bad_sample_count_rejected(self):
        self.save("a.json", self.image([1]))
        p = self.policy("image", reference="a.json", candidate="a.json", limits={"max_abs": 0, "rmse": 0})
        with self.assertRaises(ValueError):
            domain.evaluate(p)

    def test_roundtrip_hidden_layer_loss(self):
        self.save("a.json", {"schema_version": 1, "document": {"layers": ["visible", "hidden"]}})
        self.save("b.json", {"schema_version": 1, "document": {"layers": ["visible"]}})
        p = self.policy("roundtrip", original="a.json", reopened="b.json")
        self.assertFalse(domain.evaluate(p)["passed"])

    def test_interaction_rejection_difference(self):
        a = {"schema_version": 1, "scenario": "undo", "steps": [{"action": {"undo": True}, "result": {"ok": True}, "state": {"history": 0}}]}
        self.save("a.json", a)
        a["steps"][0]["result"]["ok"] = False
        self.save("b.json", a)
        p = self.policy("interaction", reference="a.json", candidate="b.json")
        self.assertFalse(domain.evaluate(p)["passed"])

    def test_performance_tail_device_workload_and_samples(self):
        values = {"schema_version": 1, "device": "TV", "workload": "large-doc", "latency_ms": [10]*20, "peak_memory_mb": 100}
        self.save("m.json", values)
        p = self.policy("performance", measurements="m.json", device="TV", workload="large-doc",
                        limits={"p95_ms": 16, "peak_memory_mb": 200, "min_samples": 20})
        self.assertTrue(domain.evaluate(p)["passed"])
        for mutation in ({"latency_ms": [10]*18+[50]*2}, {"device": "Desktop"}, {"workload": "empty-doc"}, {"latency_ms": [1]}):
            self.save("m.json", {**values, **mutation})
            self.assertFalse(domain.evaluate(p)["passed"])

    def test_report_recomputation_detects_changed_policy(self):
        self.save("a.json", {"schema_version": 1, "document": {"x": 1}})
        p = self.policy("roundtrip", original="a.json", reopened="a.json")
        report = self.save("report.json", domain.evaluate(p))
        domain.verify_report(report)
        policy = json.loads(p.read_text())
        policy["rationale"] = "Changed after test"
        self.save("policy.json", policy)
        with self.assertRaises(ValueError):
            domain.verify_report(report)

    def test_escape_rejected(self):
        p = self.policy("roundtrip", original="../outside.json", reopened="a.json")
        with self.assertRaises(ValueError):
            domain.evaluate(p)
