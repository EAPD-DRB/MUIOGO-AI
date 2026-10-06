# Macro and open-economy block

Method, pitfall and exemplar for each parameter, then the capital share and the gross-vs-net `K_f`
question. The `K/Y` closed form these rows refer to is in SKILL.md, Step zero.

Contents
- start_year
- Debt (initial_debt_ratio, debt_ratio_ss)
- zeta_D
- zeta_K
- world_int_rate_annual
- g_y_annual
- r_gov base wedge (r_gov_scale, r_gov_shift)
- r_gov floor
- Remittances and aid
- Debt-elastic premium (r_gov_DY, r_gov_DY2)
- initial_Kg_ratio
- Initial household wealth
- delta_annual
- beta_annual
- alpha_T
- Capital share (gamma)
- K_f gross vs net

## start_year

**Method.** A calibration decision, not a default: the most recent year the calibration can
observe, not a projection year. Check which anchors are observations and which are extrapolations
under each candidate year. The initial debt ratio is the sharp test: it must equal the debt ratio at
the start of the start year (end of the prior year). Levels observed in year X (remittances/GDP,
interest actuals) are data for a year-X start but extrapolations for X+1. Changing it regenerates
demographics (and everything derived from them) through the country's regeneration tool, and
re-maps the fiscal glide to the program years.

**Pitfall.** Inheriting a future start year from a sibling. PHL shipped start 2026 while its latest
data was 2025: the packaged `initial_debt_ratio` 0.60 was the beginning-of-2025 value (a 2026 start
needed ~0.62), and the 2025-observed remittance ratio was treated as a 2026 extrapolation.

**Exemplar.** PHL (caught by the user, moved 2026 → 2025).

## Debt (initial_debt_ratio, debt_ratio_ss)

**Method.** `initial_debt_ratio` is measured (national, IMF or QPSD series). `debt_ratio_ss` is a
policy anchor (program target or stance), a separate parameter that shapes the whole steady state.

**Pitfall.** Leaving `debt_ratio_ss` inherited and undocumented. Not checking whether a debt-ratio
jump is a valuation effect (an FX float revaluing external debt) rather than real deterioration. A
wrong `initial_debt_ratio` is invisible to the steady state; only the transition starts from it
(see fiscal-consistency.md).

**Exemplar.** IDN, ETH.

## zeta_D

**Method.** Default: set it equal to `initial_foreign_debt_ratio` (the foreign share of new issuance
equals the foreign share of the stock).

**Pitfall.** Using the realized flow when it is a crisis-period outlier (donor surge, debt
standstill). Use the DSA's projected medium-term flow instead.

**Exemplar.** USA measures the flow directly; ETH uses the DSA projection.

## zeta_K

**Method.** A marginal fill share no dataset measures, so calibrate it by the level it produces.
Tune until the solved steady-state `K_f/K` matches the IIP foreign-capital share (two or three SS
solves bracket it; PHL sensitivity ≈ 0.4pp of `K_f/K` per 0.01 of `zeta_K`). The normalized
Chinn-Ito index is the prior that locates the plausible range, not the target. Decide gross vs net
`K_f` first (last section). **Re-validate after any tax-side change.** Tax recalibration moves
domestic saving, which moves `K_f/K` at a fixed `zeta_K` (PHL: honest taxes pushed it 0.26 → 0.14;
`zeta_K` 0.4 → 0.47 restored the 0.20 IIP anchor).

**Pitfall.** The `zeta_K = 0.9` placeholder ("implies high openness"). It drives domestic capital
`K_d = B − D_d` negative. `aggregates.get_K_splits` then floors `K_d` at `0.05·B` (`np.fmax`, with a
"K_d has negative elements" print) while `K_f` is still computed from the unfloored formula, so
`K = K_d + K_f` no longer adds up to the intended split and the transition breaks. Also: treating
Chinn-Ito as the target and never solving for the level. The opposite failure: a placeholder 0.10
(the OG-Core default) that left the JPN `K/Y` and consumption gaps open for fourteen rounds.

**Exemplar.** Method: IDN, ETH; level tuning executed on PHL. The 0.9 pitfall: IDN and PHL both hit
it and fixed it.

## world_int_rate_annual

