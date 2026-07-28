# MUIO JSON implementation workflow

Use this reference while writing the model-specific generator. Inspect the host repository because MUIO forks differ.

## Contents

1. Source files
2. Safe generator contract
3. Parameter coverage
4. Scenario inheritance
5. Constraint construction
6. Mandatory ENV_WATER fallback publication
7. Regeneration
8. Validation

## 1. Source files

Typical case files under `WebAPP/DataStorage/<case>` include:

| File | Environmental-accounting role |
|---|---|
| `genData.json` | Technologies, commodities, emissions, groups, constraints, scenarios, years, timeslices, modes, and metadata |
| `RT.json` | Region-technology parameters such as discount rate and model-period activity limit |
| `RYT.json` | Annual technology costs, residual capacity, availability, and annual activity/capacity bounds |
| `RYTM.json` | Mode-specific annual variable cost and mode activity limits |
| `RYTTs.json` | Technology-timeslice parameters such as capacity factor |
| `RYC.json` | Annual commodity demands and reserve-margin metadata |
| `RYCTs.json` | Commodity demand profiles by timeslice |
| `RYTCM.json` | Input and Output Activity Ratios by technology, commodity, mode, and year |
| `RYCn.json` | Annual constraint constants |
| `RYTCn.json` | Technology multipliers for constraints |
| `RYTEM.json` | Emission Activity Ratios and activity-change emission ratios |
| `view/resData.json` | Saved case/scenario combinations; copy definitions, refresh valid runtime metadata |

Use `WebAPP/DataStorage/Parameters.json` to obtain defaults. Do not assume every fork has exactly these parameter identifiers.

## 2. Safe generator contract

The generator should:

1. Reject any source other than the explicitly named model.
2. Reject source and target paths that resolve to the same directory.
3. Recursively fingerprint every copied input, including selected nested view definitions.
4. Copy only source JSON and selected view definitions into a separate target.
5. Detect identifier and human-readable-name collisions before appending.
6. Reject source/target symlink or ancestor relationships that could overwrite the source.
7. Support `--dry-run`; write formatted UTF-8 JSON to a temporary sibling and atomically rename only after validation.
8. Validate the generated case and an allowlisted structural diff.
9. Re-fingerprint the source and fail if it changed.
10. Derive expected technology, commodity, and constraint counts from the account definitions rather than hardcoding totals.
11. Assert that explicitly excluded names and IDs do not appear in the generated accounting structures.

Make target replacement explicit with an `--overwrite` flag. Preserve saved results, validation reports, and model-fix documents separately before overwriting a derived case. Validate a staged sibling first; if a target exists, rename it to a recoverable backup, rename the stage into place, and restore the backup on failure. Retain the backup until the promoted case passes generation, preprocessing, matrix validation, optimization, closure, and regression checks. If generation and computational validation are separate commands, leave the backup in place and report its path until acceptance. Write timestamped or uniquely labeled validation reports so a rerun cannot erase baseline-control or disposable-run evidence.

When migrating an older environmental-accounting case, treat category-specific terminals as an explicit replacement set. Preserve their physical input commodities, remap those commodities to the documented modes of `ENV_WATER` or `ENV_LAND`, and remove only the superseded technologies and their parameter rows. Reconstruct the aggregate constraints from effective source ratios instead of summing or copying old terminal-specific multipliers blindly.

## 3. Parameter coverage

Adding a technology or commodity to `genData.json` is insufficient. Append complete rows for every parameter family that MUIO expects.

For each terminal technology whose domain independently passes the exactness
proof, and for the unforced `ENV_WATER` fallback when its proof fails:

- always add `ENV_WATER`, with one documented operating mode per category;
  add its forcing constraint only when the exactness proof passes; add
  `ENV_LAND` only when its independent proof passes;
