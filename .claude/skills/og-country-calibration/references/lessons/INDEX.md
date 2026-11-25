<!-- GENERATED FILE - do not edit here.
     Source: docs/og-lessons/INDEX.md
     Regenerate: python scripts/sync_shared.py -->

# Lessons by situation

Find the features your country shares with others, then read those countries' cases. Each line
names a country file and the heading of the entry in it (search the file for the heading). The
cases record what happened and the numbers; the method they back is in the skill.

Contents
- Economy and data
- Public finance
- Households and demographics
- Running, tuning and validating
- Multi-industry

## Economy and data

**Large informal or self-employed sector**
- ETH: Capital share (gamma): triangulate the labour share for an informal economy
- ETH: Informality: the maturity ladder: graded household non-compliance ("Option A")
- IDN: Informality: the maturity ladder: a structural two-sector demo ("Option B")
- BRA: Capital share (gamma): split mixed income per industry first
- BRA: Informality: the maturity ladder: BRA is at "narrative only"
- ETH: Capital share: inefficiency counted once, side implications checked, published sources

**Subsistence consumption, fast growth, thin credit markets**
- ETH: Preferences: a subsistence floor instead of a high sigma
- ETH: Patience: one discount factor to the long-run return when the state finances investment (superseded)
- ETH: Patience: as much saving as the return evidence allows, judged on the first years
- ETH: A cross-country table value was a formula applied out of sample
- ETH: The poorest group's bequest weight broke a reform

**Investment financed by the state or state enterprises**
- ETH: An investment gap: decompose it with the financing identity before choosing a lever
- ETH: State enterprises' foreign loans sit in household wealth unless counted
- ETH: Patience: one discount factor to the long-run return when the state finances investment (superseded)

**National accounts rebased, or ratios on a mixed GDP basis**
- PHL: GDP price basis: ratios to market-price GDP
- ETH: Capital stock on one GDP basis after a rebasing
- ETH: Capital stock at current national prices; public capital in nominal terms
- ZAF: Capital stock: a PPP stock with national-price depreciation

**Data newer than the model's start year, or fiscal years that differ from calendar years**
- PHL: start_year: a start one year past the latest data
- PHL: r_gov base wedge: news stories mislabel fiscal years
- KOR: The data window: the last usable year is one before the last data year

**A high-denomination currency**
- KOR: Pensions: a high-denomination currency needs income in millions

**Starting from a sibling repo**
- KOR: De-siblinging a bootstrap copy: grep for the sibling and audit every inherited value
- KOR: De-siblinging a bootstrap copy: replace the sibling's example reform
- THA: (entries under og-country-calibration/references/bootstrap.md)
- JPN: The mental model: anything you do not set stays American

## Public finance

**Distressed or sub-investment-grade sovereign; negative real interest rates; financial repression**
- ZAF: world_int_rate_annual: say which rule you applied to a sub-investment-grade sovereign
- JPN: r_gov floor: a negative real sovereign rate was clipped to zero
- PHL: r_gov base wedge: the LMWW intercept over-predicts what the treasury pays (also ZAF)
- ZAF: r_gov base wedge: effective r_gov levels (also PHL)
- ZAF: g_y_annual: g_y consistent with the debt anchor
- ZAF: A hot interest-growth differential forces spending too low

**Large concessional or official external debt**
- ETH: External debt at its own interest rate

**Government holds large financial assets; net creditor country**
- KOR: Debt: a government that owns large financial assets
- KOR: Two traps when adding rows: a trade surplus with a positive NIIP
- JPN: K_f gross vs net: calibrate to the gross IIP share and state the omitted portfolio
- JPN: The mental model: `K_f/K` is first-tier, and gross vs net decides its sign

**A fiscal program or consolidation path to compare against**
- PHL: Transition-path validation against the fiscal program: compare the baseline paths
- PHL: The alpha_G glide: a flat alpha_G pays debt far below target
- KOR: The alpha_G glide: a path from the transition, with pb from the debt path
- ZAF: Fiscal consistency: the budget must balance at the debt target (proven by TPI simulations)
- JPN: Validation priority: the near-term fiscal path caught a wrong `initial_debt_ratio`
- PHL: The budget identity: alpha_I belongs in it
- ZAF: The budget identity: frame the residual honestly
- JPN: The budget identity: pension outlays are a primary outlay

**Taxes: progressive income tax, payroll, non-tax revenue, bequests**
- PHL: Payroll is additive on top of the ETR function
- PHL: Progressive-fit recipe: φ2 carries the effective-rate wedge (also ZAF)
- ZAF: Progressive-fit recipe (GS): tune φ2 to collections (also PHL)
- PHL: Capturing non-tax and residual-tax revenue: leaving it out forces spending too low
- PHL: Capturing non-tax and residual-tax revenue: property-type taxes on the wealth tax
- PHL: Statutory-for-effective errors bias reforms: a CIT cut's effect doubled
- PHL: Standing check: the bequest tax at a statutory rate collected 17x actual estate revenue
- BRA, ETH, IDN: Standing check: the bequest tax
- PHL: Sourcing hierarchy: the OECD Revenue Statistics country note
- JPN: Audit each instrument's base, not just its yield

