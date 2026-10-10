# Heavy Duty configuration applicability (staged)

This is an incoming contract and reference consumer, not a released EC-60
content correction. Current snapshots have no applicability declaration. The
helper reports `metadata_unavailable` for them. Production activation requires
reviewed content and a verified coordinated rebuild; no publication is implied.

Fault IDs and existing core columns stay stable. HD SQLite v2 adds four relational
companions; Standard/OEM SQLite remains v1. Historical HD v1 can be browsed with
the explicit limitation above. Strict readers must opt into v2.

| Table | Columns |
| --- | --- |
| hd_applicability_contexts | context_key, dimension_key, value_key, context_label |
| hd_fault_contexts | fault_id, context_key, source_id, source_sha256, source_pages |
| hd_fix_contexts | fix_id, fault_id, context_key |
| hd_part_contexts | part_id, fix_id, context_key |

Keys are persistent authored identifiers. Supply a verified installed
configuration; never infer it from SPN, rank, labels or component names. Fault
membership declares complete review of its emitted guidance for one documented
dimension, with at least two values. Coverage remains partial across the corpus.
Parts must belong to the declared parent fix and context. An empty part list
means no documented suggestion, not that replacement is never needed.

| State | Result |
| --- | --- |
| Exact covered fault, supported verified context | matched guidance and eligible parts |
| Configuration unknown | configuration_required; labeled alternatives, empty selected lists |
| Uncovered fault in valid metadata | not_assessed; existing guidance explicitly unassessed |
| Unsupported or conflicting context | invalid_context; no selected guidance |
| Broad lookup matches multiple faults | ambiguous_fault; require exact selection |
| Legacy snapshot without declaration | metadata_unavailable |
| Declared files missing, mixed or corrupt | validation error |

The standalone standard-library helper accepts CSV directories or HD SQLite
files and verifies declared file checksums, release binding and relationships:

```sh
python scripts/lookup_heavyduty.py /path/to/licensed/heavyduty --fault-id YOUR_FAULT_ID
python scripts/lookup_heavyduty.py /path/to/licensed/mechanicdb-heavyduty.sqlite --fault-id YOUR_FAULT_ID --context VERIFIED_CONTEXT_KEY
python scripts/lookup_heavyduty.py /path/to/licensed/heavyduty --spn YOUR_SPN --fmi YOUR_FMI
```

Core CSV and Parquet queries still work. Guidance restricted to a configuration
must also state the condition in its title/instructions for older consumers.
The probability_rank is authored display order, not probability or fitment.
Filtered ranks retain their original values, including gaps; do not renumber.

For Parquet, first validate the companion declaration using the helper. Then
check full Parquet/CSV membership parity and perform an explicit join:

```python
from pathlib import Path
import pandas as pd
from scripts.lookup_heavyduty import load_dataset, lookup, SCHEMAS, normalize

root = Path("/path/to/licensed/heavyduty")
core, membership, metadata = load_dataset(root)
for table in SCHEMAS:
    frame = pd.read_parquet(root / f"{table}.parquet")
    assert normalize(table, frame.to_dict("records")) == membership[table]

# Use an exact fault and a verified key supplied by the caller.
selected = lookup(core, membership, metadata,
                  fault_id=fault_id, contexts=[verified_context_key])
if selected["applicability_status"] == "matched":
    fixes = pd.read_parquet(root / "diagnostic_fixes.parquet")
    links = pd.read_parquet(root / "hd_fix_contexts.parquet")
    ids = links.loc[(links.fault_id == fault_id) &
                    (links.context_key == verified_context_key), "fix_id"]
    eligible = fixes.loc[fixes.fix_id.isin(ids)].sort_values("probability_rank")
```

Use semijoins when showing multiple conditional alternatives; do not multiply
fix counts or cost totals by membership rows. SQLite consumers likewise precheck
fault/context membership before selecting fixes, then eligible parts through
their explicit parent links.

Applicability revision and data_release_id detect configuration guidance changes.
Existing identity-map content_digest retains its core-row meaning. Vendor
snapshots should be replaced transactionally after backup; customer annotations
on retired fix/part references stay attached to those historical references.
There is no automatic annotation transfer to a new component-specific procedure.

Fixed sample membership is preserved. The two proposed EC-60 faults are outside
the free sample; activation must emit typed empty sample companions and no unused
paid context definitions. The SAE-only Apify actor does not gain HD access.