**Method.** Open, investment-grade: risk-free (~4%) plus the country's sovereign spread.
Near-closed or distressed: leave it at the ~4% benchmark and route country risk through a low
`zeta_K` and the debt-elastic premium instead. At high `zeta_K` this constant sets `r`, so source it
(SKILL.md, default sweep).

**Pitfall.** Adding a spread for a defaulted or restructuring sovereign (wrong model); leaving it
undocumented.

**Sign check.** The world rate sets the sign of `K_f`, not only its size. If it sits above the solved
domestic return, foreign capital flows out and `K_f` turns negative whatever `zeta_K` is. After setting
it, solve and confirm `K_f/K` has the sign the target needs. A sub-investment-grade but not distressed
sovereign sits between the two cases above; say which rule you applied and why. **[ZAF]**

**Exemplar.** IDN (open); ETH (distressed).

## g_y_annual

**Method.** Measure per hour, not per worker. Labour input is people × hours × ability and
steady-state hours per worker are constant, so a trend in hours per worker is transitional and must
be stripped, exactly like a trending participation rate; treat the two consistently (it is easy to
strip one and leave the other). PWT via FRED: real GDP ÷ (persons engaged × average hours). JPN
2000–2019: +0.557%/yr per worker, −0.472%/yr hours, +1.035%/yr per hour **[net-new: JPN]**. Choose
the growth window as named constants with a rationale (start after a structural break, end before
the latest shock, reject unrepeatable booms). The steady state is a long-run state, so `g_y` must be
consistent with the growth the `debt_ratio_ss` anchor assumes (`GDP growth ≈ g_y + g_n_ss`). If the
debt target is a stabilization plan built on a medium-term recovery, use that recovery's
productivity growth (medium-term GDP growth − `g_n_ss`), not the stagnant realized window.

**Pitfall.** Naive "all history" or an inline date argument. Or a realized-stagnation `g_y` paired
with a stabilization `debt_ratio_ss`: internally inconsistent (that is the pessimistic,
debt-drifts-up scenario), so the model's debt will not hold at the target.

**Exemplar.** IDN, ETH, PHL. ZAF: the realized 0.6% was inconsistent with the 0.765 anchor's ~1.8%
growth, so `g_y` rose to ~1.4% (= 1.8% − `g_n` 0.42%).

## r_gov base wedge (r_gov_scale, r_gov_shift)

**Method.** `r_gov = scale·r − shift + premium`, and it multiplies the whole debt stock in
`debt_service = r_gov·D`, so it is an average, effective real rate. Keep the LMWW slope (`scale`, the
estimated sovereign-vs-corporate pass-through), but re-anchor the `shift` so the steady-state
`r_gov` equals the country's actual real effective rate on debt: interest payments ÷ gross debt,
minus expected inflation. Take both from the treasury's own cash-operations or budget report (news
stories mislabel fiscal years; PHL's widely quoted "FY2024" interest figure was FY2025). Expect
`r_gov < g` for many emerging markets. Then the debt-stabilizing primary balance `pb*` is a deficit,
matching how such countries stabilize debt while running primary deficits. State the consolidation
gap (actual primary balance vs `pb*`) in the docs, since the stable-debt steady state embeds it.

**Pitfall.** The LMWW intercept is a cross-country EM average that maps a nominal USD bond-yield
level onto the model's real MPK. It over-predicted ZAF by ~0.5–0.6pp and PHL by ~3pp (5.1% vs the
~2.0% the Treasury pays), inflating the debt-stabilizing primary surplus and forcing spending too
low. Do not use the 10-year or inflation-linked marginal yield either: that is new-issue cost, not
the stock average.

**Exemplar.** ZAF (~3.7%), PHL (~2.0%).

## r_gov floor

**Method.** `fiscal.get_r_gov` wraps the wedge in a lower bound, 0.0 by default. Newer ogcore lets
you set it (`r_gov_floor`); older versions hard-code it. For a sovereign in a sustained
negative-real-rate regime, set the floor below the effective rate you calibrate to. The tell of clipping is a reported `r_gov`
of exactly `0.0000` when the formula returns a negative number.

**Pitfall.** The clip matters less through the interest bill than through `pb*`, hence government
spending (0.51pp of GDP on JPN). Do not compensate elsewhere; if your ogcore cannot set the floor,
bump it.

**Exemplar.** **[net-new: JPN]**

## Remittances and aid (alpha_RM_1, alpha_RM_T, eta_RM, g_RM, alpha_FA)

