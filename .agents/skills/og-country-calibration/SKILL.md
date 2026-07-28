---
name: og-country-calibration
description: >-
  Calibrate or refine an OG-Core overlapping-generations country model (OG-USA/PHL/ZAF/IDN/BRA/ETH
  and new ports), single- or multi-industry. Use when setting or reviewing macro/open-economy
  parameters (debt, zeta_K/zeta_D, g_y, remittances, aid, debt-elastic premium), the capital share
  gamma, the earnings e-matrix, demographics, chi_n, tax rates, informality, or a SAM-based
  multi-industry split; when porting the model to a new country; when validating a steady state
  against country data; or when the user mentions calibration, a country repo, a SAM/multisector
  build, or steady-state targets. Encodes the family's transferable methods, pitfalls, and house
  rules — methods, not one country's numbers.
---

# Calibrating an OG-Core country model

Transferable lessons distilled from the OG-Core country family (OG-USA, OG-PHL, OG-ZAF, OG-IDN,
OG-BRA, OG-ETH). This is a **method-and-pitfall playbook**, not a table of one country's values —
every number below is an *example*; you re-derive it for your country. Each item is tagged with
**provenance** so you know what is battle-tested vs. emerging vs. novel:

- **[family]** — done the same way across most/all repos.
- **[emerging]** — a good practice in only 1–2 repos (usually OG-IDN/OG-ETH); adopt and propagate it.
- **[net-new]** — not done in any repo yet; do it anyway because it prevents real errors.

Two reading rules:

- **Country tags are provenance, not scope.** `[ZAF]`/`[ETH]`/`[PHL]` record *where a lesson was
  learned and battle-tested* — the evidence trail — never *which country it applies to*. Every method
  here is on the menu for every country. Where applicability genuinely is conditional, the condition
  is a country **characteristic** stated in the item itself (agrarian/informal, aid- or
  remittance-dependent, distressed sovereign, rectangular vs diagonal make matrix) — never a country
  name.
- **Best effort on every block, graded honestly.** Most blocks have a ladder from minimal to ideal
  (flat → progressive → microdata PIT; narrative → structural informality; borrowed → re-tilted
  `chi_n`; naive → value-added `io_matrix`; direct solve → continuation). Calibrate each block at the
  **highest rung the country's data supports**; when the data isn't there, take the lower rung *and
  say so in the docs* — a documented fallback ("chi_n borrowed from OG-USA, uncalibrated") is a
  legitimate calibration, while an **undocumented placeholder is the pitfall half this file exists to
  prevent** (the 0.9 `zeta_K`, the flat 22% PIT, the stray bequest tax). Never let one block's missing
  data stall the rest of the calibration. And for every number — calibration input or validation
  anchor — **actively search for the most authoritative source that exists for this country**,
  starting with the official national institution that owns the number (see the sourcing hierarchy in
  Validation); named sources in this file are roles to search by, not a closed menu.

Always verify a claim against the **actual checked-out ref** of the repo in front of you — sibling
docs sometimes cite a *cousin repo's feature branch* as if it were canonical, and docs drift from
code. Open the file; don't trust memory or a sibling's citation.

## The mental model (read this first)

1. **The packaged `og<xxx>_default_parameters.json` is the source of truth.** `Calibration(p,
   update_from_api=False)` (the default) fetches nothing and overlays only no-op identity values
   (single-industry: `alpha_c=[1.0]`, `io_matrix=[[1.0]]`; empty for multi-industry) — `macro_params`
   and `demographic_params` are `{}` and `e` is `None`. A curated few parameters refresh only when a
   caller passes `update_from_api=True`. **[family]**
2. **Most parameters are weakly identified alone.** The real test of a calibration is whether the
   **joint steady state** resembles the country's economy — validate the SS against a dashboard of
   data moments, not each parameter in isolation. **Lead that dashboard with fiscal data — it is the
   sharpest validator.** Tax collections by instrument (PIT / CIT / VAT+indirect as % of GDP), the
   debt ratio, its foreign share, and the effective real rate on debt are (a) **published precisely**
   by the treasury / revenue service / IMF, to the currency unit; (b) **convention-free** — they map
   one-to-one onto model ratios, unlike GDP / wage / consumption *levels* (arbitrary model units,
   need `factor`), sector *nominal* output shares (numeraire-distorted, never comparable), or `r` /
   K_f/K (open-economy modeling latitude); and (c) **self-checking** via the government budget
   identity (see Fiscal consistency), so a miscalibration surfaces as an inconsistency in the SS and
   as an outright debt runaway on the transition. So a calibration that nails its fiscal ratios is
   validated on its most trustworthy *and* most stability-critical dimension. `factor` itself is a
   fiscal diagnostic — it sets the currency income at which the tax functions are evaluated, so a
   `factor` gap is a mis-collected-tax error, not a cosmetic one. Treat the production / preference /
   earnings moments (sector VA shares, hours, the Gini) as a necessary second tier that fiscal data
   can't speak to. **[emerging: IDN, ETH; the fiscal-first framing net-new: ZAF]**
