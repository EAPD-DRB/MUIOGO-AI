#!/usr/bin/env python3
# GENERATED FILE - do not edit here.
# Source: skills/clews-model-review/audit.py
# Regenerate: python scripts/sync_shared.py
# This local copy keeps the installed skill self-contained in Claude and Codex.
"""Audit MUIO/OSeMOSYS CLEWs model folders for structure and data consistency.

Companion to SKILL.md (clews-model-review). Runs the objective checks in the
rubric against one or more model folders under WebAPP/DataStorage/. Each MUIO
data file is named after its OSeMOSYS index set (R=Region, Y=Year, T=Technology,
C=Commodity, E=Emission, S=Storage, Ts=TimeSlice, ...) and holds parameters
split by scenario (SC_*).

Usage:
    python audit.py                      # audit every model folder
    python audit.py NamibiaCLEWs [...]   # audit specific model(s) by name
    python audit.py --datastorage <path> [models...]
    python audit.py MODEL --removable TEC_x [COM_y EMI_z ...] [--json out.json]

Exit status is non-zero if any FAIL-level finding is present (gates CI).

``--removable`` is the safe-structural-fix gate: it answers "may this object be
deleted without changing any solved value?" and prints nothing else. Exit 0 only
when every requested ID is defined in genData.json and referenced nowhere else;
1 when at least one is undefined or still referenced; 2 for an unusable request
(unrecognized ID prefix). NB: the gate deliberately looks only outside
genData.json, exactly like the orphan warnings - it proves nothing in the data
constrains the object, not that genData's own editor metadata is tidy.

``inventory()``/``inventory_main()`` expose the same checks as a JSON structural
inventory; assess-clews-calibration/scripts/audit_muiogo_model.py is a shim over
them, so both skills share one implementation of every check.
"""
from __future__ import annotations
import argparse, glob, json, os, re, sys
from collections import Counter, defaultdict

# Default: WebAPP/DataStorage relative to the repo root (…/.claude/skills/clews-model-review/audit.py)
DEFAULT_DS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "WebAPP", "DataStorage"))

# Sector detection by tech/commodity CODE prefix (works even without descriptions).
SECTOR_CODES = {
    "Energy": ["PWR", "ELC", "COA", "DSL", "SOL", "WND", "HYD", "NGS", "HFO", "GSL", "KER", "LPG", "BIO"],
    "Land/Agriculture": ["LND", "CRP", "LVS", "AGR", "FOR", "GRS", "PAS"],
    "Water": ["WAT", "WTR", "GWT", "SUR", "PRC", "DES", "EVT"],
}
# Compared against Desc stripped and lower-cased, so "Default Commodity " counts too.
PLACEHOLDER_DESCS = {"", "default commodity", "default technology"}
# Short keys used by the JSON inventory for the sectors above.
DOMAIN_KEYS = {"Energy": "energy", "Land/Agriculture": "land", "Water": "water"}
# Lower/upper bound parameter pairs. When both pin the same row and year to the
# same number the variable is fixed, so a matching historical outcome is imposed
# rather than reproduced. See assess-clews-calibration/references/forcing-classification.md.
BOUND_PAIRS = (
    ("TMPAL", "TMPAU", "model-period activity"),
    ("TAL", "TAU", "annual activity"),
    ("TAMinC", "TAMaxC", "annual capacity"),
    ("TAMinCI", "TAMaxCI", "annual capacity investment"),
)
# ID prefix -> (label, genData collection, ID field) for objects --removable can clear.
REMOVABLE_KINDS = {
    "TEC_": ("technology", "osy-tech", "TechId"),
    "COM_": ("commodity", "osy-comm", "CommId"),
    "EMI_": ("emission", "osy-emis", "EmisId"),
}
_ORDER = {"FAIL": 0, "WARN": 1, "INFO": 2, "OK": 3}
MODEL_ID_RE = re.compile(
    r"^(?P<kind>TEC|COM|EMI|SC)_[A-Za-z0-9_.:-]+$"
)


def clean_unit(u): return re.sub("<[^>]+>", "", u or "")
def load_json(path):
    with open(path) as fh: return json.load(fh)


