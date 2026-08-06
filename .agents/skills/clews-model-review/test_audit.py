"""Regression tests for the CLEWs structural audit."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


AUDIT_PATH = Path(__file__).with_name("audit.py")
SPEC = importlib.util.spec_from_file_location("clews_model_audit", AUDIT_PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def make_model(root: Path, extra_id: str | None = None) -> Path:
    model = root / "UnderscoreIds"
    write_json(
        model / "genData.json",
        {
            "osy-casename": "UnderscoreIds",
            "osy-version": 1,
            "osy-desc": "Regression fixture",
            "osy-date": "2026-07-28",
            "osy-years": ["2020"],
            "osy-ts": [],
            "osy-techGroups": [{"TG": "ENERGY"}, {"TG": "ENVIRONMENT"}],
            "osy-tech": [
                {
                    "TechId": "TEC_envland_v12",
                    "Tech": "ENV_LAND",
                    "Desc": "Land account",
                    "IAR": [],
                    "OAR": ["COM_env_lcrp_v12"],
                }
            ],
            "osy-comm": [
                {
                    "CommId": "COM_env_lcrp_v12",
                    "Comm": "ENV_LAND_CROP",
                    "Desc": "Cropland account",
                    "UnitId": "km2",
                }
            ],
            "osy-emis": [
                {
                    "EmisId": "EMI_pm_2_5",
                    "Emis": "PM2_5",
                    "Desc": "Fine particulate matter",
                }
            ],
            "osy-scenarios": [
                {
                    "ScenarioId": "SC_base_case",
                    "Scenario": "BASE",
                    "Desc": "Base",
                }
            ],
        },
    )
    identifiers = {
        "SC_base_case": {
            "TechId": "TEC_envland_v12",
            "CommId": "COM_env_lcrp_v12",
            "EmisId": "EMI_pm_2_5",
        }
    }
    if extra_id:
        identifiers["SC_base_case"]["OtherTechId"] = extra_id
    write_json(model / "RT.json", {"TEST": identifiers})
    write_json(
        model / "view" / "resData.json",
        {"osy-cases": [{"Case": "BASE_V14"}]},
    )
    results = model / "res" / "BASE_V14" / "results.txt"
    results.parent.mkdir(parents=True)
    results.write_text("Optimal - objective value 1\n", encoding="utf-8")
    return model


def make_gate_model(root: Path) -> Path:
    """A model holding one referenced and one unreferenced object of each kind."""
    model = root / "GateModel"
    write_json(
        model / "genData.json",
        {
            "osy-casename": "GateModel",
            "osy-years": ["2020"],
            "osy-tech": [
                {"TechId": "TEC_live_v1", "Tech": "PWRSOL", "Desc": "Solar"},
                {"TechId": "TEC_dead_v1", "Tech": "PWRDEAD", "Desc": "Unused"},
            ],
            "osy-comm": [
                {"CommId": "COM_live_v1", "Comm": "ELC001", "Desc": "Electricity"},
                {"CommId": "COM_dead_v1", "Comm": "COMDEAD", "Desc": "Unused"},
            ],
            "osy-emis": [
                {"EmisId": "EMI_live_v1", "Emis": "CO2", "Desc": "Carbon dioxide"},
                {"EmisId": "EMI_dead_v1", "Emis": "CH4", "Desc": "Unused"},
            ],
            "osy-scenarios": [{"ScenarioId": "SC_0", "Scenario": "BASE", "Desc": "Base"}],
        },
    )
    write_json(
        model / "RYTCM.json",
        {"OAR": {"SC_0": [{"TechId": "TEC_live_v1", "CommId": "COM_live_v1", "2020": 1}]}},
    )
    write_json(
        model / "RYTE.json",
        {"EAR": {"SC_0": [{"TechId": "TEC_live_v1", "EmisId": "EMI_live_v1", "2020": 0.1}]}},
    )
    return model


class RemovableGateTest(unittest.TestCase):
    """`--removable` is the precondition for a structural fix that cannot move a result."""

    def run_gate(self, tmp: str, *identifiers: str, json_path: Path | None = None):
        argv = ["--datastorage", tmp, "GateModel", "--removable", *identifiers]
        if json_path is not None:
            argv += ["--json", str(json_path)]
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = AUDIT.main(argv)
        return code, buffer.getvalue()

    def test_unreferenced_technology_is_removable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_gate_model(Path(tmp))
            code, out = self.run_gate(tmp, "TEC_dead_v1")
        self.assertEqual(code, 0)
        self.assertIn("REMOVABLE", out)

    def test_referenced_technology_is_blocked_and_names_the_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_gate_model(Path(tmp))
            code, out = self.run_gate(tmp, "TEC_live_v1")
        self.assertNotEqual(code, 0)
        self.assertIn("RYTCM.json", out)
        self.assertIn("RYTE.json", out)

    def test_undefined_id_is_not_removable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_gate_model(Path(tmp))
            code, out = self.run_gate(tmp, "TEC_never_existed")
        self.assertNotEqual(code, 0)
        self.assertIn("NOT DEFINED", out)

    def test_unrecognized_prefix_is_reported_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_gate_model(Path(tmp))
            code, out = self.run_gate(tmp, "PWRSOL")
        self.assertEqual(code, 2)
        self.assertIn("BAD PREFIX", out)

    def test_commodities_and_emissions_are_handled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_gate_model(Path(tmp))
            clean, _ = self.run_gate(tmp, "COM_dead_v1", "EMI_dead_v1")
            blocked, out = self.run_gate(tmp, "COM_live_v1", "EMI_live_v1")
        self.assertEqual(clean, 0)
        self.assertNotEqual(blocked, 0)
        self.assertIn("RYTCM.json", out)
        self.assertIn("RYTE.json", out)

    def test_one_blocked_id_fails_the_whole_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_gate_model(Path(tmp))
            code, out = self.run_gate(tmp, "TEC_dead_v1", "COM_dead_v1", "COM_live_v1")
        self.assertNotEqual(code, 0)
        self.assertIn("NOT REMOVABLE", out)

    def test_gate_suppresses_the_full_audit_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_gate_model(Path(tmp))
            _, out = self.run_gate(tmp, "TEC_dead_v1")
        self.assertNotIn("findings:", out)
        self.assertNotIn("SUMMARY", out)

    def test_json_report_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_gate_model(Path(tmp))
            report_path = Path(tmp) / "reports" / "removable.json"
            code, _ = self.run_gate(
                tmp, "TEC_dead_v1", "TEC_live_v1", json_path=report_path
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertNotEqual(code, 0)
        self.assertIs(report["removable"], False)
        self.assertEqual([item["id"] for item in report["objects"]],
                         ["TEC_dead_v1", "TEC_live_v1"])
        self.assertEqual(sorted(report["objects"][0]),
                         ["id", "reason", "referenced_in", "removable"])
        self.assertIs(report["objects"][0]["removable"], True)
        self.assertEqual(report["objects"][0]["referenced_in"], [])
        self.assertIs(report["objects"][1]["removable"], False)
        self.assertEqual(report["objects"][1]["referenced_in"],
                         ["RYTCM.json", "RYTE.json"])
        self.assertTrue(report["objects"][1]["reason"])


class MergedCheckTest(unittest.TestCase):
    """Checks absorbed from assess-clews-calibration/scripts/audit_muiogo_model.py."""

    def test_only_exactly_equal_bound_pairs_are_flagged(self) -> None:
        parameters = {
            "TAL": {"SC_0": [{"TechId": "TEC_a_v1", "2020": 3.0, "2025": 1.0}]},
            "TAU": {"SC_0": [{"TechId": "TEC_a_v1", "2020": 3.0, "2025": 9.0}]},
            "TAMinC": {"SC_0": [{"TechId": "TEC_b_v1", "2020": 1.0}]},
            "TAMaxC": {"SC_0": [{"TechId": "TEC_b_v1", "2020": 2.0}]},
        }
        matches = AUDIT.exact_bound_matches(parameters, ["2020", "2025"])
        self.assertEqual(
            [(m["lower_parameter"], m["year"]) for m in matches], [("TAL", "2020")]
        )
        self.assertEqual(matches[0]["identity"]["TechId"], "TEC_a_v1")
        self.assertEqual(matches[0]["kind"], "annual activity")

    def test_year_split_covers_every_scenario_and_year(self) -> None:
        parameters = {
            "YS": {
                "SC_0": [
                    {"Ts": "S1D1", "2015": 0.5, "2020": 0.4},
                    {"Ts": "S2D1", "2015": 0.5, "2020": 0.4},
                ],
                "SC_pol_v1": [{"Ts": "S1D1", "2015": 0.7}],
            }
        }
        issues = AUDIT.year_split_issues(parameters, ["2015", "2020", "2025"])
        # 2025 holds no YearSplit value at all, so it is unpopulated, not unnormalized.
        self.assertEqual(
            [(i["scenario"], i["year"]) for i in issues],
            [("SC_0", "2020"), ("SC_pol_v1", "2015")],
        )

    def test_inventory_does_not_truncate_underscore_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = AUDIT.inventory(str(make_model(Path(tmp))))
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["reference_counts"]["technology"], 1)
        codes = [item["code"] for item in report["findings"]]
        self.assertNotIn("unknown_technology_references", codes)
        self.assertNotIn("unknown_commodity_references", codes)
        self.assertNotIn("unknown_scenario_references", codes)

    def test_calibration_shim_delegates_to_this_audit(self) -> None:
        shim_path = (
            Path(__file__).resolve().parents[1]
            / "assess-clews-calibration"
            / "scripts"
            / "audit_muiogo_model.py"
        )
        if not shim_path.is_file():
            self.skipTest("assess-clews-calibration is not installed alongside this skill")
        spec = importlib.util.spec_from_file_location("muiogo_shim", shim_path)
        shim = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(shim)
        self.assertEqual(
            Path(shim.audit_module().__file__).resolve(), AUDIT_PATH.resolve()
        )
        with tempfile.TemporaryDirectory() as tmp:
            model = make_model(Path(tmp))
            output = Path(tmp) / "inventory.json"
            code = shim.main([str(model), "--output", str(output)])
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(report["metadata"]["case_name"], "UnderscoreIds")


class AuditRegressionTest(unittest.TestCase):
    def test_complete_underscore_ids_and_run_label_are_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = AUDIT.audit_model(
                str(make_model(Path(tmp)))
            )
        messages = [message for _, message in report.findings]
        self.assertFalse(
            any("missing from genData" in message for message in messages)
        )
        self.assertFalse(
            any("defined but never referenced" in message for message in messages)
        )
        self.assertFalse(
            any("scenario labels" in message for message in messages)
        )

    def test_unknown_underscore_id_is_reported_in_full(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = AUDIT.audit_model(
                str(make_model(Path(tmp), "TEC_missing_part"))
            )
        failures = [
            message
            for level, message in report.findings
            if level == "FAIL"
        ]
        self.assertTrue(
            any("TEC_missing_part" in message for message in failures)
        )


class BoundSentinelTests(unittest.TestCase):
    """Upstream OSeMOSYS activates bounds asymmetrically.

    Upper limits are guarded ``<> -1`` (TCC1/NCC1/AAC2/TAC2) and lower limits
    ``> 0`` (TCC2/NCC2/AAC3/TAC3), so -1 disables a bound while 0 is a live upper
    bound that pins the variable to zero. See osemosys.txt:195, which itself
    branches on both ``<> 0`` and ``<> -1``.
    """

    @staticmethod
    def _pair(lower, upper):
        return {
            "TAMinC": {"SC_0": [{"TechId": "TEC_a_v1", "2020": lower}]},
            "TAMaxC": {"SC_0": [{"TechId": "TEC_a_v1", "2020": upper}]},
        }

    def test_inactive_sentinel_pair_is_not_a_lock(self) -> None:
        # -1/-1 is the default "no limit" row: it constrains nothing at all.
        self.assertEqual(
            AUDIT.exact_bound_matches(self._pair(-1.0, -1.0), ["2020"]), []
        )

    def test_matching_positive_pair_is_a_lock(self) -> None:
        matches = AUDIT.exact_bound_matches(self._pair(5.0, 5.0), ["2020"])
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["value"], 5.0)

    def test_active_zero_upper_bound_is_reported(self) -> None:
        # 0 is not a sentinel: it switches the technology off for that year, and
        # it needs no matching lower bound to bite.
        params = {"TAMaxC": {"SC_0": [{"TechId": "TEC_b_v1", "2020": 0.0}]}}
        self.assertEqual(AUDIT.exact_bound_matches(params, ["2020"]), [])
        forced = AUDIT.forced_off_bounds(params, ["2020"])
        self.assertEqual(len(forced), 1)
        self.assertEqual(forced[0]["upper_parameter"], "TAMaxC")

    def test_no_limit_upper_bound_is_not_forced_off(self) -> None:
        params = {"TAMaxC": {"SC_0": [{"TechId": "TEC_c_v1", "2020": -1.0}]}}
        self.assertEqual(AUDIT.forced_off_bounds(params, ["2020"]), [])


class YearSplitToleranceTests(unittest.TestCase):
    """Match upstream's own tolerance (osemosys.txt:200-201: 0.9999 / 1.0001)."""

    @staticmethod
    def _ys(*values):
        return {"YS": {"SC_0": [{"Ts": f"Ts_{i}", "2020": v}
                                for i, v in enumerate(values)]}}

    def test_rounding_within_upstream_tolerance_passes(self) -> None:
        # Sums to 0.99995 - accepted by OSeMOSYS's own check, so we must accept it.
        self.assertEqual(
            AUDIT.year_split_issues(self._ys(0.49997, 0.49998), ["2020"]), []
        )

    def test_real_normalization_error_still_fails(self) -> None:
        self.assertEqual(
            len(AUDIT.year_split_issues(self._ys(0.5, 0.4), ["2020"])), 1
        )


if __name__ == "__main__":
    unittest.main()
