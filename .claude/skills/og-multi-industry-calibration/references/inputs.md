# Building the inputs from data

Which repo to read for which piece is in SKILL.md. alignment.md covers keeping the two models in
agreement, solving, and checking the result.

Contents
- Packaging
- Finding the data
- Concordances
- Defining industries and goods
- alpha_c
- gamma_m
- io_matrix
- L_m
- Z_m
- Tax rates by industry and good
- Public capital
- What the data do not identify

## Packaging

A lean overlay: a JSON holding only what the multi model changes, loaded after the single-industry
base (`Specifications.update_specifications(base)` then `(overlay)`). The maintainers asked for it,
and PHL, ZAF and BRA all ship it. A base recalibration then flows through with no regeneration, and
economy-wide values live in one place.

- **The builder** (`og<xxx>/create_multisector_calibration.py`, with `build_multisector_params()`
  and `main()`, run as `uv run python -m og<xxx>.create_multisector_calibration`) writes the overlay.
  It reads the base JSON for anything it converts (chi, sigma). Never hand-edit the overlay.
- **Where the code lives:** derivation functions in `input_output.py`; concordances and shared
  constants (`TOTAL_CAPITAL_SHARE`, `PUBLIC_CAPITAL_SHARE`, capital-output ratio) in `constants.py`,
  so the builder and the live `Calibration` class cannot drift. Keep the legacy naive
  `get_io_matrix` only if the live `Calibration(update_from_api=True)` path still calls it, and know
  that path is partial: PHL's rebuilds only `io_matrix` and `gamma`, ZAF's still calls the naive
  matrix. The overlay is the complete object.
- **What goes in:** the structure (`M`, `I`, `alpha_c`, `io_matrix`, `c_min`, `gamma`, `epsilon`,
  `gamma_g`, `Z`); `chi_b` and `chi_n` (converted, alignment.md); solver settings the multi model needs
  (`nu`, `TPI_outer_method`); per-industry `cit_rate` and per-good `tau_c` only when they differ
  from the base; public-capital settings only when the multi changes them. Solver seeds stay in the
  base.
- **Loaded alone, an overlay falls back to OG-Core's US defaults** for everything it omits, with no
  error. Every example, tutorial and docs script must do the two-step load. Tests that loop over
  every packaged JSON expecting a full parameter set (demographics, `J`) will fail on an overlay;
  scope them to the base file.
- **One example script** (`examples/run_og_<xxx>_multi_industry*.py`): build the specifications,
  solve, validate, baseline transition, one reform, the macro table and plots. A `--ss-only` flag
  that runs the solve and the structural checks is worth having (PHL, BRA).

## Finding the data

Search; do not assume a SAM exists or does not.

1. **Statistics office or central bank.** Supply-and-use or IO tables are enough; the make/use
   algebra runs on them directly. Some series publish the pieces you need ready made (BRA's
   Alves-Passoni–Freitas annual series built from IBGE tables ships the market-share matrix, a
   domestic use table and a domestic Leontief inverse).
2. **Research institutes.** IFPRI Nexus SAMs (standardised, about 40 activities, labour by education,
   land and capital rows, 10 household groups; PHL, IDN, ETH) and UNU-WIDER's country SAMs (ZAF,
   with a technical note).
3. **Global databases, last and marked lower-confidence:** GTAP (licensed), EORA, OECD ICIO. Their
   balancing goes beyond the national accounts and most lack the household and factor detail.

What qualifies: factor rows (labour; capital or operating surplus; ideally mixed income
separately), household expenditure columns, activity and commodity accounts, a rest-of-world
account, product-tax rows. Note:
- **diagonal or rectangular make** (one activity per commodity, or several); it decides the
  `io_matrix` algebra. Check it: PHL's off-diagonal share is exactly 0; ZAF's median commodity has
  more than one producer;
- **domestic vs total use**: a domestic use table lets you skip import assumptions;
- **a "total" row or column**: exclude it explicitly, or every sum doubles;
- **the year**: match it to the employment data and the national accounts.

Delivery: never read the publisher's URL at run time. Ship a compact extract in the package's
`data/` and register it in package data (PHL ships the SAM CSV; BRA ships five CSV extracts, keeps
the raw workbook out of git, and has a `fetch_data.sh` plus an extractor that asserts the workbook
layout), or mirror it in `EAPD-DRB/SAM-files` (ZAF, which then needs a network connection to
rebuild). Record publisher, technical note and year in the reader's docstring and the docs.

Employment comes from outside the factor accounts: a labour force survey by industry, same year
(PHL ships PSA LFS by PSIC section as a CSV; ZAF uses QLFS 2019; BRA uses the IO table's occupations
row). Say what it counts: persons or jobs.

**Check the data reproduces the national accounts before trusting it.** Its value-added shares by
broad sector should track the statistics office's GDP by industry (ZAF's 2019 SAM matched Stats SA to
about 0.5pp on primary, secondary and tertiary); employment shares should match the labour force
survey; `alpha_c` should match household consumption's goods/services split. A table that does not
reproduce the sector structure is the wrong vintage or mis-aggregated; fix that before reading
anything off the multi-industry steady state.

