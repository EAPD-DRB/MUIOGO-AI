# Macro and open-economy block

Method, pitfall and exemplar for each parameter, then the capital share and the gross-vs-net `K_f`
question. The `K/Y` closed form these rows refer to is in method.md, Step zero.

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

**Pitfall.** A start year past the latest data, whether inherited from a sibling or set ahead in a
parameter update. A start one year past the latest data
makes the packaged `initial_debt_ratio` the prior year's value (the later start needs a different
one), and turns the latest observed levels, such as the remittance ratio, into extrapolations.
**[PHL]** (history: PHL)

**Exemplar.** PHL (caught by the user, moved back to its latest data year).

## Debt (initial_debt_ratio, debt_ratio_ss)

**Method.** `initial_debt_ratio` is measured (national, IMF or QPSD series). `debt_ratio_ss` is a
policy anchor (program target or stance), a separate parameter that shapes the whole steady state.

**Pitfall.** Leaving `debt_ratio_ss` inherited and undocumented. Not checking whether a debt-ratio
jump is a valuation effect (an FX float revaluing external debt) rather than real deterioration. A
wrong `initial_debt_ratio` is invisible to the steady state; only the transition starts from it
(see fiscal-consistency.md).

**A government that owns large financial assets.** OG-Core's government has debt but no assets.
Where it holds a large funded pension reserve or sovereign fund, choose the perimeter and say it:
gross debt (D2-type) paired with the effective rate on gross debt (validation-dashboard.md, "Pair
the debt concept with the interest concept"), with the asset side and its income left out. That
income is then missing from revenue, so the budget closure lands `G/Y` below the data by about that
much (on KOR, ~2.4% of GDP of property income): report it as that omission, not as a consolidation
gap.
Do not route it through `alpha_FA`: that parameter is foreign aid and also enters the resource
constraint as an inflow from abroad. **[KOR]**

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
domestic saving, which moves `K_f/K` at a fixed `zeta_K` (on PHL, honest taxes moved it from 0.26
to 0.14, and re-tuning `zeta_K` restored the IIP anchor). (history: PHL)

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
(method.md, default sweep).

**Pitfall.** Adding a spread for a defaulted or restructuring sovereign (wrong model); leaving it
undocumented.

**Sign check.** The world rate sets the sign of `K_f`, not only its size. If it sits above the solved
domestic return, foreign capital flows out and `K_f` turns negative whatever `zeta_K` is. After setting
it, solve and confirm `K_f/K` has the sign the target needs. A sub-investment-grade but not distressed
sovereign sits between the two cases above; say which rule you applied and why. **[ZAF]**

**When the sign check fails at the data's own `K/Y`.** For a high-saving net creditor, the domestic
return at the data-consistent private `K/Y` can sit at or below the world rate, so the excess capital
demand that `zeta_K` scales is zero or negative. Then no `zeta_K` produces a positive gross `K_f/K`,
and `zeta_K` is not identified by the steady state. Do not invent a world rate to rescue the target,
and do not distort `K/Y`. Keep the sourced world rate, set `zeta_K` from the openness prior with a
written reason, judge it on the transition, and report the `K_f/K` miss with its cause. (On KOR,
every `zeta_K` from 0.17 to 0.5 left gross `K_f/K` negative, −0.9% to −3.3%, against a positive
target.) **[KOR]** (history: KOR)

**Exemplar.** IDN (open); ETH (distressed).

## g_y_annual

**Method.** Measure per hour, not per worker. Labour input is people × hours × ability and
steady-state hours per worker are constant, so a trend in hours per worker is transitional and must
be stripped, exactly like a trending participation rate; treat the two consistently (it is easy to
strip one and leave the other). PWT via FRED: real GDP ÷ (persons engaged × average hours). On JPN,
falling hours per worker meant measuring per hour raised `g_y` by about 0.5pp a year over measuring
per worker **[net-new: JPN]** (history: JPN). Choose
the growth window as named constants with a rationale (start after a structural break, end before
the latest shock, reject unrepeatable booms). The steady state is a long-run state, so `g_y` must be
consistent with the growth the `debt_ratio_ss` anchor assumes (`GDP growth ≈ g_y + g_n_ss`). If the
debt target is a stabilization plan built on a medium-term recovery, use that recovery's
productivity growth (medium-term GDP growth − `g_n_ss`), not the stagnant realized window.

**Pitfall.** Naive "all history" or an inline date argument. Or a realized-stagnation `g_y` paired
with a stabilization `debt_ratio_ss`: internally inconsistent (that is the pessimistic,
debt-drifts-up scenario), so the model's debt will not hold at the target.

**Exemplar.** IDN, ETH, PHL. ZAF: the realized-window `g_y` was inconsistent with the growth its
`debt_ratio_ss` anchor assumes, so `g_y` was set to that growth less `g_n`, a rise of about 0.8pp
(history: ZAF).

## r_gov base wedge (r_gov_scale, r_gov_shift)

**Method.** `r_gov = scale·r − shift + premium`, and it multiplies the whole debt stock in
`debt_service = r_gov·D`, so it is an average, effective real rate. Keep the LMWW slope (`scale`, the
estimated sovereign-vs-corporate pass-through), but re-anchor the `shift` so the steady-state
`r_gov` equals the country's actual real effective rate on debt: interest payments ÷ gross debt,
minus expected inflation. Take both from the treasury's own cash-operations or budget report (news
stories mislabel fiscal years **[PHL]**; history: PHL). Expect
`r_gov < g` for many emerging markets. Then the debt-stabilizing primary balance `pb*` is a deficit,
matching how such countries stabilize debt while running primary deficits. State the consolidation
gap (actual primary balance vs `pb*`) in the docs, since the stable-debt steady state embeds it.

