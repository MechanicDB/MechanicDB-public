"""Read-only by default migration of customer JSONL annotations.

Each input requires domain, entity_type, legacy_numeric_id. --source accepts an
exact verified table artifact, catalogue release, or month (reported ambiguous).
--apply writes a NEW customer file only; source annotations/vendor tables stay intact.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

DIRECTORY = Path(__file__).resolve().parents[1] / "data/curated/identity"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def safe_path(directory, relative):
    """Catalogue paths are portable relative paths confined to the bundle."""
    if not isinstance(relative, str) or "\\" in relative or ":" in relative:
        raise ValueError("unsafe catalogue path")
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts or any(p in {"..", "."} for p in relative.split("/")):
        raise ValueError("unsafe catalogue path")
    target = (Path(directory) / relative).resolve()
    if not target.is_relative_to(Path(directory).resolve()):
        raise ValueError("unsafe catalogue path")
    return target


def crosswalk_spec(edition, revision=None):
    default = dict(crosswalk_revision=edition.get("crosswalk_revision", "original"),
                   crosswalk_path=edition.get("crosswalk_path", "legacy_crosswalks/" + edition["source_artifact_id"] + ".jsonl"),
                   crosswalk_sha256=edition["crosswalk_sha256"])
    for field in ("evidence_path", "evidence_sha256"):
        if field in edition:
            default[field] = edition[field]
    revisions = edition.get("crosswalk_revisions", [])
    names = [r["crosswalk_revision"] for r in revisions]
    if len(names) != len(set(names)):
        raise ValueError("ambiguous crosswalk revision")
    declared_default = [r for r in revisions if r["crosswalk_revision"] == default["crosswalk_revision"]]
    if declared_default and declared_default[0] != default:
        raise ValueError("ambiguous catalogue revision selection")
    if revision is None or revision == default["crosswalk_revision"]:
        return default
    choices = [r for r in revisions if r["crosswalk_revision"] == revision]
    if len(choices) != 1:
        raise ValueError("unknown/ambiguous crosswalk revision")
    return choices[0]


def migration_report(annotations, source, directory=DIRECTORY, revision=None):
    directory = Path(directory)
    catalogue = [json.loads(line) for line in (directory / "releases.jsonl").read_text(encoding="utf-8").splitlines()]
    editions = [r for r in catalogue if source in (r["source_artifact_id"], r["source_release_id"], r["month"])]
    artifacts = sorted({r["source_artifact_id"] for r in editions})
    maps = {}
    selected = {}
    for artifact in artifacts:
        specs = [crosswalk_spec(r, revision) for r in editions if r["source_artifact_id"] == artifact]
        if len({canonical(r) for r in specs}) != 1:
            raise ValueError("ambiguous catalogue revision selection")
        spec = specs[0]
        selected[artifact] = spec
        path = safe_path(directory, spec["crosswalk_path"])
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != spec["crosswalk_sha256"]:
            raise ValueError("unpinned/altered legacy crosswalk")
        if "evidence_path" in spec:
            evidence = safe_path(directory, spec["evidence_path"]).read_bytes()
            if hashlib.sha256(evidence).hexdigest() != spec["evidence_sha256"]:
                raise ValueError("unpinned/altered review evidence")
        for line in raw.decode("utf-8").splitlines():
            row = json.loads(line)
            if row["source_artifact_id"] != artifact:
                raise ValueError("crosswalk artifact scope mismatch")
            key = (artifact, row["domain"], row["entity_type"], row["legacy_numeric_id"])
            if key in maps:
                raise ValueError("duplicate/ambiguous crosswalk key")
            maps[key] = row
    results = []
    for annotation in annotations:
        domain, kind, legacy = annotation["domain"], annotation["entity_type"], str(annotation["legacy_numeric_id"])
        if domain not in {"obd", "hd"} or kind not in {"code", "fault", "fix", "part"} or not legacy.isdecimal():
            raise ValueError("annotation requires explicit valid domain/entity/numeric ID")
        candidates = [maps[artifact, domain, kind, legacy] for artifact in artifacts if (artifact, domain, kind, legacy) in maps]
        status = "unresolved"
        target = ""
        if len(artifacts) > 1:
            status = "ambiguous_release"
        elif len(candidates) == 1 and candidates[0]["mapping_status"] in {"exact", "reviewed"}:
            status = candidates[0]["availability"] if candidates[0].get("availability") in {"merged", "split"} else candidates[0]["mapping_status"]
            target = candidates[0]["canonical_entity_ref"]
        elif len(candidates) == 1:
            status = candidates[0]["mapping_status"]
        results.append(dict(original=annotation, source=source, status=status, entity_ref=target,
                            candidates=candidates, manual_review=status not in {"exact", "reviewed"}))
    return dict(source=source, crosswalk_revision=revision or "catalogue-default", selected_crosswalks=selected, candidate_artifacts=artifacts, total=len(results),
                automatically_mappable=sum(not r["manual_review"] for r in results), results=results)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--crosswalk-revision", help="explicit pinned revision; default is catalogue selection")
    parser.add_argument("--identity-dir", type=Path, default=DIRECTORY,
                        help="directory containing licensed releases.jsonl and legacy_crosswalks/")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--apply", type=Path, help="new customer annotation file; refuses overwrite")
    args = parser.parse_args(argv)
    annotations = [json.loads(line) for line in args.annotations.read_text(encoding="utf-8").splitlines()]
    report = migration_report(annotations, args.source, args.identity_dir, args.crosswalk_revision)
    # Reports are also explicit new files, preventing accidental overwrite of input.
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    if args.apply:
        with args.apply.open("x", encoding="utf-8") as stream:
            for result in report["results"]:
                record = dict(result["original"], migration=result)
                if not result["manual_review"]:
                    record["entity_ref"] = result["entity_ref"]
                stream.write(canonical(record)+"\n")
    print(f"{'Applied to new file' if args.apply else 'Dry run'}: {report['automatically_mappable']}/{report['total']} exact/reviewed; inspect {args.report}")


if __name__ == "__main__":
    main()