def model_ids(value):
    """Yield complete model IDs from JSON keys and values.

    MUIOGO-generated IDs are usually alphanumeric, but derived models may use
    underscores or other safe separators. Parse complete JSON scalars instead
    of searching serialized text so IDs such as ``TEC_envland_v12`` are not
    truncated to ``TEC_envland``.
    """
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str) and MODEL_ID_RE.fullmatch(key):
                yield key
            yield from model_ids(child)
    elif isinstance(value, list):
        for child in value:
            yield from model_ids(child)
    elif isinstance(value, str) and MODEL_ID_RE.fullmatch(value):
        yield value


def is_placeholder_desc(desc):
    """True when a Desc is blank or one of the generator's default strings."""
    return isinstance(desc, str) and desc.strip().lower() in PLACEHOLDER_DESCS


def scan_data_files(model_dir, errors=None):
    """Read every model data file once (all ``*.json`` except genData.json).

    Returns ``(ids_by_file, parameters)`` where ``ids_by_file`` maps a file's
    basename to the complete model IDs it mentions (see ``model_ids`` - never a
    regex over serialized text) and ``parameters`` maps a parameter ID such as
    ``IAR`` or ``TAL`` to ``{scenario: [row, ...]}``. Parameters are discovered
    from the files themselves rather than from an assumed file layout.

    ``errors`` collects ``"file: message"`` for files that fail to parse; when it
    is None a parse failure propagates, because the default audit fails loudly.
    """
    ids_by_file, parameters = {}, {}
    for f in sorted(glob.glob(os.path.join(model_dir, "*.json"))):
        base = os.path.basename(f)
        if base == "genData.json":
            continue
        try:
            payload = load_json(f)
        except (OSError, ValueError) as exc:      # JSONDecodeError is a ValueError
            if errors is None:
                raise
            errors.append(f"{base}: {exc}")
            continue
        ids_by_file[base] = set(model_ids(payload))
        if not isinstance(payload, dict):
            continue
        for param, scenarios in payload.items():
            if not isinstance(scenarios, dict):
                continue
            normalized = {}
            for scenario, rows in scenarios.items():
                if rows is None:
                    normalized[str(scenario)] = []
                elif isinstance(rows, list):
                    normalized[str(scenario)] = [r for r in rows if isinstance(r, dict)]
            parameters[param] = normalized
    return ids_by_file, parameters


def collect_references(ids_by_file):
    """Map every ID used outside genData.json to the files that reference it.

    This is the evidence behind both the orphan warnings and the ``--removable``
    gate: the data files carry the UDC ``*Cn.json`` coefficients, cost rows,
    bounds and emission ratios, so an ID that is absent here appears in no
    constraint and in no objective term.
    """
    refs = defaultdict(list)
    for base, ids in ids_by_file.items():        # already in sorted filename order
        for identifier in sorted(ids):
            refs[identifier].append(base)
    return refs


def exact_bound_matches(parameters, years):
    """Lower/upper bound rows that pin the same row and year to one value."""
    matches, year_set = [], set(years)

    def expanded(rows):
        result = {}
        for row in rows:
            identity = tuple(sorted(
                (str(key), str(value)) for key, value in row.items()
                if key not in year_set and value is not None))
            for year in years:
                value = row.get(year)
                if isinstance(value, (int, float)):
                    result[(identity, year)] = float(value)
        return result

    for lower_id, upper_id, kind in BOUND_PAIRS:
        lower, upper = parameters.get(lower_id, {}), parameters.get(upper_id, {})
        for scenario in sorted(set(lower) & set(upper)):
            low_values, high_values = expanded(lower[scenario]), expanded(upper[scenario])
            for key in sorted(set(low_values) & set(high_values)):
                low, high = low_values[key], high_values[key]
                # Upstream OSeMOSYS activates these constraints asymmetrically: upper
                # limits are guarded `<> -1` (TCC1/NCC1/AAC2/TAC2) and lower limits
                # `> 0` (TCC2/NCC2/AAC3/TAC3). So a matching pair only pins anything
                # when the shared value is positive. A -1/-1 row - the standard "no
                # limit" default - constrains nothing at all, and reporting it as a
                # lock would bury the real findings.
                if low <= 0:
                    continue
                if abs(low - high) <= max(1e-9, 1e-9 * max(abs(low), abs(high))):
                    identity, year = key
                    matches.append({
                        "kind": kind, "lower_parameter": lower_id, "upper_parameter": upper_id,
                        "scenario": scenario, "year": year,
                        "identity": dict(identity), "value": low,
                    })
    return matches