**Pitfall.** The LMWW intercept is a cross-country EM average that maps a nominal USD bond-yield
level onto the model's real MPK. It over-predicted ZAF by ~0.5–0.6pp and PHL by ~3pp against what
each treasury actually pays, inflating the debt-stabilizing primary surplus and forcing spending too
low. Do not use the 10-year or inflation-linked marginal yield either: that is new-issue cost, not
the stock average.

**Exemplar.** ZAF, PHL (history: ZAF, PHL).

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
trade surplus and an implausible fiscal squeeze. A nominal growth rate in the `g_RM` slot: on PHL,
a Dec-on-Dec USD growth rate there, well below the model-consistent denominator, made RM/Y fall 35%
below its calibrated share by t≈24, recovering only after t≈100, with nothing in the docs intending
it. The cash-measure trap: a level taken from a central-bank headline that was the cash series, not
the personal one **[PHL]**. (history: PHL)

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

**Test an initial-wealth build on your country before adopting it.** Two designs have been tried.
Rescaling the initial distribution inside the transition loop can oscillate: on an old population
it ran ten damped iterations without decaying, where the same calibration without it converged.
A static anchor set before the solve (reforms inherit the baseline's B(0)) converged and landed
close to the target. Neither fixes an early consumption spike caused by unsolved start cohorts
(og-solver-diagnosis, class M), which looks the same; rule that out first. Record which build each
result came from, and adopt an unreleased build only if it measurably fixes your country's
symptom. **[KOR]** (history: KOR)

**Diagnose first.** Before setting anything, see what initial condition your ogcore imposes by
default and what it does to the first years. Older ogcore rescaled the steady-state profile so
aggregate B(0) = B_ss, which hands every initial household a uniform windfall when the initial
population is younger than the stationary one (confiscation when older); the per-household scale is
`B_ss / get_B(b_sp1, p, "SS", True)`. The default above avoids that windfall but gives an aggregate
B(0) set by demographics, not data. On KOR the two differ by that factor: the old rescale multiplied
wealth by 1.53, and the rescaled level happened to land near the data target. That is luck, not
method; take the level from data (history: KOR). Either way the fingerprint of a wrong initial condition is a
violent year-1-or-2 consumption spike concentrated in ages 60+ across all j, an investment
collapse, a `tau_c` revenue pulse and a spurious debt paydown (or the mirror images). It is
invisible in reform-minus-baseline tables, because both paths share the initial condition.

**The level: what number to target.** The parameter asks for aggregate household wealth / GDP in
the start year. Two ways to measure it, and they differ:
- *Capital side (model-consistent):* the model forces B(0) = K_d(0) + D_d(0), so
  `(K/Y_PWT − public capital/Y) × (1 − IIP foreign-owned share) + domestic-held share × D/Y`.
  Compute the PWT ratio from the raw current-PPP series pair (capital `CKSPPP…` over output
  `CGDPOS…` on FRED), never from memory; PHL moved 3.33 (2019) → 3.97 (2023).
- *Household balance sheets* (UBS Global Wealth Databook class, or the national accounts' household
  sector). Usually lower for emerging markets, because they undercount real property.
  (history: PHL, ZAF, ETH)

Prefer the capital-side number, cross-check against the balance-sheet one, and write down which you
used and why. Expect initial < steady-state wealth ratio for a fast-growing economy.

**The shape.** Ones is a defensible start. If survey data gives wealth by age (and income group),
set the factors to data relative to the model's steady-state profile, so the young and old start
where they actually are. Check the result stays inside the valid range; a factor pinned at a bound
means the steady-state profile itself is far from the data, which is a finding.

**Check the solve, not just the target.**
- Confirm the solved `B_1/Y_1` equals the target.
- Rescaling initial wealth between transition iterations is the step that misbehaved before
  (PSLmodels/OG-Core#1189): it drove the initial cohorts into negative-consumption solutions that satisfied the extended
  first-order conditions and passed OG-Core's constraint checker, which watches a different object.
  Always read minimum household consumption from the pickle, and watch that the outer-loop distance
  still falls. If the targeted run misbehaves, a fixed level reached by tuning the factor matrix over
  a few runs (target off) is the static alternative.
- **Report the initial foreign capital share** `K_f(0)/K(0)` against the IIP; it is untargeted.
  Where the model's `K/Y` overshoots the PWT, measured household wealth and the measured foreign
  share cannot both be hit: the model fills its larger capital stock with foreign inflows. Keep the
  wealth anchor and document the foreign-share miss with its cause (on PHL, hitting the IIP share
  would have needed household wealth about 28% above the measured level; history: PHL).
- Then re-tune the `alpha_G` glide; it was fit against the old initial condition's revenue path.

**Pitfall.** PHL's old default scale was 1.625 (a 63% windfall): retirees consumed at 3–7× steady
state for years, C jumped 41% for one year, domestic investment fell to ~2% of long run, and debt was
paid down 10pp of GDP below its target. It surfaced only in level exercises. (history: PHL)

**Exemplar.** PHL (diagnosis, fix, and the in-loop rescaling failure; PSLmodels/OG-Core#1189).

## delta_annual

**Method.** Source it; no repo does. `delta = (CFC/Y)/(K/Y)`: consumption of fixed capital from
the national accounts (or World Bank `NY.ADJ.DKAP.GN.ZS`, converting the GNI basis to GDP), `K/Y`
from PWT. Decisive in a slow- or negative-growth economy: steady-state investment is
`(g + delta)·K/Y`, so as `g → 0` depreciation is nearly the only thing generating investment demand.

**Both sides of the ratio are private.** OG-Core's `K` is private capital; public capital `K_g` is a
separate stock with its own `delta_g`. PWT's capital stock and total CFC include the government's, so
use `private K/Y = PWT K/Y − public K/Y` (the same subtraction the initial-wealth construction makes)
both as the `K/Y` dashboard target and as the denominator here, and take government CFC out of the
numerator. Set `delta_g` from government CFC over the public stock. Scoring the model's private
`K/Y` against total PWT `K/Y` sends `beta` after a gap that is not there, and moves `r` across the
world rate (on KOR, the private split raised `delta` by 0.4pp, and scoring against total `K/Y` put
the implied `r` about 0.9pp below the world rate). **[KOR]** (history: KOR)

**Pitfall.** Leaving OG-Core's 0.05, a US value **[JPN]**.

**Exemplar.** **[net-new: JPN]**; private/public split **[KOR]**.

## beta_annual

**Method.** Not observable; calibrate it to the capital-output ratio through the firm FOC (method.md,
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
consumption directly. On JPN the shipped `alpha_T` was three times the true cash share, the largest
single error in its consumption fit (history: JPN). Worst wherever health care is publicly
provided in kind, which is most of the OECD.

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
  - *A sourcing choice, not a tuning lever.* Make the adjustment once, from the evidence, before
    tuning. Moving `gamma` to close a `K/Y` gap chases the family's `K/Y` overshoot
    (validation-dashboard.md, "Know the family traits") and can push `r` below the world rate.
    **[THA]** (history: THA)
  - *Cross-sectional rescale* **[multi-industry; PHL]**: keep the SAM's per-industry dispersion but
    rescale so the value-added-weighted mean equals the economy-wide capital share. Where the table
    has a mixed-income row, split it per industry first **[BRA]** (og-multi-industry-calibration).
- **Pitfall [ETH, verified].** The `update_from_api=True` path recomputes the naive `1 − ILOSTAT`
  and silently clobbers a hand-triangulated `gamma` (on ETH, with a value about 0.2 higher; case
  notes: ETH), undoing the
  whole argument in the docs. Because some examples call that path whenever online (SKILL.md, mental
  model 1), this sits in the default run. Remove curated structural parameters from the live path
  entirely, as IDN did; an `if update_from_api` guard is not enough.

## K_f gross vs net

Settle this before tuning `zeta_K`; for a net-creditor country the two readings differ in sign.

The identity is `K = K_d + K_f` with `K_d = B − D_d`, so `K_f` reads as the **gross** foreign-owned
share of the domestic capital stock: households hold domestic capital and domestic government debt,
and nothing else. On that reading the IIP target is inward direct-investment equity (including
reinvested earnings) + inward portfolio equity, ÷ GDP ÷ `K/Y`, where `K/Y` is the model's *private*
capital ratio (PWT less public capital; see `delta_annual`), or the share is understated (on KOR,
total PWT capital understated it by 1.3pp). On JPN, a placeholder `zeta_K = 0.10` produced about a
tenth of the gross target. (history: KOR, JPN)

But `K_f = zeta_K·(K_demand_open − B + D_d)` is not clamped, and the outflow term
`(r + delta)·K_f − new_borrowing_f + debt_service_f` reverses cleanly, so a negative `K_f` is
arithmetically fine and reads as a **net** creditor position. For a large net creditor, the net
reading gives a target of the opposite sign (history: JPN).

**Which to use.** The identity is the stronger argument: `K_d = B − D_d` leaves households no foreign
asset, so a negative `K_f` is an unclamped edge case rather than a designed representation.
Calibrate to gross. Say plainly what that costs: the model omits the country's foreign portfolio, so
household wealth `B` is understated by it and the primary income it earns is absent from the
resource constraint (on JPN, roughly 3.8% of GDP a year of income). This is
an OG-Core limitation, not a calibration choice: there is one `K_f`, so a two-sided external balance
sheet cannot be expressed. Check the sign of the country's NIIP, state which reading you took, and
note the omission in the audit. **[net-new: JPN]**
