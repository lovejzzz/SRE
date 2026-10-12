import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/software-resynthesis/scripts"))
from sre_adapter import run_adapter

SCRIPT = '''import json, sys, time
r = json.load(sys.stdin)
mode = r['fixture'].get('mode')
if mode == 'timeout':
    print('started', file=sys.stderr, flush=True)
    time.sleep(60)
if mode == 'exit':
    sys.exit(7)
if mode == 'malformed':
    print('not JSON')
    sys.exit(0)
steps = [{'action': a, 'result': {'value': a['value']}, 'state': {'done': True}} for a in r['actions']]
if mode == 'omit': steps = []
print(json.dumps({'schema_version':1, 'scenario':r['scenario'], 'steps':steps,
                 'lifecycle': {'reset': mode != 'no-reset', 'finalize': True}}, ensure_ascii=False))
'''


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "adapter.py").write_text(SCRIPT, encoding="utf-8")
        self.manifest = self.root / "manifest.json"
        self.manifest.write_text(json.dumps({"schema_version": 1, "id": "fixture", "build": "fixture-v1",
            "kind": "source-runtime", "argv": ["{python}", "{adapter_dir}/adapter.py"], "build_files": ["adapter.py"]}))
        self.request = self.root / "request.json"

    def run_case(self, mode=None):
        self.request.write_text(json.dumps({"schema_version": 1, "scenario": "echo", "fixture": {"mode": mode},
                                           "actions": [{"value": "文件"}]}, ensure_ascii=False), encoding="utf-8")
        return run_adapter(self.manifest, self.request, self.root / "run", timeout=.25 if mode == "timeout" else 10)

    def test_success_preserves_unicode_and_provenance(self):
        result = self.run_case()
        self.assertTrue(result["passed"])
        trace = json.loads((self.root / "run/trace.json").read_text(encoding="utf-8"))
        self.assertEqual("文件", trace["steps"][0]["result"]["value"])
        self.assertTrue(trace["provenance"]["build_files"])
        with self.assertRaises(FileExistsError):
            self.run_case()

    def test_missing_build_file_is_preflight_error(self):
        (self.root / "adapter.py").unlink()
        with self.assertRaisesRegex(ValueError, "Missing build file: adapter.py"):
            self.run_case()
        self.assertFalse((self.root / "run").exists())

    def test_timeout_retains_diagnostics(self):
        result = self.run_case("timeout")
        self.assertEqual("timeout", result["status"])
        self.assertTrue((self.root / "run/stderr.log").exists())
        self.assertFalse((self.root / "run/trace.json").exists())

    def test_nonzero_exit_retained(self):
        result = self.run_case("exit")
        self.assertFalse(result["passed"])
        self.assertEqual(7, result["exit_code"])

    def test_malformed_output_fails(self):
        self.assertFalse(self.run_case("malformed")["passed"])

    def test_omitted_action_fails(self):
        self.assertFalse(self.run_case("omit")["passed"])

    def test_missing_reset_fails(self):
        self.assertFalse(self.run_case("no-reset")["passed"])
