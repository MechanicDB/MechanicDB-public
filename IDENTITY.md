# Stable identifiers

Since edition 2026.10 the identity contract keeps the existing numeric code_id,
fault_id, fix_id and part_id values across expansion and editorial changes; the
paid editions and this sample ship its companion files. The sample's exact
edition is identified by its `identity_metadata.json`, not the monthly badge.

IDs are sparse and meaningful only within domain and entity type. Use qualified
references such as `mechanicdb:v1:obd:fix:571` or
`mechanicdb:v1:hd:fix:571` for external annotations. A DTC alone does not identify
an OEM definition; an SPN/FMI pair alone does not identify a source/controller
fault assertion. Tier, locale, CSV/Parquet/SQLite encoding and display order do
not renumber rows. Fix IDs identify procedures under one code/fault; part IDs
identify authored component suggestions under one fix, not universal SKUs or
verified vehicle fitment.

The core schema and SQLite version 1 remain unchanged. Numeric tables export in
permanent-ID order; procedures display by probability_rank, with numeric CAST for
Standard TEXT SQL. That rank retains the I01 authored consideration-order meaning
and is never an identity or a measured probability.

| Companion | Purpose |
| --- | --- |
| identity_metadata.json | immutable shared data release ID, exact artifact fingerprint, domain/profile and registry digest |
| identity_map.csv / .parquet | entitled row references, decimal-text numeric aliases, parent references, authored procedure/part-use keys and content revision digests |
| identity_events.csv | relevant lifecycle information; public samples exclude unrelated and withdrawn content |

Descriptions, rank, costs and component names can change without changing their
intended identity. Withdrawn or retired identities remain reserved. Reinstatement
recovers the same issued identity; merge/split changes require reviewed migration.
Content digests detect revisions and do not allocate IDs. Public maps contain
only the fixed free samples; the private allocation ledger is not distributed.
The actor keeps its default response shape and can opt into qualified references
and the immutable release ID with `include_identity: true`.

Historical bare integers are release-scoped aliases. Two known September 2026
HD artifacts reused fault 571 for different entities after a source withdrawal.
The month alone cannot disambiguate them. Verified crosswalks use exact artifact
fingerprints or verified source-release IDs. Available Git table history is
explicitly distinguished from evidence of an actually delivered package; missing
old editions and changed/nonunique procedures remain unresolved.

Back up your annotations, identify the exact original artifact, and run the
provided migration report. It preserves original IDs/source and reports
unresolved/ambiguous/merge/split cases instead of guessing. Automatically carry
only one-to-one exact/reviewed mappings. Obtain the appropriate licensed
crosswalk/catalogue from support; historical licensed data is not in this sample.
Load each complete snapshot into staging, validate joins and companions, then
switch your application transactionally. Retain annotations on inactive targets.

With a licensed catalogue/crosswalk directory, run the standalone example:

```sh
python scripts/migrate_annotations.py notes.jsonl --identity-dir licensed-history --source EXACT_ARTIFACT --report report.json
```

The default produces a report only. `--apply NEW_FILE` writes a new annotation
copy and refuses to overwrite existing files.


Paid packages and the actor ship the filtered Parquet identity map to satisfy
the unchanged 25 MiB ZIP limit and keep actor bundles compact. Generated master directories and public
samples retain both map formats. The declared sha256-128 content digest is a
revision detector, with full SHA-256 checksums for files/registry/releases.

The pinned old public OBD sample had 42 conflicting fix aliases and 61 part
aliases; its exact 859-row historical crosswalk preserves every intended entity.
The regenerated sample uses paid-master allocations. Private/Kaggle samples
already match those allocations. Content, ranks, sample membership and counts
are unchanged. Legacy sample numeric aliases require their pinned artifact.

## Scoped migration support and revision pins

For the old public OBD sample, use its exact artifact fingerprint:
`sample-tables-sha256-176d6921520e0bc28720a801ece4308775df5a39ce8bc5aa246cdc5fd7bdc1cc`.
The sample-only support bundle contains the standalone Python migration tool,
instructions, a scoped catalogue and the complete 859-row pinned crosswalk.
It corrects the 42 fix and 61 part aliases above. It contains no private registry,
paid tables, unrelated customer history or withdrawn source content.

From the extracted bundle, run:

```sh
python migrate_annotations.py notes.jsonl --source sample-tables-sha256-176d6921520e0bc28720a801ece4308775df5a39ce8bc5aa246cdc5fd7bdc1cc --identity-dir identity --report report.json
```

Review the report before optionally adding `--apply NEW-notes.jsonl`. Original
annotations remain intact. Verify the bundle manifest/checksums through the
trusted channel supplying it. A historical Git artifact alone does not prove
that a customer received that snapshot. Month-only identifiers remain insufficient.

The tool now supports explicit catalogue revision/path pins. Select a retained
revision using `--crosswalk-revision original`; default selection follows the
catalogue. Reports preserve the selected revision/path/checksum. Legacy catalogues
remain compatible. Tampered crosswalk/evidence bytes, conflicting revision pins
and paths escaping the supplied identity directory are rejected. Customer bundles
must be scoped to the verified original artifact and recipient entitlement.
