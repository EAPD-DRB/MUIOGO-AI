"""`muiogo` CLI — thin commands over MuiogoClient/MuiogoServer.

Orientation (works with no server running):
  muiogo status                                      where everything is installed
  muiogo adopt --scan | --auto                       use installs you already have
  muiogo worlds                                      which worlds exist; * = active
  muiogo use <name>                                  switch world (live | runtime)

Models and scenarios:
  muiogo cases                                       list cases
  muiogo scenarios --case NAME                       scenarios and runs in a case
  muiogo new-run --case NAME --run RUN --activate A,B create a scenario combination
  muiogo copy   --case NAME                          copy a case to NAME_copy
  muiogo delete --case NAME --yes                    delete a case

Running:
  muiogo serve  [--detach]                           headless server; --detach backgrounds it
  muiogo stop                                        stop it (by pid, not by port)
  muiogo run    --case NAME --run RUN [--solver cbc] generate + solve one run
  muiogo batch  --case NAME --runs A,B,C             generate + solve several (CBC)
  muiogo log    --case NAME --run RUN                solver log for a run

Bringing models in and out:
  muiogo import --zip FILE.zip                       install a MUIO case archive
  muiogo import --xls BOOK.xlsx --case NAME          load an Excel workbook
  muiogo export --case NAME [--out DIR]              download a shareable .zip
  muiogo validate --case NAME --run RUN              check inputs before solving
  muiogo og catalog | installed | install --key KEY  OG country models

Results and analysis:
  muiogo results --case NAME --run RUN [--out DIR]   list result CSVs, or download all
  muiogo variables --case NAME --run RUN             what result variables exist
  muiogo compare --case NAME --runs A,B --var V      compare runs; --chart out.png
  muiogo verify --case NAME --run RUN [--resolve]     prove a result still reproduces

All commands take --url (default http://127.0.0.1:5002). Paths and ports come
from the installed workspace manifest when not given.
"""
import argparse
import sys

from muiogo_client import workspace
from muiogo_client.client import DEFAULT_URL, MuiogoClient, MuiogoError
from muiogo_client.server import MuiogoServer, ServerError


def _answers(url):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"{url}/getSession", timeout=1.5):
            return True
    except (urllib.error.URLError, OSError):
        return False


def _resolve_url(args):
    """Explicit --url wins; otherwise this workspace's own URL. Never guess.

    Falling back to "whatever port answers" was actively dangerous: with two
    worlds on one machine — live checkouts and an installed runtime — a command
    meant for one could silently drive the other's server. So we use the
    workspace's recorded URL and say so if nothing is listening there.
    """
    if getattr(args, "url", None):
        return args.url
    try:
        return workspace.summary()["muiogo_url"] or DEFAULT_URL
    except workspace.WorkspaceError:
        return DEFAULT_URL


def _warn_other_world(args):
    """Warn when another world's server is up but this one's is not."""
    if getattr(args, "url", None):
        return
    try:
        info = workspace.summary()
    except workspace.WorkspaceError:
        return
    mine = info["muiogo_url"]
    if not mine or _answers(mine):
        return
    for other in workspace.list_workspaces():
        if other["active"] or not other.get("port"):
            continue
        url = f"http://127.0.0.1:{other['port']}"
        if _answers(url):
            print(f"note: nothing is listening on {mine} for the "
                  f"{info['kind']} workspace, but a {other['kind']} workspace IS "
                  f"running on {url}.\n"
                  f"      Start this one with `muiogo serve`, or target the other "
                  f"explicitly with --url {url}.", file=sys.stderr)
            return


def _client(args):
    return MuiogoClient(base_url=_resolve_url(args))


def _data_storage(args):
    """DataStorage path: explicit flag, else from the workspace manifest."""
    if getattr(args, "data_storage", None):
        return args.data_storage
    info = workspace.summary()
    if not info["data_storage"]:
        raise MuiogoError("manifest has no MUIOGO path; pass --data-storage")
    return info["data_storage"]


