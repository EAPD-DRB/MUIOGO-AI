# Permitted country adaptations

Country adaptations define the modelled system. They must be evidence-based,
documented, and chosen independently of historical model-output error.

## Country identity and horizon

Set:

- country name and ISO3 code;
- scenario name explicitly containing `raw` or `uncalibrated`;
- start/end years and planning horizon;
- time zone;
- source and access date for every structural input.

Do not select a horizon boundary to hide a bad historical transition.

## Energy geography and topology

Define national or subnational nodes according to actual grid topology and the
intended resolution. Document aggregation of separate grids or islands.

Configure:

- cross-border trade applicability;
- internal transmission topology;
- isolated systems;
- storage representation;
- import/export availability;
- physically applicable technology families.

Technology inclusion/exclusion must follow resource, infrastructure, or
institutional evidence—not improvement in historical dispatch. Record uncertain
technologies and test them later as structural sensitivities.

Do not override installed capacity, generation, demand, fuel use, availability,
cost, efficiency, or retirement profiles to match historical records.

## Temporal structure

Define seasons and dayparts from climate and system structure:

- wet/dry or other country-relevant seasons;
- local time shift;
- day/night or finer load/renewable periods;
- day types when supported.

Document what variability the chosen time slices cannot represent. Do not add
time slices or ramping solely to smooth historical discrepancies.

## Geospatial structure

Use authoritative boundaries with explicit version and license. Configure:

- administrative level;
- boundary and island components;
- working and equal-area coordinate systems;
- clustering variables and number of clusters;
- aggregation rules.

Choose cluster count using spatial diagnostics, computational tractability, and
the intended question—not agreement with national historical totals.

National-area normalization is permitted as structural geometry harmonization
when:

- the target is an authoritative definition of the model domain;
- the raw geometric area and scale factor are retained;
- every affected extensive quantity is identified;
- relative cell/cluster proportions are preserved;
- it is not presented as historical calibration.

Prefer a corrected authoritative boundary over scaling when available.

## Climate representation

Select an upstream-supported RCP/climate pathway and document why it is the raw
reference. Do not claim robustness from one pathway. Record other pathways for
later sensitivity analysis.

## Crops, land, and water

Map country crops to available GAEZ categories by taxonomy and agronomic
similarity. Aggregation and proxy mappings are permitted when exact layers do
not exist.

For every proxy, record:

- original crop;
- exact source item/code, selection rank/value/year/unit, and source quality
  flag;
- model crop code and GAEZ layer;
- reason for the mapping;
- climate model, pathway, period, water-supply condition, input level, and
  available-water-capacity assumption used by the layer;
- expected differences in yield, water demand, management, and climate
  sensitivity;
- whether results must be labelled as an aggregate/proxy.

Use exact source-item joins. Prevent proxy crops from also entering an `other`
category, reject duplicate proxy rasters, and ensure that multiple source items
mapped to one proxy do not duplicate its physical potential.

Do not calculate yield multipliers, water factors, land coefficients, or
management shares by solving backward from observed production or harvested
area. Leave raw upstream values unchanged and list the mismatch for calibration.

## Baseline scenario settings

Keep the raw build free of country policy constraints unless the user explicitly
requests a separate policy scenario after raw delivery. Do not embed:

- renewable generation targets;
- emissions limits or carbon prices;
- fossil phase-outs;
- historical activity locks;
- future capacity mandates;
- policy-driven technology build rates.

Structural impossibility is not policy. Clearly distinguish the two.

## Documentation table

For each adaptation, provide:

| Field | Required content |
|---|---|
| Adaptation | Exact configuration or mapping |
| Type | Native configuration / structural data / technical patch |
| Evidence | Source and version |
| Rationale | Why it defines the country system |
| Result influence | Parameters, sets, or equations affected |
| Uncertainty | Known ambiguity |
| Sensitivity candidate | Alternative to test later |
| Historical fit used? | Must be `No` |

Also complete the exact source and government-review fields required by
`source-and-government-review.md`.