**Method.** Hand-set JSON values, never fetched. Turning them on lets a low-income economy reproduce
a real trade deficit and a fiscally sustainable government.

- **Level.** Use the personal (BPM6) remittance measure: the model's `RM` is household income from
  abroad. Central banks often headline a GDP ratio only for the narrower cash (formal-channel)
  series, ~1pp of GDP lower. Derive personal/GDP on one consistent denominator.
- **Path.** `alpha_RM_1 = alpha_RM_T` pins only the endpoints. `get_RM` compounds
  `(1+g_RM)/(e^{g_y}(1+g_n))`, so a flat RM/Y requires `g_RM[t] = e^{g_y}(1+g_n[t-1]) − 1`, a
  time-varying path (no scalar works when `g_n` moves; regenerate it with the demographics).
  `g_RM` is in model growth units, never the nominal-USD growth rate from a press release. The
  steady state never reads `g_RM` (`RM_ss = alpha_RM_T·Y`), so a wrong path corrupts only the
  transition.
- **Distribution.** ogcore's default `eta_RM` is population-proportional; survey evidence
  (FIES-type) shows remittance value concentrated at the top. Build group shares as quintile mean
  income × remittance share of income (equal-count quintiles give the value share directly), map to
  the J groups by interpolating the cumulative distribution, and spread per capita over ages. Note
  the caveats: ranking by current rather than lifetime income overstates concentration; uniform
  within the top quintile understates it.
- **Schema.** `eta_RM` in the parameters JSON is `(S, J)`; the `(T+S, S, J)` on a live
  `Specifications` object is internal tiling.

**Pitfall.** Leaving remittances or aid off for an aid- or remittance-dependent economy: a spurious
trade surplus and an implausible fiscal squeeze. A nominal growth rate in the `g_RM` slot: PHL
shipped `g_RM = 0.03` (Dec-on-Dec USD growth) against a ~5.7% model-consistent denominator, so RM/Y
fell 35% below its calibrated share by t≈24 and recovered only after t≈100, with nothing in the docs
intending it. The cash-measure trap: PHL's 0.072 came from a central-bank headline that was the cash
series (personal was 8.1%).

**Exemplar.** PHL (all three, fixed); ETH (aid).

## Debt-elastic premium (r_gov_DY, r_gov_DY2)

**Method.** The base wedge is a country-agnostic OLS inversion of Li-Magud-Werner (the same numbers
everywhere). Add the convex Schmitt-Grohé/Uribe term in centered form around `debt_ratio_ss`,
expand, and fold the constant into `r_gov_shift`. The premium is then exactly zero at the steady-state
target and prices only transition overshoot: `r_gov_DY = -2·r_gov_DY2·D̄`,
`r_gov_shift = base − r_gov_DY2·D̄²`.

**Pitfall.** A live-refresh path that returns the raw LMW shift silently de-centers the premium and
moves the steady state. Freeze it.

**Exemplar.** IDN, ETH.

## initial_Kg_ratio

**Method.** Solve the model's own steady-state law of motion
`K̄g/Ȳ = (1−φg)·αI / (e^{gy}(1+gn) − (1−δg))`. If the measured stock is far above sustainable (an
SOE-built boom), start at the measured value and let it depreciate.

**Pitfall.** Inheriting a sibling's `0.2` undocumented. OG-Core's default is `0.0`, and the value
only matters when `gamma_g > 0`.

**Exemplar.** ETH only; replicate wherever `gamma_g > 0`.

## Initial household wealth

The family uses rickecon's approach (OG-Core's draft on calibrating the initial wealth
distribution; parameter names may still change in review, so check what your build has). Work built
on earlier designs migrates to it: carry over the data target (the initial wealth-to-GDP ratio and
its construction), not the old parameter value, which was scaled differently. Two pieces:

- **Shape.** An S×J matrix of factors on the steady-state wealth profile:
  `b(s, j, t=1) = factor(s, j) × b_ss(s, j)`. All ones (the default) starts every household at its
  steady-state wealth. Valid range 0.4–2.0.
- **Level.** An optional target for initial aggregate household wealth / initial-year GDP
  (`initial_BY_ratio`, switched on by `use_initial_BY_ratio`; valid range 0.8–7.0). Because
  first-year GDP is endogenous, the transition rescales the whole initial distribution by a common
  factor each iteration until `B_1/Y_1` hits the target.