## Concordances

The mapping from activities to industries (`PROD_DICT` or `ACTIVITY_TO_SECTOR`) and from
commodities to goods (`CONS_DICT`) must partition the data exactly: every code in exactly one group,
nothing in the dicts that is not in the data.

Unchecked mappings ship silently wrong, because `isin` and `groupby` skip what they cannot match:
ZAF had two misspelled commodity codes that dropped out of every sum; PHL's food group lists a code
the SAM does not have. A test catches the class (BRA's: lengths equal the activity and product
counts, value sets equal the group keys, no product in the data has an unmapped code). Add a
run-time assert as well, since a new data vintage can introduce codes the test fixture does not.

Mapping products to activities by code prefix (BRA: 5-digit product → 4-digit activity) is fine when
the classification is nested; check it covers every product.

## Defining industries and goods

- **The capital-goods producer goes last.** OG-Core makes the last industry the numeraire and the
  only producer of investment and government goods (alignment.md). Manufacturing, in all three repos.
  Code that normalises by position (`Z / Z[-1]`) changes the numeraire silently if someone reorders
  the dict; say so in a comment or assert the name.
- **Fold real estate into a broader services or finance group.** Imputed owner-occupier rent is
  booked as operating surplus, not corporate profit. A standalone real-estate industry gets a
  capital share near 1 (degenerate) and a diluted effective CIT. All three repos fold it in (an
  earlier BRA draft kept it separate at M=10 and was merged down to M=9). The same goes for any
  activity whose surplus is mostly imputed or resource rent.
- **Split out what the policy questions need.** Energy work needs electricity apart from water
  (PHL: Electricity and Water; ZAF: Electricity and Water & Waste; BRA: electricity_gas, which also
  carries piped gas, and water_waste). Watch what else rides along in a split.
- **Goods** (`CONS_DICT`): household-relevant groups, typically food, energy, non-durables, durables,
  services (PHL and ZAF I=5; BRA I=7 with electricity, water and fuels separate).
- OG-Core has two private factors, so land and resource rent fold into capital. That is one reason
  raw SAM capital shares come out high.

## alpha_c

Household spending by good at purchaser prices, summed over the household columns and normalised to
sum to 1. All three repos do this. Not total commodity supply (`total − row`), which is what the
upstream scaffold used. With an IO table instead of a SAM, use household consumption at consumer
prices (BRA). Check the services share against HFCE.

## gamma_m

**Raw share** per industry from the factor rows over the industry's activities: capital (plus land)
over value added at factor cost (no taxes).

**Mixed income.** Self-employed mixed income is labour and capital together; booking it all as
capital overstates capital shares most where self-employment is large (agriculture, trade, informal
services). Where the data has a mixed-income row, split it per industry with the economy's own
capital share of the unambiguous income:

```
phi    = OS_total / (comp_total + OS_total)
cap_m  = OS_m + phi · mixed_m
lab_m  = comp_m + (1 − phi) · mixed_m
gamma_m = cap_m / (cap_m + lab_m)
```

(BRA, phi = 0.428.) IFPRI and UNU-WIDER SAMs have no separate mixed-income row, so the split has
already happened inside their labour and capital rows, or not at all; say which.

**Rescale to a level.** Multiply every share by `target / (VA-weighted mean of the raw shares)`, so
the value-added-weighted mean equals the target and the cross-industry pattern survives. The target
must be the single model's total capital share (its `gamma + gamma_g`), so both models describe the
same economy. PHL lands exactly (target 0.58785, private mean 0.53785 = the base `gamma`). BRA's
target is the table's own share (0.428) while its single model uses an ILO-based 0.407, a gap that
has to be closed one way or the other.

**Carve out public capital after the rescale:** `gamma_m = total_m − gamma_g` (PHL changed to this
order after maintainer review).

Healthy capital-intensive industries (mining, utilities around 0.78 in PHL) solve fine; it is the
imputed-rent-driven 0.9+ shares that break things.

## io_matrix

`io_matrix` (I × M, rows sum to 1) says which industries' value added a unit of each consumption
good contains. Build it by tracing household final demand for each good back through the domestic
supply chain:

```
VA by activity, for good c  =  v ∘ ( L · (D · f_c) )
  f_c   household demand for good c's commodities, net of imports
  D     market-share matrix: which activities make each commodity (V / g)
  L     domestic Leontief inverse (industry by industry)
  v     value added per unit of output
then sum activities into industries and normalise each row to 1
```

How to get each piece depends on the data:

| Data | `L` | Imports | Repo |
|---|---|---|---|
| Diagonal make | `(I − A_d)^-1`, `A_d = σ · use / output`; D is the identity | `σ = output / (output + imports)` scales domestic use and weights demand | PHL |
| Rectangular make | `(I − D·B)^-1`, `D = V / g`, `B = U / q`, `v = VA / q` | `dom_share = g / (g + imports)` scales household demand | ZAF |
| Published domestic tables | read it | already domestic; no proportionality assumption | BRA |