def forced_off_bounds(parameters, years):
    """Upper-bound rows set to an active zero, which switches the object off.

    Zero is not a sentinel: the upper-limit constraints are guarded `<> -1`, so an
    upper bound of 0 is live and pins the variable to zero. That needs no matching
    lower bound to bite, so `exact_bound_matches` cannot see it.
    """
    found, year_set = [], set(years)
    for _lower_id, upper_id, kind in BOUND_PAIRS:
        for scenario, rows in sorted((parameters.get(upper_id) or {}).items()):
            for row in rows:
                identity = {str(k): str(v) for k, v in row.items()
                            if k not in year_set and v is not None}
                for year in years:
                    value = row.get(year)
                    if isinstance(value, (int, float)) and value == 0:
                        found.append({
                            "kind": kind, "upper_parameter": upper_id,
                            "scenario": scenario, "year": year,
                            "identity": identity, "value": 0.0,
                        })
    return found


def year_split_issues(parameters, years):
    """YearSplit sums that differ from 1.0, over every scenario and every year.

    A (scenario, year) with no numeric YS value at all is skipped: that is an
    unpopulated parameter, not a broken normalization.
    """
    issues = []
    for scenario in sorted(parameters.get("YS", {})):
        rows = parameters["YS"][scenario]
        for year in years:
            values = [row[year] for row in rows if isinstance(row.get(year), (int, float))]
            if not values:
                continue
            total = float(sum(values))
            # Match upstream OSeMOSYS, which validates YearSplit itself with
            #   check{y in YEAR}: sum{l in TIMESLICE} YearSplit[l,y] >= 0.9999;
            #   check{y in YEAR}: sum{l in TIMESLICE} YearSplit[l,y] <= 1.0001;
            # (osemosys.txt:200-201). A tighter bound here would fail models the
            # solver itself accepts - timeslice shares derived from real hour counts
            # routinely round at the fifth decimal. Do not tighten this.
            if abs(total - 1.0) > 1e-4:
                issues.append({"scenario": scenario, "year": year, "sum": round(total, 9)})
    return issues


def removability(model_dir, identifiers):
    """Verdict per requested ID: may it be deleted without changing any result?

    Removable means genData.json defines the object and no other file in the
    model folder mentions its ID anywhere - no activity ratio, cost, bound,
    emission ratio, UDC coefficient or constrained group. Nothing referenced it,
    so no constraint and no objective term contained it, and deleting it cannot
    move a solved value.
    """
    gd = load_json(os.path.join(model_dir, "genData.json"))
    refs = collect_references(scan_data_files(model_dir)[0])
    verdicts = []
    for identifier in identifiers:
        prefix = next((p for p in REMOVABLE_KINDS if identifier.startswith(p)), None)
        if prefix is None:
            verdicts.append({
                "id": identifier, "removable": False, "code": "bad_prefix",
                "reason": "unrecognized ID prefix (expected one of TEC_, COM_, EMI_)",
                "referenced_in": [],
            })
            continue
        label, collection, field = REMOVABLE_KINDS[prefix]
        defined = {row.get(field) for row in (gd.get(collection) or []) if isinstance(row, dict)}
        files = refs.get(identifier, [])
        if identifier not in defined:
            code = "undefined"
            reason = f"no {label} with this ID is defined in genData.json"
            if files:
                # Undefined *and* referenced: a dangling reference, which the full
                # audit reports as a FAIL. Say both, or the appended file list below
                # reads as though the ID were defined there.
                reason += (f" - but {len(files)} file(s) still reference it, so the "
                           f"model is inconsistent; fix that before removing anything")
        elif files:
            code, reason = "referenced", f"{label} is referenced in model data ({len(files)} file(s))"
        else:
            code, reason = ("removable",
                            f"{label} is defined in genData.json and referenced in no model data file")
        verdicts.append({
            "id": identifier, "removable": code == "removable", "code": code,
            "reason": reason, "referenced_in": files,
        })
    return verdicts


