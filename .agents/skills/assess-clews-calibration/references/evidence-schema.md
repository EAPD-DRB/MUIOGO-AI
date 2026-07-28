# Evidence and file schemas

## Historical comparison CSV

Required columns:

| Column | Meaning |
|---|---|
| `domain` | `energy`, `land`, `water`, `climate`, or `nexus` |
| `metric` | Human-readable outcome, such as electricity generation from hydro |
| `observed` | Historical observation |
| `modeled` | Model result at matching scope |
| `tolerance` | Allowed relative error as a fraction, for example `0.10` |
| `forcing_class` | `E`, `J`, or `H` |

Recommended columns:

| Column | Meaning |
|---|---|
| `phase` | `calibration` or `validation` |
| `weight` | Decision/materiality weight; default 1 |
| `year`, `period`, `region`, `unit` | Alignment metadata |
| `source` | Observation source or evidence-register ID |
| `tolerance_absolute` | Required instead of relative tolerance when observed is zero |
| `constraint_refs` | Model parameters/constraints relevant to forcing |
| `notes` | Transformation, uncertainty, or interpretation |

The script rejects negative tolerances, nonpositive weights, invalid forcing classes, and zero observations without an absolute tolerance.

## Assessment JSON

```json
{
  "model": {
    "name": "Example CLEWs",
    "country": "Exampleland",
    "version": "commit-or-release",
    "claimed_scope": ["energy", "land", "water", "climate", "nexus"],
    "calibration_period": "2018-2020",
    "validation_period": "2021",
    "intended_use": "national policy option comparison"
  },
  "gates": {
    "executable_case": {"status": "pass", "evidence": "solver log ..."},
    "referential_integrity": {"status": "pass", "evidence": "inventory ..."},
    "physical_accounting": {"status": "pass", "evidence": "balance tests ..."},
    "scope_integrity": {"status": "pass", "evidence": "domain/link map ..."},
    "historical_evidence": {"status": "pass", "evidence": "evidence register ..."},
    "forcing_disclosure": {"status": "pass", "evidence": "constraint audit ..."},
    "reproducibility": {"status": "pass", "evidence": "versioned run bundle ..."}
  },
  "dimensions": {
    "evidence_provenance": {"score": 80, "rationale": "...", "evidence": ["..."]},
    "country_representation": {"score": 75, "rationale": "...", "evidence": ["..."]},
    "historical_initial_state": {"score": 78, "rationale": "...", "evidence": ["..."]},
    "physical_accounting_integrity": {"score": 90, "rationale": "...", "evidence": ["..."]},
    "historical_reproduction": {"score": 74, "rationale": "...", "evidence": ["history.json"]},
    "nexus_fidelity": {"score": 70, "rationale": "...", "evidence": ["..."]},
    "forcing_independence": {"score": 72, "rationale": "...", "evidence": ["..."]},
    "heldout_validation": {"score": 65, "rationale": "...", "evidence": ["history.json"]},
    "robustness_reproducibility": {"score": 70, "rationale": "...", "evidence": ["..."]}
  },
  "domains": {
    "energy": {"score": 78, "rationale": "..."},
    "land": {"score": 72, "rationale": "..."},
    "water": {"score": 69, "rationale": "..."},
    "climate": {"score": 76, "rationale": "..."},
    "nexus": {"score": 66, "rationale": "..."}
  },
  "forcing": {
    "endogenous_weight": 60,
    "justified_weight": 25,
    "history_fixed_weight": 15
  },
  "heldout_validation_present": true,
  "robustness_tests_present": true,
  "confidence": "medium",
  "fitness": [
    {
      "use": "national policy option comparison",
      "rating": "conditionally suitable",
      "rationale": "Improve water and nexus validation before formal use."
    }
  ],
  "strengths": ["..."],
  "weaknesses": ["..."],
  "required_improvements": ["..."]
}
```

All seven gates, nine dimensions, and all claimed domains are required. Scores must be integers or decimals from 0 through 100. Rationales must be substantive; the scoring script validates structure but cannot verify truth.

If a dimension genuinely does not apply, explain why in the assessment and map the scope correctly rather than deleting a required dimension. For a non-nexus OSeMOSYS assessment, score `nexus_fidelity` on appropriate sector coupling and explicitly note the limited scope.
