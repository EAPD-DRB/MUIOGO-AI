---
name: og-scenario-report
description: >-
  Turn a completed OG-Core baseline-vs-reform run (OUTPUT_BASELINE / OUTPUT_REFORM directories)
  into the standard deliverable: macro-aggregate comparison charts, tables, and narrative
  paragraphs. Use whenever a scenario/simulation run has finished and someone needs results
  presented — "summarize the reform run", "make the charts/tables", "write up the scenario",
  "compare baseline and reform", preparing slides or a report for a ministry/UN audience — for
  any OG country model (OG-USA/PHL/ZAF/IDN/BRA/ETH) or an OG-simulations scenario folder.
---

# OG scenario report

Every scenario run in this family terminates in the same hand-rebuilt deliverable. This skill
pins the house standard so it's produced once, completely, instead of re-invented per scenario.

## The standard artifact set

A finished scenario folder (reference: `OG-PHL/examples/OG-PHL-Example/`) contains:

1. `OUTPUT_BASELINE/` and `OUTPUT_REFORM/` — the run's pickles (`SS/SS_vars.pkl`,
   `TPI/TPI_vars.pkl`, `model_params.pkl`). Inputs, never edited.
2. `<Country>_example_output.csv` — `ogcore.output_tables.macro_table(..., var_list=["Y","C","K",
   "L","r","w"], output_type="pct_diff", num_years=10)`.
3. `<name>_plots/` — `ogcore.output_plots.plot_all(base_dir, reform_dir, save_path)`: ~30 PNGs
   (MacroAgg/Fiscal pct-change, r/w levels, Spend/Debt/Revenue-to-GDP ratios, by-ability-group
   pct-change bars, SS lifecycle profiles). These two stock calls are the whole de-facto standard —
   run them first, in the country repo's own venv.
4. `report.md` — tables + narrative. Generate the skeleton with the bundled script (repo venv
   python; needs only numpy):

   ```bash
   <repo>/.venv/bin/python scripts/scenario_report.py \
     --base <...>/OUTPUT_BASELINE --reform <...>/OUTPUT_REFORM \
     --out report.md [--start-year 2025] [--num-years 10]
   ```

   It emits the macro pct-change table, a fiscal pct-change table, SS revenue-by-instrument as
   % of GDP, D/Y, and sign-aware narrative sentences with the numbers filled in and TODO slots
   for the interpretation — the part that stays yours.
5. A filled `README.md` in the scenario folder: what the reform is (the exact changed parameters
   and their policy meaning), how to re-run, where the deliverables are. The fleet's scenario
   folders are full of *unfilled* README stubs — write it while the run context is fresh, it does
   not survive otherwise.

## Judgment: what the stock tooling does not cover

These are the gaps repeatedly filled by hand (mined from `~/Projects/OG-simulations`); add them
when relevant, and only then:

- **Input-parameter diagnostics.** `plot_all` plots outputs only. If the reform perturbs a
  parameter *path* (phased productivity `e`, `chi_n`, phased `alpha_G`), plot the baseline vs
  reform parameter itself (solid vs dashed by group/time) and eyeball it *before* trusting the
  run — a mis-built reform path is invisible in the output charts.
- **Multi-reform comparisons.** ogcore only compares one reform against one baseline. For N
  reforms, run the stock pair per reform (separate output dirs), then build one combined table:
  rows = variables, one column-block per reform, all against the same baseline. Never let each
  reform's deliverable live only in its own folder — the cross-reform table is what the audience
  asks for.
- **Narrative interpretation.** Fill every TODO the script leaves: the mechanism paragraph
  (which margin moves and why), the fiscal-closure caveat (state which closure rule and
  tG1/tG2 absorbed the budget), the distributional paragraph (read the `PctChange_*` by-ability
  PNGs), and the units caveat (model levels are not currency; only ratios and % changes are
  quotable). A table without the mechanism sentence is not a deliverable.
- **Rates vs percentages.** The house tables show r and w as pct-*change* like everything else,
  but for prose quote r in percentage-*point* terms when the audience is non-technical, and say
  which you're doing.

## Checks before shipping

- Sanity-anchor one number against the calibration: baseline SS `D/Y` must equal the repo's
  `debt_ratio_ss` (the dry-run reference hit 60.00 exactly); baseline revenue/GDP should match the
  calibration dashboard. If not, you may be reading the wrong output dir — or an unconverged run.
- Confirm the solve actually completed (`Time path iteration complete` in the log) and note any
  binding-guard warnings (`K_d has negative elements`) in the caveats; if the run itself looks
  sick, switch to the `og-solver-diagnosis` skill before reporting numbers.
- This skill reads *finished* outputs. If an output dir is missing or stale, never quietly
  re-run the solve to fill the gap — a model run is a user-approved action (see
  the approval gates in SKILLS.md); report what's missing and propose the run instead.
- Multi-industry runs: aggregate consumption comparisons use `p_tilde·C`, never raw `C` (see
  `og-country-calibration` → comparison dashboard); the bundled script sums industry dimensions,
  which is correct for quantities in numeraire units but check before quoting sector detail.

## Related skills

- `og-run` — producing the OUTPUT_BASELINE / OUTPUT_REFORM directories this reads.
- `og-analysis-studio` — when the question needs bespoke figures rather than the standard deliverable.
- `muiogo-analyze` — the equivalent for CLEWs/MUIOGO results, which this skill does NOT cover.
- `og-solver-diagnosis` — if the run you are reporting on looks unhealthy.

These live in the MUIOGO-AI collection; if one is not available to you,
do the job directly and say which skill would have covered it.