- require every input to a given terminal to use the same physical unit;
- set exactly one IAR of 1 for each active terminal mode and no terminal output;
- use zero capital, fixed, and variable costs;
- use availability/capacity factors consistent with unconstrained annual accounting;
- provide sufficient residual capacity and nonbinding activity limits;
- prevent investment when residual accounting capacity is intended;
- populate every year, timeslice, mode, and scenario record expected by the host model.

Increase the global operating-mode count if an implemented terminal needs a higher mode ID than the source model provides. Inspect the host generation loops and densify every mode-indexed JSON family they traverse—not only rows belonging to the new terminals. Common examples are `RYTM.json`, `RYTCM.json`, `RYTEM.json`, and any storage-mode table. Use the host parameter defaults for inactive base rows and its normal `null` convention for inheriting scenarios. After preprocessing, verify `MODEperTECHNOLOGY`: every original technology retains exactly its intended modes, while each implemented `ENV_WATER` or `ENV_LAND` terminal contains only its documented modes.

Derive capacity settings from the host equations: the maximum feasible terminal activity must remain below residual capacity multiplied by capacity-to-activity conversion and effective availability/capacity factors. Set investment limits to zero when the terminal is not an investment option, and keep annual/model-period activity bounds nonbinding unless implementing a proven-fixed account. For the unforced `ENV_WATER` fallback, use a defensible production envelope or the host's documented unbounded convention rather than an arbitrary large value. For other domains, stop or use reporting-only accounting when no safe envelope exists.

For stock commodities:

- append annual commodity defaults;
- append timeslice demand-profile defaults if the file schema requires them;
- add metadata and units in `genData.json`.

For constraints:

- add constraint metadata and connected technology IDs;
- add annual constants using the host equality tag and zero right-hand side;
- add annual technology multipliers;
- inspect the solver file to verify tag semantics and equations.

Never copy a Namibia internal ID such as `TEC_*`, `COM_*`, or `CO_*` into another model.

## 4. Scenario inheritance

MUIO models commonly store full values in the base scenario and `null` in policy scenarios to inherit the base. Preserve the target model's convention.

Before deriving balance coefficients, resolve whether non-base scenarios override any connected IAR/OAR values. If they do, either:

- construct case-combination-aware coefficients; or
- stop the exact forcing attempt and use the `ENV_WATER` publication fallback
  for water, or reporting-only accounting for another domain.

Do not silently use base coefficients for a scenario with effective ratio changes.

Inspect the host MUIO scenario resolver (for example `getScOrder` and the parameter-generation loops) and reproduce its exact precedence; do not assume list order. The usual conceptual pattern is parameter defaults, then base values, then active-scenario non-null overrides. Resolve independently for every full index tuple, region, mode, and year. If two saved-case combinations require different coefficients but MUIO exposes only one shared constraint parameterization, stop rather than generating a misleading account.

## 5. Constraint construction

For each environmental domain `D`, first define the set of same-unit commodities consumed by the modes of `ENV_WATER` or `ENV_LAND`. For every connected region, technology, mode, and year, derive:

```text
net[D,r,t,m,y]
  = sum[c in D] (
      effective_OAR[r,t,c,m,y] - effective_IAR[r,t,c,m,y]
    )
```

The common MUIO CAM (Constraint Activity Multiplier) is technology-level, not mode-level. For each original technology, require `net[D,r,t,m,y]` to be identical in every active mode. That common value is the technology's aggregate coefficient. If the values differ by mode, stop: a single technology-level CAM cannot reproduce the commodity balances exactly.

Add every terminal mode's IAR first. Because each is 1, the total-activity coefficient of the corresponding terminal is `-1`. Construct one zero-right-hand-side equality per domain:

```text
sum[t] alpha[D,r,t,y] * TotalAnnualTechnologyActivity[r,t,y]
- TotalAnnualTechnologyActivity[r,ENV_D,y]
= represented demand/capacity/trade terms
```

Individual commodity balances make every category residual nonnegative. The aggregate equality sets the sum of residuals to zero, forcing every terminal mode to consume its full mapped residual. Include only original technologies with a nonzero aggregate coefficient in at least one year, plus the corresponding terminal.

