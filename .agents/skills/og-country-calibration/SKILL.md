---
name: og-country-calibration
description: >-
  Calibrates or reviews an OG-Core overlapping-generations country model (OG-USA/PHL/ZAF/IDN/BRA/ETH
  or a new port), single- or multi-industry. Use when setting or checking macro and open-economy
  parameters, gamma, the earnings matrix, demographics, pensions, chi_n, taxes, informality or a
  SAM-based industry split; when porting the model to a new country; or when validating a steady
  state or transition path against country data. Methods and pitfalls, not one country's numbers.
---

# Calibrating an OG-Core country model

Transferable lessons from the OG-Core country family (OG-USA, OG-PHL, OG-ZAF, OG-IDN, OG-BRA,
OG-ETH, and the OG-JPN port). This is a method-and-pitfall playbook, not a table of values. Every
number here is an example; re-derive it for your country. Items carry provenance tags:

- **[family]**: done the same way across most or all repos.
- **[emerging]**: good practice in only one or two repos; adopt it and propagate it.
- **[net-new]**: not done in any repo yet; do it anyway, because it prevents real errors.

Two reading rules:

- **Country tags are provenance, not scope.** `[ZAF]`, `[PHL]`, `[JPN]` record where a lesson was
  learned, never which country it applies to. Where a method really is conditional, the condition is
  a country characteristic stated in the item (agrarian or informal, aid- or remittance-dependent,
  distressed sovereign, rectangular vs diagonal make matrix), never a country name.
- **Best effort on every block, graded honestly.** Most blocks have a ladder from minimal to ideal
  (flat to progressive to microdata PIT; narrative to structural informality; borrowed to re-tilted
  `chi_n`; naive to value-added `io_matrix`; direct solve to continuation). Use the highest rung the
  data supports. When the data is not there, take a lower rung and say so in the docs. A documented
  fallback ("chi_n borrowed from OG-USA, uncalibrated") is a legitimate calibration. An undocumented
  placeholder is the error half this skill exists to prevent (the 0.9 `zeta_K`, the flat 22% PIT,
  the stray bequest tax). Never let one block's missing data stall the rest. For every number, input
  or validation anchor, search for the most authoritative source that exists, starting with the
  national institution that owns it. Named sources here are roles to search by, not a closed list.

Verify every claim against the checked-out ref of the repo in front of you. Sibling docs sometimes
cite a cousin repo's feature branch as if it were canonical, and docs drift from code. Version facts
below are written as checks (`hasattr(...)`) because releases move.

## Which world

This skill acts on **one** world: the runtime installation reached by `muiogo-ai`,
unless the user explicitly asked for their own live one (`muiogo-live`). Never use
bare `muiogo`, and never fall back to it. Every command prints a `world:` line to
stderr — read it, and name that world when you report a result or a number. Worlds
hold different OG checkouts and different model registries, so the same country
model can exist in both at different commits. Locate the checkout you mean with
`muiogo-ai status` rather than assuming a path. Full rules:
`../WORLD_DISCIPLINE.md`.


## The mental model

1. **The packaged `og<xxx>_default_parameters.json` is the source of truth.**
   `Calibration(p, update_from_api=False)` (the class default) fetches nothing and overlays only
   no-op identity values (single-industry `alpha_c=[1.0]`, `io_matrix=[[1.0]]`; empty for
   multi-industry); `macro_params` and `demographic_params` are `{}` and `e` is `None`. A curated
   few parameters refresh when a caller passes `update_from_api=True`. **That call can be in the
   default run path:** OG-PHL's shipped `examples/run_og_phl.py` calls
   `Calibration(p, update_from_api=True)` whenever `is_connected()` is true. Read your example
   before trusting that a hand-set value survives a run. **[family]**
1b. **Anything you do not set stays American. Count what your `Calibration` actually delivers.**
   OG-JPN delivered seven parameters; thirty-four mattered. The US defaults that bite hardest, and
   that no repo reliably overrides: `delta_annual` 0.05; `beta_annual` 0.96; `mean_income_data` in
   US dollars (it scales `factor`, so every tax function and the pension formula run at US income
   levels); `pension_system` US Social Security; `alpha_db` 0.0 (Defined Benefits without it pays
   zero pensions); `tax_func_type` `DEP` (US microdata); `cit_rate` 0.21; `p_wealth` 0.0;
   `initial_foreign_debt_ratio` and `zeta_D` 0.4; `debt_ratio_ss` 2.0; the `initial_guess_*` set.
   This is the argument for the packaged JSON: it makes the whole surface visible, where a handful
   of Python functions hides everything unset. **[net-new: JPN]**