def _checkout_state(path):
    """Live branch, HEAD and cleanliness of a checkout — not a recorded snapshot.

    A recorded ref goes stale the moment someone switches branch, and telling a
    user the wrong code is installed is worse than saying nothing.
    """
    import subprocess
    if not path:
        return "no path"
    def git(*a):
        r = subprocess.run(["git", "-C", str(path), *a], capture_output=True,
                           text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else ""
    head = git("rev-parse", "--short=8", "HEAD")
    if not head:
        return "not a git checkout"
    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "?"
    dirty = " +uncommitted changes" if git("status", "--porcelain") else ""
    where = "detached" if branch == "HEAD" else f"on {branch}"
    return f"{where} at {head}{dirty}"


def cmd_status(args):
    """Orientation: what is installed and where. Needs no running server."""
    try:
        info = workspace.summary()
    except workspace.WorkspaceError as exc:
        if getattr(args, "json", False):
            import json as _json
            print(_json.dumps({"error": str(exc)}))
        else:
            print(f"No workspace found.\n{exc}", file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        import json as _json
        client = MuiogoClient(base_url=info["muiogo_url"] or DEFAULT_URL, timeout=5)
        try:
            info["cases"] = client.list_cases()
            info["server_running"] = True
        except Exception:                                        # noqa: BLE001
            info["server_running"] = False
            from pathlib import Path as _P
            ds = info.get("data_storage")
            info["cases"] = sorted(
                x.name for x in _P(ds).iterdir() if (x / "genData.json").is_file()
            ) if ds and _P(ds).is_dir() else []
        info["other_workspaces"] = [w for w in workspace.list_workspaces() if not w["active"]]
        print(_json.dumps(info, indent=2, default=str))
        return 0

    print(f"world         {info['kind'].upper()}  ({info['kind_note']})")
    print(f"workspace     {info['workspace']}")
    print(f"manifest      {info['manifest']}")
    print(f"recorded      {info['generated']}")
    live = _checkout_state(info["muiogo_path"])
    print(f"MUIOGO        {info['muiogo_path']}  ({live})")
    print(f"model data    {info['data_storage']}")
    print(f"server URL    {info['muiogo_url']}")

    others = [w for w in workspace.list_workspaces() if not w["active"]]
    client = MuiogoClient(base_url=info["muiogo_url"] or DEFAULT_URL, timeout=5)
    try:
        cases = client.list_cases()
        print(f"server        running — {len(cases)} case(s)")
    except Exception:
        cases = None
        print("server        not running   (start it: muiogo serve)")

    if cases is None:
        from pathlib import Path

        ds = info["data_storage"]
        if ds and Path(ds).is_dir():
            cases = sorted(
                p.name for p in Path(ds).iterdir()
                if (p / "genData.json").is_file()
            )
    for case in cases or []:
        print(f"  case        {case}")

    # MUIOGO's own registry is authoritative for OG models; the manifest is only
    # a fallback for when no server is running to ask.
    registered = None
    if cases is not None:
        try:
            registered = client.og_installed()
        except Exception:
            registered = None
    if registered:
        for entry in registered:
            print(f"  OG model    {entry.get('country_id','?'):<5} "
                  f"{entry.get('local_path') or entry.get('country_name','')}"
                  f"   [{entry.get('install_state','?')}]")
    elif info["og_models"]:
        # An empty registry is not proof a model is unregistered: this world's
        # server reads the registry its own environment points at, so a model
        # registered in the other world legitimately shows as absent here.
        # Claiming "not registered with MUIOGO" would be a false statement
        # about the user's other installation.
        state = ("not in this world's registry" if cases is not None
                 else "unverified — no server running")
        for model in info["og_models"]:
            print(f"  OG model    {model.get('key'):<8} {model.get('path')}   [{state}]")
        if cases is not None:
            print(f"              registry: {info['muiogo'].get('og_state_dir', '?')}")
    if info["link_path"]:
        print(f"  link        {info['link_path']}")
    solvers = info["solvers"]
    if solvers:
        print(f"  solvers     glpk={bool(solvers.get('glpsol'))} cbc={bool(solvers.get('cbc'))}")
    if others:
        print()
        print(f"{len(others)} other world(s) on this machine — `muiogo worlds` to see them,")
        print("`muiogo use <name>` to switch.")
    return 0


def cmd_use(args):
    """Point the tooling at a registered world, explicitly."""
    try:
        workspace.set_active(args.name)
    except workspace.WorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    info = workspace.summary()
    print(f"active world: {args.name} ({info['kind']})")
    print(f"  MUIOGO  {info['muiogo_path']}")
    print(f"  server  {info['muiogo_url']}")
    return 0


def cmd_worlds(args):
    """List every workspace on this machine and mark the active one."""
    rows = workspace.list_workspaces()
    if getattr(args, "json", False):
        import json as _json
        for w in rows:
            w["running"] = bool(w.get("port")) and _answers(f"http://127.0.0.1:{w['port']}")
        print(_json.dumps(rows, indent=2, default=str))
        return 0 if rows else 1
    if not rows:
        print("No workspaces found. `muiogo adopt --scan` finds existing checkouts.")
        return 1
    for w in rows:
        mark = "*" if w["active"] else " "
        live = "running" if w.get("port") and _answers(f"http://127.0.0.1:{w['port']}") else "stopped"
        print(f" {mark} {w.get('name','?'):<9} {w['kind']:<10} port {str(w.get('port') or '?'):<5} "
              f"{live:<8} {w['muiogo_path']}")
        print(f"   {'':<10} {w['manifest']}")
    print()
    print("* = active. Switch with:  muiogo use <name>")
    return 0


def cmd_adopt(args):
    """Point the tooling at installations that already exist on this machine."""
    found = workspace.discover()
    if args.scan:
        print("MUIOGO checkouts:")
        for p in found["muiogo"] or ["  (none found)"]:
            print(f"  {p}")
        print("OG country models:")
        for p in found["og_models"] or ["  (none found)"]:
            print(f"  {p}")
        print("OG-CLEWs link:")
        for p in found["link"] or ["  (none found)"]:
            print(f"  {p}")
        print("\nAdopt them with:  muiogo adopt --auto")
        return 0

    muiogo_path = args.muiogo
    og_models = [m for m in (args.og_model or [])]
    link_path = args.link

    if args.auto:
        if not muiogo_path:
            if not found["muiogo"]:
                print("No MUIOGO checkout found. Pass --muiogo PATH.", file=sys.stderr)
                return 1
            if len(found["muiogo"]) > 1:
                print("Several MUIOGO checkouts found — name one with --muiogo:",
                      file=sys.stderr)
                for p in found["muiogo"]:
                    print(f"  {p}", file=sys.stderr)
                return 1
            muiogo_path = found["muiogo"][0]
        og_models = og_models or found["og_models"]
        link_path = link_path or (found["link"][0] if found["link"] else None)

    if not muiogo_path:
        print("Pass --muiogo PATH, or --auto to discover it.", file=sys.stderr)
        return 1

    try:
        dest, manifest = workspace.adopt(muiogo_path, og_models, link_path, port=args.port)
    except workspace.WorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Register the OG models with MUIOGO itself, so its registry — the record the
    # GUI and the link read — knows about them too. Needs a running server; the
    # manifest alone is only a fallback.
    registered, pending = [], []
    if manifest["og_models"]:
        try:
            client = MuiogoClient(base_url=manifest["muiogo"]["url"], timeout=120)
            client.list_cases()                       # is anything listening?
            for m in manifest["og_models"]:
                cid = m["repo"].rsplit("-", 1)[-1].upper()
                try:
                    client.og_register_local(cid, m["repo"], m["path"],
                                             package_name=m.get("package"))
                    registered.append(m["key"])
                except Exception as exc:              # noqa: BLE001
                    pending.append(f"{m['key']} ({exc})")
        except Exception:
            pending = [m["key"] for m in manifest["og_models"]]

    print(f"adopted -> {dest}")
    print(f"  MUIOGO      {manifest['muiogo']['path']}  (ref {manifest['muiogo']['ref']})")
    print(f"  cases       {len(manifest['clews_cases'])}")
    for m in manifest["og_models"]:
        print(f"  OG model    {m['key']:<8} {m['path']}")
    if manifest["ogclews_link"]["path"]:
        print(f"  link        {manifest['ogclews_link']['path']}")
    if registered:
        print(f"  registered with MUIOGO: {', '.join(registered)}")
    if pending:
        print(f"  {len(pending)} model(s) recorded but NOT registered with MUIOGO —")
        print("  start a server and re-run so its registry (and the GUI) sees them:")
        print("    muiogo serve --detach && muiogo adopt --auto")
    print("\nCheck it with:  muiogo status")
    return 0


def cmd_cases(args):
    _warn_other_world(args)
    for case in _client(args).list_cases():
        print(case)
    return 0


def cmd_scenarios(args):
    client = _client(args)
    ds = _data_storage(args)
    scenarios = client.list_scenarios(args.case, ds)
    runs = client.list_runs(args.case, ds)

    print(f"scenarios in {args.case}:")
    for s in scenarios:
        base = "  (base)" if s.get("ScenarioId") == "SC_0" else ""
        print(f"  {s.get('Scenario'):<18} {s.get('Desc','')}{base}")
    print(f"\nruns in {args.case}:")
    for r in runs:
        active = [s["Scenario"] for s in r.get("Scenarios", []) if s.get("Active")]
        print(f"  {r.get('Case'):<18} activates: {', '.join(active)}")
    return 0


def cmd_new_run(args):
    client = _client(args)
    ds = _data_storage(args)
    activate = [a.strip() for a in (args.activate or "").split(",") if a.strip()]
    body = client.create_run(args.case, args.run, activate, ds, desc=args.desc or "")
    print(body.get("message", body))
    if body.get("status_code") == "exist":
        return 1
    print(f"Now solve it:  muiogo run --case \"{args.case}\" --run {args.run}")
    return 0


def cmd_copy(args):
    print(_client(args).copy_case(args.case).get("message", ""))
    return 0


def cmd_delete(args):
    if not args.yes:
        print("Refusing to delete without --yes.", file=sys.stderr)
        return 2
    print(_client(args).delete_case(args.case).get("message", ""))
    return 0


def _record_provenance(args, run, solver):
    """Write RUN.json beside a freshly solved run. Never fails the run itself."""
    from muiogo_client import provenance
    try:
        ds = _data_storage(args)
        muiogo_path = None
        try:
            muiogo_path = workspace.summary()["muiogo_path"]
        except workspace.WorkspaceError:
            pass
        path, record = provenance.write(ds, args.case, run,
                                        solver=solver, muiogo_path=muiogo_path)
        return record
    except Exception as exc:                                     # noqa: BLE001
        print(f"warning: could not record provenance: {exc}", file=sys.stderr)
        return None


def cmd_run(args):
    _warn_other_world(args)
    body = _client(args).run(args.case, args.run, solver=args.solver)
    print(f"status: {body.get('status_code')}")
    timer = (body.get("timer") or "").strip()
    if timer:
        print(timer)
    if not args.no_provenance:
        record = _record_provenance(args, args.run, args.solver)
        if record:
            print(f"provenance: objective={record['objective']} "
                  f"input={(record['input_sha256'] or '?')[:12]} "
                  f"results={(record['results_sha256'] or '?')[:12]}")
    return 0


def cmd_verify(args):
    """Re-check a recorded run against what is on disk, and optionally re-solve."""
    from muiogo_client import provenance
    ds = _data_storage(args)
    stored = provenance.read(ds, args.case, args.run)
    if stored is None:
        print(f"No provenance record for {args.case!r}/{args.run!r}. "
              f"Solve it once with `muiogo run` to create one.", file=sys.stderr)
        return 1

    print(f"recorded {stored['recorded']}  objective={stored['objective']}  "
          f"scenarios={stored.get('scenarios_active')}")

    if args.resolve:
        print("re-solving to confirm reproducibility…")
        _client(args).run(args.case, args.run, solver=stored.get("solver", "cbc"))
        fresh = provenance.build(ds, args.case, args.run, solver=stored.get("solver", "cbc"))
        same_obj = fresh["objective"] == stored["objective"]
        same_res = fresh["results_sha256"] == stored["results_sha256"]
        print(f"  objective: {stored['objective']} -> {fresh['objective']}  "
              f"{'MATCH' if same_obj else 'DIFFERENT'}")
        print(f"  results hash: {'MATCH' if same_res else 'DIFFERENT'}")
        if same_obj and same_res:
            print("\nReproduced exactly.")
            return 0
        print("\nDid NOT reproduce — the case's input data has changed since this "
              "run was recorded.", file=sys.stderr)
        return 1

    ok, diffs = provenance.compare_to_current(ds, args.case, args.run)
    if ok:
        print("On-disk results still match the record.")
        return 0
    for d in diffs:
        print(f"  MISMATCH {d}")
    print("\nThe stored results no longer match the record. Re-solve, or use "
          "--resolve to check reproducibility.", file=sys.stderr)
    return 1


def cmd_batch(args):
    _warn_other_world(args)
    runs = [r.strip() for r in args.runs.split(",") if r.strip()]
    if not runs:
        print("No runs given.", file=sys.stderr)
        return 2
    client = _client(args)
    body = client.batch_run(args.case, runs)
    if body.get("time"):
        print(f"elapsed: {float(body['time']):.1f}s")

    # /batchRun reports no per-run status_code, so verify each run on disk
    # rather than trusting the batch response.
    from muiogo_client import analysis
    ds = _data_storage(args)
    failed = []
    for run in runs:
        n = len(analysis.available_variables(ds, args.case, run))
        if n:
            rec = None if args.no_provenance else _record_provenance(args, run, "cbc")
            obj = f"  objective={rec['objective']}" if rec else ""
            print(f"  {run}: {n} result variables{obj}")
        else:
            print(f"  {run}: NO RESULTS — did not solve")
            failed.append(run)
    if failed:
        print(f"\n{len(failed)} of {len(runs)} run(s) produced nothing: "
              f"{', '.join(failed)}", file=sys.stderr)
        return 1
    return 0


def cmd_log(args):
    client = _client(args)
    if args.server:
        print(client.server_log() or "(server log empty)")
        return 0
    text = client.run_output(args.case, args.run, _data_storage(args))
    if not text:
        print(f"No solver output for run {args.run!r} — it has never produced results.\n"
              f"For the server's own log: muiogo log --server --case X --run Y")
        return 1
    print(text)
    return 0


def cmd_results(args):
    _warn_other_world(args)
    client = _client(args)
    if args.out:
        paths = client.download_all_csvs(args.case, args.run, args.out)
        print(f"Downloaded {len(paths)} CSVs to {args.out}")
    else:
        for name in client.list_result_csvs(args.case, args.run):
            print(name)
    return 0


def cmd_variables(args):
    _warn_other_world(args)
    """What result variables a solved run offers."""
    from muiogo_client import analysis
    names = analysis.available_variables(_data_storage(args), args.case, args.run)
    if not names:
        print(f"no results for run {args.run!r} — not solved, or the solve failed")
        return 1
    for n in names:
        print(n)
    return 0


def cmd_compare(args):
    """Compare runs on one result variable; optionally chart it."""
    from muiogo_client import analysis
    filters = {}
    for spec in args.filter or []:
        if "=" not in spec:
            print(f"bad --filter {spec!r}; want COLUMN=VALUE", file=sys.stderr)
            return 2
        col, val = spec.split("=", 1)
        filters[col] = val
    runs = [r.strip() for r in args.runs.split(",") if r.strip()]

    try:
        df, warnings = analysis.compare(
            _data_storage(args), args.case, runs, args.var, filters, args.by)
    except analysis.AnalysisError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    # Comparing runs of different vintages gives a confidently wrong answer: a
    # case ships with pre-computed results, so a freshly solved run compared
    # against a shipped one measures the gap between two MUIOGO versions as if
    # it were the scenario's effect.
    from muiogo_client import provenance
    for w in provenance.consistency(_data_storage(args), args.case, runs):
        print(f"warning: {w}", file=sys.stderr)

    if args.by and len(df.columns) > args.top:
        keep = df.sum().sort_values(ascending=False).head(args.top).index
        print(f"(showing the {len(keep)} largest of {len(df.columns)} groups)")
        df = df[keep]

    label = args.var + (
        "  [" + ", ".join(f"{k}={v}" for k, v in filters.items()) + "]" if filters else "")
    print(label)
    print(analysis.summarise(df, columns_are_runs=not args.by).to_string(
        float_format=lambda v: f"{v:,.2f}" if abs(v) < 1000 else f"{v:,.0f}"))

    if args.table:
        print()
        print(df.to_string(float_format=lambda v: f"{v:,.2f}" if abs(v) < 1000 else f"{v:,.0f}"))

    if args.chart:
        title = f"{args.var} — {args.case}"
        if filters:
            title += " (" + ", ".join(f"{k}={v}" for k, v in filters.items()) + ")"
        out = analysis.chart(df, args.chart, title=title, ylabel=args.var, kind=args.kind)
        print(f"\nchart: {out}")
    return 0


def cmd_validate(args):
    """MUIOGO ships ten input-consistency checks; its output carries HTML for
    the browser, so strip it and report pass/fail plainly."""
    import re as _re
    body = _client(args).validate_inputs(args.case, args.run)
    raw = body.get("msg") or body.get("message") or "" if isinstance(body, dict) else str(body)
    text = _re.sub(r"<[^>]+>", "", raw)
    checks, failures = [], []
    for line in (l.strip() for l in text.splitlines()):
        m = _re.match(r"(CHECK \d+):\s*(\w+)", line)
        if m:
            checks.append(m.group(1))
            if m.group(2).lower() != "success":
                failures.append(line)
        elif line.startswith("CHECK") and ":" in line:
            pass
    for f in failures:
        print(f"  FAIL {f}")
    if checks:
        print(f"{len(checks) - len(failures)}/{len(checks)} input checks passed")
    else:
        print(text.strip() or body)
    if failures:
        print("\nFix these before solving — they cause infeasible or wrong results.",
              file=sys.stderr)
        return 1
    return 0


def cmd_import(args):
    client = _client(args)
    before = set(client.list_cases())
    if args.xls:
        if not args.case:
            print("--xls needs --case (the case to load the workbook into)", file=sys.stderr)
            return 2
        body = client.import_xls(args.case, args.xls)
        print(body.get("message", body) if isinstance(body, dict) else body)
        return 0
    body = client.import_case(args.zip)
    after = set(client.list_cases())
    new = sorted(after - before)
    if new:
        for case in new:
            print(f"imported: {case}")
        return 0
    print(f"No new case appeared. Server said: "
          f"{body.get('message', body) if isinstance(body, dict) else body}", file=sys.stderr)
    return 1


def cmd_export(args):
    out = _client(args).export_case(args.case, args.out or ".")
    size = out.stat().st_size / (1 << 20)
    print(f"exported: {out}  ({size:.1f} MB)")
    return 0


def cmd_og(args):
    client = _client(args)
    if args.og_command == "catalog":
        installed = {c.get("country_id") for c in (client.og_installed() or [])}
        for entry in client.og_catalog() or []:
            mark = "installed" if entry.get("country_id") in installed else ""
            print(f"  {entry.get('catalog_key',''):<12} {entry.get('country_id',''):<5} "
                  f"{entry.get('country_name','')[:40]:<42}{mark}")
        return 0
    if args.og_command == "installed":
        rows = client.og_installed() or []
        if not rows:
            print("no OG country models installed")
        for entry in rows:
            print(f"  {entry.get('country_id',''):<5} {entry.get('country_name','')[:38]:<40}"
                  f"{entry.get('install_state','')}")
        return 0
    # install
    body = client.og_install(catalog_key=args.key, repo_url=args.repo_url, branch=args.branch)
    install_id = body.get("install_id")
    print(f"install started: {install_id}  ({body.get('install_state')})")
    if args.wait:
        import time
        for _ in range(240):
            status = client.og_install_status(install_id)
            state = status.get("install_state")
            if state in ("installed", "failed"):
                print(f"  {state}: {status.get('progress_label','')}")
                return 0 if state == "installed" else 1
            time.sleep(5)
        print("  still running — check with: muiogo og installed", file=sys.stderr)
        return 1
    print("Poll it with:  muiogo og installed")
    return 0


def cmd_stop(args):
    """Stop the server this workspace started, by pid rather than by port."""
    root = args.root
    if not root:
        root = workspace.summary()["muiogo_path"]
    port = args.port or workspace.summary().get("muiogo_port") or 5002
    server = MuiogoServer(root, port=port)
    pid = server.stop_detached()
    if pid:
        print(f"stopped server (pid {pid})")
        return 0
    if server.is_running():
        print("a server is answering but this workspace has no pidfile — it was "
              "started another way, so stop it where you started it.", file=sys.stderr)
        return 1
    print("no server running for this workspace")
    return 0


def cmd_serve(args):
    root = args.root
    if not root:
        info = workspace.summary()
        root = info["muiogo_path"]
        if not root:
            raise ServerError("no MUIOGO path in the manifest; pass --root")
    port = args.port
    if port is None:
        try:
            port = workspace.summary()["muiogo_port"] or 5002
        except workspace.WorkspaceError:
            port = 5002
    server = MuiogoServer(root, port=port)
    if args.detach:
        pid = server.start_detached(log_path=args.log)
        print(f"MUIOGO serving headless on {server.url} (pid {pid})")
        print(f"  log:  {args.log or server.pidfile().with_suffix('.log')}")
        print(f"  stop: muiogo stop")
        return 0
    server.start()
    print(f"MUIOGO serving headless on {server.url} — Ctrl+C to stop.")
    try:
        server.process.wait()
    except KeyboardInterrupt:
        server.stop()
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="muiogo", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=None,
                        help=f"server URL (default: the workspace's, else {DEFAULT_URL})")
    parser.add_argument("--data-storage", help="MUIOGO DataStorage path (default: from manifest)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status", help="where everything is installed (no server needed)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_status)
    p = sub.add_parser("adopt", help="point the tooling at existing installations")
    p.add_argument("--scan", action="store_true", help="show what was found, change nothing")
    p.add_argument("--auto", action="store_true", help="adopt everything discovered")
    p.add_argument("--muiogo", help="path to an existing MUIOGO checkout")
    p.add_argument("--og-model", action="append", help="path to an OG country model (repeatable)")
    p.add_argument("--link", help="path to an ogclews-link checkout")
    p.add_argument("--port", type=int, default=5002)
    p.set_defaults(func=cmd_adopt)

    p = sub.add_parser("use", help="switch which world the tooling acts on")
    p.add_argument("name")
    p.set_defaults(func=cmd_use)

    p = sub.add_parser("worlds", help="list workspaces on this machine, mark the active one")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_worlds)
    sub.add_parser("cases", help="list cases").set_defaults(func=cmd_cases)

    p = sub.add_parser("scenarios", help="scenarios and runs defined in a case")
    p.add_argument("--case", required=True)
    p.set_defaults(func=cmd_scenarios)

    p = sub.add_parser("new-run", help="create a run activating chosen scenarios")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--activate", default="", help="scenario names, comma-separated (base is automatic)")
    p.add_argument("--desc", default="")
    p.set_defaults(func=cmd_new_run)

    p = sub.add_parser("copy", help="copy a case to <name>_copy")
    p.add_argument("--case", required=True)
    p.set_defaults(func=cmd_copy)

    p = sub.add_parser("delete", help="delete a case")
    p.add_argument("--case", required=True)
    p.add_argument("--yes", action="store_true", help="confirm deletion")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("run", help="generate data file and solve one run")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--solver", default="cbc", choices=["cbc", "glpk"],
                   help="cbc is the working default; glpk is broken upstream")
    p.add_argument("--no-provenance", action="store_true",
                   help="skip writing RUN.json beside the results")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("verify", help="check a run against its provenance record")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--resolve", action="store_true",
                   help="re-solve and confirm the objective and results reproduce")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("batch", help="generate and solve several runs (CBC)")
    p.add_argument("--case", required=True)
    p.add_argument("--runs", required=True, help="run names, comma-separated")
    p.add_argument("--no-provenance", action="store_true")
    p.set_defaults(func=cmd_batch)

    p = sub.add_parser("log", help="a run's solver output (or --server for the app log)")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--server", action="store_true",
                   help="show MUIOGO's process-wide log instead of this run's output")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("results", help="list result CSVs, or download all with --out")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.add_argument("--out", help="directory to download all CSVs into")
    p.set_defaults(func=cmd_results)

    p = sub.add_parser("variables", help="result variables available for a solved run")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.set_defaults(func=cmd_variables)

    p = sub.add_parser("compare", help="compare runs on a result variable, and chart it")
    p.add_argument("--case", required=True)
    p.add_argument("--runs", required=True, help="run names, comma-separated")
    p.add_argument("--var", required=True, help="result variable (see: muiogo variables)")
    p.add_argument("--filter", action="append", metavar="COL=VALUE",
                   help="restrict rows, e.g. e=CO2 (repeatable)")
    p.add_argument("--by", help="break down by a dimension (t, f, e, ...) instead of totalling")
    p.add_argument("--top", type=int, default=8, help="with --by, keep the N largest groups")
    p.add_argument("--table", action="store_true", help="also print the full year-by-year table")
    p.add_argument("--chart", help="write a chart image here (.png)")
    p.add_argument("--kind", default="line", choices=["line", "area", "bar"])
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("validate", help="check a run's inputs before a long solve")
    p.add_argument("--case", required=True)
    p.add_argument("--run", required=True, dest="run")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("import", help="bring in a case .zip, or an Excel workbook")
    p.add_argument("--zip", help="a MUIO case archive to install")
    p.add_argument("--xls", help="an Excel workbook to load into --case")
    p.add_argument("--case", help="target case (required with --xls)")
    p.set_defaults(func=cmd_import)

    p = sub.add_parser("export", help="download a case as a shareable .zip")
    p.add_argument("--case", required=True)
    p.add_argument("--out", help="file or directory to write to (default: here)")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("og", help="OG country models: catalog, installed, install")
    ogsub = p.add_subparsers(dest="og_command", required=True)
    ogsub.add_parser("catalog", help="country models available to install")
    ogsub.add_parser("installed", help="country models installed here")
    q = ogsub.add_parser("install", help="install a country model")
    q.add_argument("--key", help="catalog key, e.g. og-zaf")
    q.add_argument("--repo-url", help="install from a git URL instead")
    q.add_argument("--branch")
    q.add_argument("--wait", action="store_true", help="poll until it finishes")
    p.set_defaults(func=cmd_og)

    p = sub.add_parser("serve", help="run a headless MUIOGO server in the foreground")
    p.add_argument("--root", help="MUIOGO checkout (default: from manifest)")
    p.add_argument("--port", type=int, default=None, help="default: the workspace's port, else 5002")
    p.add_argument("--detach", action="store_true",
                   help="run in the background and record the pid (headless default choice)")
    p.add_argument("--log", help="where a detached server writes its output")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("stop", help="stop this workspace's detached server")
    p.add_argument("--root", help="MUIOGO checkout (default: from manifest)")
    p.add_argument("--port", type=int, default=None)
    p.set_defaults(func=cmd_stop)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (MuiogoError, ServerError, workspace.WorkspaceError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:                                     # noqa: BLE001
        # A stopped server is the common case here and deserves a sentence
        # rather than a stack trace from deep inside urllib3.
        name = type(exc).__name__
        if "Connect" in name or "Timeout" in name:
            url = _resolve_url(args)
            print(f"error: no MUIOGO server is answering at {url}.\n"
                  f"       Start it with `muiogo serve`, or see `muiogo worlds`.",
                  file=sys.stderr)
            return 1
        raise


if __name__ == "__main__":
    raise SystemExit(main())