This proof is valid only when all non-activity balance terms are represented. Inspect annual demand, accumulated demand, trade, new-capacity inputs, total-capacity inputs, and any fork-specific terms. If the UDC cannot represent one of them, use the mandatory unforced-terminal/Pivot-publication fallback for `ENV_WATER`; use reporting-only accounting or request a mode-aware extension for another domain.

For a zero-right-hand-side equality, scaling every coefficient by the same value preserves the identity. Use scaling only to improve conditioning and validate closure from unscaled physical results.

Keep account selection separate from coefficient provenance. Build each domain's producer and consumer membership from the actual commodity links and effective ratios, not from the list of technologies assigned to environmental groups. Use the complete physical contributor set when deriving coefficients and finite activity/capacity envelopes.

## 6. Mandatory ENV_WATER fallback publication

Use this fallback automatically when the exact `ENV_WATER` proof fails. Do
not stop at a reporting-only water ledger and do not ask for another
authorization. Keep the source and an unchanged control intact, and generate
a clearly labeled derived case whose name or metadata states that water is
unforced and postprocessed. Inform the user that the fallback is active and
that publication is required after every solve.

The fallback terminal must:

- consume one mapped same-unit commodity at IAR 1 in each documented mode;
- have no OAR, demand, forcing UDC, policy target, or negative/positive cost
  that could encourage or discourage activity;
- prohibit investment and use finite residual capacity plus annual and
  model-period activity bounds derived from a defensible source-production
  envelope;
- remain nonbinding in every solved run; and
- be described in model metadata as unforced, non-authoritative, and
  unsuitable for use without reconciliation.

Calculate the authoritative reference independently as:

```text
reference[r,c,y]
  = production_by_all_technologies[r,c,y]
  - use_by_all_technologies_except_ENV_WATER[r,c,y]
```

Excluding the terminal's own use prevents double subtraction. Compare that
reference with the terminal's annual activity by matching mode. For every run,
region, year, and mode, write:

```text
reference_available
terminal_counted
unaccounted_gap = reference_available - terminal_counted
coverage_percent = 100 * terminal_counted / reference_available
status = FULL | PARTIAL | ZERO | EMPTY | INVALID
```

Use a declared result-precision tolerance. `INVALID` means negative,
non-finite, over-counted beyond tolerance, or otherwise inconsistent. The
other statuses are observations: even all-`FULL` results would not prove
structural exactness because another cost-identical solver basis may choose
different slack allocation.

Validate optimality, source hashes, allowlisted JSON changes, active terminal
modes, absence of a forcing mechanism, nonbinding bounds, objective/cost/
demand/emission invariants, and preservation of any exact terminal already in
the source derived case. Retain complete regression differences: adding
zero-cost variables can select a different cost-identical primal solution.

### Required authoritative Pivot publication

Build the post-solve Pivot publisher whenever this fallback is active so the
unforced terminal remains visible in the Dynamic Graph and the authoritative
external reference appears under `ENV_WATER` in Results Pivot.

This is a controlled reporting-layer exception, not an optimizer fix. Keep
the fallback case name and metadata, and never describe the published
values as solver-selected terminal activity.

Build a model-specific publisher that:

1. accepts only the exact fallback case name and rejects symlinks,
   unexpected terminal structure, missing modes, outputs, forcing UDCs, or
   non-optimal runs;
2. calculates each mapped commodity at timeslice resolution as production by
   all technologies minus use by every technology except the fallback
   terminal;
3. reads only raw solver CSVs and hashes them before and after publication;
4. resolves view keys and file locations from the host `Variables.json` and
   result-view generation code;
5. updates every linked fallback activity/use representation consistently;
   in the common MUIO mapping these are `TTMPA`, `TATABM`, `ROA`, `ROUBT`, and
   `UBT`, while `PBT` and `ROPBT` remain unchanged because a terminal with no
   OAR produces nothing;
