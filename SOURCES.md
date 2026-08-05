# Data Provenance & Licensing

## Code spine (dtc_code, short_description)

- **Source:** https://github.com/Wal33D/dtc-database
  (generic SAE files `data/source-data/{p,b,c,u}_codes.txt`)
- **License:** MIT. The MIT license permits commercial use, modification, and
  redistribution. A verbatim copy of the upstream license notice is committed
  in this repository at `LICENSE-upstream.txt`; attribution is provided here.
- **Fetched:** 2026-07-06 via the MechanicDB build pipeline.
- **Transformations applied:** filtered to SAE-controlled generic ranges
  (`P0`, `P2`, `P34x–P39x`, `C0`, `B0`, `U0`, `U3`), dropped `Reserved`
  placeholders, deduplicated, normalized linebreaks, derived
  `system_category` from the code letter.
- **Underlying facts:** OBD-II code assignments and definitions originate in
  SAE J2012 / ISO 15031-6. Individual code-to-definition mappings are facts;
  facts are not subject to copyright. The SAE standard document text itself
  is NOT reproduced in this dataset.

## OEM code spine (oem_make, dtc_code, short_description)

- **Source:** the same Wal33D/dtc-database compilation — 32 per-marque files,
  upstream MIT license at `LICENSE-upstream.txt`. This sample includes 15 of
  the full dataset's 6,637 OEM codes so the OEM columns are populated here too.
- **Kept:** manufacturer-controlled ranges only (`P1`, `P30–P33`, `C1/C2`,
  `B1/B2`, `U1/U2`). Generic-range lines in brand files are dropped — the SAE
  spine above is the sole authority for generic ranges.
- **Excluded:** `other_codes.txt` (definitions with no brand attribution —
  manufacturer-range codes are meaningless without the make).
- **Badge engineering:** marques within an engineering group (GM's seven
  marques, Ford/Mercury/Lincoln, Honda/Acura, …) share most definitions; rows
  are kept per marque so make-filtered lookups work as buyers expect.

## Authored content (all other columns)

`detailed_technical_explanation`, fault families, ranked fixes, difficulty
ratings, cost/labor estimates, step-by-step instructions, and part mappings
are original content authored for MechanicDB. Cost and labor figures are
editorial estimates for typical aftermarket parts and independent-shop labor
in the US market; they are not quotes.

## Dataset license

This free sample is offered under ODbL v1.0; the full database is available
under commercial license tiers (see README.md and the LICENSE file).