**Diagnose first.** Before setting anything, see what initial condition your ogcore imposes by
default and what it does to the first years. Older ogcore rescaled the steady-state profile so
aggregate B(0) = B_ss, which hands every initial household a uniform windfall when the initial
population is younger than the stationary one (confiscation when older); the per-household scale is
`B_ss / get_B(b_sp1, p, "SS", True)`. The default above avoids that windfall but gives an aggregate
B(0) set by demographics, not data. Either way the fingerprint of a wrong initial condition is a
violent year-1-or-2 consumption spike concentrated in ages 60+ across all j, an investment
collapse, a `tau_c` revenue pulse and a spurious debt paydown (or the mirror images). It is
invisible in reform-minus-baseline tables, because both paths share the initial condition.

**The level: what number to target.** The parameter asks for aggregate household wealth / GDP in
the start year. Two ways to measure it, and they differ:
- *Capital side (model-consistent):* the model forces B(0) = K_d(0) + D_d(0), so
  `(K/Y_PWT − public capital/Y) × (1 − IIP foreign-owned share) + domestic-held share × D/Y`.
  Compute the PWT ratio from the raw current-PPP series pair (capital `CKSPPP…` over output
  `CGDPOS…` on FRED), never from memory; PHL moved 3.33 (2019) → 3.97 (2023).
- *Household balance sheets* (UBS databook class; OG-Core's own documentation tabulates these, e.g.
  PHL 2.50, ZAF 2.56, ETH 1.70). Usually lower for emerging markets, because they undercount real
  property.

Prefer the capital-side number, cross-check against the balance-sheet one, and write down which you
used and why. Expect initial < steady-state wealth ratio for a fast-growing economy.

**The shape.** Ones is a defensible start. If survey data gives wealth by age (and income group),
set the factors to data relative to the model's steady-state profile, so the young and old start
where they actually are. Check the result stays inside the valid range; a factor pinned at a bound
means the steady-state profile itself is far from the data, which is a finding.

**Check the solve, not just the target.**
- Confirm the solved `B_1/Y_1` equals the target.
- Rescaling initial wealth between transition iterations is the step that misbehaved before: on
  JPN it drove the initial cohorts into negative-consumption solutions that satisfied the extended
  first-order conditions and passed OG-Core's constraint checker, which watches a different object.
  Always read minimum household consumption from the pickle, and watch that the outer-loop distance
  still falls. If the targeted run misbehaves, a fixed level reached by tuning the factor matrix over
  a few runs (target off) is the static alternative.
- **Report the initial foreign capital share** `K_f(0)/K(0)` against the IIP; it is untargeted.
  Where the model's `K/Y` overshoots the PWT, measured household wealth and the measured foreign
  share cannot both be hit: the model fills its larger capital stock with foreign inflows. Keep the
  wealth anchor and document the foreign-share miss with its cause (PHL: hitting the IIP share would
  have needed 4.3 against a measured 3.35).
- Then re-tune the `alpha_G` glide; it was fit against the old initial condition's revenue path.

**Pitfall.** PHL's old default scale was 1.625 (a 63% windfall): retirees consumed at 3–7× steady
state for years, C jumped 41% for one year, domestic investment fell to ~2% of long run, and debt was
paid down to 50% against a 60% target. It surfaced only in level exercises.

**Exemplar.** PHL (diagnosis and fix); JPN (the in-loop rescaling failure).

## delta_annual

**Method.** Source it; no repo does. `delta = (CFC/Y)/(K/Y)`: consumption of fixed capital from
World Bank `NY.ADJ.DKAP.GN.ZS` (convert the GNI basis to GDP), `K/Y` from PWT. Decisive in a slow- or
negative-growth economy: steady-state investment is `(g + delta)·K/Y`, so as `g → 0` depreciation is
nearly the only thing generating investment demand.

**Pitfall.** Leaving OG-Core's 0.05, a US value. JPN 0.05 → 0.062 moved investment 2.7pp of GDP.

**Exemplar.** **[net-new: JPN]**

## beta_annual

