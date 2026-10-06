"""Tests for install.py: it keeps or backs up, and never deletes local work.

Run from this folder:  python -m pytest -q test_install.py
"""
from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("pull_install", HERE / "install.py")
INSTALL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(INSTALL)

CASE = "Testland_v1"
FILES = {"genData.json": '{"osy-casename": "Testland_v1"}', "RYT.json": '{"CC": {}}'}


class InstallTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "CLEWs-TST"
        self.live = self.repo / "case" / CASE
        self.backups = self.repo / "case" / ".backups"
        self.datastorage = self.root / "MUIOGO" / "WebAPP" / "DataStorage"
        self.datastorage.mkdir(parents=True)
        self.archive = self.root / "case.zip"
        with zipfile.ZipFile(self.archive, "w") as zf:
            for name, text in FILES.items():
                zf.writestr(f"{CASE}/{name}", text)

    def write_case(self, where: Path, extra: dict | None = None) -> None:
        for name, text in {**FILES, **(extra or {})}.items():
            path = where / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def run_install(self, apply_: bool = True):
        plan = INSTALL.Plan()
        ok = INSTALL.install(plan, str(self.archive), str(self.live), apply_)
        return ok, plan

    def run_link(self, apply_: bool = True):
        plan = INSTALL.Plan()
        ok = INSTALL.link(plan, str(self.live), str(self.datastorage), CASE, apply_)
        return ok, plan

    def test_matching_live_case_is_kept_with_its_results(self) -> None:
        self.write_case(self.live, {"res/run1/results.txt": "Optimal"})
        ok, plan = self.run_install()
        self.assertTrue(ok)
        self.assertEqual((self.live / "res/run1/results.txt").read_text(), "Optimal")
        self.assertFalse(self.backups.exists())
        self.assertIn("keep live case", [s for s, _ in plan.steps])

    def test_differing_live_case_is_backed_up_not_deleted(self) -> None:
        self.write_case(self.live, {"res/run1/results.txt": "Optimal"})
        (self.live / "genData.json").write_text('{"local": "edit"}', encoding="utf-8")
        ok, _ = self.run_install()
        self.assertTrue(ok)
        self.assertEqual((self.live / "genData.json").read_text(), FILES["genData.json"])
        saved = list(self.backups.iterdir())
        self.assertEqual(len(saved), 1)
        self.assertEqual((saved[0] / "genData.json").read_text(), '{"local": "edit"}')
        self.assertEqual((saved[0] / "res/run1/results.txt").read_text(), "Optimal")

    def test_real_datastorage_folder_is_moved_aside(self) -> None:
        # The reviewer's reproduction: a real case folder with a local edit and
        # results where MUIOGO's entry belongs. The old script deleted it.
        self.write_case(self.live)
        real = self.datastorage / CASE
        self.write_case(real, {"res/run1/results.txt": "Optimal"})
        (real / "genData.json").write_text('{"local": "edit"}', encoding="utf-8")
        ok, _ = self.run_link()
        self.assertTrue(ok)
        self.assertTrue((self.datastorage / CASE).is_symlink())
        saved = [p for p in self.backups.iterdir() if "-datastorage-" in p.name]
        self.assertEqual(len(saved), 1)
        self.assertEqual((saved[0] / "genData.json").read_text(), '{"local": "edit"}')
        self.assertEqual((saved[0] / "res/run1/results.txt").read_text(), "Optimal")

    def test_wrong_link_is_moved_aside(self) -> None:
        self.write_case(self.live)
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        os.symlink(elsewhere, self.datastorage / CASE)
        ok, _ = self.run_link()
        self.assertTrue(ok)
        self.assertEqual(os.path.realpath(self.datastorage / CASE), os.path.realpath(self.live))
        saved = [p for p in self.backups.iterdir() if p.is_symlink()]
        self.assertEqual([os.path.realpath(p) for p in saved], [os.path.realpath(elsewhere)])

    def test_plan_changes_nothing(self) -> None:
        self.write_case(self.live)
        (self.live / "genData.json").write_text('{"local": "edit"}', encoding="utf-8")
        real = self.datastorage / CASE
        self.write_case(real)
        self.run_install(apply_=False)
        self.run_link(apply_=False)
        self.assertEqual((self.live / "genData.json").read_text(), '{"local": "edit"}')
        self.assertTrue(real.is_dir() and not real.is_symlink())
        self.assertFalse(self.backups.exists())

    def test_new_case_is_created(self) -> None:
        ok, plan = self.run_install()
        self.assertTrue(ok)
        self.assertEqual((self.live / "RYT.json").read_text(), FILES["RYT.json"])
        self.assertIn("create live case", [s for s, _ in plan.steps])


if __name__ == "__main__":
    unittest.main()
