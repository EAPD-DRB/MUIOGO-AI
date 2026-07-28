# Forcing classification

Classify each scored historical outcome. The question is: **could the model have produced a materially different value, given the constraints in the assessed run?**

## E — Endogenous

The model chooses the outcome through optimization or internally modeled dynamics.

Examples:

- generation by technology when demand is fixed but generation shares and dispatch are free;
- new capacity when no historical capacity floor or exact bound fixes it;
- crop mix chosen within documented land, water, demand, and agronomic constraints;
- water-source mix chosen subject to physical availability and infrastructure;
- emissions calculated from endogenous activity and emission factors.

An outcome is not automatically endogenous merely because its variable is mathematically free. Very tight bounds, binding share constraints, or calibrated penalties may effectively determine it.

## J — Justified constraint

A constraint restricts the outcome because it represents a documented real-world boundary, not because the reviewer wanted the model to match history.

Examples:

- residual installed capacity fixed to an official asset register;
- hydropower generation bounded by observed water availability or plant capability;
- legal land-protection limits;
- physical transmission, reservoir, desalination, or irrigation capacity;
- a policy that was actually in force during the historical period;
- minimum stable generation or reserve requirements supported by system evidence.

Requirements for `J`:

1. cite the source;
2. explain the physical, legal, or institutional mechanism;
3. show that the bound is not an undocumented tuning device;
4. state whether it binds;
5. test a plausible relaxation when it materially affects the conclusion.

`J` evidence can support country realism but offers less independent calibration evidence than `E`.

## H — History-fixed

The model is directly or effectively made to reproduce the historical outcome being tested.

Examples:

- setting generation by technology equal to observed generation;
- equal lower and upper bounds on historical activity, capacity additions, crop area, or water withdrawal;
- forcing observed technology or crop shares;
- technology-specific limits tuned until the target output is matched without independent justification;
- using the assessed observation both to set the constraint and to claim successful reproduction;
- an objective penalty so strong that deviation from history is practically impossible.

`H` points are useful for initialization or diagnostic accounting but receive no historical-reproduction credit.

## Classification procedure

For every comparison:

1. Trace the result variable to all relevant bounds, demands, residual stocks, activity ratios, policies, penalties, and scenario overrides.
2. Determine which of these constraints bind in the assessed solution.
3. Ask whether the observation being scored was used directly or indirectly to set them.
4. Assign the most conservative class supported by evidence.
5. Record the parameter or constraint IDs and the rationale.

If the evidence does not allow classification, use `U` (undisclosed) in working notes. `U` is invalid in the final comparison file and triggers **Not assessable** until resolved.

## Forcing caps

Use importance weights, not the number of rows.

- History-fixed share `>= 50%` of scored outcome weight: Unacceptable as an independent calibration.
- History-fixed share `>= 25%` and `< 50%`: maximum Acceptable.
- History-fixed share `> 0%` and `< 25%`: disclose it; maximum Good unless held-out evidence tests the same behavior endogenously.
- Undisclosed forcing on a core outcome: Not assessable.

Fixed final-service demand alone does not make all results history-fixed. It does mean demand reproduction cannot be claimed; supply mix, capacity, resource use, and cross-sector flows may still be tested for independent reproduction.
