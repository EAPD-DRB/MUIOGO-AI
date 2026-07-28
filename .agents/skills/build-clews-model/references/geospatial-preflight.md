# GeoCLEWs preflight and archipelago-safe processing

Run these checks before the expensive GeoCLEWs workflow and retain a
machine-readable report.

## Cache inventory

Inventory every expected raster by:

- source product and version;
- variable;
- crop or land category;
- climate model, pathway, and period;
- irrigation/rain-fed condition;
- input level;
- size and readability.

Reject zero-byte, unreadable, duplicate, unexpected-country, unexpected-crop,
or wrong-scenario files. A filename match alone is insufficient when embedded
metadata or a catalogue record is available. Never silently reuse an
unclassified cache entry.

## Boundary and coverage checks

Before attribute extraction:

1. validate geometry and coordinate reference systems;
2. enumerate multipart, island, coastal, and antimeridian components;
3. choose a suitable projected/equal-area CRS;
4. report raw boundary area and retained land-cell area;
5. measure non-null raster coverage by variable, component, and area;
6. detect constant-value columns before normalization; and
7. declare warning and failure thresholds for missing cells and missing area.

Do not drop a disconnected component merely because its raster coverage is
incomplete.

## Missing-value handling

Use NaN-aware minima, maxima, means, and normalization. Handle a
constant-valued column explicitly rather than dividing by zero.

When necessary, nearest-valid-land-cell imputation is a permitted technical
correction only when:

- the target is a retained land cell inside the model boundary;
- the source is a valid land cell in a suitable projected CRS;
- only missing attributes are filled;
- measured values are never overwritten;
- the source distance, variable, cell count, and affected area are recorded;
- the declared missing-area threshold is not exceeded; and
- a regression fixture proves deterministic behavior.

Do not use imputation to make national yields, land shares, or water totals
match observations.

## Clustering and diagnostics

Separate visualization cost from model computation. A dendrogram or diagnostic
plot may use a deterministic documented sample when the full plot is
impractical. Production clustering must still use every retained land cell.

Record:

- diagnostic sample size and seed/method;
- production cell count;
- clustering variables and normalization;
- cluster count and selection rationale;
- cluster areas and total retained area;
- imputed cell and area shares by cluster.

## Pass conditions

Pass only when:

- required raster combinations are complete;
- cache entries match the configured country and scenario;
- every retained boundary component is represented;
- missing-value handling is explicit and within threshold;
- production clustering uses the full retained dataset; and
- cluster areas reconcile to the retained model domain within tolerance.