The diagonal shortcut is wrong on a rectangular make. Published domestic tables are best: the
proportional-import assumption (every user of a commodity imports the same share) is the weakest
link in the other two.

**Why it matters.** The naive direct-use matrix (commodity rows × activity columns, normalised) is
not an accounting identity, and it puts most goods on manufacturing. Traced, household energy goes
mostly to electricity (74% in PHL, 45% in ZAF, against a manufacturing-heavy naive split); BRA's
food row goes 28% to manufacturing traced against 73% direct.

**Checks when you build L yourself:** the SAM balances (gross output = intermediate + value added
+ production taxes, to machine precision); the spectral radius of `D·B` (or `A_d`) is below 1; the
"total" accounts are excluded; rows sum to 1; spot-check the energy row lands on electricity.

What the trace leaves out (PHL lists it): transaction-cost margins, product and production taxes,
and non-household final demand. Only household demand weights the rows, which is what OG-Core's
`io_matrix` represents.

## L_m

Employment by industry, used only to compute Z (the model's own `L_m` is solved). It must come from
outside the SAM's factor accounts, or Z collapses into a function of factor shares.

When the survey is coarser than the industries (QLFS reports electricity, gas and water together),
split the aggregate by the SAM's labour-compensation shares of the pieces, not by output or a guess.
A labour-intensive piece (waste) employs more per unit of output than a capital-intensive one
(power). In ZAF a guessed 77/23 split put Water & Waste Z at 5.3; the compensation split (about
53/47) brought it to 3.5.

## Z_m

Sector TFP as a Solow residual, normalised so the last industry = 1:

```
Z_m = Y_m / ( K_m^gamma_m · L_m^(1 − gamma_m − gamma_g) )
  Y_m  value added
  K_m  national capital stock allocated by capital income
       K_nat = (capital-output ratio) × total value added
```

- The public-capital term `K_g^gamma_g` is the same for every industry and cancels in the
  normalisation; use the private `gamma_m` (after the carve-out).
- **Allocate `K_m` by the same capital income that defines `gamma_m`.** If `gamma` uses the
  mixed-income split, so must the allocation. BRA allocates by operating surplus plus all mixed
  income while its `gamma` takes only phi of it, which is inconsistent.
- **The capital-output ratio** from PWT for the SAM year (PHL 2.91, ZAF 2.9, BRA 4.36). Its level
  matters little: under the normalisation it enters relative Z only through the dispersion of
  `gamma`. Take it from PWT and move on; PHL notes the ranking holds across 2.9–5.3.
- **Reject establishment-survey capital stocks.** They omit informal capital and can invert the
  ranking (PHL tried and dropped one).
- Spot-check the ranking for sense (agriculture lowest in PHL; mining and utilities high in BRA)
  and watch small industries for outliers, which usually mean a bad employment number.

The level is free under the normalisation; whether to rescale it is in alignment.md.

## Tax rates by industry and good

OG-Core accepts `cit_rate` as T × M and `tau_c` as T × I; scalars broadcast. Do not invent
heterogeneity the data cannot support (PHL's guide): use the single model's scalars unless
sector-effective rates are actually published. When they are (BRA):

- `tau_c` per good = taxes on products / (household spending at consumer prices − those taxes),
  from the use table. Energy goods come out high (BRA electricity 0.34, fuels 0.29), services low.
- `cit_rate` per industry = corporate tax collected by sector (BRA: IRPJ + CSLL by CNAE section, a
  three-year mean) / gross operating surplus. Map the tax classification to industries with its own
  concordance.

**Mind how OG-Core turns `cit_rate` into a tax.** The rate firms face is
`cit_rate × c_corp_share_of_assets × adjustment_factor_for_cit_receipts`. Country bases set those two
factors to turn a statutory rate into an effective one. A per-industry rate computed as collections
over operating surplus is already effective, so leaving the base's factors in place discounts it
twice (BRA: average rate about 9%, times 0.7 × 0.3, gives about 2%, against about 7% in the single
model). Either set both factors to 1 in the overlay, or express the industry pattern as multipliers on
the single model's statutory rate.

Then check the aggregates against the single model: the consumption-weighted mean `tau_c` must
reproduce its `tau_c`, and CIT revenue / GDP must match. Folding real estate into a group dilutes
that group's effective CIT (imputed rent sits in the denominator but is not taxed); say so.

## Public capital

With `gamma_g > 0` the model needs a public capital stock and the investment that sustains it:
`initial_Kg_ratio > 0` (OG-Core requires it), `alpha_I` and `delta_g_annual`. PHL inherits them from
its base; BRA sets them in the overlay from IMF PIMA (Kg/Y 0.35); ZAF uses `gamma_g` = 0. Whatever
`gamma_g` is, use the same in both models.

## What the data do not identify

Set these uniform at the single model's value and say so: `epsilon` (Cobb-Douglas, 1.0, unless the
country has estimates), `gamma_g`, `c_min` = 0, and the tax rates above when no sector data exists.
