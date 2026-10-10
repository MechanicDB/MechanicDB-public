"""Read-only HD CSV/SQLite reference lookup; standard library only.

Run outside either repository: python lookup_heavyduty.py DATASET --fault-id 262
Add --context KEY only after verifying installed output configuration.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3

CONTRACT = "mechanicdb-hd-applicability:v1"
SCHEMAS = {
    "hd_applicability_contexts": "context_key dimension_key value_key context_label".split(),
    "hd_fault_contexts": "fault_id context_key source_id source_sha256 source_pages".split(),
    "hd_fix_contexts": "fix_id fault_id context_key".split(),
    "hd_part_contexts": "part_id fix_id context_key".split(),
}
KEY = re.compile(r"[a-z][a-z0-9_-]*\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
IDS = {"fault_id", "fix_id", "part_id"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def revision(tables):
    payload = {name: sorted(rows, key=canonical) for name, rows in tables.items() if name in SCHEMAS}
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def normalize(name, rows):
    result = []
    for row in rows:
        if set(row) != set(SCHEMAS[name]):
            raise ValueError(f"{name}: columns/order differ")
        converted = {}
        for field, value in row.items():
            if field in IDS:
                if isinstance(value, bool) or not re.fullmatch(r"[1-9][0-9]*", str(value)) or int(value) > 9223372036854775807:
                    raise ValueError(f"{name}: invalid {field}")
                converted[field] = int(value)
            else:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{name}: blank/non-text {field}")
                if field.endswith("_key") or field == "source_id":
                    if not KEY.fullmatch(value):
                        raise ValueError(f"{name}: invalid key {field}")
                if field == "source_sha256" and not HASH.fullmatch(value):
                    raise ValueError(f"{name}: invalid evidence hash")
                if field == "source_pages":
                    if not re.fullmatch(r"[1-9][0-9]*(,[1-9][0-9]*)*", value):
                        raise ValueError(f"{name}: invalid pages")
                    pages = list(map(int, value.split(",")))
                    if pages != sorted(set(pages)):
                        raise ValueError(f"{name}: noncanonical pages")
                converted[field] = value
        result.append(converted)
    return result


def validate_memberships(tables, core):
    if set(tables) != set(SCHEMAS):
        raise ValueError("applicability table surface differs")
    tables = {name: normalize(name, rows) for name, rows in tables.items()}
    contexts = tables["hd_applicability_contexts"]
    faults = tables["hd_fault_contexts"]
    fixes = tables["hd_fix_contexts"]
    parts = tables["hd_part_contexts"]
    for rows, fields in [(contexts, ["context_key"]), (contexts, ["dimension_key", "value_key"]),
                         (faults, ["fault_id", "context_key"]), (fixes, ["fix_id", "context_key"]),
                         (parts, ["part_id", "context_key"])]:
        keys = [tuple(row[f] for f in fields) for row in rows]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate applicability relationship")
    catalogue = {row["context_key"]: row for row in contexts}
    fault_core = {int(row["fault_id"]): row for row in core["j1939_faults"]}
    fix_core = {int(row["fix_id"]): int(row["fault_id"]) for row in core["diagnostic_fixes"]}
    part_core = {int(row["part_id"]): int(row["fix_id"]) for row in core["replacement_parts"]}
    fc = {(r["fault_id"], r["context_key"]) for r in faults}
    xc = {(r["fix_id"], r["context_key"]) for r in fixes}
    for row in faults:
        fault = fault_core.get(row["fault_id"])
        if fault is None or row["context_key"] not in catalogue or fault["source_id"] != row["source_id"]:
            raise ValueError("fault/context/source relationship differs")
    if set(catalogue) != {r["context_key"] for r in faults}:
        raise ValueError("unreachable context definition")
    covered = {r["fault_id"] for r in faults}
    for fault in covered:
        values = [catalogue[c] for f, c in fc if f == fault]
        if len({r["dimension_key"] for r in values}) != 1 or len(values) < 2:
            raise ValueError("covered fault requires one dimension and at least two values")
    for row in fixes:
        if fix_core.get(row["fix_id"]) != row["fault_id"] or (row["fault_id"], row["context_key"]) not in fc:
            raise ValueError("fix context outside declared fault/parent")
    for row in parts:
        if part_core.get(row["part_id"]) != row["fix_id"] or (row["fix_id"], row["context_key"]) not in xc:
            raise ValueError("part context outside declared fix/parent")
    if {f for f, fault in fix_core.items() if fault in covered} != {r["fix_id"] for r in fixes}:
        raise ValueError("incomplete fix applicability coverage")
    if {p for p, f in part_core.items() if fix_core.get(f) in covered} != {r["part_id"] for r in parts}:
        raise ValueError("incomplete part applicability coverage")
    return tables


def read_csv(path, fields=None):
    if not path.is_file():
        raise ValueError(f"missing dataset file: {path.name}")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="|")
        if fields is not None and reader.fieldnames != fields:
            raise ValueError(f"{path.name}: columns/order differ")
        return list(reader)


def validate_identity_fingerprint(directory, metadata):
    """Verify the same declared artifact surface as the identity v1 writer."""
    formats = metadata.get("map_formats")
    if metadata.get("identity_contract") != "mechanicdb:v1" or metadata.get("canonicalization") != 1 or formats not in (["csv", "parquet"], ["parquet"]):
        raise ValueError("unknown identity metadata contract")
    names = {"identity_events.csv", "ordering_metadata.json", "mechanicdb.sqlite", "mechanicdb-heavyduty.sqlite", "applicability_metadata.json"}
    names |= {f"identity_map.{fmt}" for fmt in formats}
    tables = ["j1939_fmi", "j1939_spn", "j1939_faults", "diagnostic_fixes", "replacement_parts", "j1939_fixes_joined"] + list(SCHEMAS)
    for table in tables:
        for fmt in ("csv", "parquet"):
            names |= {f"{table}.{fmt}", f"{fmt}/{table}.{fmt}"}
    if (directory / "csv").is_dir():
        names |= {p.name for p in directory.iterdir() if p.is_file() and p.suffix.lower() in {".md", ".txt"}}
    checksums = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in sorted(names) if (directory / name).is_file()}
    unsigned = {k: v for k, v in metadata.items() if k != "artifact_id"}
    expected = "mechanicdb-artifact-v1-" + hashlib.sha256(canonical(dict(metadata=unsigned, files=checksums)).encode("utf-8")).hexdigest()
    if metadata.get("artifact_id") != expected:
        raise ValueError("identity artifact fingerprint mismatch")


def normalize_core(core):
    """CSV decimal scalars and SQLite numeric scalars have one response shape."""
    integers = IDS | {"spn", "fmi", "probability_rank"}
    reals = {"est_parts_cost_min_usd", "est_parts_cost_max_usd", "est_labor_hours"}
    for rows in core.values():
        for row in rows:
            for field in integers & set(row):
                value = row[field]
                low = 0 if field == "fmi" else 1
                high = 31 if field == "fmi" else 524287 if field == "spn" else 9223372036854775807
                if isinstance(value, bool) or not re.fullmatch(r"0|[1-9][0-9]*", str(value)) or not low <= int(value) <= high:
                    raise ValueError(f"invalid core integer: {field}")
                row[field] = int(value)
            for field in reals & set(row):
                value = float(row[field])
                if not math.isfinite(value) or value < 0:
                    raise ValueError(f"invalid core estimate: {field}")
                row[field] = value
    return core


def load_dataset(path):
    path = Path(path)
    sql = path.is_file()
    directory = path.parent if sql else path
    manifest_path = directory / "applicability_metadata.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    if manifest is not None and sql and path.name != "mechanicdb-heavyduty.sqlite":
        raise ValueError("declared HD SQLite must use its fingerprinted filename")
    core_names = ["j1939_faults", "diagnostic_fixes", "replacement_parts"]
    if sql:
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as con:
            version = con.execute("PRAGMA user_version").fetchone()[0]
            if version not in (1, 2):
                raise ValueError("unknown HD SQLite schema version")
            if (version == 2) != (manifest is not None):
                raise ValueError("SQLite applicability declaration/version mismatch")
            def read(name):
                cursor = con.execute(f"SELECT * FROM {name}")
                fields = [item[0] for item in cursor.description]
                if name in SCHEMAS and fields != SCHEMAS[name]:
                    raise ValueError("SQLite applicability columns differ")
                return [dict(zip(fields, row)) for row in cursor]
            core = {name: read(name) for name in core_names}
            tables = {name: read(name) for name in SCHEMAS} if manifest else None
    else:
        def location(name):
            flat = directory / f"{name}.csv"
            return flat if flat.exists() else directory / "csv" / f"{name}.csv"
        core = {name: read_csv(location(name)) for name in core_names}
        tables = {name: read_csv(location(name), fields) for name, fields in SCHEMAS.items()} if manifest else None
    core = normalize_core(core)
    if manifest is None:
        if not sql and any((directory / f"{name}.csv").exists() or (directory / "csv" / f"{name}.csv").exists() for name in SCHEMAS):
            raise ValueError("applicability files without declaration")
        return core, None, None
    if (manifest.get("applicability_contract"), manifest.get("selection_semantics"), manifest.get("coverage_mode"), manifest.get("domain")) != (
            CONTRACT, "explicit_context_membership_v1", "partial_fault_coverage", "hd"):
        raise ValueError("unknown applicability contract")
    if manifest.get("tables") != list(SCHEMAS) or manifest.get("formats") != ["csv", "parquet"]:
        raise ValueError("applicability format/table declaration differs")
    identity = json.loads((directory / "identity_metadata.json").read_text(encoding="utf-8"))
    validate_identity_fingerprint(directory, identity)
    if manifest.get("data_release_id") != identity.get("data_release_id") or manifest.get("profile") != identity.get("profile") or identity.get("domain") != "hd":
        raise ValueError("mixed applicability/identity release or profile")
    expected_files = {f"{name}.{fmt}" for name in SCHEMAS for fmt in manifest["formats"]}
    nested = (directory / "csv").is_dir()
    expected_files = {f"{name.rsplit('.', 1)[1]}/{name}" if nested else name for name in expected_files}
    if set(manifest.get("checksums", {})) != expected_files:
        raise ValueError("missing declared applicability pins")
    for name, pin in manifest["checksums"].items():
        candidate = directory / name
        if not candidate.is_file() or hashlib.sha256(candidate.read_bytes()).hexdigest() != pin:
            raise ValueError(f"applicability checksum mismatch: {name}")
    tables = validate_memberships(tables, core)
    if manifest.get("applicability_revision") != revision(tables):
        raise ValueError("applicability logical revision differs")
    counts = {name: len(rows) for name, rows in tables.items()}
    if manifest.get("row_counts") != counts or manifest.get("covered_faults") != len({r["fault_id"] for r in tables["hd_fault_contexts"]}):
        raise ValueError("applicability coverage counts differ")
    return core, tables, manifest


def lookup(core, tables, manifest, fault_id=None, spn=None, fmi=None, contexts=()):
    candidates = [r for r in core["j1939_faults"] if
                  (fault_id is None or int(r["fault_id"]) == int(fault_id)) and
                  (spn is None or int(r["spn"]) == int(spn)) and
                  (fmi is None or int(r["fmi"]) == int(fmi))]
    if fault_id is None and (spn is None or fmi is None):
        raise ValueError("supply exact fault ID or SPN and FMI")
    result = dict(applicability_status="fault_not_found", fixes=[], parts=[], conditional_options=[])
    if len(candidates) != 1:
        result.update(applicability_status="ambiguous_fault" if candidates else "fault_not_found", candidates=candidates)
        return result
    fault = candidates[0]
    fid = int(fault["fault_id"])
    result.update(fault_ref=f"mechanicdb:v1:hd:fault:{fid}", fault=fault)
    all_fixes = sorted([r for r in core["diagnostic_fixes"] if int(r["fault_id"]) == fid], key=lambda r: int(r["probability_rank"]))
    if tables is None:
        result.update(applicability_status="metadata_unavailable", unassessed_fixes=all_fixes)
        return result
    result.update(data_release_id=manifest["data_release_id"], applicability_revision=manifest["applicability_revision"])
    supported = {r["context_key"] for r in tables["hd_fault_contexts"] if r["fault_id"] == fid}
    options = [r for r in tables["hd_applicability_contexts"] if r["context_key"] in supported]
    result["conditional_options"] = sorted(options, key=lambda r: r["context_key"])
    if contexts and (len(contexts) != 1 or contexts[0] not in supported):
        result["applicability_status"] = "invalid_context"
        return result
    if not supported:
        result.update(applicability_status="not_assessed", unassessed_fixes=all_fixes)
        return result
    if not contexts:
        result["applicability_status"] = "configuration_required"
        return result
    context = contexts[0]
    eligible = {r["fix_id"] for r in tables["hd_fix_contexts"] if r["fault_id"] == fid and r["context_key"] == context}
    fixes = [r for r in all_fixes if int(r["fix_id"]) in eligible]
    part_ids = {r["part_id"] for r in tables["hd_part_contexts"] if r["fix_id"] in eligible and r["context_key"] == context}
    ranks = {int(r["fix_id"]): int(r["probability_rank"]) for r in fixes}
    parts = sorted([r for r in core["replacement_parts"] if int(r["part_id"]) in part_ids], key=lambda r: (ranks[int(r["fix_id"])], int(r["part_id"])))
    result.update(applicability_status="matched", selected_context_key=context, fixes=fixes, parts=parts)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--fault-id", type=int)
    parser.add_argument("--spn", type=int)
    parser.add_argument("--fmi", type=int)
    parser.add_argument("--context", action="append", default=[])
    args = parser.parse_args()
    try:
        core, tables, manifest = load_dataset(args.dataset)
        print(json.dumps(lookup(core, tables, manifest, args.fault_id, args.spn, args.fmi, args.context), indent=2, ensure_ascii=False))
    except (ValueError, OSError, sqlite3.Error, KeyError) as exc:
        parser.exit(2, f"Invalid dataset/request: {exc}\n")


if __name__ == "__main__":
    main()