2. **Most parameters are weakly identified alone.** The real test is whether the joint steady state
   resembles the economy. **Lead the dashboard with fiscal data.** Tax collections by instrument,
   the debt ratio, its foreign share, and the effective real rate on debt are published precisely,
   map one-to-one onto model ratios (unlike GDP or wage levels, sector nominal output shares, or
   `r`), and self-check through the government budget identity, so a miscalibration shows up as an
   inconsistency in the steady state and as a debt runaway on the transition. `factor` is a fiscal
   diagnostic too: it sets the currency income at which tax functions are evaluated, so a `factor`
   gap mis-collects tax. Production, preference and earnings moments (sector VA shares, hours, the
   Gini) are a necessary second tier. **[emerging: IDN, ETH; fiscal-first framing net-new: ZAF]**
2b. **`K_f/K` is a first-tier moment: published, and a lever on `K/Y`.** An older version of this
   skill grouped it with `r` as "open-economy modelling latitude" while also listing it as a
   dashboard target. When two parts of a playbook disagree, the weaker one wins, and JPN shipped
   `zeta_K` as a placeholder for fourteen tuning rounds. `r` stays in the latitude bucket; `K_f/K`
   does not. Settle gross vs net `K_f` before picking a target: for a net-creditor country the two
   readings differ in sign ([macro-open-economy.md](references/macro-open-economy.md)).
   **[net-new: JPN]**
3. **Single-industry first; multi-industry is a separate, non-destructive file** with its own JSON
   and its own example; the single-industry default keeps working untouched. Two packaging choices
   are legitimate (a lean overlay [PHL], or a self-sufficient file [ZAF]); either way the file is
   regenerated by a builder, never hand-written. One representation = one JSON loaded one way + one
   example script (baseline + one representative reform). Do not ship reform-variant scripts
   (`*_cit_cut.py`); a reform is a few lines the user edits. Trade-offs in
   [multi-industry-sam.md](references/multi-industry-sam.md). **[family]**
4. **Calibrate effective, not statutory, quantities.** Where much activity is informal, exempt or
   uncovered, the rate = actual collections ÷ the model-wide base. Apply it to every instrument
   (OG-BRA discounts PIT for informality but leaves payroll at the full statutory rate). **[family]**

## Running the model: the owner's rules

These come from the model owner (stated 2026-08-12) and override any older advice in this family.

- **A healthy baseline solve takes under 10 minutes.** Longer means something is wrong: stop and
  diagnose (og-solver-diagnosis) rather than wait.
