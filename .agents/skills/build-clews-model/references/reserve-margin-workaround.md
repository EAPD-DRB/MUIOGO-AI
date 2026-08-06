# Workaround for unsupported reserve-margin tags

Use this only after proving that the installed MUIO version cannot natively
store and enforce `ReserveMargin`, `ReserveMarginTagFuel`, and
`ReserveMarginTagTechnology`. Prefer native support whenever it is complete.

This is a formulation-port workaround. It is not calibration.

## Why direct substitutions are wrong

Do not translate technology capacity credits into:

- `InputActivityRatio` or `OutputActivityRatio`: these define conversion
  efficiency and alter energy balances;
- `CapacityFactor` or `AvailabilityFactor`: these limit production over time;
- `ReserveMargin.csv` alone: it is one system requirement and cannot encode
  technology-specific dependable-capacity fractions.

A hydro credit of `0.3` means one unit of hydro nameplate capacity contributes
0.3 units to the reserve-capacity test. It does not mean hydro produces only
30% of its input or has a 30% output ratio.

## Mathematical representation

The native OSeMOSYS reserve condition compares credited installed capacity
with the reserve-adjusted demand rate in every timeslice. Its capacity side is
independent of timeslice, so the family of timeslice inequalities can be
collapsed to the maximum annual timeslice requirement:

```text
credited_capacity[y]
  = sum_t(
      CapacityToActivityUnit[t]
      * ReserveMarginTagTechnology[t,y]
      * TotalCapacityAnnual[t,y]
    )

peak_requirement[y]
  = max_l(
      sum_f(
        SpecifiedAnnualDemand[f,y]
        * SpecifiedDemandProfile[f,l,y]
        / YearSplit[l,y]
        * ReserveMarginTagFuel[f,y]
      )
      * ReserveMargin[y]
    )

credited_capacity[y] >= peak_requirement[y]
```

MUIO UDCs use a `<=` inequality, so install:

```text
-credited_capacity[y] <= -peak_requirement[y]
```

Use the source reserve-margin value. When the source CSV is empty, use the
default declared by the matching otoole/OSeMOSYS configuration—normally 1.0.
Do not confuse this with the separate 5% `DiscountRate` fallback.

## Fiji-style internal-node workaround

CLEWs Global may tag an internal electricity commodity while placing
`SpecifiedAnnualDemand` on a downstream final-electricity commodity. A literal
reserve equation then has no tagged exogenous demand.

Substitute the downstream demand commodity only when all are proven:

1. the tagged internal commodity and demand commodity belong to the same
   electricity service;
2. the path between them is explicit and unambiguous;
3. every intervening transformation is 1:1 for the relevant mode;
4. no losses, storage, trade, competing consumers, or endogenous activity make
   the downstream demand an invalid proxy; and
5. the substitution would be made without knowing historical outcomes.

Document both commodity names, the intervening technologies, ratios, and the
proof. Label this an **internal-node reserve-demand workaround**, because it
implements the intended reserve test rather than literally preserving a
misplaced tag.

If these conditions fail, do not invent a port. Report that the installed MUIO
feature set cannot represent the reserve condition safely without a general
software extension or a separately authorized modelling decision.

## MUIO representation

Create one inequality UDC unless the model structure requires separate proven
systems. Use a conspicuous name such as:

```text
RESERVE_PROXY_RUN_CHECK_IF_DEMAND_OR_MARGIN_CHANGES
```

Populate:

- `genData.json` → one `osy-constraints` item:
  - stable `ConId`;
  - warning name and description;
  - `Tag = 0` for inequality;
  - `CM` listing every credited technology;
- `RYCn.json` → `UCC` equal to `-peak_requirement[y]`;
- `RYTCn.json` → `CCM` equal to
  `-CapacityToActivityUnit[t] * capacity_credit[t,y]`;
- `RYTCn.json` → `CAM = 0` and `CNCM = 0`.

Preserve unrelated constraints and rows. Use stable identifiers and atomic
writes. Keep a pre-workaround run for comparison.

## Mandatory stale-data guard

The UDC is derived data. MUIO does not know that its constants depend on demand
and temporal parameters. Create a model-local configuration and checker.

The configuration must record:

- constraint ID and warning name;
- tagged source commodity;
- substituted demand commodity, if any;
- reserve margin by scenario or an explicit base fallback;
- technology capacity credits;
- structural proof for any internal-node substitution.

The checker must:

1. read the live MUIO case;
2. resolve base values plus scenario overrides;
3. recalculate `UCC` and `CCM` for every model year and scenario;
4. compare them with stored UDC values within a declared tolerance;
5. validate the constraint metadata and technology membership;
6. compare a deterministic input fingerprint;
7. print `CURRENT` and exit 0 only on zero mismatches;
8. print `STALE`, list differences, and exit 2 when regeneration is required;
9. offer a separate explicit `--update` mode; and
10. never edit the case in default check mode.

Changes to annual demand, demand profile, `YearSplit`,
`CapacityToActivityUnit`, credits, reserve margin, years, timeslices, or
scenarios must invalidate the check.

Store the warning and fingerprint inside the MUIO case so they travel in its
ZIP. Store the executable checker and editable configuration in the country
package. Put the warning in the visible UDC name and description.

## Validation

Before final solve:

- prove an intentional demand change makes the checker return `STALE` and exit
  2;
- restore the case and run `--update`;
- require `CURRENT` with zero mismatches;
- generate the MUIO data file;
- confirm one annual UDC row per model year;
- inspect the generated equation signs and coefficients;
- solve;
- verify credited capacity is at least the requirement within solver
  tolerance;
- compare pre- and post-workaround objectives and outputs without interpreting
  the difference as calibration improvement.

## Required documentation language

State:

> MUIO does not natively support the CLEWs reserve-margin tag parameters in
> this installed version. The case therefore uses an annual user-defined
> constraint as a documented workaround. It preserves technology-specific
> capacity credits and the peak-demand requirement under the stated structural
> assumptions. The derived constants must be regenerated after relevant demand
> or scenario changes. This workaround is not historical calibration.
