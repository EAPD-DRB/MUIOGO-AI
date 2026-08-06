#!/usr/bin/env python3
"""Project the Fisheries registers into the canonical six-table ledger.

Why this exists
---------------
This skill authors eight registers. Every other CLEWs skill validates the
canonical six-table ledger described in ``references/SCHEMA.md``. The registers
are a **superset** of the canonical required columns, so the ledger does not need
to be authored a second time — it can be derived.

So: the registers stay the thing an analyst fills in, this script projects them
into ``data_sources/``, and ``scripts/validate_ledger.py`` runs the same
``provenance.py`` every other skill runs. Nothing is authored twice and nothing
is thrown away: register columns with no canonical home are folded into the
optional ``notes`` column as ``key=value`` pairs.

    source-register.csv       -> SOURCES.csv
    assumption-register.csv   -> ASSUMPTIONS.csv
    calculation-register.csv  -> CALCULATIONS.csv
    parameter-register.csv    -> MODEL_MAP.csv
    boundary-register.csv     -> GAPS.csv  (flows excluded from the boundary)
    completeness-register.csv -> GAPS.csv  (data gaps and not-applicable items)
    --change-* arguments      -> CHANGES.csv  (append-only; see below)

``policymaker-trace-test.csv`` and ``residual-capacity-input.csv`` are not
projected. The trace test carries no lineage and the residual-capacity file is a
script input, not a register.

``CHANGES.csv`` is a log, not a projection, so it is never regenerated. It is
created with headers only, and ``--change-id`` appends one row whose
``map_rows_affected`` is filled from the rows this run just wrote — that field
has to list real ``MAP_`` IDs, which is exactly the enumeration nobody should do
by hand.

Usage
-----
    python scripts/project_registers_to_ledger.py --registers . --out data_sources
    python scripts/project_registers_to_ledger.py --registers . --out data_sources \
        --change-id CHG_FSH_ADD_20260731 --change-class B \
        --change-description "Add Fisheries sector" --author "A. Analyst" \
        --commit 1a2b3c4

Exit 0 on success, 1 when a register is unreadable or an output would be
overwritten without ``--force``.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    import provenance
except ImportError:  # pragma: no cover - the vendored copy sits beside this file
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import provenance


# Register file -> canonical table it feeds. Order matters only for reporting.
REGISTER_FILES = {
    "sources": "source-register.csv",
    "assumptions": "assumption-register.csv",
    "calculations": "calculation-register.csv",
    "parameters": "parameter-register.csv",
    "boundaries": "boundary-register.csv",
    "completeness": "completeness-register.csv",
}

# Register ID column -> the canonical prefix its IDs must carry.
ID_COLUMN = {
    "sources": ("source_id", "SRC_"),
    "assumptions": ("assumption_id", "ASM_"),
    "calculations": ("calculation_id", "CALC_"),
    "parameters": ("parameter_record_id", "MAP_"),
}

# A leading legacy marker is dropped when doing so keeps every ID distinct:
# ``A-FSH-14`` reads better as ``ASM_FSH-14`` than ``ASM_A-FSH-14``.
LEGACY_MARKER = {
    "assumptions": re.compile(r"^A[-_]", re.IGNORECASE),
    "calculations": re.compile(r"^C[-_]", re.IGNORECASE),
    "parameters": re.compile(r"^(?:M|P)[-_]", re.IGNORECASE),
}

ILLEGAL_ID_CHARS = re.compile(r"[^A-Za-z0-9._-]")
LEADING_NON_ALNUM = re.compile(r"^[^A-Za-z0-9]+")

# Register columns folded into the canonical ``notes`` column, in this order.
FOLDED = {
    "sources": ("publication_date", "archived_url", "quality_grade"),
    "assumptions": ("sensitivity_required", "owner", "review_status"),
    "calculations": (
        "output_description",
        "conversion_factors",
        "method",
        "rounding",
        "review_status",
    ),
    "parameters": ("secondary_entity", "uncertainty", "confidence"),
}

EXCLUDED_PREFIXES = ("exclud", "out", "no")


class Projection:
    """Reads the registers, renames IDs, and writes the canonical tables."""

    def __init__(self, registers: Path, out: Path, copy_evidence: bool = False) -> None:
        self.registers = registers
        self.out = out
        self.copy_evidence = copy_evidence
        self.rows: Dict[str, List[Dict[str, str]]] = {}
        self.id_map: Dict[str, str] = {}
        self.notes: List[str] = []
        self.copied: List[str] = []
        self.errors: List[str] = []

    # ------------------------------------------------------------ reading

    def read_registers(self) -> None:
        for key, filename in REGISTER_FILES.items():
            path = self.registers / filename
            if not path.is_file():
                self.rows[key] = []
                self.notes.append(f"{filename} is absent; nothing projected from it")
                continue
            try:
                with path.open(newline="", encoding="utf-8-sig") as handle:
                    self.rows[key] = [
                        {(k or "").strip(): (v or "").strip() for k, v in row.items()}
                        for row in csv.DictReader(handle)
                    ]
            except (OSError, UnicodeDecodeError) as exc:
                self.errors.append(f"cannot read {filename}: {exc}")
                self.rows[key] = []

    # ------------------------------------------------------------- IDs

    def build_id_map(self) -> None:
        """Map every register ID to a canonical one, deterministically.

        Stripping the legacy marker is preferred but only applied when the
        stripped set stays collision-free, so the mapping never depends on row
        order and never silently merges two records.
        """
        for key, (column, prefix) in ID_COLUMN.items():
            originals = [
                row.get(column, "") for row in self.rows.get(key, []) if row.get(column)
            ]
            marker = LEGACY_MARKER.get(key)
            stripped = [
                self._sanitize(marker.sub("", value) if marker else value)
                for value in originals
            ]
            plain = [self._sanitize(value) for value in originals]
            use_stripped = len(set(stripped)) == len(set(originals)) and all(stripped)
            chosen = stripped if use_stripped else plain
            for original, token in zip(originals, chosen):
                candidate = prefix + token
                existing = self.id_map.get(original)
                if existing and existing != candidate:
                    self.errors.append(
                        f"{original} maps to both {existing} and {candidate}"
                    )
                    continue
                self.id_map[original] = candidate
            collisions = {
                candidate
                for candidate in (prefix + token for token in chosen)
                if list(prefix + t for t in chosen).count(candidate) > 1
            }
            for candidate in sorted(collisions):
                self.errors.append(
                    f"two {column} values both become {candidate}; "
                    "make the register IDs distinct in more than punctuation"
                )

    @staticmethod
    def _sanitize(value: str) -> str:
        token = ILLEGAL_ID_CHARS.sub("_", value.strip())
        token = LEADING_NON_ALNUM.sub("", token)
        return token

    def rename(self, value: str) -> str:
        """Rename one register ID, leaving an unknown ID visibly unresolved."""
        value = value.strip()
        if not value:
            return ""
        mapped = self.id_map.get(value)
        if mapped:
            return mapped
        self.notes.append(
            f"reference {value} matches no register row; it is carried through as "
            f"UNRESOLVED_{self._sanitize(value)} so the ledger reports it"
        )
        return "UNRESOLVED_" + self._sanitize(value)

    def rename_list(self, *values: str) -> str:
        out: List[str] = []
        for value in values:
            for item in provenance.split_ids(value):
                mapped = self.rename(item)
                if mapped and mapped not in out:
                    out.append(mapped)
        return "; ".join(out)

    # ------------------------------------------------------- notes folding

    def fold_notes(self, key: str, row: Dict[str, str], extra: Sequence[str] = ()) -> str:
        parts: List[str] = []
        if row.get("notes"):
            parts.append(row["notes"])
        identifier_column = ID_COLUMN.get(key, ("", ""))[0]
        original = row.get(identifier_column, "")
        if original and self.id_map.get(original) != original:
            parts.append(f"legacy_id={original}")
        for column in FOLDED.get(key, ()):
            if row.get(column):
                parts.append(f"{column}={row[column]}")
        parts.extend(extra)
        return "; ".join(parts)

    # ------------------------------------------------------- projections

    def sources(self) -> List[Dict[str, str]]:
        out = []
        for row in self.rows.get("sources", []):
            local_file = self._relocate(
                row.get("local_file", ""), row.get("source_id", "<no id>")
            )
            if row.get("sha256") and not local_file:
                self.notes.append(
                    f"{row.get('source_id', '<no id>')} records a sha256 but no "
                    "local_file; the canonical ledger rejects a digest it cannot "
                    "compare against bytes, so name the retained file or drop the "
                    "digest"
                )
            out.append(
                {
                    "source_id": self.rename(row.get("source_id", "")),
                    "provider": row.get("provider", ""),
                    "product": row.get("title", ""),
                    "edition": row.get("edition", ""),
                    "reference_period": row.get("reference_period", ""),
                    "geography": row.get("geography", ""),
                    "variable": row.get("variable", ""),
                    "source_unit": row.get("original_unit", ""),
                    "exact_locator": row.get("exact_locator", ""),
                    "url": row.get("url", ""),
                    "access_date": row.get("access_date", ""),
                    "license": row.get("license", ""),
                    "sha256": row.get("sha256", ""),
                    "local_file": local_file,
                    "notes": self.fold_notes("sources", row),
                }
            )
        return out

    def _relocate(self, local_file: str, source_id: str) -> str:
        """Make a register-relative retained-copy path ledger-relative.

        The canonical ledger only accepts a digest it can verify, which means the
        retained file has to sit under the ledger directory. ``--copy-evidence``
        puts it there; without it the path is left pointing outside and reported,
        because silently dropping the retained copy would lose the evidence.
        """
        if not local_file:
            return ""
        origin = (self.registers / local_file).resolve()
        if self.copy_evidence:
            target = self.out / "evidence" / Path(local_file).name
            if origin.is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists() or target.read_bytes() != origin.read_bytes():
                    target.write_bytes(origin.read_bytes())
                    self.copied.append(f"evidence/{target.name}")
                return f"evidence/{target.name}"
            self.notes.append(
                f"{source_id} names local_file {local_file}, which does not exist "
                "relative to the registers, so it could not be copied"
            )
        rewritten = os.path.relpath(origin, self.out.resolve()).replace(os.sep, "/")
        if rewritten.startswith(".."):
            self.notes.append(
                f"{source_id} retains {local_file} outside the ledger; the canonical "
                "ledger verifies digests against files beneath it, so re-run with "
                "--copy-evidence or move the file under "
                f"{self.out.name}/evidence/"
            )
        return rewritten

    def assumptions(self) -> List[Dict[str, str]]:
        return [
            {
                "assumption_id": self.rename(row.get("assumption_id", "")),
                "statement": row.get("statement", ""),
                "central_value": row.get("central_value", ""),
                "unit": row.get("unit", ""),
                "evidence_source_ids": self.rename_list(
                    row.get("evidence_source_ids", "")
                ),
                "lower_bound": row.get("lower_bound", ""),
                "upper_bound": row.get("upper_bound", ""),
                "rationale": row.get("rationale", ""),
                "notes": self.fold_notes("assumptions", row),
            }
            for row in self.rows.get("assumptions", [])
        ]

    def calculations(self) -> List[Dict[str, str]]:
        return [
            {
                "calculation_id": self.rename(row.get("calculation_id", "")),
                "formula": row.get("formula", ""),
                "source_ids": self.rename_list(row.get("source_ids", "")),
                "assumption_ids": self.rename_list(row.get("assumption_ids", "")),
                "input_calculation_ids": self.rename_list(
                    row.get("input_calculation_ids", "")
                ),
                "input_values": row.get("input_values", ""),
                "input_units": row.get("input_units", ""),
                "output_value": row.get("output_value", ""),
                "output_unit": row.get("output_unit", ""),
                "script_path": row.get("script_path", ""),
                "script_version": row.get("script_version", ""),
                "notes": self.fold_notes("calculations", row),
            }
            for row in self.rows.get("calculations", [])
        ]

    def model_map(self) -> List[Dict[str, str]]:
        out = []
        disagreements: Dict[Tuple[str, str], int] = {}
        for row in self.rows.get("parameters", []):
            evidence = self.rename_list(
                row.get("source_ids", ""),
                row.get("calculation_id", ""),
                row.get("assumption_ids", ""),
            )
            derived = self._derive_evidence_type(evidence)
            declared = row.get("evidence_type", "").strip().lower()
            extra: List[str] = []
            if declared and declared != derived:
                # The registers use a four-type vocabulary that admits ``proxy`` and
                # requires a calculation behind an ``estimated`` value. The ledger
                # instead derives the type from lineage and rejects a stored value
                # that disagrees, so the declaration moves into notes — §5 of
                # source-traceability.md still wants a proxy labelled as one.
                extra.append(f"declared_evidence_type={declared}")
                key = (declared, derived or "nothing")
                disagreements[key] = disagreements.get(key, 0) + 1
            out.append(
                {
                    "map_id": self.rename(row.get("parameter_record_id", "")),
                    "model_file": row.get("model_file", ""),
                    "parameter": row.get("parameter", ""),
                    "entity": row.get("entity", ""),
                    "mode": row.get("mode", ""),
                    "scenario": row.get("scenario", ""),
                    "years": self._years(row),
                    "value_or_expression": row.get("value_expression", ""),
                    "model_unit": row.get("model_unit", ""),
                    "evidence_ids": evidence,
                    "superseded_by": row.get("superseded_by", ""),
                    "evidence_type": derived,
                    "notes": self.fold_notes("parameters", row, extra),
                }
            )
        for (declared, derived), count in sorted(disagreements.items()):
            self.notes.append(
                f"{count} parameter row(s) declare evidence_type={declared} where the "
                f"lineage makes it {derived}; MODEL_MAP carries the derived type and "
                "keeps the declaration as declared_evidence_type"
            )
        return out

    # Prefix -> canonical type, in the order the canonical validator resolves them:
    # a calculation anywhere in the lineage wins, then an assumption, then a source.
    CANONICAL_TYPE_BY_PREFIX = (
        ("CALC_", "derived"),
        ("ASM_", "estimated"),
        ("SRC_", "direct"),
    )

    @classmethod
    def _derive_evidence_type(cls, evidence: str) -> str:
        tokens = provenance.split_ids(evidence)
        for prefix, derived in cls.CANONICAL_TYPE_BY_PREFIX:
            if any(token.startswith(prefix) for token in tokens):
                return derived
        return ""

    @staticmethod
    def _years(row: Dict[str, str]) -> str:
        start = row.get("year_start", "")
        end = row.get("year_end", "")
        if start and end and start != end:
            return f"{start}-{end}"
        return start or end

    def gaps(self) -> List[Dict[str, str]]:
        """Collect deliberately absent items from two registers.

        ``item`` is the key of GAPS.csv, so it is qualified with the subsector and
        then, only if still ambiguous, with the register's own ID.
        """
        collected: List[Tuple[str, Dict[str, str]]] = []
        for row in self.rows.get("completeness", []):
            status = row.get("status", "").strip().lower()
            if status not in ("data_gap", "not_applicable"):
                continue
            label = row.get("parameter_or_flow", "") or row.get("item_id", "")
            subsector = row.get("subsector", "")
            # ``why_absent`` must be the reason, not a restatement of the status, so
            # the register's own explanation is preferred and the status is only a
            # last resort.
            why = row.get("data_gap", "")
            notes = row.get("notes", "")
            if not why and notes:
                why, notes = notes, ""
            if not why:
                applicability = row.get("applicability", "")
                why = (
                    f"status={status}"
                    + (f"; applicability={applicability}" if applicability else "")
                )
                self.notes.append(
                    f"{row.get('item_id', label)} has status={status} but states no "
                    "reason; GAPS.csv why_absent restates the status until the "
                    "register explains it"
                )
            collected.append(
                (
                    row.get("item_id", ""),
                    {
                        "item": f"{subsector}: {label}" if subsector else label,
                        "why_absent": why,
                        "upgrade_source": row.get("upgrade_source", ""),
                        "priority": row.get("priority", ""),
                        "notes": notes,
                    },
                )
            )
        for row in self.rows.get("boundaries", []):
            include = row.get("include_status", "").strip().lower()
            if not include.startswith(EXCLUDED_PREFIXES):
                continue
            origin = row.get("origin_statistical_sector", "")
            action = row.get("double_count_action", "").strip()
            # Same rule as above: the register's own explanation leads, and the
            # boundary bookkeeping only qualifies it. "Excluded" is a restatement.
            reason = row.get("notes", "").strip()
            clauses = [reason or "excluded from the Fisheries boundary"]
            if origin:
                clauses.append(f"retained by {origin}")
            if action and action.lower() not in ("none", "n/a", "na"):
                clauses.append(f"double_count_action={action}")
            if not reason:
                self.notes.append(
                    f"{row.get('boundary_record_id', '') or row.get('flow', '')} is "
                    "excluded but states no reason; GAPS.csv why_absent restates the "
                    "exclusion until the register explains it"
                )
            collected.append(
                (
                    row.get("boundary_record_id", ""),
                    {
                        "item": row.get("flow", ""),
                        "why_absent": "; ".join(clauses),
                        "upgrade_source": "",
                        "priority": "",
                        "notes": "",
                    },
                )
            )
        counts: Dict[str, int] = {}
        for _, gap in collected:
            counts[gap["item"]] = counts.get(gap["item"], 0) + 1
        out = []
        for identifier, gap in collected:
            if counts.get(gap["item"], 0) > 1 and identifier:
                gap["item"] = f"{gap['item']} [{identifier}]"
            out.append(gap)
        return out

    # ------------------------------------------------------------ writing

    def write(self, force: bool) -> Dict[str, int]:
        projected = {
            "SOURCES.csv": self.sources(),
            "ASSUMPTIONS.csv": self.assumptions(),
            "CALCULATIONS.csv": self.calculations(),
            "MODEL_MAP.csv": self.model_map(),
            "GAPS.csv": self.gaps(),
        }
        self.out.mkdir(parents=True, exist_ok=True)
        written = {}
        for table, rows in projected.items():
            path = self.out / table
            payload = self._render(table, rows)
            if path.is_file() and not force:
                current = path.read_text(encoding="utf-8")
                if current != payload and _has_rows(current):
                    self.errors.append(
                        f"{table} already holds rows that differ from the projection; "
                        "re-run with --force once you have confirmed the registers "
                        "are the source of truth"
                    )
                    continue
            path.write_text(payload, encoding="utf-8")
            written[table] = len(rows)
        # CHANGES.csv is a log: created empty, never regenerated.
        changes = self.out / "CHANGES.csv"
        if not changes.is_file():
            changes.write_text(self._render("CHANGES.csv", []), encoding="utf-8")
            written["CHANGES.csv"] = 0
        return written

    @staticmethod
    def _render(table: str, rows: Iterable[Dict[str, str]]) -> str:
        columns = list(provenance.REQUIRED_COLUMNS[table]) + list(
            provenance.OPTIONAL_COLUMNS.get(table, ())
        )
        lines: List[str] = []
        import io

        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer, fieldnames=columns, lineterminator="\n", extrasaction="ignore"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
        lines.append(buffer.getvalue())
        return "".join(lines)

    def append_change(self, args: argparse.Namespace) -> str | None:
        """Append one CHANGES.csv row, filling map_rows_affected from the ledger."""
        path = self.out / "CHANGES.csv"
        _, existing = provenance.read_table(path)
        if any(row.get("change_id") == args.change_id for row in existing):
            self.errors.append(
                f"CHANGES.csv already has {args.change_id}; a change log is "
                "append-only, so choose a new change_id"
            )
            return None
        _, map_rows = provenance.read_table(self.out / "MODEL_MAP.csv")
        known = [row["map_id"] for row in map_rows]
        selector = (args.change_map_rows or "active").strip()
        if selector == "active":
            affected = [
                row["map_id"] for row in map_rows if not row.get("superseded_by", "")
            ]
        elif selector == "all":
            affected = known
        elif selector == "retired":
            # What a retirement change must list: the rows this very change retired.
            affected = [
                row["map_id"]
                for row in map_rows
                if row.get("superseded_by", "") == args.change_id
            ]
        elif selector == "none":
            affected = []
        else:
            affected = provenance.split_ids(selector)
            unknown = [item for item in affected if item not in known]
            if unknown:
                self.errors.append(
                    "--change-map-rows lists {0}, which MODEL_MAP.csv does not "
                    "contain".format(", ".join(unknown))
                )
                return None
        row = {
            "change_id": args.change_id,
            "date": args.change_date,
            "class": args.change_class,
            "description": args.change_description,
            "model_objects": args.model_objects,
            "evidence_path": args.evidence_path,
            "map_rows_affected": "; ".join(affected),
            "resolve_status": args.resolve_status,
            "author": args.author,
            "commit": args.commit,
            "notes": "",
        }
        columns = list(provenance.REQUIRED_COLUMNS["CHANGES.csv"]) + list(
            provenance.OPTIONAL_COLUMNS.get("CHANGES.csv", ())
        )
        with path.open("a", newline="", encoding="utf-8") as handle:
            csv.DictWriter(
                handle, fieldnames=columns, lineterminator="\n", extrasaction="ignore"
            ).writerow(row)
        return f"{args.change_id} ({len(affected)} MODEL_MAP rows)"


def _has_rows(text: str) -> bool:
    return len([line for line in text.splitlines() if line.strip()]) > 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--registers",
        type=Path,
        default=Path("."),
        help="directory holding the eight Fisheries registers",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data_sources"),
        help="directory to write the six canonical tables into",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite canonical tables that already hold differing rows",
    )
    parser.add_argument(
        "--copy-evidence",
        action="store_true",
        help="copy retained source files under OUT/evidence/ so their digests can "
        "be verified against bytes beneath the ledger",
    )
    parser.add_argument("--id-map", type=Path, help="write the ID mapping as JSON")
    parser.add_argument("--change-id", help="append this CHG_ row to CHANGES.csv")
    parser.add_argument("--change-date", default="", help="ISO date of the change")
    parser.add_argument("--change-class", default="B", choices=("A", "B", "C"))
    parser.add_argument("--change-description", default="")
    parser.add_argument("--model-objects", default="")
    parser.add_argument("--evidence-path", default="")
    parser.add_argument(
        "--resolve-status",
        default="resolved",
        choices=("objective_unchanged", "resolve_required", "resolved"),
    )
    parser.add_argument("--author", default="")
    parser.add_argument("--commit", default="")
    parser.add_argument(
        "--change-map-rows",
        default="active",
        metavar="active|all|retired|none|MAP_ID;…",
        help=(
            "which MODEL_MAP IDs the appended change lists as affected: the live rows "
            "(default), every row, the rows this change retires, none, or an explicit "
            "list — which is checked against MODEL_MAP.csv"
        ),
    )
    args = parser.parse_args(argv)

    projection = Projection(
        args.registers.expanduser(), args.out.expanduser(), args.copy_evidence
    )
    projection.read_registers()
    projection.build_id_map()
    written = projection.write(args.force)

    appended = None
    if args.change_id:
        if not args.change_date:
            projection.errors.append("--change-id requires --change-date")
        else:
            appended = projection.append_change(args)

    if args.id_map:
        args.id_map.parent.mkdir(parents=True, exist_ok=True)
        args.id_map.write_text(
            json.dumps(projection.id_map, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    print(f"Projected {args.registers} -> {args.out}")
    for table in provenance.LEDGER_TABLES:
        if table in written:
            print(f"  {table}: {written[table]} row(s)")
    if appended:
        print(f"  CHANGES.csv: appended {appended}")
    for copied in projection.copied:
        print(f"  copied retained evidence: {copied}")
    if projection.notes:
        print("\nTranslation notes — what did not carry across verbatim:")
        for note in dict.fromkeys(projection.notes):
            print(f"  - {note}")
    if projection.errors:
        print("\nErrors:", file=sys.stderr)
        for error in dict.fromkeys(projection.errors):
            print(f"  - {error}", file=sys.stderr)
        return 1
    print("\nNext: python scripts/validate_ledger.py " + str(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