**Method.** Not observable; calibrate it to the capital-output ratio through the firm FOC (SKILL.md,
Step zero). With `gamma` and `delta` sourced, `K/Y` is a function of `r`, and `r` is what `beta`
moves; two or three SS solves bracket it. `beta` is one of eleven levers on `K/Y`, so check Step
zero before concluding it is the binding one. Order matters: sourced parameters first, then look at
`K/Y`. If it already sits on the PWT value, `beta` has no room and moving it is curve-fitting; if
`K/Y` is off, `beta` is the right instrument.

**Pitfall.** Leaving OG-USA's 0.96 unexamined, or moving `beta` while `K/Y` is already on target.
Re-ask after any change to `gamma`, `delta` or `g_y`; on JPN the answer flipped twice.

**Exemplar.** **[net-new: JPN]**

## alpha_T

**Method.** Cash transfers only. Health, long-term care and education delivered in kind are
government final consumption in the national accounts; in OG-Core they belong in `G`, which stays
out of the household budget, not `TR`, which enters it. Split from OECD SOCX or the national
social-security accounts.

**Pitfall.** In-kind spending in `alpha_T` hands households income they do not have and inflates
consumption directly. JPN shipped 0.075 against a true cash ~0.025: three times too high, the largest
single error in its consumption fit. Worst wherever health care is publicly provided in kind, which
is most of the OECD.

**Exemplar.** **[net-new: JPN]**

## Capital share (gamma)

- **Baseline [family].** `gamma = 1 − labour share` (ILOSTAT or national accounts), then carve
  `gamma_g` (the public capital share) out of the capital side. Fine for formal economies (USA).
- **Gollin / self-employment adjustment, for agrarian or informal economies.** Raw labour shares are
  biased because self-employed mixed income is booked as capital. Two methods:
  - *Aggregate triangulation* **[ETH]**: adjust the economy-wide labour share up using non-circular
    evidence: a growth-accounting check `gamma = (r+δ)(K/Y)` (an implausible implied return flags a
    wrong share), the Gollin direction-of-bias argument, and country institutions (e.g. state-owned
    land). State the result as a range with a center, not a point.
  - *Cross-sectional rescale* **[multi-industry; PHL]**: keep the SAM's per-industry dispersion but
    rescale so the value-added-weighted mean equals the economy-wide capital share. Where the table
    has a mixed-income row, split it per industry first **[BRA]** (og-multi-industry-calibration).
- **Pitfall [ETH, verified].** The `update_from_api=True` path recomputes the naive `1 − ILOSTAT`
  and silently clobbers a hand-triangulated `gamma` (e.g. overwrites 0.30 with 0.515), undoing the
  whole argument in the docs. Because some examples call that path whenever online (SKILL.md, mental
  model 1), this sits in the default run. Remove curated structural parameters from the live path
  entirely, as IDN did; an `if update_from_api` guard is not enough.

## K_f gross vs net

Settle this before tuning `zeta_K`; for a net-creditor country the two readings differ in sign.

The identity is `K = K_d + K_f` with `K_d = B − D_d`, so `K_f` reads as the **gross** foreign-owned
share of the domestic capital stock: households hold domestic capital and domestic government debt,
and nothing else. On that reading the IIP target is inward direct-investment equity (including
reinvested earnings) + inward portfolio equity, ÷ GDP ÷ `K/Y`. Japan end-2024:
(34.5 + 334.8) / 609 / 3.70 = +16.4%, against the 1.5% a placeholder `zeta_K = 0.10` produced.

But `K_f = zeta_K·(K_demand_open − B + D_d)` is not clamped, and the outflow term
`(r + delta)·K_f − new_borrowing_f + debt_service_f` reverses cleanly, so a negative `K_f` is
arithmetically fine and reads as a **net** creditor position. Japan's net IIP is +¥533tn, 87.5% of
GDP; on the net reading the target is −23.7%, the opposite sign.

**Which to use.** The identity is the stronger argument: `K_d = B − D_d` leaves households no foreign
asset, so a negative `K_f` is an unclamped edge case rather than a designed representation.
Calibrate to gross. Say plainly what that costs: the model omits the country's foreign portfolio, so
household wealth `B` is understated by it and the primary income it earns is absent from the
resource constraint (for Japan, ¥1,659tn of assets and roughly 3.8% of GDP a year of income). This is
an OG-Core limitation, not a calibration choice: there is one `K_f`, so a two-sided external balance
sheet cannot be expressed. Check the sign of the country's NIIP, state which reading you took, and
note the omission in the audit. **[net-new: JPN]**
