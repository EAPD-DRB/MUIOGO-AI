# Assessment protocol

## What is being evaluated

Country tailoring is established through a chain of evidence:

1. **Representation:** the model contains the important country-specific technologies, resources, infrastructure, policies, institutions, and cross-sector links.
2. **Initialization:** inherited stocks and boundary conditions reproduce the historical starting state.
3. **Accounting:** commodity, land, water, capacity, activity, and emissions balances are coherent.
4. **Historical behavior:** outcomes match observations at the spatial and temporal resolution relevant to the stated use.
5. **Independence:** the match is not merely the direct consequence of fixing those outcomes.
6. **Validation:** parameters chosen during calibration also perform on data not used to tune them.
7. **Robustness:** conclusions survive plausible data uncertainty, alternative assumptions, and reasonable model formulations.
8. **Reproducibility:** another analyst can trace inputs, rebuild the case, rerun it, and obtain the assessed results.

Calibration is therefore not a single base-year error statistic.

## Assessment sequence

### 1. Define the claim

Record:

- country and modeled regions;
- base year, calibration years, and held-out validation years;
- claimed domains: energy, land, water, climate, and cross-nexus links;
- temporal and spatial resolution;
- intended decision and audience;
- version or commit of code, data, and scenarios.

If the model claims only an energy scope, do not penalize it for absent land and water modules. If it claims full CLEWs, all domains and material links are required.

### 2. Establish evidence quality

Create an evidence register. Each important datum needs source, publication or retrieval date, unit, geographic scope, time basis, transformation, uncertainty, and parameter destination. Prefer official national statistics where credible, then authoritative international datasets, peer-reviewed studies, and transparent engineering estimates. Retain conflicting values instead of silently selecting one.

### 3. Run critical gates

The score cannot compensate for a critical failure.

| Gate | Pass condition | Failure consequence |
|---|---|---|
| Executable case | The assessed case solves to an accepted optimum with no unexplained numerical warnings | Unacceptable |
| Referential integrity | Sets, parameters, scenarios, and result identities are consistent | Unacceptable |
| Physical/accounting integrity | Material balances close within declared numerical tolerances; conversions and units are coherent | Unacceptable |
| Scope integrity | Every domain and material cross-link claimed by the model is represented | Unacceptable |
| Historical evidence | Traceable observations exist for the core outcomes used to claim calibration | Not assessable |
| Independence disclosure | Constraints affecting scored outcomes can be classified E/J/H | Not assessable if undisclosed; otherwise forcing caps apply |
| Reproducibility | Assessed inputs, configuration, solver, and outputs can be identified | Maximum Acceptable when materially incomplete |

### 4. Compare history

Compare the model to observations at more than one layer:

- **stocks:** installed capacity, reservoirs, irrigated area, land cover, livestock, infrastructure;
- **annual flows:** generation, fuel supply, crop production, abstractions, emissions, imports and exports;
- **shares:** generation mix, crop mix, water-source mix, sector demand shares;
- **time pattern:** seasonality, load or generation shape, rainfall/runoff timing, irrigation timing where the model is meant to resolve them;
- **nexus transfers:** electricity and fuels used for water and agriculture, water used for power and crops, biomass/land flows into energy, and associated emissions.

Aggregate national agreement cannot excuse a wrong regional, sectoral, or seasonal pattern when that pattern matters to the intended use.

### 5. Classify forcing

Use `E`, `J`, or `H` from `forcing-classification.md`. Classification is attached to the outcome, not just the parameter. One outcome may be endogenous in one scenario and fixed in another.

### 6. Hold out evidence

Whenever the data permit:

- choose parameters using calibration years;
- freeze those parameters;
- evaluate a different historical year or period;
- disclose structural breaks and policies that were unknowable or omitted.

Absence of held-out evidence caps the grade at Good. A held-out failure can make the model Unacceptable even if its calibration-year fit is excellent.

### 7. Test robustness

Vary the uncertain inputs and modeling choices most likely to change the decision:

- demand and resource data;
- costs, efficiencies, yields, and losses;
- climate inputs;
- temporal aggregation;
- bounds, growth rates, reserve margins, and policy constraints;
- discount rate and trade assumptions;
- alternative plausible source datasets.

Assess whether the substantive conclusion changes, not merely whether the objective value changes.

## Interpretation principles

- A diagnostic history-fixed run can be useful for testing accounting, but it is not independent validation.
- A model may be well calibrated in aggregate but poorly tailored for distributional, operational, or subnational questions.
- Several parameter sets can reproduce the same observations. Treat that as equifinality and lower parameter-identification confidence.
- The purpose of an optimization model is normally insight under assumptions, not literal prediction. Calibration supports credibility; it does not validate future forecasts.
- Use expert and stakeholder review as complementary evidence for institutional realism and data interpretation, not as a substitute for quantitative comparison.
