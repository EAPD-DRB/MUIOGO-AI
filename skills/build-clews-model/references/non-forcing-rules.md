# No-historical-forcing rules

The build stage creates a raw model. Calibration is a later, separate stage.

## Bright-line rule

Do not use a historical outcome to choose a model input, coefficient, bound, or
constraint during the build.

Ask:

> If the historical result were hidden, would the same value and modification
> still be selected?

If not, defer it.

## Allowed now versus deferred

| Allowed during build | Defer to calibration |
|---|---|
| Country and ISO codes | Capacity scaled to an observed fleet total |
| Authoritative boundaries | Demand scaled to observed consumption |
| Time zone and evidence-based seasons | Availability adjusted to reproduce output |
| Grid/island topology | Capacity factors tuned to generation |
| Structural technology applicability | Efficiencies or costs tuned to dispatch |
| GAEZ crop taxonomy proxy | Yield factor fitted to harvested area |
| Administrative resolution and clustering | Water coefficient fitted to withdrawal |
| Climate-pathway selection | Fuel limit fitted to historical use |
| Diagnostic historical comparison | Any equal lower/upper historical activity lock |
| Source and data-gap inventory | Any historical capacity min/max lock |

## Forbidden patterns

Reject:

- `historical_generation_shares` or equivalent country-output overrides;
- `power_capacity_calibration`, `historical_availability_factors`, or fitted
  `crop_yield_factors`;
- identical positive lower and upper activity bounds for an observed
  technology-year;
- identical positive minimum and maximum capacity constraints introduced for a
  historical year;
- a one-year parameter adjustment that disappears in the next year;
- inverse calculations such as observed production divided by modelled yield
  when the result is then inserted as a yield multiplier;
- iterative parameter selection based on reducing RMSE or visual mismatch;
- copying fitted parameters from another country model without returning to the
  raw upstream source;
- calling forced equality a validation check.

## Observations may be collected

Create a gap table with:

- source, URL, access date, license;
- geography, period, unit, and definition;
- observed value and uncertainty;
- raw model value;
- absolute and percentage difference;
- suspected structural/data causes;
- candidate future parameter or constraint;
- explicit field `applied_in_raw_model: false`.

Do not feed the table back into the build.

## Historical capacity nuance

Installed capacity is an observed stock and may later be a legitimate model
input. It is still a calibration-stage change when it replaces upstream data to
improve country historical agreement. During this raw build, preserve the
upstream OSeMOSYS Global values and record the discrepancy.

The later calibration stage may decide to replace capacity data, construct
plant-level retirement schedules, or fix genuinely historical years. That
decision must be explicit and versioned outside this skill.

## Validation language

Permitted:

> The model solves and passes technical integrity checks. Raw outputs differ
> from observations as documented.

Forbidden:

> The model is calibrated because a constrained historical value matches its
> source.

Do not score forced values as model performance.
