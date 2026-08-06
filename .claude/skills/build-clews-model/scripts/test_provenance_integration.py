#!/usr/bin/env python3
"""Integration tests for the build skill's self-contained provenance workflow."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import provenance  # noqa: E402


class BuildProvenanceIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.isolated_skill = self.work / "build-clews-model"
        shutil.copytree(SKILL_ROOT, self.isolated_skill)
        self.package = self.work / "package"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_python(
        self, script: Path, *arguments: str, expect_success: bool = True
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(script), *arguments],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.work,
        )
        if expect_success and result.returncode:
            self.fail(
                f"{script.name} exited {result.returncode}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def scaffold(self) -> None:
        self.run_python(
            self.isolated_skill / "scripts" / "init_country_package.py",
            str(self.package),
            "--country",
            "Exampleland",
            "--iso3",
            "EXP",
        )

    @staticmethod
    def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=list(provenance.REQUIRED_COLUMNS[path.name]),
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)

    def populate_build_package(self, include_config_map: bool = True) -> None:
        self.scaffold()
        (self.package / "config" / "config.yaml").write_text(
            "country: Exampleland\niso3: EXP\n", encoding="utf-8"
        )
        pins = {
            "workflow": {
                "repository": "https://example.test/clews-global.git",
                "commit": "a" * 40,
            },
            "submodules": {},
            "muiogo": {
                "repository": "https://example.test/muiogo.git",
                "commit": "b" * 40,
                "version": None,
            },
            "toolchain": {"python": "3.12", "solver": "CBC"},
        }
        (self.package / "config" / "upstream_versions.json").write_text(
            json.dumps(pins, indent=2) + "\n", encoding="utf-8"
        )
        (self.package / "model" / "inputs" / "DiscountRate.csv").write_text(
            "REGION,VALUE\nEXP,0.05\n", encoding="utf-8"
        )
        source = {
            "source_id": "SRC_DISCOUNT",
            "provider": "Example statistics office",
            "product": "National accounts",
            "edition": "2025",
            "reference_period": "2024",
            "geography": "Exampleland",
            "variable": "social discount rate",
            "source_unit": "fraction",
            "exact_locator": "Table 2, row 7",
            "url": "https://example.test/national-accounts",
            "access_date": "2026-07-30",
            "license": "CC-BY-4.0",
            "sha256": "",
        }
        model_rows = [
            {
                "map_id": "MAP_DISCOUNT",
                "model_file": "model/inputs/DiscountRate.csv",
                "parameter": "DiscountRate",
                "entity": "GLOBAL",
                "mode": "",
                "scenario": "raw",
                "years": "all",
                "value_or_expression": "0.05",
                "model_unit": "fraction",
                "evidence_ids": "SRC_DISCOUNT",
                "superseded_by": "",
            }
        ]
        if include_config_map:
            model_rows.append(
                {
                    "map_id": "MAP_CONFIG",
                    "model_file": "config/config.yaml",
                    "parameter": "country",
                    "entity": "Exampleland",
                    "mode": "",
                    "scenario": "raw",
                    "years": "all",
                    "value_or_expression": "Exampleland",
                    "model_unit": "text",
                    "evidence_ids": "SRC_DISCOUNT",
                    "superseded_by": "",
                }
            )
        self.write_rows(self.package / "data_sources" / "SOURCES.csv", [source])
        self.write_rows(
            self.package / "data_sources" / "MODEL_MAP.csv", model_rows
        )

    def test_scaffold_uses_exact_canonical_six_ledgers(self) -> None:
        self.scaffold()
        ledger_dir = self.package / "data_sources"
        csv_names = sorted(path.name for path in ledger_dir.glob("*.csv"))
        self.assertEqual(csv_names, sorted(provenance.LEDGER_TABLES))
        self.assertNotIn("MODEL_DATA_MAP.csv", csv_names)
        for table in provenance.LEDGER_TABLES:
            with (ledger_dir / table).open(
                newline="", encoding="utf-8"
            ) as handle:
                header = next(csv.reader(handle))
            self.assertEqual(header, list(provenance.REQUIRED_COLUMNS[table]))

        result = self.run_python(
            self.package / "scripts" / "validate_provenance.py",
            str(self.package),
            "--stage",
            "scaffold",
        )
        self.assertEqual(json.loads(result.stdout)["status"], "pass")

    def test_allow_existing_never_rewrites_an_existing_csv(self) -> None:
        self.scaffold()
        source_path = self.package / "data_sources" / "SOURCES.csv"
        sentinel = "user_owned_column\nkeep-me\n"
        source_path.write_text(sentinel, encoding="utf-8")
        self.run_python(
            self.isolated_skill / "scripts" / "init_country_package.py",
            str(self.package),
            "--country",
            "Exampleland",
            "--iso3",
            "EXP",
            "--allow-existing",
        )
        self.assertEqual(source_path.read_text(encoding="utf-8"), sentinel)

    def test_build_validation_covers_inputs_and_country_config(self) -> None:
        self.populate_build_package()
        result = self.run_python(
            self.package / "scripts" / "validate_provenance.py",
            str(self.package),
            "--stage",
            "build",
        )
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["populated_input_count"], 1)
        self.assertEqual(report["covered_input_count"], 1)
        self.assertEqual(report["model_map_count"], 2)

    def test_build_validation_rejects_unmapped_country_config(self) -> None:
        self.populate_build_package(include_config_map=False)
        result = self.run_python(
            self.package / "scripts" / "validate_provenance.py",
            str(self.package),
            "--stage",
            "build",
            expect_success=False,
        )
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertTrue(
            any("config/config.yaml" in failure for failure in report["failures"])
        )

    def test_freeze_and_delivery_validation_use_the_split_checkers(self) -> None:
        self.populate_build_package()
        diagnostics = self.package / "diagnostics"
        (diagnostics / "validation_summary.json").write_text(
            json.dumps(
                {
                    "upstream_raw": {"status": "pass"},
                    "muio_import": {
                        "status": "pass",
                        "nondefault_errors": 0,
                        "unsupported_nondefault_rows": 0,
                    },
                    "muio_final": {"status": "pass"},
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (diagnostics / "no_forcing_audit.json").write_text(
            '{"status": "pass", "failure_count": 0}\n', encoding="utf-8"
        )
        (diagnostics / "resource_estimate.json").write_text(
            '{"traffic_light": "green", "actual": {"rows": 1}}\n',
            encoding="utf-8",
        )
        muio_archive = self.package / "muio" / "Exampleland_raw_MUIO.zip"
        with zipfile.ZipFile(muio_archive, "w") as handle:
            handle.writestr("case/model.json", "{}\n")
            handle.writestr("case/result.sol", "optimal\n")

        self.run_python(
            self.package / "scripts" / "freeze_raw_baseline.py",
            str(self.package),
            "--muio-archive",
            str(muio_archive),
            "--date",
            "2026-07-30",
        )
        result = self.run_python(
            self.package / "scripts" / "validate_delivery.py",
            str(self.package),
        )
        self.assertEqual(json.loads(result.stdout)["status"], "pass")

    def test_copied_skill_has_no_repository_relative_runtime_dependency(self) -> None:
        self.scaffold()
        result = self.run_python(
            self.isolated_skill / "scripts" / "provenance.py",
            str(self.package / "data_sources"),
            "--stage",
            "scaffold",
        )
        self.assertIn("provenance: PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