- **Run from the country repo's own environment, the way its example scripts do.** `uv sync
  --extra dev`, then `uv run python examples/run_og_<xxx>.py`. Nothing bespoke for an official run.
- **Always parallel.** The examples build one dask `Client(n_workers=min(cpu_count(), 7),
  threads_per_worker=1)` and call `runner(p, time_path=True, client=client)` once per scenario.
  `SS.py` and `TPI.py` submit one task per lifetime-income group (`for j in range(p.J)`), so workers
  beyond `J` idle: seven is maximum parallelism when `J = 7` (the ports); OG-USA ships `J = 10`.
- **Use the Anderson solver every time,** with `nu` 0.2 or lower: set `TPI_outer_method =
  "anderson"` and `nu <= 0.2` in the packaged parameters, not the script. It is available since
  ogcore 0.16.4 (check `hasattr(Specifications(), "TPI_outer_method")`; the ogcore default is
  `"picard"` with `nu` 0.4). If the repo's resolved ogcore predates it, bumping ogcore is its own
  change. Evidence [PHL]: Anderson cut the M=1 transition from ~30–70 damped iterations (~20 min) to
  11–12 (~2–2.5 min) with monotonically falling distances. Watch the distance series the first
  time; if it oscillates or stalls, fall back to damped `nu`. Anderson is TPI-only (it does nothing
  for the steady state) and never fixes a fiscal runaway.
- **A serial SS-only driver is fine for tuning iterations,** because it is fast; official and
  reported runs go through the example's client pattern. `runner` always re-solves the steady state,
  so `runner(time_path=False)` followed by `runner(time_path=True, client=client)` solves it twice.
- **Preflight before every solve:** use og-run-preflight (branch and HEAD of every repo, imports
  resolve inside the intended checkout, its own venv). Editable installs, script-dir shadowing and
  cwd shadowing silently run another checkout's code. **Propose runs; the user launches them.**

Environment facts: uv, not conda; `AGENTS.md` is the setup source of truth (the contributor guide is
stale in most repos). Never commit a `uv.lock` change from calibration work (`git restore uv.lock`).
The repos' resolved ogcore versions have not converged, so check `name = "ogcore"` in `uv.lock`, not
the `pyproject.toml` floor. The example run is a smoke test, not a correctness check. Detail in
[solving-tuning.md](references/solving-tuning.md).

## The traps that cost the most

Each one shipped in a real repo. Detail is in the linked reference.

- **Budget does not balance at the debt target.** `alpha_G`, `alpha_T`, revenue and
  `debt_ratio_ss` must satisfy one identity (with pensions, UBI and `alpha_I` in it), or the
  transition runs away while the steady state looks fine. [fiscal-consistency.md](references/fiscal-consistency.md)
- **Statutory rates in effective slots:** `tau_bq` (three instances), payroll additive on top of the
  ETR function (a hidden 5.8% of GDP on PHL), flat PIT over-collecting. [taxes-informality.md](references/taxes-informality.md)
- **Placeholder `zeta_K`:** 0.9 drives `K_d` below zero; 0.10 left `K/Y` and consumption gaps open
  for fourteen rounds. Tune it to the IIP `K_f/K` level, and re-tune after any tax change. [macro-open-economy.md](references/macro-open-economy.md)
- **`r_gov` from the cross-country LMWW intercept:** ~3pp too high on PHL. Re-anchor the shift to
  the treasury's effective real rate. [macro-open-economy.md](references/macro-open-economy.md)
- **Wrong `initial_debt_ratio`:** invisible to the steady state, obvious in period one of a
  transition panel (JPN: 28pp of GDP). [fiscal-consistency.md](references/fiscal-consistency.md)
- **Initial-wealth windfall:** a one-to-two-year consumption spike at the start of the baseline is
  the imposed initial condition, not dynamics. [macro-open-economy.md](references/macro-open-economy.md)
- **Two-year demographic window:** sets the long-run growth rate silently (JPN `g_n_ss` −1.07%
  vs −0.46%). [households-demographics.md](references/households-demographics.md)
- **Live-API clobber:** `update_from_api=True` recomputes naive `gamma` over a hand-triangulated
  value. Remove curated structural parameters from the live path entirely. [macro-open-economy.md](references/macro-open-economy.md)
- **Cold-start steady state:** suspect the seed before the calibration; warm-start from a solved
  state. [solving-tuning.md](references/solving-tuning.md)
- **Leaving remittances or aid off** for an aid- or remittance-dependent economy: a spurious trade
  surplus and a fiscal squeeze. [macro-open-economy.md](references/macro-open-economy.md)

## Step zero: write the equations down before you touch a parameter

Before tuning anything, produce a moment × lever table and commit it. Build it from the equations
OG-Core evaluates (`firm.py`, `aggregates.py`, `household.py`, `fiscal.py`, `tax.py`), not from
convention or this skill's tables. It takes under an hour and is the highest-value hour in a
calibration. For each target moment write:

1. **The closed form,** every symbol in it. Reproduce the solved value from your formula to 4
   decimals before trusting it. A mismatch means you read the wrong equation, and finding that out
   now costs minutes.
2. **Every parameter in it,** marked `sourced` / `tuned-to-<moment>` / `default-unexamined`.
3. **Which other moments share those levers.**

Worked example, `K/Y`, where convention names one instrument (`beta`). From `firm.get_r`,
`r = (1-tau_b)·p_m·MPK - delta + tau_b·delta_tau + inv_tax_credit·delta`, so under Cobb-Douglas:

```
K/Y = (1 - tau_b)·gamma / (r + delta - tau_b·delta_tau - inv_tax_credit·delta)

  gamma            sourced (PWT labour share)
  delta            sourced (CFC/K)
  tau_b            = cit_rate x c_corp_share_of_assets x adjustment_factor
                     c_corp_share_of_assets = 0.55 is a US default, and it is not
                     separately identified from adjustment_factor -- only the product is
  delta_tau        default 0.027 (US tax depreciation)
  inv_tax_credit   default 0.0
  r                not a parameter -- the household Euler pins the portfolio return r_p,
                     and r solves r_p = weighted avg of r (on K) and r_gov (on D).
                     So beta, sigma, g_y, debt_ratio_ss, r_gov_scale/shift,
                     zeta_K and world_int_rate are all levers on K/Y.

  shares levers with: C/Y (via I), I/Y, K_f/K, r