def print_removability(model_dir, verdicts):
    """Print one verdict line per requested ID and a single RESULT line."""
    tags = {"removable": "REMOVABLE", "referenced": "BLOCKED",
            "undefined": "NOT DEFINED", "bad_prefix": "BAD PREFIX"}
    width = max([len(v["id"]) for v in verdicts] or [1])
    print(f"REMOVABILITY GATE: {os.path.basename(os.path.normpath(model_dir))}")
    for v in verdicts:
        where = f": {', '.join(v['referenced_in'])}" if v["referenced_in"] else ""
        print(f"  {tags[v['code']]:11s}  {v['id']:{width}s}  {v['reason']}{where}")
    blocked = [v for v in verdicts if not v["removable"]]
    if blocked:
        print(f"RESULT: NOT REMOVABLE - {len(blocked)} of {len(verdicts)} requested "
              f"object(s) blocked ({', '.join(v['id'] for v in blocked)})")
    else:
        print(f"RESULT: REMOVABLE - all {len(verdicts)} requested object(s) can be deleted "
              "without changing any solved value")


def removable_exit_code(verdicts):
    """0 when every requested object is removable, 2 for a bad request, else 1."""
    if any(v["code"] == "bad_prefix" for v in verdicts):
        return 2
    return 0 if all(v["removable"] for v in verdicts) else 1


class Report:
    def __init__(self, name):
        self.name, self.findings = name, []
    def add(self, level, msg): self.findings.append((level, msg))
    @property
    def worst(self):
        rank = {"FAIL": 3, "WARN": 2, "INFO": 1, "OK": 0}
        return max((rank[l] for l, _ in self.findings), default=0)


