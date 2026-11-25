#!/usr/bin/env python3
"""Vendor the Model-tools skills listed in scripts/MODEL_TOOLS_PIN into .agents/skills.

These skills live in EAPD-DRB/Model-tools and are carried here unchanged at a pinned commit.
Never edit them here: fix them in Model-tools, then move the pin.

  python scripts/model_tools_skills.py --check                 # copies equal the pinned commit?
  python scripts/model_tools_skills.py --update <commit>       # re-vendor at a new commit
  ... [--from PATH]   use a local Model-tools clone instead of fetching from GitHub

After --update, run ./scripts/install-skills.sh --sync to refresh .claude/skills.
"""
import argparse
import filecmp
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIN = ROOT / "scripts" / "MODEL_TOOLS_PIN"
SKILLS = ROOT / ".agents" / "skills"


def read_pin():
    pin = {}
    for line in PIN.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            k, v = line.split("=", 1)
            pin[k.strip()] = v.strip()
    pin["skills"] = pin["skills"].split()
    return pin


def write_commit(commit):
    lines = [f"commit={commit}" if l.startswith("commit=") else l for l in PIN.read_text().splitlines()]
    PIN.write_text("\n".join(lines) + "\n")


def export(pin, commit, source, dest):
    """Extract skills/<name> for every pinned skill at `commit` into dest/<name>."""
    if source is None:
        clone = Path(dest) / "model-tools"
        subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", pin["repo"], str(clone)], check=True)
        source = clone
    archive = Path(dest) / "skills.tar"
    paths = [f"skills/{s}" for s in pin["skills"]]
    subprocess.run(["git", "-C", str(source), "archive", "--format=tar", "-o", str(archive), commit, *paths], check=True)
    out = Path(dest) / "out"
    with tarfile.open(archive) as t:
        try:
            t.extractall(out, filter="data")
        except TypeError:  # Python before 3.12; the archive comes from git, not from a stranger
            t.extractall(out)
    return out / "skills"


def differences(a, b):
    cmp = filecmp.dircmp(a, b)
    _, changed, errors = filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)
    diffs = [f"{p}: differs" for p in changed + errors] + [f"{p}: only in pinned" for p in cmp.left_only] + [f"{p}: only here" for p in cmp.right_only]
    for sub in cmp.common_dirs:
        diffs += [f"{sub}/{d}" for d in differences(Path(a) / sub, Path(b) / sub)]
    return diffs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--update", metavar="COMMIT")
    ap.add_argument("--from", dest="source", type=Path)
    args = ap.parse_args()
    pin = read_pin()
    commit = args.update or pin["commit"]
    with tempfile.TemporaryDirectory() as tmp:
        pinned = export(pin, commit, args.source, tmp)
        if args.update:
            for s in pin["skills"]:
                target = SKILLS / s
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(pinned / s, target)
            write_commit(commit)
            print(f"vendored {len(pin['skills'])} skills at {commit}; now run ./scripts/install-skills.sh --sync")
            return 0
        problems = []
        for s in pin["skills"]:
            if not (SKILLS / s).exists():
                problems.append(f"{s}: missing")
            else:
                problems += [f"{s}/{d}" for d in differences(pinned / s, SKILLS / s)]
        for p in problems:
            print(p)
        print(f"{len(problems)} difference(s) from Model-tools {commit}" if problems
              else f"all {len(pin['skills'])} vendored skills equal Model-tools {commit}")
        return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