```

Write the tax terms in full; they are not small (on JPN they move the numerator 14% and the
denominator 3.5%), and `gamma/(r+delta)` sends you after the wrong lever. The table has eleven
levers; convention has one. A bigger stock of government debt forces capital to pay more, which
shrinks `K`, so `debt_ratio_ss` and `r_gov` are levers too. OG-JPN tuned `beta` alone, watched it
run out of road at 0.984, wrote "acceptable band", and shipped, while `zeta_K` sat at a placeholder
that closed over half the gap when set from data.

**The table is also the tuning order:** sourced levers first, then tuned dials, then re-check
anything that shares a lever with what you moved.

## Finding every lever on a moment

The failure this prevents: OG-JPN's `K/Y` came in at 3.50 against a PWT 3.70. `beta` needed 0.984,
and at 0.984 the steady state stopped solving. That was written up as an acceptable miss and a
"family trait". It was neither. `zeta_K`, at a placeholder 0.10 that the repo's own comment
labelled `NEEDS TUNING ... pending the IIP anchor`, closed 79% of the `K/Y` gap and 85% of a
separate consumption gap when set from the IIP data. Fourteen tuning rounds ran without touching it.

Four mechanical rules:

1. **Write the model's own closed form for the moment, then list its arguments** (Step zero). Not
   the conventional pairing.
2. **Every parameter ends in one of three states, and "placeholder" is not one:** sourced;
   tuned to a named moment; deliberately defaulted with a written reason. A `NEEDS TUNING` marker is
   a debt with an exit criterion. Make it a release gate and a test
   (`test_no_unresolved_tuning_markers`, as OG-JPN has). The JPN comment even named the dataset; it
   shipped anyway, because nothing failed.
3. **Two moments that move together are one moment.** Check for shared levers before diagnosing
   either. JPN's consumption gap (+2.3pp) and `K/Y` gap (−0.20) were analysed separately for a whole
   calibration. They were the same gap: too little capital means too little investment, and
   `C = Y - I - I_g - G - NX` makes consumption absorb it. One lever closed both. Symptom-by-symptom
   tuning always finds a spurious "structural" residual.
4. **A lever that runs out of road is the wrong lever, not proof the gap is structural.** If the
   instrument needs a value that will not solve, or one outside its plausible range, go back to
   rule 1. Do not write "acceptable band"; that language launders an untuned parameter into a family
   trait.

**Then sweep the defaults you did not source.** Perturb every unsourced parameter and record which
target moments move. Anything that moves one materially must be sourced or explicitly declared.
Relevance depends on settings you have not chosen yet: `world_int_rate` (default 0.04) is invisible
at `zeta_K = 0.10` and sets `r` at `zeta_K = 0.78`; dropping it to 3.5% moved JPN's `K/Y` from 3.67
to 3.81 and `K_f/K` from 17% to 27%. High openness hands the interest rate from the country's
households to an unsourced global constant. Run the sweep after the parameters settle. **[net-new: JPN]**

## Dashboard completeness: an unscored moment cannot pull its parameter

The general form of the `zeta_K` failure. It sat at a placeholder because `K_f/K` was not a row on
the dashboard. The loop optimised what it could see. Three rules, all mechanically checkable:

1. **Every tuned parameter's identifying moment must be on the dashboard.** Grep the tuned dials,
   grep the dashboard rows, and require a one-to-one match. A dial with no scored moment drifts
   silently.
2. **A dial moved to close a residual is a free parameter, not a calibration.** OG-JPN's `p_wealth`
   and `tau_bq` were nominally tuned to property and inheritance tax but in practice scaled to close
   total revenue, so they absorbed every other line's error. Tune each dial to its own moment; total
   revenue is the check that the parts add up, never the thing you steer.
3. **Score every component of the resource constraint,** not just the residual. Put `I/Y`, `I_g/Y`,
   `G/Y` and `NX/Y` next to `C/Y`.

The moments most often tuned for but never scored, their sources, and the traps when adding rows
(per-household arrays, trade balance vs current account) are in
[validation-dashboard.md](references/validation-dashboard.md). **[net-new: JPN]**

## End-to-end sequence for a new country

Copy this into the work log and tick it off. Mechanics throughout: run with
`uv run python examples/run_og_<xxx>.py`; the earnings tilt is solved in `income.py`'s
`get_e_interp(gini_to_match=...)`; read moments with `ogcore.utils.safe_read_pickle` from
`OUTPUT_BASELINE/SS/SS_vars.pkl`, `TPI/TPI_vars.pkl` and `model_params.pkl`.

```
- [ ] 0a. Plan two dashboards together: the near-term fiscal PATH (debt, primary balance,
          revenue, public investment vs actuals and the country's program) and the steady state.
          The path catches what the SS cannot, above all a wrong initial_debt_ratio.
- [ ] 0.  Step zero: moment x lever table from OG-Core's equations; one dashboard row per target
          moment and per resource-constraint component. Dashboard first, tuning second.
- [ ] 1.  Bootstrap from the closest sibling; fix the copied country_id, package name, egg-info.
- [ ] 2.  Environment: uv sync --extra dev; note the resolved ogcore in uv.lock; check
          TPI_outer_method exists; run og-run-preflight.
- [ ] 3.  Demographics: country_id as a named constant + regression test; data window to the
          terminal UN rates; cache the arrays; check g_n_ss against the UN projection's CAGR.
- [ ] 4.  Earnings: Gini on the same welfare concept as the US reference; solve the tilt; add the
          NTA age shape if available.
- [ ] 5.  Macro: start_year (latest observed year), debt (measured initial, anchored SS), zeta_D,
          zeta_K tuned to the IIP K_f/K level, world rate (open vs distressed), g_y per hour and
          consistent with the debt anchor, remittances/aid if material, r_gov shift to the
          treasury's effective real rate (and r_gov_floor if real rates are negative), centered
          debt-elastic premium, initial_Kg_ratio if gamma_g > 0, initial wealth, delta, alpha_T
          cash only.
- [ ] 6.  Capital share: 1 - labour share, Gollin-adjusted if agrarian/informal; take gamma out of
          the live-API path.
- [ ] 7.  Taxes by instrument from the OECD Revenue Statistics country note: GS progressive PIT;
          effective VAT/CIT/payroll/bequest; non-tax revenue on nearest-margin instruments;
          informality rung. Close the budget identity:
          alpha_G + alpha_T + alpha_I + pensions/Y + UBI/Y = revenue/Y - pb*.
- [ ] 8.  Pensions in local currency (alpha_db if DB); chi_n borrowed-and-documented or re-tilted.
- [ ] 9.  beta against K/Y, only after sourced parameters settle.
- [ ] 10. Validate: SS dashboard, revenue by instrument, value-pinning test, AND a baseline TPI
          with the fiscal path panel.
- [ ] 11. Save and ship a warm-start seed from the first converged solve.
- [ ] 12. Optional multi-industry: SAM sourcing, concordance assert, five inputs, numeraire last,
          direct solve first, chi conversion, Z-level rescale, same-reform acceptance test.
- [ ] 13. Final standalone solve of the packaged JSON, no overrides.
- [ ] 14. Wrap up: make format; pytest -m 'not local'; CHANGELOG (before -> after + citation);
          docs with glue-from-JSON; goodness-of-fit table. Ask before push; ask before PR.
```

Loop-backs. Do not move forward past a failed check:

- **After any tax change, go back to step 5 and re-tune `zeta_K`.** Tax changes move domestic
  saving, which moves `K_f/K` at a fixed `zeta_K` (PHL: honest taxes pushed it 0.26 → 0.14).
- **After any sourced-parameter change (`gamma`, `delta`, `g_y`, window, spending shares), redo the
  tax dials (step 7), then `beta` (step 9).** Every tuned dial was fitted against the old base. JPN
  took fourteen rounds because sourced values were corrected after the dials were tuned.
- **If the standalone solve of the packaged JSON fails (step 13), go back to the overrides you just
  folded in.** It catches schema errors and seed problems the overrides path hides.
- **If the baseline TPI resource-constraint error is not small and monotone in the distance series
  (step 10), do the `RC_error` triage before any tuning** ([solving-tuning.md](references/solving-tuning.md)).
  Tuning against a transition artifact bakes the artifact in.
- **If the steady state is right but the transition runs away, check the fiscal identity before any
  solver setting.** Damping and Anderson do not fix an unbalanced budget.

Why the baseline TPI is not optional: the steady state consumes one number from each time-varying
path (its terminal value), so a whole mis-specified path is invisible to it. On JPN a wrong
demographic window survived eleven steady-state rounds with every fiscal moment inside 0.2pp of GDP;
one transition run caught it.

## House rules

- **uv only, run as a user would.** Let uv resolve Python and ogcore. Never commit a `uv.lock`
  change from calibration work, and keep `uv.lock` and `.python-version` out of the PR diff.
- **Non-destructive.** The single-industry default keeps working; multi-industry ships as its own
  builder-regenerated file, never by editing the single-industry JSON.
- **Document every calibrated value with a source,** even stylized placeholders. Add inline
  citations to tax docs that lack them when you touch them.
- **No undocumented placeholders, no `NEEDS TUNING` at release.** Pin the decision in a test.
- **Approval gates.** Calibrate, edit and commit locally freely. Launching solves beyond a quick SS
  check, pushing, opening PRs, and anything fleet-scale are proposed and wait for the user. Ask
  before push and before the PR, never in the same step. Never merge.
- **PR style:** narrative, plain language, the why first, detail in the docs; a changed-parameters
  table, a goodness-of-fit table, and an example macro-results table
  ([calibration-pr.md](references/calibration-pr.md)).

## Reference files

Read the one that matches the block you are working on. Each is self-contained.

| File | Read when |
|---|---|
| [macro-open-economy.md](references/macro-open-economy.md) | Setting `start_year`, debt, `zeta_D`, `zeta_K`, world rate, `g_y`, `r_gov` wedge and floor, remittances/aid, debt-elastic premium, `initial_Kg_ratio`, initial wealth, `delta`, `beta`, `alpha_T`, `gamma`; deciding gross vs net `K_f` |
| [fiscal-consistency.md](references/fiscal-consistency.md) | Setting spending shares; the budget identity; debt runs away on the transition; building the near-term fiscal path panel and the `alpha_G` glide |
| [taxes-informality.md](references/taxes-informality.md) | Any tax rate; the PIT form (GS/HSV); payroll and bequest checks; informality; non-tax revenue |
| [households-demographics.md](references/households-demographics.md) | The `e` matrix and Gini; demographics, data window, income gradients; pensions; `chi_n` |
| [multi-industry-sam.md](references/multi-industry-sam.md) | Any M>1 work: packaging, finding a SAM, `PROD_DICT`, the five inputs, single↔multi alignment, continuation solve |
| [validation-dashboard.md](references/validation-dashboard.md) | Building or scoring the SS dashboard; sourcing data anchors; reading pickles; tests that pin values |
| [solving-tuning.md](references/solving-tuning.md) | Run engineering detail; a steady state that will not converge (warm start); tuning-loop order; `RC_error` triage; running against unreleased ogcore |
| [calibration-pr.md](references/calibration-pr.md) | Writing the calibration PR |

## Related skills

- `og-run`: launching the baseline and reform solves.
- `og-run-preflight`: the go/no-go check before any solve.
- `og-solver-diagnosis`: a solve that does not converge, diverges or oscillates.
- `calibration-provenance`: tracing one parameter to its source.
- `muiogo-explain`: explaining the calibration to a person.
- `og-clews-linked-run`: coupling the calibrated model to a CLEWs energy scenario.

If one is not available to you, do the job directly and say which skill would have covered it.