def audit_model(model_dir):
    name = os.path.basename(model_dir.rstrip("/"))
    rep = Report(name)
    gd = load_json(os.path.join(model_dir, "genData.json"))
    L = lambda k: gd.get(k, []) or []

    techs = {t["TechId"]: t for t in L("osy-tech")}
    comms = {c["CommId"]: c for c in L("osy-comm")}
    emis = {e["EmisId"]: e for e in L("osy-emis")}
    scens = {s["ScenarioId"]: s for s in L("osy-scenarios")}
    tgroups, years, ts = L("osy-techGroups"), L("osy-years"), L("osy-ts")

    print("=" * 92)
    print(f"MODEL: {name}")
    print("=" * 92)
    print(f"  case={gd.get('osy-casename')!r}  version={gd.get('osy-version')}  "
          f"desc={gd.get('osy-desc')!r}  date={gd.get('osy-date')!r}")
    print(f"  years={len(years)} ({years[0] if years else '-'}..{years[-1] if years else '-'})  "
          f"tech={len(techs)} comm={len(comms)} emis={len(emis)} "
          f"techGroups={len(tgroups)} scenarios={len(scens)} timeslices={len(ts)}")

    # referential integrity + orphans + scenario-id consistency
    defined_sc = set(scens)
    year_keys = [str(y) for y in years]
    ids_by_file, parameters = scan_data_files(model_dir)
    refs = collect_references(ids_by_file)
    used_tid = {identifier for identifier in refs if identifier.startswith("TEC_")}
    used_cid = {identifier for identifier in refs if identifier.startswith("COM_")}
    used_eid = {identifier for identifier in refs if identifier.startswith("EMI_")}
    bad_sc = {}
    for base, ids in ids_by_file.items():
        extra = {
            identifier for identifier in ids
            if identifier.startswith("SC_")
        } - defined_sc
        if extra:
            bad_sc[base] = sorted(extra)

    unknown = (used_tid - set(techs)) | (used_cid - set(comms)) | (used_eid - set(emis))
    if unknown:
        rep.add("FAIL", f"data references {len(unknown)} id(s) missing from genData: {sorted(unknown)[:8]}")
    if set(techs) - used_tid:
        rep.add("WARN", f"{len(set(techs)-used_tid)} technologies defined but never referenced in data")
    if set(comms) - used_cid:
        rep.add("WARN", f"{len(set(comms)-used_cid)} commodities defined but never referenced in data")
    if bad_sc:
        rep.add("FAIL", f"file(s) reference unknown scenario IDs: {bad_sc}")

    # placeholder / missing descriptions
    t_ph = [t for t in techs.values() if is_placeholder_desc(t.get("Desc", ""))]
    c_ph = [c for c in comms.values() if is_placeholder_desc(c.get("Desc", ""))]
    if techs and len(t_ph) == len(techs):
        rep.add("FAIL", f"ALL {len(techs)} technologies have placeholder/empty descriptions")
    elif t_ph:
        rep.add("WARN", f"{len(t_ph)}/{len(techs)} technologies have placeholder/empty descriptions")
    if comms and len(c_ph) == len(comms):
        rep.add("FAIL", f"ALL {len(comms)} commodities have placeholder/empty descriptions")
    elif c_ph:
        rep.add("WARN", f"{len(c_ph)}/{len(comms)} commodities have placeholder/empty descriptions")

    # dangling technologies (no IAR and no OAR in any scenario)
    rytcm_path = os.path.join(model_dir, "RYTCM.json")
    if os.path.exists(rytcm_path):
        rytcm = load_json(rytcm_path)
        io_techs = {r["TechId"] for param in ("IAR", "OAR")
                    for recs in rytcm.get(param, {}).values() for r in (recs or []) if "TechId" in r}
        dangling = sorted(techs[t]["Tech"] for t in set(techs) - io_techs)
        if dangling:
            lvl = "WARN" if len(dangling) <= max(1, len(techs) // 20) else "FAIL"
            rep.add(lvl, f"{len(dangling)} technologies dangling (no input AND no output): {dangling[:8]}")

    # YearSplit sums to 1.0 across timeslices - every scenario, every year
    ys_issues = year_split_issues(parameters, year_keys)
    for issue in ys_issues[:8]:
        rep.add("WARN", f"YearSplit for {issue['scenario']} {issue['year']} "
                        f"sums to {issue['sum']:.4f} (should be 1.0)")
    if len(ys_issues) > 8:
        rep.add("WARN", f"...and {len(ys_issues) - 8} further scenario-year YearSplit "
                        "sum(s) differ from 1.0")

    # exact lower/upper bound pairs: the variable is pinned, so a historical match
    # is imposed rather than reproduced (assess-clews-calibration calls this history-fixing)
    fixed_bounds = exact_bound_matches(parameters, year_keys)
    if fixed_bounds:
        sample = ", ".join(
            "{}/{} {} {} {}={:g}".format(
                m["lower_parameter"], m["upper_parameter"], m["scenario"], m["year"],
                m["identity"].get("TechId") or m["identity"].get("CommId")
                or m["identity"].get("EmisId") or "?", m["value"])
            for m in fixed_bounds[:4])
        rep.add("WARN", f"{len(fixed_bounds)} exact lower/upper bound pair(s) pin a variable to a "
                        f"single value (possible history-fixing): {sample}")

    # Stranded outputs: a commodity that is produced (OAR) but has NO sink at all -
    # not consumed by any technology's activity (IAR) OR capacity (INCR/ITCR), and no
    # demand. These render as "Missing Target Technology" in MUIO's Dynamic Diagram AND
    # are genuine model dead-ends (e.g. an export "for-export" commodity nothing uses).
    # NB: MUIO's RES diagram only draws IAR/OAR links, so a commodity consumed *only*
    # via capacity (INCR/ITCR) also shows as Missing Target in the diagram but is NOT
    # stranded in the model - we deliberately do not flag those (avoids crying wolf on
    # land/capacity commodities like LNDSOL).
    if os.path.exists(rytcm_path):
        produced, consumed = set(), set()
        for recs in rytcm.get("OAR", {}).values():
            for r in (recs or []):
                produced.add(r.get("CommId"))
        for recs in rytcm.get("IAR", {}).values():
            for r in (recs or []):
                consumed.add(r.get("CommId"))
        rytc_path = os.path.join(model_dir, "RYTC.json")   # INCR/ITCR = capacity inputs
        if os.path.exists(rytc_path):
            rytc = load_json(rytc_path)
            for param in ("INCR", "ITCR"):
                for recs in rytc.get(param, {}).values():
                    for r in (recs or []):
                        consumed.add(r.get("CommId"))
        demanded = set()
        ryc_path = os.path.join(model_dir, "RYC.json")
        if os.path.exists(ryc_path):
            for recs in (rr for p in ("SAD", "AAD")
                         for rr in load_json(ryc_path).get(p, {}).values()):
                for r in (recs or []):
                    if any(isinstance(r.get(y), (int, float)) and r.get(y) for y in years):
                        demanded.add(r.get("CommId"))
        stranded = sorted(comms[c]["Comm"] for c in produced
                          if c in comms and c not in consumed and c not in demanded)
        if stranded:
            rep.add("WARN", f"{len(stranded)} commodit(y/ies) produced but with no sink at all "
                            f"(no IAR/capacity consumer, no demand -> stranded & RES 'Missing Target'): {stranded[:8]}")

    # commodity unit consistency within single-fuel domains
    unit_by_domain = defaultdict(Counter)
    for c in comms.values():
        u, d = clean_unit(c.get("UnitId", "")), c.get("Desc", "").lower()
        for kw in ("diesel", "electric", "biomass"):
            if kw in d:
                unit_by_domain[kw][u] += 1
    for kw, cnt in unit_by_domain.items():
        if len(cnt) > 1:
            rep.add("WARN", f"'{kw}' commodities use mixed units: {dict(cnt)}")

    # sector coverage (CLEW completeness)
    codes = " ".join(t["Tech"] for t in techs.values()) + " " + " ".join(c["Comm"] for c in comms.values())
    missing = [s for s, kws in SECTOR_CODES.items() if not any(k in codes for k in kws)]
    if missing:
        rep.add("WARN", f"no tech/commodity codes found for sector(s): {missing}")
    if len(emis) == 0:
        rep.add("WARN", "no emissions defined (climate dimension absent)")

    # organization
    if len(scens) <= 1:
        rep.add("INFO", "only the base scenario defined (no policy scenarios)")
    if len(tgroups) <= 1 and len(techs) > 40:
        rep.add("INFO", f"only {len(tgroups)} tech group(s) for {len(techs)} technologies (hard to navigate)")

    # solve / results status
    resdir = os.path.join(model_dir, "res")
    if not os.path.isdir(resdir) or not os.listdir(resdir):
        rep.add("WARN", "no saved results (model has not been solved on record)")
    else:
        folders = sorted(
            folder for folder in os.listdir(resdir)
            if os.path.isdir(os.path.join(resdir, folder))
        )
        statuses = []
        for s in folders:
            rf = os.path.join(resdir, s, "results.txt")
            if os.path.exists(rf):
                with open(rf) as result_stream:
                    first = result_stream.readline().strip()
            else:
                first = ""
            statuses.append((s, first[:38]))
            if not first:
                rep.add(
                    "WARN",
                    f"result folder '{s}' has no solver status",
                )
            elif not first.lower().startswith("optimal"):
                rep.add("WARN", f"result '{s}' is not optimal: {first[:60]!r}")
        print("  results:", statuses)
        resdata_path = os.path.join(model_dir, "view", "resData.json")
        if os.path.exists(resdata_path):
            saved_runs = {
                item.get("Case")
                for item in load_json(resdata_path).get("osy-cases", [])
                if item.get("Case")
            }
            unregistered = sorted(set(folders) - saved_runs)
            missing_results = sorted(saved_runs - set(folders))
            if unregistered:
                rep.add(
                    "INFO",
                    "result folder(s) absent from view/resData.json "
                    f"(possibly stale): {unregistered[:8]}",
                )
            if missing_results:
                rep.add(
                    "INFO",
                    "saved run metadata has no result folder "
                    f"(possibly incomplete): {missing_results[:8]}",
                )

    print("  findings:")
    if not rep.findings:
        print("    OK  — no issues detected")
    for level, msg in sorted(rep.findings, key=lambda x: _ORDER[x[0]]):
        print(f"    {level:4s} {msg}")
    print()
    return rep


def finding(level, code, message, evidence=None):
    """One JSON-inventory finding record."""
    item = {"level": level, "code": code, "message": message}
    if evidence is not None:
        item["evidence"] = evidence
    return item


def inventory(model_dir):
    """Structural and constraint inventory for one model folder, as JSON-ready data.

    Screening only: spot-check domain detection, saved-result freshness and every
    exact-bound finding before using them in a grade. Consumed by
    assess-clews-calibration (schema_version 1).
    """
    model_dir = str(model_dir)
    gen_path = os.path.join(model_dir, "genData.json")
    if not os.path.isfile(gen_path):
        raise ValueError(f"genData.json not found in {model_dir}")
    gen = load_json(gen_path)
    if not isinstance(gen, dict):
        raise ValueError("genData.json must contain a JSON object")

    def by_id(collection, field):
        return {str(row.get(field)): row for row in (gen.get(collection) or [])
                if isinstance(row, dict) and row.get(field)}

    techs = by_id("osy-tech", "TechId")
    comms = by_id("osy-comm", "CommId")
    emissions = by_id("osy-emis", "EmisId")
    scenarios = by_id("osy-scenarios", "ScenarioId")
    years = [str(year) for year in (gen.get("osy-years") or [])]

    parse_errors = []
    ids_by_file, parameters = scan_data_files(model_dir, errors=parse_errors)
    findings = [finding("fail", "json_parse", "Could not parse model data file", error)
                for error in parse_errors]

    used = defaultdict(set)
    for ids in ids_by_file.values():
        for identifier in ids:
            used[identifier.split("_", 1)[0]].add(identifier)
    reference_counts = {}
    for category, prefix, defined in (("technology", "TEC", techs), ("commodity", "COM", comms),
                                      ("emission", "EMI", emissions), ("scenario", "SC", scenarios)):
        found = used.get(prefix, set())
        reference_counts[category] = len(found)
        unknown = sorted(found - set(defined))
        if unknown:
            findings.append(finding(
                "fail", f"unknown_{category}_references",
                f"{len(unknown)} referenced {category} IDs are not defined", unknown[:25]))

    for category, rows in (("technology", techs), ("commodity", comms)):
        placeholders = [key for key, row in rows.items() if is_placeholder_desc(row.get("Desc", ""))]
        if placeholders:
            findings.append(finding(
                "fail" if len(placeholders) == len(rows) else "warn",
                f"placeholder_{category}_descriptions",
                f"{len(placeholders)}/{len(rows)} {category} descriptions are blank or placeholders",
                placeholders[:25]))

    io_techs = set()
    for param in ("IAR", "OAR"):
        for rows in parameters.get(param, {}).values():
            io_techs.update(str(row["TechId"]) for row in rows if row.get("TechId"))
    dangling = sorted(set(techs) - io_techs)
    if dangling:
        findings.append(finding(
            "warn", "dangling_technologies",
            f"{len(dangling)} technologies have neither input nor output activity ratios",
            dangling[:25]))

    ys_issues = year_split_issues(parameters, years)
    if ys_issues:
        findings.append(finding(
            "warn", "year_split_not_normalized",
            f"{len(ys_issues)} scenario-year YearSplit sums differ from 1", ys_issues[:25]))

    labels = " ".join(
        str(value)
        for row in list(techs.values()) + list(comms.values())
        for value in (row.get("Tech"), row.get("Comm"), row.get("Desc"))
        if value).upper()
    domains = {DOMAIN_KEYS[sector]: any(code in labels for code in codes)
               for sector, codes in SECTOR_CODES.items()}
    domains["climate"] = bool(emissions)
    domains["nexus"] = sum(domains.values()) >= 3 and bool(parameters.get("IAR") or parameters.get("OAR"))

    result_statuses = []
    for result_file in sorted(glob.glob(os.path.join(model_dir, "res", "*", "results.txt"))):
        try:
            with open(result_file, encoding="utf-8", errors="replace") as stream:
                first_line = stream.readline().strip()
        except OSError as exc:
            first_line = f"ERROR: {exc}"
        result_statuses.append({
            "label": os.path.basename(os.path.dirname(result_file)),
            "first_line": first_line,
            "appears_optimal": first_line.lower().startswith("optimal"),
        })
    if not result_statuses:
        findings.append(finding("warn", "no_saved_results", "No saved solve results were found"))
    elif not any(item["appears_optimal"] for item in result_statuses):
        findings.append(finding("fail", "no_optimal_result", "No saved result appears optimal"))
    elif any(not item["appears_optimal"] for item in result_statuses):
        findings.append(finding("warn", "nonoptimal_saved_results",
                                "Some saved results do not appear optimal"))

    fixed_matches = exact_bound_matches(parameters, years)
    if fixed_matches:
        findings.append(finding(
            "warn", "exact_bound_pairs",
            f"{len(fixed_matches)} exact lower/upper bound matches may history-fix outcomes",
            fixed_matches[:25]))
    forced_off = forced_off_bounds(parameters, years)
    if forced_off:
        findings.append(finding(
            "warn", "zero_upper_bounds",
            f"{len(forced_off)} upper bound(s) set to an active zero, switching the object "
            "off for that year",
            forced_off[:25]))

    return {
        "schema_version": 1,
        "model_path": os.path.abspath(model_dir),
        "metadata": {
            "case_name": gen.get("osy-casename"),
            "description": gen.get("osy-desc"),
            "version": gen.get("osy-version"),
            "date": gen.get("osy-date"),
        },
        "dimensions": {
            "years": years,
            "technologies": len(techs),
            "commodities": len(comms),
            "emissions": len(emissions),
            "scenarios": len(scenarios),
            "time_slices": len(gen.get("osy-ts") or []),
            "technology_groups": len(gen.get("osy-techGroups") or []),
            "parameters_found": len(parameters),
        },
        "domain_signals": domains,
        "reference_counts": reference_counts,
        "saved_results": result_statuses,
        "potential_history_fixed_bounds": fixed_matches,
        "findings": findings,
        "screening_warning": (
            "Heuristic inventory only. Spot-check domain detection, saved-result freshness, "
            "and every exact-bound finding before using them in a calibration grade."
        ),
    }


def inventory_main(argv=None):
    """CLI for the JSON inventory: MODEL_FOLDER [--output PATH]."""
    ap = argparse.ArgumentParser(description=inventory.__doc__)
    ap.add_argument("model_folder", help="path to one MUIOGO model folder")
    ap.add_argument("--output", help="write JSON here instead of stdout")
    args = ap.parse_args(argv)
    try:
        report = inventory(args.model_folder)
    except (OSError, ValueError) as exc:          # JSONDecodeError is a ValueError
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        parent = os.path.dirname(os.path.abspath(args.output))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as stream:
            stream.write(payload)
    else:
        print(payload, end="")
    return 1 if any(item["level"] == "fail" for item in report["findings"]) else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("models", nargs="*", help="model folder names (default: all)")
    ap.add_argument("--datastorage", default=DEFAULT_DS, help="path to WebAPP/DataStorage")
    ap.add_argument("--removable", nargs="+", metavar="ID",
                    help="gate: exit 0 only if every TEC_/COM_/EMI_ ID given is defined in "
                         "genData.json and referenced nowhere else in the model data")
    ap.add_argument("--json", metavar="PATH", dest="json_path",
                    help="with --removable, also write the verdicts as JSON to PATH")
    args = ap.parse_args(argv)

    if args.json_path and not args.removable:
        ap.error("--json is only meaningful together with --removable")

    if args.removable:
        if len(args.models) != 1:
            ap.error("--removable needs exactly one model (a folder path or a name "
                     "under --datastorage)")
        model_dir = args.models[0]
        if not os.path.exists(os.path.join(model_dir, "genData.json")):
            model_dir = os.path.join(os.path.abspath(args.datastorage), args.models[0])
        if not os.path.exists(os.path.join(model_dir, "genData.json")):
            ap.error(f"no genData.json under {model_dir}")
        verdicts = removability(model_dir, args.removable)
        print_removability(model_dir, verdicts)
        if args.json_path:
            report = {
                "removable": all(v["removable"] for v in verdicts),
                "objects": [{"id": v["id"], "removable": v["removable"],
                             "reason": v["reason"], "referenced_in": v["referenced_in"]}
                            for v in verdicts],
            }
            parent = os.path.dirname(os.path.abspath(args.json_path))
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(args.json_path, "w", encoding="utf-8") as stream:
                json.dump(report, stream, indent=2)
                stream.write("\n")
        return removable_exit_code(verdicts)

    ds = os.path.abspath(args.datastorage)
    if not os.path.isdir(ds):
        ap.error(f"DataStorage not found: {ds} (pass --datastorage)")

    if args.models:
        dirs = [os.path.join(ds, m) for m in args.models]
    else:
        dirs = [os.path.join(ds, d) for d in sorted(os.listdir(ds))
                if os.path.exists(os.path.join(ds, d, "genData.json"))]

    reps = [audit_model(d) for d in dirs if os.path.exists(os.path.join(d, "genData.json"))]

    print("SUMMARY")
    print("-" * 92)
    label = {3: "FAIL", 2: "WARN", 1: "INFO", 0: "OK"}
    for r in reps:
        nf = sum(1 for l, _ in r.findings if l == "FAIL")
        nw = sum(1 for l, _ in r.findings if l == "WARN")
        print(f"  {label[r.worst]:4s}  {r.name:30s}  ({nf} fail, {nw} warn)")
    return 1 if any(r.worst == 3 for r in reps) else 0


if __name__ == "__main__":
    sys.exit(main())
