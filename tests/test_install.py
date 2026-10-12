import importlib.util
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

spec = importlib.util.spec_from_file_location("sre_install", Path(__file__).resolve().parents[1] / "scripts/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallationTests(unittest.TestCase):
    def test_install_is_self_contained_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            target = installer.install(root)
            self.assertTrue((target / "SKILL.md").is_file())
            self.assertTrue((target / "references/validation.md").is_file())
            self.assertTrue((target / "scripts/sre.py").is_file())
            subprocess.run([sys.executable, str(target / "scripts/sre.py"), "init", str(Path(root) / "project"),
                            "--source", "fixture", "--target", "fixture"], check=True, capture_output=True)
            self.assertTrue((Path(root) / "project/research.json").is_file())
            (target / "user-note").write_text("preserve")
            with self.assertRaises(FileExistsError):
                installer.install(root)
            self.assertEqual("preserve", (target / "user-note").read_text())

    def test_existing_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            (root / "other").mkdir()
            (root / "software-resynthesis").symlink_to(root / "other", target_is_directory=True)
            with self.assertRaises(FileExistsError):
                installer.install(root)
            self.assertEqual([], list((root / "other").iterdir()))
