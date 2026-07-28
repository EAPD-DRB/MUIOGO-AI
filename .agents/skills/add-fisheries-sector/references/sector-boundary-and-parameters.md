# Fisheries boundary and parameter semantics

## Contents

1. Completeness principle
2. Boundary design
3. Architecture choices
4. Parameter semantics
5. Existing stock
6. Demand and projections
7. Physical limits and nexus flows
8. No-forcing test

## 1. Completeness principle

Build Fisheries from sector reality and available evidence. Do not decide that
a parameter is unnecessary because an existing model sector omits it.

Classify every potentially material parameter or flow as:

- `direct`: populated from a direct observation;
- `derived`: calculated from observed inputs;
- `proxy`: transferred from a documented external analogue;
- `estimated`: transparent engineering or analyst estimate;
- `data_gap`: applicable but not responsibly quantifiable;
- `not_applicable`: physically irrelevant within the declared boundary.

Explain every `data_gap` and `not_applicable` decision in the completeness
register. Prefer an uncertainty range and sensitivity test to a silent zero.

## 2. Boundary design

Investigate these activities independently:

| Activity | Common inclusions | Common exclusions or overlaps |
|---|---|---|
| Capture fishing | vessel propulsion, onboard electricity, refrigeration, gear operation | general freight, naval activity, household fishing |
| Aquaculture | pumping, aeration, recirculation, hatcheries, pond/cage operations, feed where quantified | crop/livestock feed already retained in Agriculture |
| Landing and cold chain | landing ice, cold storage, freezing, refrigeration | economy-wide commercial refrigeration |
| Processing | canning, drying, smoking, fishmeal, cooking, wastewater, losses | aggregate Industry activity already containing fish processing |
| Production/resource | capture, farmed output, stocks, catch potential, pond/cage area | consumption demand and imports unless explicitly linked |

Use the boundary register to state what enters and leaves Fisheries, which
statistical sector originally reports each flow, and how double counting is
removed.

Do not automatically include feed milling, retail, restaurant preparation,
household cooking, or distribution to final markets. Include them only when the
declared model boundary and evidence support the transfer.

## 3. Architecture choices

### Useful-service architecture

Use useful-service demands when energy consumption is known more reliably than
physical production pathways.

Typical services:

- fleet motive service;
- aquaculture operating service;
- processing/cold-chain service.

Represent alternative technologies as converters from energy carriers to the
same service. Set OAR to 1 unless another output basis is explicitly documented.

### Production-linked architecture

Use physical production when reliable tonnes, intensities, resource limits, and
losses are available.

Possible chain:

```text
capture stock/area + fleet energy -> landed capture
water + area + feed + operating energy -> farmed fish
landed/farmed fish + processing energy -> processed fish + waste/losses
```

Keep mass and energy units distinct. Never use an energy commodity as a proxy
for tonnes of fish without an explicit conversion technology and documented
ratio.

### Combined architecture

Link useful services to production when the service intensity per tonne is
defensible. This permits technology choice while retaining a physical fish
balance. Record the production-intensity calculation and uncertainty.

## 4. Parameter semantics

| Parameter concept | Meaning | Required treatment |
|---|---|---|
| Demand | Exogenous service or production requirement | Separate observed base, normalization, and projection |
| IAR | Units of input per unit technology activity | State efficiency basis and whether activity is useful output or physical production |
| OAR | Units of output per unit activity | Use one declared output basis; document coproducts and losses |
| CAU | Maximum annual activity per capacity unit | Use consistent power/throughput conversion and units |
| Residual capacity | Pre-base-year physical stock still available | Populate for every applicable technology, directly or by estimate |
| Operating life | Economic/technical service life of new capacity | Keep distinct from remaining life of residual cohorts |
| Availability factor | Technical annual availability ceiling | Do not substitute historical utilization |
| Capacity factor | Timeslice or annual operational ceiling where applicable | Base on physical/resource conditions |
| Capital cost | Overnight or installed investment cost per capacity | State currency year, exchange rate, capacity basis, and included components |
| Fixed cost | Annual cost per installed capacity | State whether maintenance, labor, battery replacement, or overhaul is included |
| Variable cost | Cost per activity not already represented upstream | Do not duplicate fuel/electricity prices |
| Emission ratio | Direct emission per activity | State whether factor is per fuel input or useful output and convert consistently |
| Activity/capacity limit | Independent physical/resource maximum | Use only externally evidenced limits, never desired results |

For each time series, record whether values are observed, interpolated,
extrapolated, held constant, or scenario-specific.

## 5. Existing stock

Use this evidence hierarchy:

1. Nameplate equipment capacity with commissioning year.
2. Vessel engine horsepower, plant throughput, pump/aerator rating, cold-store
   capacity, or facility inventory.
3. Equipment counts multiplied by documented representative capacity.
4. Effective stock derived from observed useful service and utilization.

For method 4:

```text
RC_base = useful_service_base / (CAU × historical_utilization)
```

Check:

- `historical_utilization` is between 0 and 1;
- useful service and `CAU × capacity` use compatible annual units;
- efficiency has already been applied exactly once;
- the resulting capacity is physically plausible against fleet/facility counts;
- utilization is not copied into AvailabilityFactor without separate evidence.

Retire residual stock by cohort when age data exist. Otherwise declare an age
distribution. A uniform age distribution gives:

```text
RC(y) = RC_base × max(0, 1 - (y - base_year) / operating_life)
```

This is a stock assumption, not an activity path. Permit the optimizer to idle
the stock.

## 6. Demand and projections

Reconcile carrier inputs before deriving useful demand:

```text
useful_service = sum[carrier](final_energy_carrier / IAR_carrier)
```

Do not allocate an aggregate energy total among subsectors merely to obtain a
preferred technology share. Use reported carrier/subsector data first; otherwise
record the allocation as an assumption with a range.

Separate:

- observation year;
- model base year;
- normalization method;
- projection driver;
- scenario modification.

Examples of projection drivers include capture limits, aquaculture production,
population, dietary demand, exports, processing throughput, equipment
efficiency, and cold-chain expansion. Record both the driver series and the
formula that creates model demand.

## 7. Physical limits and nexus flows

Investigate and include when material:

- sustainable capture or catch potential;
- aquaculture water abstraction and return;
- pond, cage, coastal, or inland area;
- feed, biomass, oxygen, fuel, and electricity;
- processing yield, waste, wastewater, and refrigeration losses;
- direct combustion emissions;
- refrigerant leakage when sufficiently quantified;
- climate or water constraints affecting productivity.

A physical limit is permissible when independently sourced and expressed in the
correct model unit. Do not reverse-engineer it from observed model activity.
When evidence is weak, use a sensitivity range rather than a narrow baseline
constraint.

## 8. No-forcing test

Reject a parameter or constraint when the answer to this question is no:

> Would this exact value or rule still be introduced if the historical
> technology activity and carrier shares were unknown?

Always reject:

- `TAL = TAU` set to historical technology activity;
- fixed carrier shares introduced to match an energy balance;
- minimum activity intended to consume residual stock;
- pre-base garbage years;
- technologies that exist only to reproduce one historical year;
- zero investment followed by an arbitrary opening year;
- UDCs that encode historical capacity or activity;
- low availability chosen from observed utilization when no technical basis
  exists.

Demand, independently measured stock, and independently measured physical
limits are valid inputs. They constrain the service or resource problem, not
the historical choice of technology.
