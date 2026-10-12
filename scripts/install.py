#!/usr/bin/env python3
"""Install this skill without overwriting an existing installation."""
import argparse
import os
from pathlib import Path
import shutil
import sys


def install(skills_dir):
    source = Path(__file__).resolve().parents[1] / "skills/software-resynthesis"
    target = Path(skills_dir).expanduser() / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    # copytree refuses existing files, directories, and symlinks; no implicit upgrade.
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    return target


if __name__ == "__main__":
    default = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", default=str(default))
    args = parser.parse_args()
    try:
        print(f"Installed: {install(args.skills_dir)}\nReload skills in the host before invoking $software-resynthesis.")
    except OSError as exc:
        print(f"Installation not completed: {exc}", file=sys.stderr)
        sys.exit(2)
