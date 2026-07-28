#!/usr/bin/env python3
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

Exit status is non-zero if any FAIL-level finding is present (gates CI).
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
PLACEHOLDER_DESCS = {"", "Default commodity", "Default technology"}
_ORDER = {"FAIL": 0, "WARN": 1, "INFO": 2, "OK": 3}


def clean_unit(u): return re.sub("<[^>]+>", "", u or "")
def load_json(path):
    with open(path) as fh: return json.load(fh)


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
    tid_re, cid_re, eid_re, sc_re = (re.compile(p) for p in
        (r"TEC_[0-9a-z]+", r"COM_[0-9a-z]+", r"EMI_[0-9a-z]+", r"SC_[0-9a-z]+"))
    used_tid, used_cid, used_eid, bad_sc = set(), set(), set(), {}
    for f in sorted(glob.glob(os.path.join(model_dir, "*.json"))):
        if os.path.basename(f) == "genData.json":
            continue
        txt = open(f).read()
        used_tid |= set(tid_re.findall(txt))
        used_cid |= set(cid_re.findall(txt))
        used_eid |= set(eid_re.findall(txt))
        extra = set(sc_re.findall(txt)) - defined_sc
        if extra:
            bad_sc[os.path.basename(f)] = sorted(extra)

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
    t_ph = [t for t in techs.values() if t.get("Desc", "") in PLACEHOLDER_DESCS]
    c_ph = [c for c in comms.values() if c.get("Desc", "") in PLACEHOLDER_DESCS]
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

    # YearSplit sums to 1.0 across timeslices
    ryts_path = os.path.join(model_dir, "RYTs.json")
    if os.path.exists(ryts_path) and years:
        ys = load_json(ryts_path).get("YS", {}).get("SC_0", [])
        for y in (years[0], years[-1]):
            tot = sum(float(r.get(y, 0) or 0) for r in ys)
            if abs(tot - 1.0) > 1e-6:
                rep.add("WARN", f"YearSplit for {y} sums to {tot:.4f} (should be 1.0)")

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
        folders = sorted(os.listdir(resdir))
        scen_labels = {s.get("Scenario") for s in scens.values()} | {s.get("Desc") for s in scens.values()}
        statuses = []
        for s in folders:
            rf = os.path.join(resdir, s, "results.txt")
            first = open(rf).readline().strip() if os.path.exists(rf) else ""
            statuses.append((s, first[:38]))
            if first and not first.lower().startswith("optimal"):
                rep.add("WARN", f"result '{s}' is not optimal: {first[:60]!r}")
        print("  results:", statuses)
        if folders and scen_labels and not (set(folders) & scen_labels):
            rep.add("INFO", "saved result folder names don't match current scenario labels (possibly stale)")

    print("  findings:")
    if not rep.findings:
        print("    OK  — no issues detected")
    for level, msg in sorted(rep.findings, key=lambda x: _ORDER[x[0]]):
        print(f"    {level:4s} {msg}")
    print()
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("models", nargs="*", help="model folder names (default: all)")
    ap.add_argument("--datastorage", default=DEFAULT_DS, help="path to WebAPP/DataStorage")
    args = ap.parse_args(argv)

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