6. stages the changed views, backs up the original solver-generated files,
   atomically replaces only validated files, and restores the backup on any
   failure;
7. writes a uniquely labeled publication manifest, raw-result/view hashes,
   detailed reference ledger, validation report, and a marker inside the case
   stating that Pivot is postprocessed; and
8. is idempotent when the same raw results have already been published.

MUIO CSV output may round component rows. Declare a precision tolerance,
reject negative residuals beyond it, and handle smaller negative timeslice
artifacts deterministically. If clamping a tiny negative to zero, remove the
same correction from a positive timeslice for that commodity and year so the
authoritative annual total remains exact. Record the maximum and total
adjustments.

Validate that:

- every non-`ENV_WATER` Pivot row is structurally unchanged;
- raw result hashes, parameter JSON, and `genData.json` are unchanged;
- the Dynamic Graph terminal inputs and modes are unchanged;
- annual activity equals published use by mode;
- timeslice activity rate equals published use rate;
- model-period activity equals the sum of published annual activity;
- the independent annual reporter and Pivot agree within declared precision;
  and
- the original solver-generated views remain recoverable.

Every new solve regenerates the views. Require the publisher to be rerun
after each solve, and treat `ENV_WATER` Pivot values as untrusted whenever
publication or validation is missing or fails. Do not silently fall back to
the unforced solver activity.

## 7. Regeneration

Discover the host command with repository search, for example:

```bash
rg -n "def (generateDatafile|batchRun|run)|class DataFile" API WebAPP
```

A common Python API is conceptually:

```python
from Classes.Case.DataFileClass import DataFile

model = DataFile("<derived-case>")
for case in case_names:
    model.generateDatafile(case)
model.batchRun("cbc", case_names)
```

Do not paste this blindly. Confirm import paths, solver names, case metadata, and return status in the host repository.

Generated artifacts may include `data.txt`, `data_processed.txt`, a linear-program file, `results.txt`, CSV result variables, and Pivot/view data. Generate all of them through MUIO.

Do not infer a result key or view-file path from an abbreviation. Read the host `Variables.json` and result-viewer generation code. In forks using the common mapping, `Total Annual Technology Activity By Mode` is stored as `TATABM` in `view/RYTM.json`; `TTMPA` denotes model-period activity and is not a substitute for an annual-by-mode Pivot. Verify the mapping in the target fork before asserting that visualization output exists.

Inspect the processed `MODEperTECHNOLOGY` set before solving. Original technologies must retain their source modes; each implemented `ENV_WATER` or `ENV_LAND` terminal must expose only its documented category modes. Treat a missing, duplicated, or unintended mode as a generation failure.

## 8. Validation

### Structural

- no source hash changed;
- new IDs and names are unique;
- all metadata links reference defined IDs;
- all parameter families contain every new technology/commodity/constraint for every scenario;
- the environmental terminal set always contains `ENV_WATER`, solver-enforced
  when its proof passes and unforced when the publication fallback is active;
  `ENV_LAND` is present only when its independent proof passes;
- no superseded category-specific terminal technologies remain;
- terminal mode dictionaries, input commodities, descriptions, and same-unit requirements agree;
- every terminal mode has exactly one IAR of 1 and no output;
- a fallback `ENV_WATER` has no forcing UDC or demand and is labeled
  unforced/postprocessed;
- its Pivot publisher accepts only that fallback case, writes a
  postprocessed marker, preserves a recoverable solver-view backup, and
  changes only allowlisted terminal rows in resolved host view keys;
- all mode-indexed JSON families are dense enough for the host generator;
- processed `MODEperTECHNOLOGY` retains original modes and contains only documented terminal modes;
- base ratios and constraint multipliers have expected signs and values;
- every connected original technology has one domain net coefficient across all active modes;
- aggregate UDC terms cover every non-activity term in the represented commodity balances;
- policy scenario rows follow inheritance rules;
- generated counts equal the lengths derived from the account definitions;
- explicitly excluded names and IDs are absent from new accounting structures;
- result case metadata has valid timestamps.

