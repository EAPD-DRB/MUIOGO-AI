---
name: clews-model-fix
description: Makes structural fixes to a MUIO/OSeMOSYS CLEWs model that cannot change any solved value - removes unreferenced technologies, commodities or emissions, replaces placeholder descriptions, adjusts technology groups - and refuses anything that alters a parameter value. Use when clews-model-review flags such defects or the user asks for that kind of cleanup; value changes go to calibrate-clews-model.
---

# Fix a CLEWs model structurally

For changes that **cannot change any solved value**. These need a mechanical precondition
check and a change record — not a calibration plan, not a control run, not an A/B test, not
a re-solve.

If the change is not in scope below, stop and hand off. Do not widen this skill.

## Triage first

Use this skill only when no parameter value or source data changes. Route any evidence-based
country-data or physical-model refinement to `calibrate-clews-model`. Reject any value chosen
merely to reproduce an observed outcome under
[references/non-forcing.md](references/non-forcing.md); do not route outcome fitting to a
heavier calibration plan.

## In scope

- Delete an unreferenced `TEC_`, `COM_` or `EMI_`.
- Delete an orphaned commodity: defined, but referenced nowhere else.
- Replace a placeholder description (`TBD`, `xxx`, a repeated stub).
- Add or change a `TECHGROUP` assignment. Grouping is interface metadata and must not alter
  parameters.
- Add a deterministic time-set description.
- Correct a cosmetic label.

## Out of scope — stop and say which skill applies

- **Any evidence-based change to a numeric parameter value** → `calibrate-clews-model`.
- **Deleting an object that is still referenced** → the solution can change; use
  `calibrate-clews-model` or the relevant sector skill. This includes a stranded
  commodity (produced by some technology but consumed by nothing): its output rows
  still reference it, so removing it is calibrate's inactive-branch retirement
  procedure, not a fix here.
- **A unit correction that implies a conversion** → `calibrate-clews-model`; it requires a
  calculation and provenance.
- **Anything chosen merely to reproduce an observed outcome** → reject and record a gap.
- A description that encodes a modelling claim rather than a label → treat as a sourced
  model refinement.

## Procedure

1. **Gate.** Prove the object is referenced nowhere but its own definition:

   ```bash
   python <this skill>/audit.py MODEL_DIR --removable TEC_x --json diagnostics/removable.json
   ```

   Exit 0 means removable. Exit non-zero names the files that still reference it — read
   them. If the reference is another definition-only object, clear that one first (it is
   a second change of the same kind), re-run the gate, and record both. If clearing it
   would mean editing a parameter row, stop: that is out of scope here.

   `audit.py` ships in this skill's directory — a synced copy of the one
   `clews-model-review` owns — so the gate runs whether or not that skill is installed.
   It collects referenced IDs from every `*.json` except `genData.json`, so this
   covers activity ratios, costs, bounds, emission ratios and UDC coefficient files. Never
   substitute "it has no input/output ratio" for this gate — a dangling technology can still
   carry a capital cost with a minimum-capacity bound, and deleting that *would* change the
   objective.

2. **Back up**, then make the edit in the case JSON. Never hand-edit `data.txt`, processed
   data, LP/MPS files, solver output, result CSVs or Pivot output.

3. **Confirm.** Re-run `python <this skill>/audit.py MODEL_DIR`. Require: the ID is gone, no new
   findings, and no finding that was absent before.

4. **Record.** One row in `CHANGES.csv`
   ([references/SCHEMA.md](references/SCHEMA.md)) with `class=A`,
   the objects removed, `evidence_path` pointing at the gate output from step 1, and
   `resolve_status=objective_unchanged`. Add one dated line to
   `documentation/HISTORY.md` naming the `change_id`.

5. **Retire lineage, never delete it.** If a removed object had a `MODEL_MAP.csv` row, set
   its `superseded_by` to the `change_id`. Do not delete the row — an earlier model version
   must stay reconstructable.

## No re-solve

When the step 1 gate passes, nothing in the model referenced the object, so no constraint
and no objective term contained it. The solved values cannot change, and re-solving to
prove that is waste.

If a deliverable needs regenerated artifacts, regenerate them and assert the objective is
**identical**. That is packaging, not verification. A changed objective after a passing
gate means the gate was wrong — stop and investigate rather than accepting the new number.

## Done when

- the removability gate exited 0, and its output is retained;
- the post-change audit shows no new findings;
- `CHANGES.csv` has a `class=A` row naming that evidence;
- any affected `MODEL_MAP.csv` row is marked superseded, not deleted;
- `HISTORY.md` names the change.

`SOURCES.csv`, `CALCULATIONS.csv` and `ASSUMPTIONS.csv` are correctly untouched: a Class A
change introduces no source, no calculation and no assumption. That is not a provenance
gap — there is no lineage to record, because no data entered the model.

## Related

- `clews-model-review` — find what needs fixing (`audit.py` without `--removable`).
- `calibrate-clews-model` — evidence-based country-data and physical-model refinements.
- `assess-clews-calibration` — grade a calibration.
