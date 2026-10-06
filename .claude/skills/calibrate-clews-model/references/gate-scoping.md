# Gate scoping by parameter family

## Contents

- [Why scope by constraint block](#why-scope-by-constraint-block)
- [Gates that always apply](#gates-that-always-apply)
- [Gates that can be scoped](#gates-that-can-be-scoped)
- [Bound semantics in MUIO](#bound-semantics-in-muio)
- [Family table](#family-table)
- [Two easy mistakes](#two-easy-mistakes)
- [Recording a scoped gate](#recording-a-scoped-gate)

## Why scope by constraint block

A fuel price and an initial stock are both "one number". They do not carry the
same risk. What matters is which constraint block the parameter enters. This
table names those blocks for MUIO's active formulation,
`WebAPP/SOLVERs/model.v.5.4.txt`, with defaults from
`WebAPP/DataStorage/Parameters.json`.

It is a starting point, not a substitute for step 3. Read the local equation
before relying on a row. If the local formulation differs from the one named
here, the local file wins; record the difference.

Do not use upstream OSeMOSYS names here. MUIO has no `E3` (the penalty is
`E5`), no `EBa1`–`EBa8`, and no `EQ_SpecifiedDemand` (demand enters at `EBa9`
and `EBa11`). It has no `RM1`, and `RM3` is commented out.

## Gates that always apply

These gates apply to every change, including an explicitly requested single
change:

- `identifier_integrity`
- `equation_unit_replay`. This is where a good number lands in the wrong
  family or the wrong ratio direction.
- `generated_data_inspection`
- `schema_ledger_validation`
- `no_forcing_audit`. It catches unintended pins, exact activity bounds and
  arbitrary release years.
- At promotion: `solver_run`, `baseline_comparison`, `live_regeneration` and
  `result_free_archive_identity`.

The package validator also checks the source-diff allowlist on every material
stage. That check cannot be scoped.

## Gates that can be scoped

- `stock_resource_account_checks` and `matrix_check` may be `not_applicable`
  in any package, with a reason.
- `connectivity_review` may be `not_applicable` only for an explicitly
  requested single change, and only when the family row below says the change
  cannot alter connectivity. The package must declare
  `scope.mode = "explicit_single_change"`; see
  [Recording a scoped gate](#recording-a-scoped-gate).

A change between zero and nonzero is never a value-only change. It adds or
removes a link, an emission route, or a guarded constraint. Run
`connectivity_review` for it whatever the family.

## Bound semantics in MUIO

Lower bounds are guarded `> 0` (`TCC2`, `NCC2`, `AAC3`, `TAC3`). A zero lower
bound creates no row.

Upper bounds `TCC1`, `NCC1`, `AAC2`, `TAC2` and the emission limits `E8`, `E9`
have no guard. MUIO keeps them slack with the default `999999` (`TAMaxC`,
`TAMaxCI`, `TAU`, `TMPAU`, `AEL`, `MPEL`). So:

- `-1` does not disable an upper bound in MUIO. It sets a negative limit, and
  the model is infeasible.
- Check that `999999` really is slack in the case's units. A model-period
  emission total in kilotonnes can exceed it.

`LU1` (mode upper limit) is guarded `<> 0`, with default `99999`. A zero there
removes the row; it does not force zero activity. `LU3` and `LU4` are guarded
`<> 0`. `LU2` has no guard, but its default `0` is slack.

## Family table

"Enters" lists the active blocks in `model.v.5.4.txt`. "Objective" means the
`cost` objective. "Extra checks" adds to the always-gates above.

| Family | Enters | Extra checks | `connectivity_review` for a single change |
|---|---|---|---|
| `VariableCost` | `OC1` and objective only | Compare the objective | May be scoped if the value stays positive. Zero or negative feeds the unlimited-free supply test. |
| `FixedCost` | `OC2` and objective only | Compare the objective | May be scoped if the value stays positive |
| `CapitalCost` | `CC1`, `SV1`, `SV2` and objective | Compare the objective | May be scoped if the value stays positive |
| `DiscountRate`, `DiscountRateIdv` | Objective, `SV1`, `SV2`, `SV4`. Both also set `CapitalRecoveryFactor` and `PvAnnuity`, which the application computes in `API/Classes/Case/DataFileClass.py`. | Inspect the generated `CapitalRecoveryFactor` and `PvAnnuity`. A rate of zero writes `None` there. | May be scoped |
| `EmissionsPenalty` | `E5` and objective only | Compare the objective | May be scoped |
| `EmissionActivityRatio` | `E1`, `E2`, `E5`, objective, and the unguarded limits `E8`, `E9` | If any `AnnualEmissionLimit` or `ModelPeriodEmissionLimit` is below `999999`, check emissions headroom before solving. | Required. The emission account is a physical link. |
| `EmissionToActivityChangeRatio` | `E10`, then `E2`, `E5`, `E8`, `E9` and objective through `EmissionByActivityChange` | Same headroom check | Required |
| `AnnualEmissionLimit`, `ModelPeriodEmissionLimit` | `E8`, `E9` (no guard) | A documented real-world constraint, so `no_forcing_audit` disposition. Never use `-1` to disable. | May be scoped |
| `InputActivityRatio`, `OutputActivityRatio` | `EBa11`, `EBb4`, `EBb4_EnergyBalanceEachYear4_ICR` | Commodity-balance replay; check ratio direction | Required |
| `SpecifiedAnnualDemand`, `SpecifiedDemandProfile` | `EBa9`, `EBa11` | Commodity-balance replay; profile sums | May be scoped if no cell moves between zero and nonzero |
| `AccumulatedAnnualDemand` | `EBb4`, `EBb4_EnergyBalanceEachYear4_ICR` | Commodity-balance replay | May be scoped if no cell moves between zero and nonzero |
| `ResidualCapacity` | `CAa2`, `CAa4`, `CAb1`, `OC2`, `TCC1`, `TCC2`, objective, every year | Every-year capacity envelope. Stock above `TotalAnnualMaxCapacity` makes `TCC1` infeasible. Use `stock_resource_account_checks` when a stock account is declared. | Required. It feeds the "effectively unbounded" test. |
| `OperationalLife` | `CAa1`, `CAa2`, `CAa4`, `CAb1`, `OC2`, `TCC1`, `TCC2`, `SV1`–`SV3`, objective, and `CapitalRecoveryFactor`/`PvAnnuity` | Vintage survival and full-horizon replacement; compare the objective, since salvage moves too | Required. It changes temporal coupling. |
| `CapacityFactor` | `CAa4`, `CAb1` | Every-year, every-timeslice capacity envelope | May be scoped if no cell moves between zero and nonzero |
| `AvailabilityFactor` | `CAb1` | Every-year capacity envelope | May be scoped if no cell moves between zero and nonzero |
| `CapacityToActivityUnit` | `CAa4`, `CAb1` | Unit replay; every-year envelope | May be scoped |
| `CapacityOfOneTechnologyUnit` | `CAa5` (guarded `<> 0`); makes `NumberOfNewTechnologyUnits` integer | `matrix_check` and a runtime check, since it turns the solve into a MIP | Required when it moves from zero |
| `TotalAnnualMaxCapacity`, `TotalAnnualMaxCapacityInvestment` | `TCC1`, `NCC1` (no guard) | `no_forcing_audit`; for `TAMaxCI` follow [deployment-envelopes.md](deployment-envelopes.md) | Required. A bound can create or remove an unbounded route. |
| `TotalAnnualMinCapacity`, `TotalAnnualMinCapacityInvestment` | `TCC2`, `NCC2` (guarded `> 0`) | `no_forcing_audit` | Required |
| `TotalTechnologyAnnualActivityUpperLimit` / `LowerLimit` | `AAC2` (no guard) / `AAC3` (guarded `> 0`) | `no_forcing_audit` | Required |
| `TotalTechnologyModelPeriodActivityUpperLimit` / `LowerLimit` | `TAC2` (no guard) / `TAC3` (guarded `> 0`) | `no_forcing_audit` | Required |
| `TechnologyActivityByModeUpperLimit` / `LowerLimit` | `LU1` (guarded `<> 0`) / `LU2` | `no_forcing_audit` | Required |
| `TechnologyActivityIncreaseByModeLimit`, `...DecreaseByModeLimit` | `LU3`, `LU4` (guarded `<> 0`) | `no_forcing_audit`; adjacent-year transition check | Required |
| `InputToNewCapacityRatio`, `InputToTotalCapacityRatio` | `INC1`, `ITC1` (guarded `<> 0`), then `EBb4_EnergyBalanceEachYear4_ICR` | Commodity-balance replay | Required |
| `TradeRoute` | `EBa11`, `EBb4`, `EBb4_EnergyBalanceEachYear4_ICR` | Commodity-balance replay | Required |
| `UDCMultiplier*`, `UDCConstant`, `UDCTag` | `UDC1` (tag 0) or `UDC2` (tag 1) | `no_forcing_audit`; `matrix_check` | Required |
| Storage parameters | `S3`, `S4`, `S14`, `S9_and_S10`, `S11_and_S12`, `S39_*`, `SC1`–`SC4`, `SI2`–`SI4`, `SI6`, `SI7`, `SI9`, objective | `matrix_check` | Required |
| New or re-roled technologies, modes or sets | Structural | Role coverage, derived-set inspection, `matrix_check`, `glpsol --check` | Required. Not a single parameter change. |

No active constraint uses these. Do not calibrate them in this formulation;
record the need as a gap instead:

- `ReserveMargin` and its tags. The parameters and `RM3` are commented out.
- `ModelPeriodExogenousEmission`. It is declared but used by no constraint.
- `StorageLevelStart`. It is declared but unused; `S30` fixes the year-start
  storage level at zero.

## Two easy mistakes

- **A cost is cheap.** `VariableCost`, `FixedCost` and `CapitalCost` enter no
  limiting constraint; they only move the objective. The always-gates and one
  solve are enough, as long as the cost stays positive.
- **An emissions factor is not a cost.** It reaches `E8` and `E9`, which have
  no guard. With the `999999` default they are slack. Once a real limit is set,
  the same edit can make the model infeasible.

## Recording a scoped gate

In `calibration-package.json`:

```json
"scope": {
  "mode": "explicit_single_change",
  "requested_by": "User request of 2026-10-05: update coal CapitalCost from the national tariff study",
  "gate_scoping_row": "CapitalCost"
},
"gates": {
  "connectivity_review": {
    "status": "not_applicable",
    "artifact": null,
    "reason": "CapitalCost enters CC1, SV1, SV2 and the objective only; the new value stays positive (gate-scoping.md)"
  }
}
```

The validator accepts this only when `changes` holds exactly one
`parameter_update`. Every other mandatory gate still needs a passing report.
A wave uses `"mode": "wave"` or omits `scope`, and runs every gate.