### Physical

- every solver-enforced terminal mode equals the unscaled residual of its
  mapped commodity;
- for an unforced `ENV_WATER` fallback, the external reference
  excludes the terminal's own use; every mode-year reports raw terminal
  activity, gap, coverage, and status, while the published Pivot value equals
  the reference rather than asserting that the raw solver activity is exact;
- for the fallback Pivot publication, published annual, timeslice, and
  model-period activity/use identities close and agree with the independent
  reporter while raw solver-result hashes remain unchanged;
- the sum of category residuals equals the unscaled domain UDC identity;
- parallel land-stock outputs equal physical land activity;
- original services remain connected and unchanged;
- technologies excluded from the accounting additions retain their original links and physical contributions to other environmental balances;
- units are internally consistent;
- backstop/dummy production is excluded or separately reported.

### Regression

Compare against saved results from immediately before the change only after verifying that their generated and processed solver inputs match the current source and preprocessing chain. If either differs, label the saved outputs stale and solve a fresh unchanged control. Record the compared hashes, result timestamps, and reason for selecting or rejecting the saved baseline. Store each validation pass under a timestamped or unique label rather than overwriting earlier evidence.

Run the unchanged control and candidate in the same software and solver environment. When preprocessing traverses unordered sets, use the same explicit `PYTHONHASHSEED` and retain both processed-input hashes. A highly degenerate model may select a different cost-identical basis even in the unchanged control; distinguish this from a physical-accounting effect.

Filter only explicitly new account rows. For every intentionally excluded technology or commodity, check that its original links, annual/model-period activity, production, use, costs, and emissions remain unchanged. Also check:

- objective value;
- annual and model-period technology activity;
- capacity and investment;
- demand;
- production and use;
- emissions and activity-change emissions;
- fixed and variable costs;
- policy constraints and backstop activity.

Use both absolute and relative tolerances chosen for each unit, reject non-finite values, retain duplicate dimension keys as errors, and record exact changed keys. Parse every `results.txt` (or host equivalent) and fail on missing or non-optimal status before interpreting numeric comparisons.

When differences occur, identify exact rows, quantify absolute and relative changes, and distinguish physical changes from alternate cost-identical routing.

Assess runtime separately. Compare matrix or LP dimensions and repeated solve timings; do not attribute a one-run timing change to the accounting layer.

### Results interface

- In the Dynamic Graph, verify each in-model mapped commodity feeds the
  correct implemented terminal mode while the original service links remain.
  Confirm that `ENV_WATER` always exists; when its fallback is active, confirm
  that it is labeled unforced and postprocessed. Confirm no terminal exists
  for any other reporting-only domain.
- In Pivot, select `Total Annual Technology Activity By Mode`, filter `Tech`
  to the implemented `ENV_WATER` and/or `ENV_LAND` terminal, include `Mo Id`,
  and interpret the numeric modes with the documented dictionaries. Use the
  generated ledger for reporting-only domains.
- For water, report vapor separately from the sum of useful liquid-water modes. Never interpret total `ENV_WATER` activity as useful liquid water.
- For an unforced `ENV_WATER` fallback, show raw solver activity only beside
  the authoritative reconciliation ledger and state that solver-selected
  `FULL`, `PARTIAL`, `ZERO`, or `EMPTY` coverage is not an exactness proof.
- For the fallback publication, verify the publication marker
  corresponds to the current raw-result hashes, explain that the displayed
  values are postprocessed reporting, and rerun the publisher after every
  solve before interpreting Pivot.

Primary references:

- [OSeMOSYS documentation](https://osemosys.readthedocs.io/en/latest/manual/Introduction.html)
- [MUIO source repository](https://github.com/OSeMOSYS/MUIO)
