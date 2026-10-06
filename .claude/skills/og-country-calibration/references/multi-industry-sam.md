# Multi-industry (M>1): the SAM method

Contents
- Packaging: lean overlay or self-sufficient file
- Builder layout
- Finding the SAM
- Assert the concordances partition the SAM
- Defining the industries (PROD_DICT)
- The five SAM-derived inputs
- OG-Core structural facts
- Single ↔ multi compatibility
- The continuation solve
- Maturity honesty

## Packaging: lean overlay or self-sufficient file

Both are legitimate; pick per repo, but never hand-write the file. Always regenerate it from the
builder.

- **Lean overlay [PHL].** The multisector JSON carries only the parameters that differ (`M`, `I`, the
  per-industry vectors, `alpha_c`, `io_matrix`, the chi conversion); the example loads the base JSON
  and then the overlay. Pro: small reviewable diffs, and the economy-wide values live in one place so
  they cannot drift. Con: not standalone. Loading the overlay alone silently falls back to OG-Core
  (US-ish) defaults for everything it omits. It is tiny because ~97% of the base file is baked
  demographic arrays (`imm_rates`/`omega`/`rho`) it does not repeat.
- **Self-sufficient file [ZAF].** The builder merges base + multi-industry overrides and writes the
  full file, so it loads standalone in one step like the single-industry default. Pro: matches the
  "one file = one calibration" expectation, no footgun. Con: it duplicates the base's economy-wide
  values (including the multi-MB demographic arrays), so it can silently drift from the base if the
  base is recalibrated and this file is not regenerated. Mitigate by regenerating on every base
  change (ZAF's choice), optionally backed by a drift-guard test asserting every non-multi-industry
  key equals the base. That test is cheap insurance, though some prefer a minimal test surface.

Never let the single-industry default carry multi-industry values. The deliverable per
representation is one JSON that carries every value the model needs, loaded one way, plus one
example script (baseline + one representative reform) mirroring `run_og_<country>.py`. **[family]**

## Builder layout

A `create_multisector_calibration.py` that writes the static JSON; one example script
(`run_og_<xxx>_multiple_industry.py`); and shared constants (`TOTAL_CAPITAL_SHARE`,
`PUBLIC_CAPITAL_SHARE`, `CAPITAL_OUTPUT_RATIO`) in one `constants.py`, so the builder and the live
`Calibration` cannot drift.

## Finding the SAM

The sourcing hierarchy applies here too; search, do not assume one exists or does not.

- **Search order.**
  1. The national statistics office or central bank. Some publish an official SAM, and many more
     publish supply-and-use tables (SUTs) or IO tables, which are enough: the make/use algebra below
     runs on them directly (BRA: IBGE SUTs via the Alves-Passoni–Freitas annual IO series).
  2. Research institutes that build SAMs with national authorities: UNU-WIDER (country SAM program;
     ZAF's 2019 SASAM, with a technical note) and IFPRI (the Nexus country-SAM program on the IFPRI
     Dataverse: standardized ~42-activity SAMs with labour-by-education, land and capital factor rows
     and 10 household groups; PHL's 2018 SAM). These are the family's two workhorses, free and
     documented, covering many developing countries.
  3. Global harmonized or modelled databases, last, marked lower-confidence: GTAP (licensed; one-time
     tiered fee for the current version, older versions free; has factor detail), EORA (190-country
     MRIO; free for academic use, licensed otherwise), OECD ICIO (free; built from national SUTs but
     harmonized and balanced). Their estimation and balancing go beyond the national accounts, and
     most lack the SAM's full household and factor detail.
- **What qualifies.** Separate factor rows (labour, ideally disaggregated, and a capital or
  operating-surplus row), household expenditure columns, activity (and possibly commodity) accounts,
  an imports / rest-of-world account, and production-tax rows. Note whether the make is diagonal or
  rectangular; it decides the `io_matrix` algebra. Match the vintage to the rest of the calibration:
  the employment survey year must equal the SAM year (ZAF: 2019 SASAM ↔ QLFS 2019), and the SAM must
  reproduce the same-year national accounts (validation-dashboard.md, structural validation).
- **Delivery.** Never read the publisher's URL at runtime; links move and break. Either mirror the
  file in the family's `EAPD-DRB/SAM-files` repo and read the raw URL (ZAF), or ship a compact extract
  in the package's `data/` (PHL, BRA). Record publisher, technical note and year in the reader's
  docstring and the docs.

## Assert the concordances partition the SAM

Before anything else: every activity in exactly one `PROD_DICT` industry and every commodity in
exactly one `CONS_DICT` good, a one-line set-equality check. ZAF shipped two silently wrong commodity
codes (`colig` for `coilg`, `ccmemb` for `cmemb`) that dropped those commodities from every
aggregation; the assert catches the whole error class. **[net-new: ZAF]**

## Defining the industries (PROD_DICT)

Grouping rules that prevent degenerate capital shares:

- **Manufacturing, the capital-goods producer, goes last.** It must be the numeraire (structural
  facts below).
- **Never let real estate or dwellings stand alone [PHL, BRA].** Its measured capital share is
  dominated by imputed owner-occupier rent, booked as operating surplus but not corporate profit. That
  pushes its `gamma_m` toward ~1 (degenerate in the CES production function) and dilutes its
  effective CIT (imputed rent is not taxable profit but sits in the denominator). Fold it into a
  broader FIRE / finance–business-services aggregate, as OG-PHL and OG-BRA do. More generally, merge
  any activity whose surplus is dominated by imputed or resource rent (dwellings; watch mining and
  extractives). Healthy capital-intensive sectors (mining, utilities ~0.78 in PHL) solve fine; it is
  the imputed-rent-driven ~0.9+ shares that break things.
- OG-Core has only two private factors, so land and resource rent fold into capital income in
  `gamma_m`. That is a second reason raw SAM capital shares come out high (needing the VA-weighted
  rescale) and why rent-dominated activities need grouping.

## The five SAM-derived inputs

In `input_output.py`; OG-PHL is the reference, OG-BRA the most advanced.

0. **`alpha_c`**: household expenditure shares over the I consumption goods, from the SAM's
   household columns (purchaser prices, the budget households actually allocate), summing to 1. Not
   the legacy `total − row` shortcut (that is total commodity demand, not household spending). Keep
   the legacy naive `get_io_matrix` for the live `Calibration(update_from_api=True)` path and its unit
   tests; the builder uses the value-added version below. PHL and ZAF both follow this split.
1. **`gamma_m`**: `(capital+land)/(labour+capital+land)` per industry from the SAM factor rows, then
   rescaled so the VA-weighted mean equals an independent economy-wide capital share (keeps the
   cross-industry pattern, fixes the level). BRA adds a per-industry mixed-income (Gollin) split
   first.
2. **`io_matrix`**: the value-added version. Trace household consumption of each good back through
   the domestic supply chain to value added by industry, weighted by household consumption net of
   imports, rows renormalized to 1. Not the naive direct-intermediate-cell version (a legacy baseline
   that is not an accounting identity; IDN and ETH shipped only that version when last checked). The
   correction is large: household energy spending maps to ~45% electricity in ZAF (~74% in PHL), vs
   the manufacturing-heavy split a naive matrix implies.
   - **Match the algebra to the SAM's make structure;** this is the error-prone piece. A diagonal make
     (one activity per commodity, PHL) collapses to `A_d = σ·use/output` and Leontief `(I−A_d)^-1`.
     A rectangular make (ZAF's SASAM: 61 activities × 108 commodities, median commodity produced by
     more than one activity) needs the full industry-technology make/use algebra: market-share matrix
     `D` (`V/g`, allocating each commodity's domestic output to producing activities), use
     coefficients `B` (`U/q`), industry-by-industry Leontief `(I − D·B)^-1`, then VA per unit output
     `v = VA/q`; VA by activity `= v·(L @ (D @ f))` for commodity final demand `f`. The diagonal
     shortcut is wrong on a rectangular make.
   - Derive `D`/`B`/Leontief from the SAM yourself when no pre-computed IO table ships (ZAF), or read
     them if it does (BRA).
   - Sanity checks before trusting the result: SAM balance
     (`gross output = intermediate + VA + production tax`, to machine precision), Leontief validity
     (spectral radius of `D·B` < 1), and a "total" row or column in the SAM (a 2× inflation tell) that
     must be excluded.
3. **`L_m` employment**: measured independently of the SAM (labour force survey by industry), so
   `Z_m` does not collapse into a mechanical function of factor shares. When the survey's industry
   aggregation is coarser than `PROD_DICT` (e.g. QLFS lumps electricity, gas and water into
   "utilities"), split the aggregate by the SAM's labour-compensation shares of the sub-activities,
   not an arbitrary or output-based split. A labour-intensive sub-industry (waste and sanitation)
   employs more per unit of output than a capital-intensive one (power generation). A too-low
   headcount in a small sub-industry produces a wild TFP outlier (ZAF Water & Waste `Z` fell 5.3 →
   3.5 once split by labour compensation instead of a guessed 77/23).
4. **`Z_m` sector TFP**: Solow residual `Y_m/(K_m^γm · Kg^γg · L_m^(1−γm−γg))`, normalized so the
   numeraire (last) industry = 1. `K_m` allocates a national stock (PWT capital-output ratio × total
   VA) across industries by capital-income share. The ratio's level is a weak lever (with the
   numeraire normalization it enters relative Z only through the γ dispersion); take it from the PWT
   and move on. Reject establishment-survey capital (it omits informal capital and inverts the
   ranking).

## OG-Core structural facts

- **The last industry (index M−1) is the numeraire and the only non-consumption producer.** All
  investment, government, net-outflow, remittance and aid demand loads on it, so its nominal output
  share is inflated and never comparable to a value-added share. Put the capital-goods or
  manufacturing industry last in `PROD_DICT`.
- **One economy-wide wage; households do not choose a sector** (`L_m` is firm-side labour demand). A
  formal/informal wage gap or sector-choice margin is not representable without extending OG-Core.
- `cit_rate`/`tau_c`/`delta_tau`/`inv_tax_credit` can vary by industry or good; the wage and
  household labour supply cannot.
- The composite-consumption price is unnormalized, carrying a units constant
  `k = prod_i(alpha_c_i^−alpha_c_i)` (= 1 when I = 1). It is behaviourally relevant, not cosmetic.

## Single ↔ multi compatibility

So the two representations agree:

- **Copy economy-wide values verbatim** (demographics, preferences, fiscal ratios, open-economy
  dials, `g_y`, statutory rates). Any difference is a bug.
- `gamma_m`: keep the SAM's dispersion, impose the single model's level (VA-weighted mean).
- `Z`: relative TFPs from the Solow residual with numeraire = 1. Two distinct uses of the Z level (a
  common Hicks-neutral rescale); do not conflate them:
  - to close rate or ratio gaps (`r`, `K_f/K`) it is a weak, sometimes wrong-signed lever; do not
    (PHL: an 11.7% Z rise moved `r` the wrong way);
  - to align the income level (`factor`) it is the right, clean lever: `r`, `r_gov` and `K/Y` are
    invariant to it, only the income level moves.

  The numeraire = 1 convention pins relative TFPs but leaves the level free, and whether it lands
  `factor` on the single's is luck (PHL: −0.02%, no rescale; ZAF: −23%, needed one). If `factor` is
  still off after the chi conversion, rescale the whole Z vector by a common constant (a log-log
  root-find on solved-SS `factor` converges in two or three solves; β ≈ 1.8 for ZAF) so the multi's
  factor matches the single's. `factor` must agree: it scales the incomes at which the progressive
  tax functions are evaluated, so a 23% gap mis-collects PIT.
- **The `chi_n`/`chi_b` units conversion is the alignment lever:** scale both by `k^(σ−1)`, derived
  (not fitted) from FOC invariance under the composite-consumption units change. In PHL it closed
  44–80% of the `r` / `K_f/K` / `B/Y` / `K/Y` gaps.
- **Solver seeds are the single-industry model's; never tune seeds separately for the multi.** Lean
  overlay: do not copy them in (inherit from the base at load). Self-sufficient file: the builder's
  merge copies them verbatim and regeneration keeps them synced. Either way the multi cold-starts
  from the single's seeds, which works because the multi's flat anchor is the shared aggregate
  economy.
- **Final acceptance: run the same reform through both models** and compare the percent-change
  tables: same signs, similar magnitudes (ZAF: CIT 27 → 30% through M=1 and M=8; all six aggregates
  agreed).
- **Comparison dashboard.** Must match: `D/Y`, tax rates. Close: `K/Y`, `factor` (a big factor gap
  means a level misalignment upstream). Ballpark with a written reason: `r`, `K_f/K`, `B/Y`. Never
  compare raw: Y, w, C levels, or raw `C/Y` in the multi (use `p_tilde·C/Y`, the numeraire's nominal
  share).

## The continuation solve

A fallback for when the calibrated multi-industry steady state will not solve cold (OG-Core seeds
every industry price at 1). Try the direct solve first: ZAF's M=8 converged cold from the shared
base-JSON seeds in ~130s (the flat anchor is close to the single economy, so the single's seeds are
close). Reach for continuation only if the direct solve fails:

1. Solve a flat anchor: all `gamma` = the economy-wide mean, `Z = 1`.
2. Walk `t: 0 → 1`, morphing `gamma(t)` and `Z(t)` together to the calibrated values, each step a
   warm-started reform off the previous; grow the step on success, halve it on failure.
3. Use the house solver settings: `TPI_outer_method = "anderson"` with `nu` ≈ 0.2 or lower (the
   default 0.4 oscillates on stiff multi-industry transitions; 0.3 is marginal). Neither damping nor
   Anderson fixes a fiscal runaway (fiscal-consistency.md).
4. Reuse the continuation's converged steady state for the baseline TPI (hand-place the pickle);
   only the reform re-solves its own steady state.

## Maturity honesty

OG-PHL is the reference implementation; the complete version with the chi conversion was first
built on a PR branch, so confirm it has reached the default branch before citing it. OG-BRA is the
most advanced port. OG-ZAF has executed the full SAM-Solow method (make/use-Leontief value-added
`io_matrix`, VA-mean-rescaled `gamma`, Solow-residual `Z` with QLFS employment, the chi conversion,
and a factor-aligning Z-level rescale, in a self-sufficient JSON regenerated by
`create_multisector_calibration.py`). OG-IDN and OG-ETH had not when last checked: their shipped
multisector JSONs were partial or placeholder (OG-IDN shipped the flat anchor gamma/Z as if
calibrated). Do not treat a sibling's multisector JSON as a worked example without checking that its
`input_output.py` has real `get_gamma`/`get_Z`/value-added `get_io_matrix` functions.