**Remittances or aid that matter**
- PHL: Remittances: a nominal growth rate in the g_RM slot
- PHL: Remittances: the cash-measure trap

## Households and demographics

**Old or fast-ageing population**
- JPN: The data window sets the long-run growth rate
- JPN: Discontinuities: the frozen window and `fixper`
- JPN: Income-differentiated demographics: high-income countries are out of scope
- KOR: Discontinuities: both breaks are OG-Core bookkeeping, not economics
- KOR: Initial household wealth: test an initial-wealth build on your country before adopting it
- KOR: Pensions: a young pension system needs two checks
- ETH: Transfer shares fixed over time overpaid the oldest

**Family support between generations; consumption by age**
- ETH: Consumption by age: the consumption adults carry, and the model's age convention

**Young, fast-growing population; initial wealth far from the steady state**
- PHL: Initial wealth: the released parameters, a data shape, and beta tuned to the first year
- PHL: Initial household wealth: the old default scale was a windfall
- ETH: Initial wealth distribution by a damped burn-in
- KOR: Initial household wealth: the default level matched the data by luck
- ETH: Starting wealth smooth across an age cutoff

**No wealth survey, or thin household balance sheets**
- PHL: Initial household wealth: balance-sheet ratios run low (also ZAF, ETH)
- ETH: Initial household wealth: the balance-sheet ratio and the capital-side number
- KOR: Moments most often tuned for but never scored: wealth by age
- ETH: Initial wealth distribution by a damped burn-in

**Earnings data: national transfer accounts, income shares**
- ETH: Earnings (the e ability matrix): ETH used the Gini tilt, then replaced it
- JPN: Earnings: the NTA age-shape half of the method
- KOR: Earnings (the e ability matrix): the NTA age-shape port
- PHL: Earnings: the single-scalar Gini tilt

**Hours and labour supply**
- PHL: Labour supply calibrated to hours per person by age
- JPN: Labour supply (chi_n): check total labour input against the US before borrowing
- ETH: Labour units: scale the earnings matrix, not productivity
- ETH: Hours by age: an extrapolated target double-counted the fall in pay
- ETH: A sourced value is not a tuning lever

**Pensions**
- JPN: Pensions: validate against pension spending as a share of GDP
- ETH: Pensions: the factor seed sits exactly at the validator cap
- IDN: Pensions: the factor seed is pinned at the validator cap

## Running, tuning and validating

**Runs outside the user's path**
- ETH: Leads come from installer copies too: hand-built probe paths produced invalid tuning rounds
- ETH: Running against an unreleased ogcore: ETH's main pins ogcore by commit
- KOR: Running against an unreleased ogcore: pin by commit, and check the build carries the PR

**Slow, stalled or failing solves**
- KOR: C. Oscillation: Anderson stalls just above mindist_TPI
- KOR: H. Cold-start seed failure: an inconsistent seed set, not a far one
- KOR: M. Unsolved start cohorts (households alive in the first year)
- PHL: N. Slow transition from a straggler worker
- PHL: Initial-guess fragility: nearness is not solvability
- JPN: Triage an RC_error by where in time it happens
- JPN: Warm-starting the steady state
- KOR: The in-model tuning loop: warm-start every solve

**Tuning order and completeness**
- JPN: Tuning-loop order: sourced parameters first
- JPN: Finding every lever on a moment: the `K/Y` miss, the `beta` that failed, and the world rate
- JPN: Completeness: a dial moved to close a residual is a free parameter
- JPN: Dashboard completeness: every tuned dial needs its own scored moment
- PHL: The in-model tuning loop: real solves are cheap
- ETH: zeta_K raises investment only through foreign ownership
- ETH: Compare return evidence with the return on capital to owners, not the portfolio return
- ETH: Exploring: one probe per idea, watch the run, one finished calibration
- ZAF: The calibration's working files: plan, targets, tuning script, scorecard

**Validation and tests**
- ETH: The steady-state dashboard: a data-comparison table in macro.md
- ETH: Fast value-pinning test: test_default_parameters.py
- ETH: Prevent doc/JSON drift with glue: the taxes chapter
- JPN: Completeness: score the first years, not only the steady state
- JPN: Two traps when adding rows: NX is the trade balance, not the current account
- JPN: Consumption is a residual: decompose its gap, and compare like with like
- PHL: Verify both tails of every path: the min-only debt check
- KOR: Two traps when adding rows: use the model's own K concept
- ETH: Consumption with a subsistence floor: score `C_i`, not `C`
- ETH: Docs numbers typed by hand went through six audits
- ETH: The calibration PR as a fit report
- ZAF: The calibration's working files: plan, targets, tuning script, scorecard

## Multi-industry

BRA, PHL and ZAF built multi-industry overlays from social accounting matrices; their entries are
filed under og-multi-industry-calibration (finding the data, concordances, defining industries and
goods, `gamma_m`, `io_matrix`, `Z_m`, reaching the steady state).