3. **Single-industry first; multi-industry is a separate, non-destructive file** — its own JSON + its
   own example; the single-industry default keeps working untouched. **Two packaging choices, both
   legitimate — pick per repo, but never hand-write the file (always regenerate from the builder):**
   - *Lean overlay* **[PHL]**: the multisector JSON carries only the parameters that differ (`M`, `I`,
     the per-industry vectors, `alpha_c`, `io_matrix`, the chi conversion); the example loads the base
     JSON *then* the overlay. Pro: small reviewable diffs, and the economy-wide values live in one
     place so they can't drift. Con: **not standalone** — loading the overlay alone silently falls
     back to OG-Core (US-ish) defaults for everything it omits (a real footgun). It is tiny because
     ~97% of the base file is baked demographic arrays (`imm_rates`/`omega`/`rho`) it doesn't repeat.
   - *Self-sufficient file* **[ZAF]**: the builder merges base + multi-industry overrides and writes
     the *full* file, so it loads standalone in one step exactly like the single-industry default. Pro:
     matches the "one file = one calibration" expectation, no footgun. Con: it duplicates the base's
     economy-wide values (including the multi-MB demographic arrays), so it can **silently drift** from
     the base if the base is recalibrated and this file isn't regenerated. Mitigate with the discipline
     of regenerating on every base change (ZAF's choice), optionally backed by a drift-guard test
     asserting every non-multi-industry key equals the base — cheap insurance against a silent, hard-to-
     spot divergence, though some prefer to keep the test surface minimal.
   Never let the single-industry default carry multi-industry values, whichever you pick. **The
   deliverable per representation is exactly one thing loaded one way:** one self-sufficient JSON that
   carries every value the model needs + one example script (baseline + one representative reform),
   mirroring the single-industry `run_og_<country>.py`. Don't ship reform-variant example scripts
   (`*_cit_cut.py`, `*_energy_tax.py`, …) — a reform is a few lines the user edits in the one example;
   parallel scripts just rot and drift. **[family]**
4. **Calibrate effective, not statutory, quantities.** Wherever a large share of activity is
   informal/exempt/uncovered, the calibrated rate = actual collections ÷ the model-wide base, not
   the statutory rate. Apply this **consistently** across every tax instrument (OG-BRA is the
   counter-example — it discounts PIT for informality but leaves payroll at the full statutory rate).
   **[family]**

## Before you start: environment & preflight

- **uv, not conda.** `uv sync --extra dev`, then `uv run <cmd>`. `AGENTS.md` is the source of truth
  for setup — `docs/book/content/contributing/contributor_guide.md` is stale (still conda) in most
  repos. **[family]**
- **Never commit a `uv.lock` change from calibration work.** The lock is Dependabot-managed; if a
  local `uv sync` touches it, `git restore uv.lock`. Confirm `uv.lock`/`.python-version` are not in
  the PR diff. **[family among EAPD-DRB repos: PHL/ZAF/IDN/ETH; PSLmodels repos BRA/USA differ]**
- **Mirror the ogcore version via the resolved `uv.lock`, not the `pyproject.toml` floor.** The
  `ogcore>=` floor strings are NOT synced across repos; the EAPD repos have all converged on the
  same resolved version in the lock. To check "does this repo match its siblings," grep
  `name = "ogcore"` in `uv.lock`, not the floor. **[family]**
- **Model-run preflight — do this before every solve.** Assert the interpreter's imports resolve
  inside the intended checkout/venv (`uv run python -c "import ogXXX, ogcore; print(ogXXX.__file__,
  ogcore.__file__)"` and check the paths) **[emerging: documented as a house rule in
  OG-ETH.informality/INFORMALITY.md]**; and print branch + HEAD of every repo involved plus
  `sys.executable` **[net-new — no repo does the full combo]**. Editable installs, script-dir
  shadowing, and cwd shadowing silently run another checkout's code. This has caught real
  contamination.
- **Confirm before launching runs.** A steady-state solve is ~1–2 min; a full example (baseline +
  reform transition) is several minutes. Propose and let the user launch.
- **The example run is a smoke test, not a correctness check.** `test_run_example.py` (`@pytest.mark.local`)
  only asserts the process is still alive after ~5 min — it never checks SS/TPI values. Numeric
  validation is manual/docs-based (the dashboard). **[family]**
- **CI-equivalent test suite:** `uv run python -m pytest -m 'not local' -q`. **[family]**

## Macro & open-economy block

Method → pitfall → exemplar.

| Sub-block | Method | Pitfall | Exemplar |
|---|---|---|---|
| Debt | `initial_debt_ratio` is *measured* (national/IMF/QPSD series); `debt_ratio_ss` is a *policy anchor* (program target/stance), a separate parameter that shapes the whole SS | Leaving `debt_ratio_ss` inherited/undocumented; not checking whether a debt-ratio jump is a **valuation effect** (FX float revaluing external debt) vs. real deterioration | IDN, ETH |
| `zeta_D` | Default: set = `initial_foreign_debt_ratio` (assume foreign share of *new* issuance = foreign share of *stock*) | Using the realized flow when it's a crisis-period **outlier** (donor surge, debt standstill) — use the DSA's projected medium-term flow instead | USA measures the flow directly; ETH uses the DSA projection |
| `zeta_K` | Anchor to the **normalized Chinn-Ito** openness index, then cross-check against an independent target (FDI stock/GDP or IIP foreign-capital share) — it's a marginal fill-share, so validate the level | The **`zeta_K = 0.9` placeholder** ("implies high openness") — drives domestic capital `K_d = B − D_d` negative, binds `K_d ≥ 0`, and breaks the transition | Method: IDN, ETH. The 0.9 pitfall: IDN hit it and fixed it; **OG-PHL `main` still ships 0.9** (a live example) |
| `world_int_rate_annual` | **OPEN, investment-grade:** risk-free (~4%) + country sovereign spread. **NEAR-CLOSED/DISTRESSED:** leave at the ~4% benchmark and route country risk through low `zeta_K` + the debt-elastic premium instead | Adding a spread for a defaulted/restructuring sovereign (wrong model); or leaving it undocumented | IDN (open); ETH (distressed) |
| `g_y_annual` | Choose the growth window as **named constants** with a rationale (start after a structural break, end before the latest shock, reject unrepeatable booms). Critically, the SS is a **long-run** state, so `g_y` must be **consistent with the growth the `debt_ratio_ss` anchor assumes** (`GDP growth ≈ g_y + g_n_ss`): if the debt target is a country's stabilization *plan* built on a medium-term recovery, use that recovery's productivity growth (`= medium-term GDP growth − g_n_ss`), not the stagnant realized window | Naive "all history"/inline date arg; **or realized-stagnation `g_y` paired with a stabilization `debt_ratio_ss`** — internally inconsistent (that's the *pessimistic, debt-drifts-up* scenario), so the model's debt won't actually hold at the target | IDN, ETH, PHL. ZAF: realized 0.6% was inconsistent with the 0.765 anchor's ~1.8% growth → raised `g_y` to ~1.4% (= 1.8% − g_n 0.42%) |
| `r_gov` base wedge (`r_gov_scale`, `r_gov_shift`) | `r_gov = scale·r − shift + premium`, and it multiplies the **whole debt stock** in `debt_service = r_gov·D` — so it is an **average/effective** real rate. Keep the LMWW **slope** (`scale`, the estimated sovereign-vs-corporate pass-through), but **re-anchor the `shift`** so the SS `r_gov` equals the country's actual real *effective* rate on debt = nominal debt-service/gross-debt (from the budget) minus expected inflation | The LMWW **intercept** is a cross-country EM average that maps a *nominal USD bond-yield* level onto the model's *real* MPK — it can over-predict a country's real borrowing cost (~0.5–0.6pp for ZAF), inflating the debt-stabilizing primary surplus and forcing spending too low. Don't use the 10-yr/ILB *marginal* yield either — that's new-issue cost, not the stock average | ZAF re-anchored to SA's ~3.7% effective real rate; PHL/IDN/ETH still ship the raw LMWW intercept |
| Remittances `alpha_RM_1`/`alpha_RM_T`, aid `alpha_FA` | Hand-set JSON values, **never fetched**; set `alpha_RM_1 = alpha_RM_T` for no transition path, and set the companion `eta_RM` household-distribution matrix. Turning them on lets a low-income economy reproduce a real trade deficit and a fiscally sustainable government | Leaving them off for an aid/remittance-dependent economy (produces a spurious trade surplus and an implausible fiscal squeeze) | ETH (both), PHL (RM) |
| Debt-elastic premium `r_gov_DY`/`r_gov_DY2` | The base wedge is a **country-agnostic** OLS inversion of Li-Magud-Werner (same numbers everywhere). Add the convex Schmitt-Grohé/Uribe term in **centered** form around `debt_ratio_ss`, expand, fold the constant into `r_gov_shift` → premium is **exactly zero at the SS target**, so it only prices transition overshoot: `r_gov_DY = -2·r_gov_DY2·D̄`, `r_gov_shift = base − r_gov_DY2·D̄²` | A live-refresh path that returns the *raw* LMW shift silently **de-centers** the premium and moves the SS — freeze it | IDN, ETH |
| `initial_Kg_ratio` | Solve the model's own SS law of motion `K̄g/Ȳ = (1−φg)·αI / (e^{gy}(1+gn) − (1−δg))`; if the *measured* stock is far above sustainable (SOE-built boom), **start at the measured value and let it depreciate** | Inheriting the sibling-shipped `0.2` undocumented when `gamma_g > 0` (OG-Core's own default is `0.0`; PHL/ZAF/IDN/BRA all ship `0.2`, but only PHL has `gamma_g>0`, so elsewhere it's inert) | ETH only — replicate wherever `gamma_g > 0` |

## Capital share (gamma)

- **Baseline [family]:** `gamma = 1 − labor_share` (ILOSTAT/national accounts), then carve `gamma_g`
  (public capital share) out of the *capital* side. Fine for formal economies (USA).
- **Gollin / self-employment adjustment — for agrarian/informal economies.** Raw labor shares are
  biased because self-employed mixed income is booked as capital. Two distinct methods:
  - *Aggregate triangulation* **[ETH]**: adjust the economy-wide labor share up using non-circular
    evidence — a growth-accounting check `gamma = (r+δ)(K/Y)` (an implausible implied return flags a
    wrong share), the Gollin direction-of-bias argument, and country institutions (e.g. state-owned
    land). State the result as a *range with a center*, not a point estimate.
  - *Cross-sectional rescale* **[multi-industry; PHL feature branch]**: keep the SAM's per-industry
    *dispersion* but rescale so the value-added-weighted mean equals the economy-wide capital share.
- **PITFALL [ETH, verified]:** the `update_from_api=True` path recomputes the **naive** `1 − ILOSTAT`
  and will **silently clobber** a hand-triangulated gamma (e.g. overwrite 0.30 with 0.515), undoing
  the whole firms.md argument. **Remove such curated structural params from the live path entirely**
  (as IDN did) — an `if update_from_api` guard is not enough.

## Earnings (the e ability matrix)

- **Method [family: PHL/IDN/BRA/ETH]:** reuse OG-USA's calibrated `e` matrix as the base and apply a
  **single-scalar exponential tilt** `e_country = e_USA · exp(a·e_USA)`, solving the one scalar `a`
  (bisection) so the model Gini matches the country's target Gini. One number per country, no bespoke
  data collection.
- **Do NOT use the ZAF-style hardcoded-coefficient method** (`get_e_orig`, WID-then-NTA two-step with
  hand-tuned arctan extrapolation) — it needs bespoke per-country re-derivation and isn't a drop-in.
- **Gini-concept trap [issue #33; family-wide risk]:** the target-country Gini and the US reference
  Gini (`gini_usa_data`) **must be the same welfare concept**. Mixing a World Bank PIP Gini
  (consumption-based for many developing countries) against the **World Bank income-concept US anchor
  (`gini_usa_data = 41.5`, WB SI.POV.GINI)** systematically understates the target's inequality. Use a
  matching concept for both (e.g. WID income) and check the docstring default matches the code.
- `lambdas` (lifetime-income groups, J=7) are byte-identical **across the country ports
  (PHL/ZAF/IDN/BRA/ETH)** and never re-derived — only the tilt `a` changes; OG-USA is the J=10 source
  the ports interpolate down from. `factor` is **solved endogenously in the SS**, not a calibration
  input.

## Demographics

- **Method [family]:** the shared `ogcore.demographics` module — fertility/mortality from the UN
  Population Division API, infant mortality taken from the UN age-0 mortality rate (same UN WPP
  series), **immigration solved as the residual** that reconciles consecutive UN population
  distributions (appropriate when immigration data is weak).
- The only per-country input is `country_id` (UN M49 code). **Use a single named constant**
  (`UN_COUNTRY_CODE`) referenced at both call sites — not an inline literal. **[safer: PHL/IDN/BRA]**
- **PITFALL [ETH, regressed twice]:** `calibrate.py` gets refreshed by copying a sibling repo, and the
  hardcoded `country_id` literal was wrong (710=South Africa instead of 231=Ethiopia) — twice, because
  a wholesale file copy forgot to swap it. **Add a regression test** asserting `country_id` matches the
  country being calibrated.

## Labor supply (chi_n)

- **Honest default state [family]:** `chi_n` (the 80-age disutility-of-labor profile) is
  **byte-identical to OG-USA's values in every country repo — never recalibrated to any country's own
  labor data.** The estimation machinery is broken or absent everywhere (USA's is commented out; most
  repos have no `labor.py`; ETH's `labor.py` is orphaned ZAF QLFS code with a missing
  `estimate_chi_n` module — see issue #71).
- **So: treat "chi_n = borrowed from OG-USA, uncalibrated" as the default state of any port, and say so
  explicitly** — never present it as calibrated.
- To actually calibrate it: either (a) a single-scalar re-tilt analogous to the earnings Gini trick,
  matching an aggregate hours or labor-force-participation target; or (b) wire the country's labor
  force survey through a rewritten `labor.py` + a real `estimate_chi_n.py`.

## Taxes & informality

- **The universal method:** every effective rate = collections ÷ base. Apply it to PIT, `tau_c` (VAT),
  CIT (via `adjustment_factor_for_cit_receipts` × `c_corp_share_of_assets`), and `tau_payroll`
  (statutory rate × covered share of the *wage bill*, not headcount). **Apply consistently** — OG-BRA
  is a cautionary tale: it discounts PIT for informality but leaves payroll at the full statutory rate.
- **PIT functional form — three paths, in increasing fidelity:**
  1. *Flat `linear`* ("given limited data"): a single ETR + MTR number. Cheapest, no progressivity.
     PHL/IDN/BRA pick the number; only ETH *derives* it (revenue identity). Fine as a first pass.
  2. *Progressive parametric form fit to the statutory schedule* **[ZAF — the best data-poor
     option]**: genuine progressivity with **no microdata** — you only need the country's statutory
     PIT schedule plus a collections target. Strongly prefer this over flat-linear whenever a
     statutory schedule exists (i.e. almost always). **Default to the GS (Gouveia-Strauss) form, not
     HSV.** GS floors the ETR at exactly zero — faithful wherever a statutory threshold + rebates
     exempt the bottom (most schedules), and numerically robust. HSV's ETR goes *negative* below the
     threshold, and that implicit bottom-end subsidy is **not cosmetic: on ZAF it drained transition
     revenue and helped push the TPI into a debt runaway, where GS with the same targets converged.**
     Recipe below.
  3. *Microdata-estimated nonlinear* (OG-USA via Tax-Calculator): a 12-parameter form fit by
     age×year to microsimulated ETR/MTR. Only feasible with a Tax-Calculator-equivalent + filer
     microdata.
- **Progressive-fit recipe (verified against ogcore `txfunc.py`).** Both forms calibrate the same
  way — the statutory schedule pins the *shape*, the collections target pins the *level* — and both
  use the *same* parameter triple/pair for `etr_params`, `mtrx_params`, `mtry_params` (analytically
  consistent; mtrx = mtry, the total-income MTR):
  - **GS** (`tax_func_type = "GS"`, params `(φ0, φ1, φ2)`): tax `T(y) = φ0·(y − (y^−φ1 + φ2)^(−1/φ1))`
    on total income. ETR = 0 exactly at the bottom and asymptotes to `φ0` at the top — so set
    **`φ0` = the statutory top marginal rate** (an anchor, not a fit), fit **`φ1`** (curvature) to the
    schedule's shape, and tune **`φ2`** (scale) in-model to the PIT/GDP collections target — the
    effective-rate/informality wedge enters here, pulling the level down to actual collections.
    (ZAF: `[0.464, 1.39288, 1.43e-8]` → PIT 10.1% of GDP, top MTR 45%.)
  - **HSV** (`tax_func_type = "HSV"`, `λ = coef0`, `τ = coef1`): `ETR = 1 − λ·y^(−τ)`,
    `MTR = 1 − λ(1−τ)·y^(−τ)`. τ (progressivity) is scale-invariant — fit it to the schedule's shape;
    λ absorbs the income scale — tune it to collections. (ZAF's HSV fit: τ≈0.14 tracked SARS — before
    the GS switch.) **Use only where a bottom-end subsidy is harmless:** below the tax threshold HSV's
    ETR goes negative, and in a tightly-balanced fiscal block that subsidy bleeds transition revenue —
    it contributed to a TPI debt runaway on ZAF. If the budget has no slack, use GS.
- **Informality — the maturity ladder** (choose the rung the data supports):
  1. *Narrative only* **[BRA]**: name informality as the reason effective ≪ statutory, pick a stylized
     flat rate, flag as provisional. No mechanism.
  2. *Structural 2-sector demo* **[IDN, "Option B"]**: use OG-Core's multi-industry `M`/`I` machinery —
     an informal industry with `cit_rate=0`, `tau_c=0`, lower capital intensity, its own `alpha_c`
     share. Illustrative/tutorial, not revenue-anchored.
  3. *Household graded non-compliance* **[ETH, "Option A", fullest]**: `labor_/capital_income_tax_
     noncompliance_rate[t,j]` and `income_tax_filer[t,j]` grade compliance by lifetime-income group
     (a proxy for formality — informal employment share → how many bottom groups get noncompliance=1),
     with the compliant-group ETR **solved from a revenue identity** and the MTR set to the statutory
     top rate. Informality = non-*remittance*, not non-*filing* (filer stays 1). If you later add an
     informal *industry* (Option B), migrate the firm-side informality out of the CIT factor to avoid
     double-counting.
- **OG-Core structural facts (guardrails):**
  - `etr_params`/`mtrx_params`/`mtry_params` vary by **(t, age s)** only — **not** by ability type j.
    Group heterogeneity enters only through each household's income arguments.
  - `noncompliance`/`income_tax_filer` vary by **(t, j)** — not by age.
  - **`mtrx_params` = marginal rate on LABOR income; `mtry_params` = marginal rate on CAPITAL income.**
    The `x`/`y` naming is non-mnemonic — any doc/skill that says "mtrx = capital" is wrong. (ETH's
    taxes.md had this reversed; it was fixed.)
- **Known OG-Core bugs in the compliance machinery** (from the ETH informality work):
  - *SS diagnostic*: `SS.py` tiles the capital-noncompliance array from the labor rate for the
    post-solve `mtry_ss` diagnostic (doesn't affect the solution). Keep labor = capital noncompliance
    and it never bites.
  - *TPI path*: `TPI.py` applies **year-0** compliance/filer values to the whole path's revenue
    accounting, so any **time-varying** compliance reform yields inconsistent transition revenue
    (behavior responds, revenue doesn't). Steady states are fine; a formalization *reform* needs the
    upstream fix. Symptom: reform revenue tracks the baseline exactly while labor supply moves.
- **Watch for doc/code drift:** e.g. OG-IDN's `taxes.md` rates are stale vs. its shipped JSON.

## Fiscal consistency — using fiscal data to dial in the calibration

**The single most destabilizing calibration error is a government budget that does not balance at the
debt target.** The spending ratios (`alpha_G`, `alpha_T`), the revenue the tax system actually
raises, and `debt_ratio_ss` are three independently-set knobs that MUST satisfy one identity, or the
model's transition blows up. **[net-new: ZAF, proven by TPI sims]**

- **The identity.** For debt to hold at `debt_ratio_ss` in the steady state, the government must run a
  primary balance `pb* = (r_gov − g)/(1 + g) · debt_ratio_ss`, where `g = g_y + g_n` (both in the
  model's real, detrended units) and `r_gov` is the SS real sovereign rate. So **primary spending
  must equal revenue − pb\***: `alpha_G + alpha_T ≈ Σ(tax revenue)/Y − pb*`. Set the spending side to
  this, don't inherit it.
- **Why it bites the transition, not the SS.** OG-Core's SS closure silently forces spending to the
  consistent level to hit the debt target, so the **steady state always solves and looks fine**. But
  the *transition* holds `alpha_G + alpha_T` at their input values for the first `tG1` periods before
  the closure adjusts — so if the input spending exceeds the consistent level, debt balloons over the
  transition before the closure violently corrects it. **With a debt-elastic premium on, that
  overshoot feeds the convex premium and the TPI runs away** (debt → ∞). Symptom: SS solves, baseline
  transition diverges or overshoots wildly. Damping and better solvers (even Anderson) do NOT fix it —
  it is a genuine fiscal runaway, not a convergence artifact.
- **Over-collecting taxes MASK the inconsistency — audit revenue by instrument.** A flat/placeholder
  tax rate set too high, or a spurious leftover tax parameter, inflates revenue and accidentally
  balances an over-set spending side; the model then looks stable until you fix the tax. Two real ZAF
  examples that hid a ~3%-of-GDP spending>revenue gap: a **flat PIT collecting ~16% of GDP** when the
  country's actual PIT is ~10% (a flat rate applied to everyone over-collects vs a progressive
  schedule), and a **spurious `tau_bq = 0.2`** (20% bequest tax) collecting 3.9% of GDP when the
  country has negligible estate duty *and the docs said bequest tax was zero* (doc/JSON drift). Check
  every revenue line against the country's actual collections **by instrument** (PIT, CIT, VAT +
  fuel/excise/customs — `tau_c` should capture ALL consumption/indirect taxes, not VAT alone —
  payroll, bequest, wealth), and grep the JSON for nonzero taxes the docs claim are off.
- **Progressive taxes expose what flat taxes hide.** A flat rate raises revenue proportionally to
  income and is robust along the transition; a progressive schedule's revenue is far more sensitive,
  so a spending>revenue gap a flat tax papered over will destabilize the transition once you switch to
  a progressive (GS/HSV) form. Don't blame the progressive form — check the fiscal balance first.
- **Reconcile against the country's OWN fiscal plan, and know what the SS represents.** Pull the
  primary-balance path and debt trajectory from the IMF Article IV / DSA and the national budget. If
  the country actually runs `pb*` (stable/declining debt), the model's SS matches current policy. If
  the country runs a deficit / rising debt (common), the model's stable-debt SS is the country's
  **targeted, post-consolidation** state — set spending to the consistent (lower) level and document
  it as such, rather than matching today's higher actual spending. Also confirm the debt is
  local-currency and rollable (usually low default risk) so you know the stable-debt SS is a modeling
  device, not a solvency claim.
- **A hot interest-growth differential forces spending too low — check `r_gov − g` against data.**
  If the model's real `(r_gov − g)` exceeds the country's actual, `pb*` is inflated and the consistent
  spending drops below the country's real spending. Diagnose both legs: `r_gov` (the LMWW wedge shift
  `μ_d` is a cross-country EM average — check it against the country's *actual* real effective
  borrowing rate = nominal debt-service/gross-debt minus inflation) and `g` (`g_y` set to a stagnant
  realized window understates a country whose debt path assumes medium-term potential growth — the
  SS is a long-run state, so a forward-looking `g_y` can be the honest choice). Bringing `r_gov − g`
  in line with the country lets spending sit at the realistic level. **[net-new: ZAF]**

## Multi-industry (M>1) — the SAM method

Build it as its own builder-regenerated file (packaging choices: mental model item 3): a
`create_multisector_calibration.py` that writes the static JSON, **one** example script
(`run_og_<xxx>_multiple_industry.py`), and shared constants (`TOTAL_CAPITAL_SHARE`,
`PUBLIC_CAPITAL_SHARE`, `CAPITAL_OUTPUT_RATIO`) in one `constants.py` so the builder and the live
Calibration can't drift.

**Finding the SAM — the sourcing hierarchy applies here too; search, don't assume one exists or
doesn't:**
- Search order: (1) the **national statistics office / central bank** — some publish an official SAM,
  and many more publish **supply-and-use tables (SUTs) / IO tables**, which are enough: the make/use
  algebra below runs on them directly (BRA: IBGE SUTs via the Alves-Passoni–Freitas annual IO
  series). (2) **Research institutes that build SAMs with the national authorities** — **UNU-WIDER**
  (country SAM program; ZAF's 2019 SASAM, distributed with a technical note) and **IFPRI** (the
  *Nexus* country-SAM program on the IFPRI Dataverse — standardized ~42-activity SAMs with
  labour-by-education/land/capital factor rows and 10 household groups; PHL's 2018 SAM) are the
  family's two workhorses, free and documented, covering many developing countries. (3) **Global harmonized/modeled databases** only as a last resort, marked
  lower-confidence: GTAP (licensed — one-time tiered fee for the current version, older versions
  free; has factor detail, being a CGE database), EORA (190-country MRIO; free for academic use,
  licensed otherwise), OECD ICIO (free; built from national SUTs but harmonized/balanced). Their
  estimation/balancing steps go beyond the national accounts, and most lack the SAM's full
  household/factor account detail — which is why they rank below a national SUT or an institute SAM.
- **What qualifies:** separate factor rows (labour — ideally disaggregated — and a capital/operating-
  surplus row), household expenditure columns, activity (and possibly commodity) accounts, an
  imports/rest-of-world account, and production-tax rows. Note whether the make is **diagonal or
  rectangular** — it decides the `io_matrix` algebra below. **Match the vintage to the rest of the
  calibration**: the employment survey year must equal the SAM year (ZAF: 2019 SASAM ↔ QLFS 2019),
  and the SAM must reproduce the same-year national accounts (structural validation, below).
- **Delivery: never read the publisher's URL at runtime** — publisher links move and break. Either
  mirror the file in the family's `EAPD-DRB/SAM-files` GitHub repo and read the raw URL (ZAF), or
  ship a compact extract in the package's `data/` (PHL, BRA). Either way record publisher, technical
  note, and year in the reader's docstring and the docs.

**Assert the concordances partition the SAM before anything else:** every activity in exactly one
`PROD_DICT` industry and every commodity in exactly one `CONS_DICT` good — a one-line set-equality
check. ZAF shipped two silently-wrong commodity codes (`colig` for `coilg`, `ccmemb` for `cmemb`)
that just dropped those commodities from every aggregation; the assert catches the whole error class.
**[net-new: ZAF]**

**Defining the industries (`PROD_DICT`) — grouping rules that prevent degenerate capital shares:**
- **Manufacturing / the capital-goods producer goes LAST** (it must be the numeraire — see structural
  facts below).
- **Never let real estate / dwellings stand alone as its own industry [PHL, BRA].** Its measured
  capital share is dominated by *imputed owner-occupier dwelling rent* — booked as operating surplus
  (capital income) but not corporate profit — which pushes its `gamma_m` toward ~1 (degenerate in the
  CES production function) and dilutes its effective CIT (imputed rent isn't taxable profit but sits in
  the denominator). Fold it into a broader **FIRE / finance–business-services** aggregate, as OG-PHL
  and OG-BRA both do. More generally, merge any activity whose surplus is dominated by imputed or
  resource rent (dwellings; watch mining/extractives) rather than modeling it alone — healthy
  capital-intensive sectors (mining, utilities ~0.78 in PHL) solve fine; it's the imputed-rent-driven
  ~0.9+ shares that break things.
- OG-Core has only **two private factors**, so **land/resource rent is folded into capital income** in
  `gamma_m` — a second reason raw SAM capital shares come out biased high (needing the VA-weighted
  rescale) and why rent-dominated activities need grouping.

**The five SAM-derived inputs** (`input_output.py`; OG-PHL is the reference, OG-BRA the most advanced):
0. **`alpha_c`** — household expenditure shares over the I consumption goods, from the SAM's
   **household columns** (purchaser prices — the budget households actually allocate), summing to 1.
   Not the legacy `total − row` shortcut (that's total commodity demand, not household spending).
   Keep the legacy naive `get_io_matrix` in place for the live `Calibration(update_from_api=True)`
   path and its unit tests — the builder uses the value-added version below; both PHL and ZAF follow
   this split.
1. **`gamma_m`** — `(capital+land)/(labor+capital+land)` per industry from SAM factor rows, then
   **rescaled** so the VA-weighted mean equals an independent economy-wide capital share (keeps the
   cross-industry pattern, fixes the level). BRA adds a per-industry mixed-income (Gollin) split first.
2. **`io_matrix`** — the **value-added** version: trace household consumption of each good back through
   the domestic supply chain to value added by industry, weighted by household consumption netted of
   imports, rows renormalized to 1. **Not** the naive direct-intermediate-cell version (a legacy
   baseline that isn't an accounting identity — IDN/ETH still ship only that legacy version). The
   correction is large: household energy spending maps to ~45% electricity in ZAF (~74% in PHL), vs. the
   manufacturing-heavy split a naive direct-use matrix implies. **Match the algebra to the SAM's make
   structure** — this is the error-prone piece: PHL's SAM has a *diagonal* make (one activity per
   commodity), which collapses to `A_d = σ·use/output`, Leontief `(I−A_d)^-1`; but a SAM that separates
   activities from commodities with a **rectangular make** (ZAF's SASAM: 61 activities × 108
   commodities, median commodity produced by >1 activity) needs the full **industry-technology make/use
   algebra** — market-share matrix `D` (`V/g`, allocates each commodity's domestic output to producing
   activities), use coefficients `B` (`U/q`), industry-by-industry Leontief `(I − D·B)^-1`, then VA per
   unit output `v = VA/q`; VA-by-activity `= v·(L @ (D @ f))` for commodity final demand `f`. The
   diagonal shortcut is *wrong* on a rectangular make. Derive `D`/`B`/Leontief from the SAM yourself
   when no pre-computed IO table ships (ZAF), or read them if it does (BRA). Sanity-check with SAM
   balance (`gross output = intermediate + VA + production tax`, machine-precision) and Leontief
   validity (spectral radius of `D·B` < 1) before trusting the result — and watch for a **"total"
   row/column** in the SAM (a 2× inflation tell) that must be excluded.
3. **`L_m` employment** — measured **independently of the SAM** (labor force survey by industry) so
   `Z_m` doesn't collapse into a mechanical function of factor shares. When the survey's industry
   aggregation is coarser than `PROD_DICT` (e.g. QLFS lumps electricity+gas+water into "utilities"),
   split the aggregate by the **SAM's labour-compensation shares** of the sub-activities, not an
   arbitrary or output-based split — a labour-intensive sub-industry (waste/sanitation) employs more per
   rand of output than a capital-intensive one (power generation). A too-low headcount in a small
   sub-industry produces a wild TFP outlier (ZAF Water&Waste `Z` fell 5.3→3.5 once split by labour
   compensation instead of a guessed 77/23).
4. **`Z_m` sector TFP** — Solow residual `Y_m/(K_m^γm · Kg^γg · L_m^(1−γm−γg))`, normalized so the
   **numeraire (last) industry = 1**. `K_m` allocates a national stock (PWT capital-output ratio ×
   total VA) across industries by capital-income share; the ratio's *level* is a weak lever (with the
   numeraire normalization it enters relative Z only through the γ dispersion) — take it from the PWT
   and move on. Reject establishment-survey capital (omits informal capital, inverts the ranking).

**OG-Core structural facts:**
- The **last industry (index M−1) is the numeraire and the only non-consumption producer** — all
  investment, government, net-outflow, remittance, and aid demand loads on it, so its nominal output
  share is inflated and is *never* comparable to a value-added share. **Put the capital-goods /
  manufacturing industry LAST** in `PROD_DICT`.
- **One economy-wide wage; households don't choose a sector** (`L_m` is firm-side labor demand). A
  formal/informal wage gap or sector-choice margin is *not* representable without extending OG-Core.
- `cit_rate`/`tau_c`/`delta_tau`/`inv_tax_credit` **can** vary by industry/good; wage and household
  labor supply cannot.
- The composite-consumption price is **unnormalized**, carrying a units constant `k =
  prod_i(alpha_c_i^−alpha_c_i)` (=1 when I=1) — behaviorally relevant, not cosmetic.

**Single ↔ multi compatibility** (so the two representations agree):
- **Copy economy-wide values verbatim** (demographics, preferences, fiscal ratios, open-economy dials,
  `g_y`, statutory rates) — any difference is a bug.
- `gamma_m`: keep the SAM's dispersion, **impose the single model's level** (VA-weighted mean).
- `Z`: relative TFPs from the Solow residual with numeraire = 1. **Two distinct uses of the Z *level*
  (a common Hicks-neutral rescale) — don't conflate them:** (a) to close *rate/ratio* gaps (r, K_f/K)
  it is a weak, sometimes wrong-signed lever — don't (PHL: an 11.7% Z rise moved r the *wrong* way);
  (b) to align the *income level* (`factor`) it is the correct, clean lever — r, r_gov and K/Y are
  invariant to it, only the income level moves. The numeraire=1 convention pins relative TFPs but leaves
  the level free, and whether it *happens* to land `factor` on the single's is luck (PHL: −0.02%, no
  rescale; ZAF: −23%, needed one). So: if `factor` is still off after the chi conversion, rescale the
  **whole Z vector by a common constant** (a quick log-log root-find on solved-SS `factor` converges in
  2–3 solves; β≈1.8 for ZAF) so the multi's factor matches the single's. `factor` *must* agree — it
  scales the incomes at which the (progressive) tax functions are evaluated, so a 23% factor gap
  mis-collects PIT.
- **The `chi_n`/`chi_b` units conversion is THE alignment lever:** scale both by `k^(σ−1)`, derived
  (not fitted) from FOC-invariance under the composite-consumption units change. In PHL this closed
  44–80% of the r / K_f/K / B/Y / K/Y gaps.
- **Solver seeds are the single-industry model's — never separately tune seeds for the multi.** Lean
  overlay: don't copy them in (inherit from the base at load). Self-sufficient file: the builder's
  merge copies them verbatim and regeneration keeps them synced. Either way the multi cold-starts from
  the single's seeds — which works because the multi's flat anchor *is* the shared aggregate economy.
- **Final acceptance: run the SAME reform through both models** and compare the percent-change tables —
  same signs, similar magnitudes (ZAF: CIT 27→30% through M=1 and M=8; all six aggregates agreed).
- **Comparison dashboard:** must-match (D/Y, tax rates); close (K/Y, `factor` — a big factor gap means
  a level misalignment upstream); ballpark with a written reason (r, K_f/K, B/Y); never compare raw
  (Y/w/C levels, raw C/Y in multi — use `p_tilde·C/Y`, the numeraire's nominal share).

**The continuation solve** (a fallback for when the calibrated multi-industry SS won't solve cold —
OG-Core seeds every industry price at 1). **Try the direct solve first:** ZAF's M=8 converged cold from
the shared base-JSON seeds in ~130s (the flat anchor ≈ the single economy, so the single's seeds are
close), so reach for continuation only if the direct solve fails:
1. Solve a **flat anchor**: all `gamma = economy-wide mean`, `Z = 1`.
2. Walk `t: 0→1`, morphing `gamma(t)` and `Z(t)` **together** to the calibrated values, each step a
   warm-started reform off the previous; grow the step on success, halve on failure.
3. Use **heavier TPI damping, `TPI_NU ≈ 0.2`** (the default 0.4 oscillates; 0.3 is marginal). ogcore
   ≥0.16.4 adds opt-in Anderson acceleration (`TPI_outer_method="anderson"`) as a further lever for
   stiff multi-industry TPI — but remember neither damping nor Anderson fixes a *fiscal* runaway
   (see Fiscal consistency); solver knobs treat oscillation, not an unbalanced budget.
4. Reuse the continuation's converged SS for the baseline TPI (hand-place the pickle) — only the
   reform re-solves its own SS.

**Maturity honesty:** OG-PHL is the reference (the complete version, with the chi conversion, lives on
PR EAPD-DRB/OG-PHL#63's branch, not `main`); OG-BRA is the most advanced port; **OG-ZAF has now
executed the full SAM-Solow method** (make/use-Leontief value-added `io_matrix`, VA-mean-rescaled
`gamma`, Solow-residual `Z` with QLFS employment, the chi conversion, and a factor-aligning Z-level
rescale — a self-sufficient JSON regenerated by `create_multisector_calibration.py`; PR
EAPD-DRB/OG-ZAF#142). OG-IDN and OG-ETH have **not** — their shipped multisector JSONs are partial or
placeholder (OG-IDN even ships the flat *anchor* gamma/Z as if calibrated). Don't treat a sibling's
multisector JSON as a worked example without checking `input_output.py` has the real
`get_gamma`/`get_Z`/value-added `get_io_matrix` functions.

## Validation — test the joint steady state

- **Build a steady-state validation dashboard [emerging: IDN, ETH — adopt it].** A table in `macro.md`
  comparing the solved SS to country data targets, each with a source column. Recurring moments: `D/Y`,
  `D_f/D`, `K_f/K`, `K_f/Y`, `C/Y`, `(I+I_g)/Y`, `K/Y`, `I_g/Y`, `TR/Y`, `NX/Y`, `RM/Y`, `r`, PIT/Y,
  CIT/Y, `T/Y`. The governing sentence: *"most parameters are only weakly identified on their own, so
  the real test is whether the steady state they jointly produce resembles the economy."*
- **Revenue by instrument:** don't just check total tax/GDP — check PIT, CIT, VAT, payroll each against
  collections. Offsetting errors can make the total look right while the composition is wrong.
- **Source the data side by actively searching for the most authoritative source that exists — never
  fill the dashboard from memory, and never treat any source list (including this one) as closed.**
  A wrong data anchor silently fails an otherwise-correct calibration, so treat the data column as
  carefully as the model column. For each moment, search in descending order of authority and stop at
  the highest rung that has the number:
  1. **The official national institution that *owns* the number** — the agency that administers it:
     revenue service for collections, treasury/finance ministry (budget review, fiscal framework,
     debt bulletin) for spending/debt/debt-service, statistics office for GDP-by-industry / HFCE /
     the labour force survey, central bank (quarterly bulletin, IIP) for external and monetary data.
     Institution *names* differ by country — search by **role** ("who administers this number
     here?"), and expect to find ministries, debt-management offices, planning commissions, or
     social-security agencies you didn't know existed. Their publications outrank everything else.
  2. **Official international compilations of national data** — IMF (Article IV statistical
     appendix, GFS, WEO), World Bank, UN, ILO, PWT — often the same national numbers, re-published
     with a lag and on standardized definitions (useful for cross-checks, weaker on vintage).
  3. **Regional development banks and bodies** — AfDB/ADB/IADB/EBRD country diagnostics, regional
     statistical commissions — frequently carry country detail (sector data, informality, fiscal
     risk) that neither the national site nor the IMF publishes cleanly.
  Typical role→moment map to start from: tax ratios ← revenue service *tax statistics* + budget
  review; debt / foreign-share / effective `r_gov` (= debt-service ÷ gross debt, deflated) ← budget
  review / debt office; sector value-added shares ← GDP-by-industry release; household consumption
  shares ← HFCE / expenditure survey / CPI weights; employment by industry ← labour force survey;
  `K/Y` ← PWT. Adversarially re-check the load-bearing numbers against a second, independent source.
  When the search genuinely comes up empty at every rung, use the best lower-rung number, note the
  vintage, and mark the moment lower-confidence rather than dropping it from the dashboard.
- **Mind the GDP vintage — the silent ratio trap.** When the statistics office *rebases* GDP, every
  `x/GDP` ratio moves without anything real changing (South Africa's 2021 rebasing shifted tax-to-GDP
  ~2.6 pp: 23.7% on the rebased base vs 26.3% on the old base, *same year*). Compare a model ratio to a
  data ratio on **one consistent GDP vintage**, and say which — a calibration tuned to an old-vintage
  ratio will look ~2–3 pp off against current data for no real reason.
- **Read the model side from the solved SS object** (`safe_read_pickle` on `SS_vars.pkl`), don't
  eyeball it: fiscal ratios are revenue lines over `Y` — PIT `iit_revenue/Y`, CIT
  `business_tax_revenue/Y`, indirect `cons_tax_revenue/Y`, total `total_tax_revenue/Y`; `D/Y`, `D_f/D`,
  `K/Y` from the aggregates over `Y`; `r`, `r_gov`, `factor` directly; consumption share as
  `p_tilde·C/Y` (never raw `C/Y` when `I>1`).
- **Structural validation (multi-industry) — check the SAM reproduces the national accounts before
  trusting it.** The SAM's value-added shares by broad sector should track the statistics office's
  GDP-by-industry (a 2019 SA SAM matched Stats SA to ~0.5 pp on primary/secondary/tertiary); employment
  shares should match the LFS (they are the source); `alpha_c` should match HFCE's goods/services
  split. A SAM that doesn't reproduce the national accounts' sector structure is the wrong vintage or
  mis-aggregated — fix that before reading anything else off the multi-industry SS.
- **Note derived quantities honestly:** e.g. "net exports" is a balance-of-payments *residual* of the
  resource constraint (OG-Core has no trade sector), not a modeled export/import.
- **Know the family traits before "fixing" them:** the model's endogenous `K/Y` runs high against the
  PWT across the whole family (ZAF 4.5 vs 3.7; PHL 4.3) — a structural feature of the saving/return
  block, not a country-calibration error. Report it with a written reason in the dashboard's ballpark
  tier; don't distort a country parameter to chase it.
- **Fast value-pinning test [emerging: ETH — adopt it].** A `test_default_parameters.py` that loads the
  shipped JSON and pins specific calibrated values with inline source citations, explicitly *not*
  asserting anything that needs a solve. Separate this from the slow example smoke test.
- **Prevent doc/JSON drift with `{glue:text}` [emerging: ETH — adopt it].** A hidden code-cell in the
  docs loads the packaged JSON and `glue()`s the numbers, so prose can never drift from the shipped
  values.

## House rules (lift verbatim into any port)

- **uv only, run as a user would.** Don't hand-pick a Python; let uv resolve Python + ogcore.
- **Never commit a `uv.lock` change** from calibration work; keep it out of the PR diff.
- **Non-destructive:** the single-industry default must keep working; ship multi-industry as its own
  builder-regenerated file (lean overlay or self-sufficient — see the packaging choices in the mental
  model), never by editing the single-industry JSON.
- **Document every calibrated value with a source** — even stylized placeholders (family norm; a few
  repos' tax docs still lack inline citations — add them when you touch those docs).
- **Ask before push, ask before PR — never in the same step.** PR style: narrative, plain language,
  explain the *why*, push detail to the docs; a changed-parameters table + a steady-state-lands table +
  an example macro-results table.

### Preparing the calibration PR — what maintainers actually ask for [PHL #63 review, jdebacker]

- **Show the before/after of every calibrated object the PR changes — upfront, don't make them ask.**
  On PHL #63 the maintainer's first request was a *new-vs-old side-by-side of the `io_matrix`*. For each
  changed array/matrix (`io_matrix`, `gamma`, `Z`, tax params), put an old→new table in the PR (or a
  reply thread) with the largest shifts called out and explained *by mechanism* — e.g. household energy
  spending moving off manufacturing onto electricity (54%→4% / 11%→74%) because the value-added method
  traces demand to the industry that makes it, not to the numeraire. The diff of a packaged JSON is
  unreadable; the side-by-side is how a reviewer verifies the change does what you claim.
- **Pre-empt the `gamma_g` question.** The maintainer flagged that the SAM books all non-labor income as
  capital with no public-capital attribution, so subtracting `gamma_g` implicitly from *labor* is wrong.
  State the construction explicitly: rescale the SAM's total capital shares to the economy-wide total,
  then subtract `gamma_g` so public capital comes out of *capital* (the SAM measures labor's share
  well). If `gamma_g = 0` (e.g. ZAF), say so — private = total, no carve-out — so the reviewer needn't
  raise it.
- **PR-explanation visuals are not docs visuals.** The maintainer asked that a figure's "what's changing
  in this PR" annotation (a dashed old-vs-new line) be *removed from the version committed to the docs*.
  Keep delta/before-after annotations in the PR conversation; the docs figure shows the calibrated state
  cleanly, because the docs describe the calibration as it *is*, not the PR's delta.
- **Explain derived mechanical corrections in plain language a non-specialist can follow.** A non-obvious
  fix (the chi/`p_tilde` units conversion; a Z-level factor rescale) needs: what was off, the arithmetic
  that causes it, and that the constant is *derived, not fitted*. Same for version-driven fixes — if an
  ogcore bump broke the example and you regenerated demographics/params to fix it, say so and give the
  before/after residual-constraint numbers.

## End-to-end sequence for a new country

*Mechanics used throughout:* solve/run via `uv run python examples/run_og_<xxx>.py` (baseline +
reform + output tables); the earnings tilt is solved inside `income.py`'s
`get_e_interp(gini_to_match=...)`; and dashboard moments are read from the solved output objects with
`ogcore.utils.safe_read_pickle` on `.../OUTPUT_BASELINE/SS/SS_vars.pkl`, `.../TPI/TPI_vars.pkl`, and
`model_params.pkl` (then form ratios like `K_f/Y`, `C/Y`, revenue/GDP).

1. Bootstrap from the closest sibling repo; **immediately fix the copied `country_id`, package name,
   and `egg-info`** (the #1 copy-paste regression).
2. Environment: `uv sync --extra dev`; confirm the resolved ogcore in `uv.lock` matches the EAPD
   siblings; run the preflight.
3. Demographics: set `country_id` (named constant) + add the regression test; solve, check SS
   population growth is sane.
4. Earnings: set the country's earnings-concept Gini (WID, matching the US reference concept); solve
   the tilt scalar.
5. Macro block: debt (initial measured, SS anchored), `zeta_K` (Chinn-Ito + cross-check), world rate
   (open vs distressed fork), `g_y` window (named constants), remittances/aid if material, the centered
   debt-elastic premium, `initial_Kg_ratio` if `gamma_g > 0`.
6. Capital share: `1 − labor_share`, Gollin-adjusted if agrarian/informal; **remove gamma from the
   live-API path** so it can't be clobbered.
7. Taxes: for PIT, prefer a **progressive form fit to the statutory schedule** over a flat rate
   whenever a schedule exists — **GS by default** (φ0 = statutory top rate, φ1 to the shape, φ2 to
   collections; floors ETR at 0); take VAT/CIT/payroll as effective rates from collections; pick the
   informality rung the data supports.
8. `chi_n`: leave at the US values but **document it as uncalibrated**, or re-tilt to an hours target.
9. Validate: build the steady-state dashboard; check revenue by instrument; add the value-pinning test.
10. (Optional) Multi-industry: source the SAM (national SUTs → UNU-WIDER/IFPRI → modeled databases;
    vintage matched to the LFS year); assert the concordances partition it; build the 5 SAM inputs,
    numeraire industry last; try the direct solve first (`nu≈0.2`; continuation only as fallback);
    apply the chi units conversion, then a Z-level rescale if `factor` is still off; verify
    single↔multi agreement via the comparison dashboard and the same-reform acceptance test.
11. Wrap up: `make format`, `pytest -m 'not local'`, CHANGELOG entry (before→after + citation), docs
    with glue-from-JSON. Ask before pushing; ask before the PR.

## Related skills

- `og-run` — actually launching the baseline and reform solves.
- `og-run-preflight` — the go/no-go check before any solve.
- `calibration-provenance` — tracing one parameter to its source.
- `muiogo-explain` — explaining the calibration to a person.
- `og-clews-linked-run` — coupling the calibrated model to a CLEWs energy scenario.

These live in the MUIOGO-AI collection; if one is not available to you,
do the job directly and say which skill would have covered it.
