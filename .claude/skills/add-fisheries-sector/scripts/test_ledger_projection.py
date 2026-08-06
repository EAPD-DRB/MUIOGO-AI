#!/usr/bin/env python3
"""Integration tests for projecting the Fisheries registers into the ledger.

The fixture is deliberately built to pass **both** validators: the eight-register
one an analyst authors against, and the canonical six-table one that ships. That
is the whole claim of this addition — the ledger is derived, not authored twice —
so a fixture that only satisfied one of them would prove nothing.

    python scripts/test_ledger_projection.py
"""

from __future__ import annotations

import csv
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

import provenance  # noqa: E402

EVIDENCE_BODY = (
    "technology,observed_useful_service_pj\n"
    "PHL_FSH_MOT,4.078\n"
    "PHL_FSH_AQC,5.971\n"
)


def rows(name: str, digest: str) -> tuple[Sequence[str], List[Dict[str, str]]]:
    """Register fixtures modelled on the Philippines Fisheries v2.3 content."""
    if name == "source-register.csv":
        columns = (
            "source_id,provider,title,edition,publication_date,reference_period,"
            "geography,variable,exact_locator,original_unit,url,access_date,license,"
            "local_file,sha256,archived_url,quality_grade,notes"
        ).split(",")
        return columns, [
            {
                "source_id": "FSH-DOE-2023",
                "provider": "Philippine Department of Energy",
                "title": "2023 Philippine Energy Situationer",
                "edition": "2023",
                "publication_date": "2024-06-01",
                "reference_period": "2023",
                "geography": "Philippines",
                "variable": "Fishery final energy",
                "exact_locator": "p. 14, Figure 11",
                "original_unit": "ktoe",
                "url": "https://example.gov.ph/situationer-2023.pdf",
                "access_date": "2026-07-25",
                "license": "public government publication",
                "quality_grade": "A",
                "notes": "control total 240.0 ktoe",
            },
            {
                "source_id": "FSH-BFAR-PROFILE-2020",
                "provider": "Bureau of Fisheries and Aquatic Resources",
                "title": "Philippine Fisheries Profile 2020",
                "edition": "2020",
                "publication_date": "2022-01-01",
                "reference_period": "2020",
                "geography": "Philippines",
                "variable": "Registered fishing vessels",
                "exact_locator": "pp. 47 and 51",
                "original_unit": "count",
                "url": "https://example.gov.ph/fisheries-profile-2020.pdf",
                "access_date": "2026-07-25",
                "license": "public government publication",
                "quality_grade": "A",
                "notes": "267,807 municipal and 5,557 commercial vessels",
            },
            {
                "source_id": "FSH-CALIB-EXTRACT",
                "provider": "Analyst extract",
                "title": "Fisheries base-year calibration inputs",
                "edition": "v2.3",
                "publication_date": "2026-07-25",
                "reference_period": "2020",
                "geography": "Philippines",
                "variable": "Observed useful service by technology",
                "exact_locator": "whole file",
                "original_unit": "PJ",
                "url": "evidence/FSH_calibration_data_v2.3.csv",
                "access_date": "2026-07-25",
                "license": "internal",
                "local_file": "evidence/FSH_calibration_data_v2.3.csv",
                "sha256": digest,
                "quality_grade": "B",
                "notes": "retained extract",
            },
        ]
    if name == "assumption-register.csv":
        columns = (
            "assumption_id,statement,rationale,evidence_source_ids,lower_bound,"
            "central_value,upper_bound,unit,sensitivity_required,owner,review_status,notes"
        ).split(",")
        return columns, [
            {
                "assumption_id": "A-FSH-14",
                "statement": "Aquaculture receives 0.352 PJ liquid and the residual electricity",
                "rationale": "No published motive/aquaculture split exists",
                "evidence_source_ids": "FSH-DOE-2023",
                "lower_bound": "0.30",
                "central_value": "0.352",
                "upper_bound": "0.40",
                "unit": "PJ",
                "sensitivity_required": "yes",
                "owner": "BFAR/DOE",
                "review_status": "requested",
            },
            {
                "assumption_id": "A-FSH-15",
                "statement": "Aquaculture demand endpoint multiplier of 2.625 by 2053",
                "rationale": "Scenario assumption consistent with expansion policy",
                "evidence_source_ids": "",
                "lower_bound": "2.0",
                "central_value": "2.625",
                "upper_bound": "3.2",
                "unit": "dimensionless",
                "sensitivity_required": "yes",
                "owner": "analyst",
                "review_status": "open",
            },
        ]
    if name == "calculation-register.csv":
        columns = (
            "calculation_id,output_description,formula,source_ids,assumption_ids,"
            "input_calculation_ids,input_values,input_units,conversion_factors,method,"
            "script_path,script_version,rounding,output_value,output_unit,review_status,notes"
        ).split(",")
        return columns, [
            {
                "calculation_id": "C-FSH-01",
                "output_description": "Fishery final energy control total in PJ",
                "formula": "240.0 ktoe * 0.041868 PJ/ktoe",
                "source_ids": "FSH-DOE-2023",
                "input_values": "240.0",
                "input_units": "ktoe",
                "conversion_factors": "1 ktoe = 0.041868 PJ",
                "method": "unit conversion",
                "rounding": "6 dp",
                "output_value": "10.048320",
                "output_unit": "PJ",
                "review_status": "accepted",
            },
            {
                "calculation_id": "C-FSH-02",
                "output_description": "Base-year motive useful service",
                "formula": "(liquid_total - 0.352) * 0.36",
                "source_ids": "FSH-CALIB-EXTRACT",
                "assumption_ids": "A-FSH-14",
                "input_calculation_ids": "C-FSH-01",
                "input_values": "10.048320; 0.352; 0.36",
                "input_units": "PJ; PJ; dimensionless",
                "method": "efficiency conversion",
                "script_path": "scripts/estimate_residual_capacity.py",
                "script_version": "e9f3823",
                "rounding": "6 dp",
                "output_value": "4.078000",
                "output_unit": "PJ",
                "review_status": "accepted",
            },
            {
                "calculation_id": "C-FSH-03",
                "output_description": "Residual motive stock from observed service",
                "formula": "4.078 / (31.536 * 0.12)",
                "source_ids": "FSH-BFAR-PROFILE-2020",
                "input_calculation_ids": "C-FSH-02",
                "input_values": "4.078; 31.536; 0.12",
                "input_units": "PJ; PJ/GW/yr; dimensionless",
                "method": "effective stock from utilization",
                "script_path": "scripts/estimate_residual_capacity.py",
                "script_version": "e9f3823",
                "rounding": "3 dp",
                "output_value": "1.078",
                "output_unit": "GW",
                "review_status": "accepted",
            },
            {
                "calculation_id": "C-FSH-04",
                "output_description": "Electric-motive capital cost learning path",
                "formula": "1200 * (1 - 0.42 * progress)",
                "assumption_ids": "A-FSH-15",
                "input_values": "1200; 0.42",
                "input_units": "USD/kW; dimensionless",
                "method": "learning curve",
                "rounding": "0 dp",
                "output_value": "700",
                "output_unit": "USD/kW",
                "review_status": "accepted",
            },
        ]
    if name == "parameter-register.csv":
        columns = (
            "parameter_record_id,model_file,parameter,entity,secondary_entity,mode,"
            "scenario,year_start,year_end,value_expression,model_unit,evidence_type,"
            "source_ids,calculation_id,assumption_ids,uncertainty,confidence,"
            "superseded_by,notes"
        ).split(",")
        return columns, [
            {
                "parameter_record_id": "P-FSH-001",
                "model_file": "RYC.json",
                "parameter": "AAD",
                "entity": "PHL_FSH_MOT",
                "scenario": "Base",
                "year_start": "2020",
                "year_end": "2053",
                "value_expression": "4.078000 rising to 4.902000",
                "model_unit": "PJ",
                "evidence_type": "derived",
                "calculation_id": "C-FSH-02",
                "assumption_ids": "A-FSH-14",
                "uncertainty": "+/-10%",
                "confidence": "medium",
            },
            {
                "parameter_record_id": "P-FSH-002",
                "model_file": "RYT.json",
                "parameter": "RC",
                "entity": "PHL_FSH_MOT_LIQ",
                "scenario": "Base",
                "year_start": "2020",
                "year_end": "2028",
                "value_expression": "1.078 declining linearly to 0",
                "model_unit": "GW",
                "evidence_type": "proxy",
                "calculation_id": "C-FSH-03",
                "uncertainty": "wide",
                "confidence": "low",
                "notes": "vessel counts are a scale check only",
            },
            {
                "parameter_record_id": "P-FSH-003",
                "model_file": "RYT.json",
                "parameter": "CC",
                "entity": "PHL_FSH_MOT_ELC",
                "scenario": "Base",
                "year_start": "2020",
                "year_end": "2053",
                "value_expression": "1200 declining to 700",
                "model_unit": "USD/kW",
                "evidence_type": "estimated",
                "calculation_id": "C-FSH-04",
                "uncertainty": "wide",
                "confidence": "low",
            },
        ]
    if name == "boundary-register.csv":
        columns = (
            "boundary_record_id,flow,include_status,origin_statistical_sector,"
            "destination_model_service,baseline_value,unit,double_count_action,"
            "calculation_id,source_ids,notes"
        ).split(",")
        return columns, [
            {
                "boundary_record_id": "B-FSH-01",
                "flow": "Fish processing energy",
                "include_status": "included",
                "origin_statistical_sector": "Industry",
                "destination_model_service": "PHL_FSH_PRO",
                "baseline_value": "1.563068",
                "unit": "PJ",
                "double_count_action": "subtracted from PHL_INDU_OTH SAD",
                "calculation_id": "C-FSH-01",
            },
            {
                "boundary_record_id": "B-FSH-02",
                "flow": "Fish transport to market",
                "include_status": "excluded",
                "origin_statistical_sector": "Transport",
                "destination_model_service": "none",
                "baseline_value": "0",
                "unit": "PJ",
                "double_count_action": "none",
                "source_ids": "FSH-DOE-2023",
                "notes": "no vehicle-km split by cargo type is published",
            },
        ]
    if name == "completeness-register.csv":
        columns = (
            "item_id,subsector,parameter_or_flow,applicability,status,"
            "parameter_record_ids,data_gap,upgrade_source,priority,notes"
        ).split(",")
        return columns, [
            {
                "item_id": "K-FSH-01",
                "subsector": "Fleet",
                "parameter_or_flow": "Motive residual stock",
                "applicability": "applicable",
                "status": "derived",
                "parameter_record_ids": "P-FSH-002",
                "priority": "high",
            },
            {
                "item_id": "K-FSH-02",
                "subsector": "Fleet",
                "parameter_or_flow": "Vessel engine horsepower distribution",
                "applicability": "applicable",
                "status": "data_gap",
                "data_gap": "BFAR FOI attachment was never obtained",
                "upgrade_source": "BFAR FOI request 1995-2020",
                "priority": "high",
            },
            {
                "item_id": "K-FSH-03",
                "subsector": "Hatcheries",
                "parameter_or_flow": "Hatchery heating demand",
                "applicability": "not applicable",
                "status": "not_applicable",
                "upgrade_source": "",
                "priority": "low",
                "notes": "tropical hatcheries need no space heating",
            },
        ]
    raise AssertionError(f"no fixture for {name}")


class LedgerProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        # Copy the skill so the test also proves it works installed on its own,
        # with only its vendored provenance.py to import.
        self.skill = self.work / "add-fisheries-sector"
        shutil.copytree(SKILL_ROOT, self.skill)
        self.package = self.work / "package"
        self.package.mkdir()
        evidence = self.package / "evidence"
        evidence.mkdir()
        (evidence / "FSH_calibration_data_v2.3.csv").write_text(
            EVIDENCE_BODY, encoding="utf-8"
        )
        digest = hashlib.sha256(EVIDENCE_BODY.encode("utf-8")).hexdigest()
        for name in (
            "source-register.csv",
            "assumption-register.csv",
            "calculation-register.csv",
            "parameter-register.csv",
            "boundary-register.csv",
            "completeness-register.csv",
        ):
            columns, fixture = rows(name, digest)
            with (self.package / name).open(
                "w", newline="", encoding="utf-8"
            ) as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=list(columns), lineterminator="\n"
                )
                writer.writeheader()
                for row in fixture:
                    writer.writerow({column: row.get(column, "") for column in columns})

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_script(
        self, name: str, *arguments: str, expect_success: bool = True
    ) -> subprocess.CompletedProcess:
        result = subprocess.run(
            [sys.executable, str(self.skill / "scripts" / name), *arguments],
            check=False,
            capture_output=True,
            text=True,
            cwd=self.package,
        )
        if expect_success and result.returncode:
            self.fail(
                f"{name} exited {result.returncode}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        if not expect_success and not result.returncode:
            self.fail(f"{name} unexpectedly succeeded\nstdout:\n{result.stdout}")
        return result

    def project(self, *extra: str) -> subprocess.CompletedProcess:
        return self.run_script(
            "project_registers_to_ledger.py",
            "--registers",
            ".",
            "--out",
            "data_sources",
            *extra,
        )

    def read(self, table: str) -> List[Dict[str, str]]:
        _, table_rows = provenance.read_table(self.package / "data_sources" / table)
        return table_rows

    def retire(self, record_id: str, change_id: str) -> None:
        """Retire a parameter-register row the way a source replacement does."""
        path = self.package / "parameter-register.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            columns = list(reader.fieldnames or [])
            register = list(reader)
        for row in register:
            if row["parameter_record_id"] == record_id:
                row["superseded_by"] = change_id
                break
        else:
            self.fail(f"{record_id} is not in the fixture")
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            writer.writerows(register)

    # ------------------------------------------------------------------ tests

    def test_registers_pass_the_register_validator(self) -> None:
        """The fixture is a valid eight-register package, unchanged by this work."""
        self.run_script(
            "validate_provenance.py",
            "--sources",
            "source-register.csv",
            "--assumptions",
            "assumption-register.csv",
            "--calculations",
            "calculation-register.csv",
            "--parameters",
            "parameter-register.csv",
            "--boundaries",
            "boundary-register.csv",
            "--completeness",
            "completeness-register.csv",
        )

    def test_projection_validates_against_the_canonical_schema(self) -> None:
        self.project("--copy-evidence")
        result = self.run_script("validate_ledger.py", "data_sources")
        self.assertIn("PASS", result.stdout)
        self.assertIn("NOT PROVEN", result.stdout, "coverage must be reported as untested")

    def test_every_canonical_table_is_written(self) -> None:
        self.project("--copy-evidence")
        for table in provenance.LEDGER_TABLES:
            path = self.package / "data_sources" / table
            self.assertTrue(path.is_file(), f"{table} was not written")
            columns, _ = provenance.read_table(path)
            expected = list(provenance.REQUIRED_COLUMNS[table])
            self.assertEqual(columns[: len(expected)], expected)

    def test_ids_gain_canonical_prefixes_and_keep_the_original(self) -> None:
        self.project("--copy-evidence")
        assumptions = {row["assumption_id"]: row for row in self.read("ASSUMPTIONS.csv")}
        self.assertIn("ASM_FSH-14", assumptions)
        self.assertIn("legacy_id=A-FSH-14", assumptions["ASM_FSH-14"]["notes"])
        calculations = {row["calculation_id"] for row in self.read("CALCULATIONS.csv")}
        self.assertEqual(
            calculations,
            {"CALC_FSH-01", "CALC_FSH-02", "CALC_FSH-03", "CALC_FSH-04"},
        )
        model_map = {row["map_id"] for row in self.read("MODEL_MAP.csv")}
        self.assertEqual(model_map, {"MAP_FSH-001", "MAP_FSH-002", "MAP_FSH-003"})

    def test_references_are_renamed_consistently(self) -> None:
        self.project("--copy-evidence")
        first = next(
            row for row in self.read("MODEL_MAP.csv") if row["map_id"] == "MAP_FSH-001"
        )
        self.assertEqual(
            provenance.split_ids(first["evidence_ids"]),
            ["CALC_FSH-02", "ASM_FSH-14"],
        )
        self.assertEqual(first["years"], "2020-2053")

    def test_evidence_type_is_derived_and_the_declaration_kept(self) -> None:
        """The ledger derives the type; a register label that disagrees goes to notes.

        ``proxy`` has no canonical type at all, and the register rules require a
        calculation behind an ``estimated`` value — which the canonical rules read
        as ``derived``. Both disagreements are recorded, not silently dropped.
        """
        result = self.project("--copy-evidence")
        self.assertIn("declare evidence_type=proxy", result.stdout)
        self.assertIn("declare evidence_type=estimated", result.stdout)
        model_map = {row["map_id"]: row for row in self.read("MODEL_MAP.csv")}
        for map_id in ("MAP_FSH-001", "MAP_FSH-002", "MAP_FSH-003"):
            self.assertEqual(model_map[map_id]["evidence_type"], "derived")
        self.assertNotIn("declared_evidence_type", model_map["MAP_FSH-001"]["notes"])
        self.assertIn(
            "declared_evidence_type=proxy", model_map["MAP_FSH-002"]["notes"]
        )
        self.assertIn(
            "declared_evidence_type=estimated", model_map["MAP_FSH-003"]["notes"]
        )

    def test_gaps_come_from_both_registers_with_unique_items(self) -> None:
        self.project("--copy-evidence")
        gaps = self.read("GAPS.csv")
        items = [row["item"] for row in gaps]
        self.assertEqual(len(items), len(set(items)), "GAPS.csv item is the key")
        self.assertIn("Fleet: Vessel engine horsepower distribution", items)
        self.assertIn("Fish transport to market", items)
        # why_absent must be the reason, so the register's own note leads it.
        hatchery = next(row for row in gaps if row["item"].startswith("Hatcheries"))
        self.assertEqual(
            hatchery["why_absent"], "tropical hatcheries need no space heating"
        )
        transport = next(row for row in gaps if row["item"] == "Fish transport to market")
        self.assertEqual(
            transport["why_absent"],
            "no vehicle-km split by cargo type is published; retained by Transport",
        )
        represented = [row for row in gaps if "Motive residual stock" in row["item"]]
        self.assertFalse(represented, "a represented parameter is not a gap")

    def test_retained_evidence_digest_is_verified_against_bytes(self) -> None:
        """Without --copy-evidence the digest cannot be checked, and that fails."""
        self.project()
        outside = self.run_script(
            "validate_ledger.py", "data_sources", expect_success=False
        )
        self.assertIn("local_file", outside.stdout)
        self.project("--copy-evidence", "--force")
        self.run_script("validate_ledger.py", "data_sources")
        copied = self.package / "data_sources" / "evidence"
        self.assertTrue((copied / "FSH_calibration_data_v2.3.csv").is_file())

    def test_tampered_evidence_fails(self) -> None:
        self.project("--copy-evidence")
        target = (
            self.package / "data_sources" / "evidence" / "FSH_calibration_data_v2.3.csv"
        )
        target.write_text(EVIDENCE_BODY.replace("4.078", "9.999"), encoding="utf-8")
        result = self.run_script(
            "validate_ledger.py", "data_sources", expect_success=False
        )
        self.assertIn("sha256 mismatch", result.stdout)

    def test_change_row_lists_real_map_ids(self) -> None:
        self.project("--copy-evidence")
        self.project(
            "--copy-evidence",
            "--force",
            "--change-id",
            "CHG_FSH_ADD_20260731",
            "--change-date",
            "2026-07-31",
            "--change-class",
            "B",
            "--change-description",
            "Add Fisheries sector",
            "--model-objects",
            "PHL_FSH_MOT; PHL_FSH_AQC",
            "--author",
            "A. Analyst",
            "--commit",
            "e9f3823",
        )
        changes = self.read("CHANGES.csv")
        self.assertEqual(len(changes), 1)
        affected = provenance.split_ids(changes[0]["map_rows_affected"])
        self.assertEqual(
            sorted(affected), ["MAP_FSH-001", "MAP_FSH-002", "MAP_FSH-003"]
        )
        self.run_script("validate_ledger.py", "data_sources")

    def test_a_retired_row_keeps_its_lineage_and_names_its_change(self) -> None:
        self.project("--copy-evidence")
        self.retire("P-FSH-002", "CHG_FSH_RETIRE_20260731")
        self.project(
            "--copy-evidence",
            "--force",
            "--change-id",
            "CHG_FSH_RETIRE_20260731",
            "--change-date",
            "2026-07-31",
            "--change-class",
            "B",
            "--change-description",
            "Replace the proxy residual motive stock",
            "--model-objects",
            "PHL_FSH_MOT_LIQ",
            "--change-map-rows",
            "retired",
            "--author",
            "A. Analyst",
        )
        retired = next(
            row for row in self.read("MODEL_MAP.csv") if row["map_id"] == "MAP_FSH-002"
        )
        self.assertEqual(retired["superseded_by"], "CHG_FSH_RETIRE_20260731")
        self.assertEqual(retired["evidence_ids"], "CALC_FSH-03", "lineage is kept")
        change = next(
            row
            for row in self.read("CHANGES.csv")
            if row["change_id"] == "CHG_FSH_RETIRE_20260731"
        )
        self.assertEqual(
            provenance.split_ids(change["map_rows_affected"]), ["MAP_FSH-002"]
        )
        self.run_script("validate_ledger.py", "data_sources")

    def test_an_unknown_affected_map_row_is_refused(self) -> None:
        self.project("--copy-evidence")
        result = self.run_script(
            "project_registers_to_ledger.py",
            "--registers",
            ".",
            "--out",
            "data_sources",
            "--copy-evidence",
            "--force",
            "--change-id",
            "CHG_FSH_TYPO_20260731",
            "--change-date",
            "2026-07-31",
            "--change-map-rows",
            "MAP_FSH-001; MAP_FSH-404",
            expect_success=False,
        )
        self.assertIn("MAP_FSH-404", result.stderr)
        self.assertEqual(len(self.read("CHANGES.csv")), 0)

    def test_change_log_is_append_only(self) -> None:
        self.project("--copy-evidence")
        arguments = (
            "--copy-evidence",
            "--force",
            "--change-id",
            "CHG_FSH_ADD_20260731",
            "--change-date",
            "2026-07-31",
            "--author",
            "A. Analyst",
        )
        self.project(*arguments)
        result = self.run_script(
            "project_registers_to_ledger.py",
            "--registers",
            ".",
            "--out",
            "data_sources",
            *arguments,
            expect_success=False,
        )
        self.assertIn("append-only", result.stderr)
        self.assertEqual(len(self.read("CHANGES.csv")), 1)

    def test_existing_ledger_rows_are_not_silently_overwritten(self) -> None:
        self.project("--copy-evidence")
        path = self.package / "data_sources" / "MODEL_MAP.csv"
        original = path.read_text(encoding="utf-8")
        path.write_text(
            original.replace("MAP_FSH-001", "MAP_FSH-999"), encoding="utf-8"
        )
        result = self.run_script(
            "project_registers_to_ledger.py",
            "--registers",
            ".",
            "--out",
            "data_sources",
            expect_success=False,
        )
        self.assertIn("--force", result.stderr)
        self.assertIn("MAP_FSH-999", path.read_text(encoding="utf-8"))

    def test_projection_is_idempotent(self) -> None:
        self.project("--copy-evidence")
        snapshot = {
            table: (self.package / "data_sources" / table).read_text(encoding="utf-8")
            for table in provenance.LEDGER_TABLES
        }
        self.project("--copy-evidence")
        for table, text in snapshot.items():
            self.assertEqual(
                (self.package / "data_sources" / table).read_text(encoding="utf-8"),
                text,
                f"{table} changed on a second projection",
            )


if __name__ == "__main__":
    unittest.main()
