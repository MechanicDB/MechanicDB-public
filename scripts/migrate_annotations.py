"""Read-only by default migration of customer JSONL annotations.

Each input requires domain, entity_type, legacy_numeric_id. --source accepts an
exact verified table artifact, catalogue release, or month (reported ambiguous).
--apply writes a NEW customer file only; source annotations/vendor tables stay intact.
"""
import argparse
import hashlib
import json
from pathlib import Path

DIRECTORY = Path(__file__).resolve().parents[1] / "data/curated/identity"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def migration_report(annotations, source, directory=DIRECTORY):
    directory = Path(directory)
    catalogue = [json.loads(line) for line in (directory / "releases.jsonl").read_text(encoding="utf-8").splitlines()]
    editions = [r for r in catalogue if source in (r["source_artifact_id"], r["source_release_id"], r["month"])]
    artifacts = sorted({r["source_artifact_id"] for r in editions})
    maps = {}
    for artifact in artifacts:
        path = directory / "legacy_crosswalks" / (artifact + ".jsonl")
        raw = path.read_bytes()
        pins = {r.get("crosswalk_sha256") for r in editions if r["source_artifact_id"] == artifact}
        if hashlib.sha256(raw).hexdigest() not in pins:
            raise ValueError("unpinned/altered legacy crosswalk")
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
    return dict(source=source, candidate_artifacts=artifacts, total=len(results),
                automatically_mappable=sum(not r["manual_review"] for r in results), results=results)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotations", type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--identity-dir", type=Path, default=DIRECTORY,
                        help="directory containing licensed releases.jsonl and legacy_crosswalks/")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--apply", type=Path, help="new customer annotation file; refuses overwrite")
    args = parser.parse_args(argv)
    annotations = [json.loads(line) for line in args.annotations.read_text(encoding="utf-8").splitlines()]
    report = migration_report(annotations, args.source, args.identity_dir)
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
