# Data Provenance & Licensing

This repository holds two free samples: the OBD-II sample (the CSV and Parquet files at the
repository root) and the Heavy Duty (J1939) sample in `samples/heavyduty/`. The first three
sections below cover the OBD-II sample; the Heavy Duty section covers the other.

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

`probability_rank` is the supported legacy name for authored procedure consideration
order, not measured cause likelihood. See the applicable `ordering_metadata.json` sidecar;
the Heavy Duty sample's class-kind mapping is generated from the validated FMI policy.

## Heavy Duty sample (J1939)

- **Files:** `samples/heavyduty/` — 100 fault rows from the MechanicDB Heavy Duty tier with their
  SPNs, ranked fixes, part mappings and the 32-row FMI register, in the same schema as the paid tier
  (DATA_DICTIONARY.md, section 6).
- **Facts:** each SPN/FMI fault pair, OEM fault code (`oem_code`) and controller assignment is a fact
  taken from a fault-code document the manufacturer publishes. Every `j1939_faults` row names its
  document in `source_id`, `source_url` and `source_doc` (plus `source_page` where the document has
  pages); the documents are listed below.
- **Authored content:** `short_description`, `spn_name`, `fmi_name`, `detailed_technical_explanation`,
  fault families, ranked fixes and part mappings are written in DataEngineered's own words. A
  `spn_name` may match the manufacturer's own plain name for the parameter (for example `Engine
  Coolant Temperature`); no sentences from OEM documents are included. Cost and labor figures are
  editorial estimates for US independent heavy-duty shops; they are not quotes and do not come from
  the OEM documents.
- **Not SAE material:** nothing is taken from the SAE J1939 Digital Annex, J1939 DBC files, or
  third-party SPN/FMI tables derived from them. The 32 FMI names are our own paraphrase, not SAE
  text.

### Source documents

The Heavy Duty tier is built from the documents below. The free sample holds rows from those marked
*yes*; rows from the others are in the paid tier only. Sources added to or withdrawn from the tier
are recorded in [CHANGELOG.md](CHANGELOG.md).

| `source_id` | OEM | Controller | Document | URL | In free sample |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `bendix_sd134869` | Bendix | ABS/ESC | SD-13-4869 EC-60 ABS/ATC/ESP service data sheet (2013) | <https://www.bendixvrc.com/itemDisplay.asp?documentID=6735> | yes |
| `bendix_sd134983` | Bendix | ABS/ESC | SD-13-4983 EC-80 ABS/ATC service data sheet (2014) | <https://www.bendixvrc.com/itemDisplay.asp?documentID=6722> | yes |
| `cat_c10882888` | Caterpillar | Engine ECU | 1200 Series marine auxiliary engines troubleshooting guide | <https://s7d2.scene7.com/is/content/Caterpillar/C10882888> | yes |
| `cummins_a042j565` | Cummins | Engine ECU | A042J565 fire pump drive engine IOM, fault code charts | <https://mart.cummins.com/imagelibrary/data/assetfiles/0056191.pdf> | yes |
| `cummins_mddca` | Cummins | Engine ECU | Onan marine generator MDDCA operator manual | <https://www.cummins.com/sites/default/files/2024-07/cummins-onan-manual-marlin.pdf> | yes |
| `eaton_trts0950` | Eaton | Transmission | TRTS0950 Endurant HD fault code index | <https://productinfo.serviceranger4.com/books/TRTS0950/lang/en-us/section/TS0950FCIndex> | yes |
| `eaton_trts0960` | Eaton | Transmission | TRTS0960 Endurant XD fault code index | <https://productinfo.serviceranger4.com/books/TRTS0960/lang/en-us/section/TS0960FCIndex> | yes |
| `deere_omh229936` | John Deere | Engine ECU | OMH229936 9670/9770 STS engine control unit DTCs | <http://manuals.deere.com/omview/OMH229936_19/OUO6075_0000B3D_19_02AUG07_1.htm> | yes |
| `deere_omrg35856` | John Deere | Engine ECU | OMRG35856 PowerTech DTC list | <http://manuals.deere.com/omview/OMRG35856_19/OURGP12,00001FC_19_20100408.html> | yes |
| `navistar_s082504` | Navistar | Body controller | s082504 Electrical System Troubleshooting Guide fault-code XML | <http://bodybuilder.navistar.com/General/documents/s08/s082504_FC.xml> | no |
| `navistar_s08327` | Navistar | Body controller | S08327 Body Controller Diagnostic Trouble Codes (2010) | <http://bodybuilder.navistar.com/General/documents/svcmanpdf/S08327.pdf> | yes |
| `perkins_sebu8601` | Perkins | Engine ECU | SEBU8601-07 1206E-E70TTA industrial engine OMM, Table 3 diagnostic codes | <https://s7d2.scene7.com/is/content/Caterpillar/CM20260911-9f181-9e283> | yes |
| `psi_60l_obdhd` | PSI | Engine ECU | PSI 6.0L OBD-HD engine diagnostic manual (FCCC chassis) | <https://dtnacontent-dtna.prd.freightliner.com/content/dam/dtna-servicelit/dtna/pdfs/en_us/fccc/engines/6.0L%20OBD%20MT-88%20HD%20Gasoline%20Diagnostic%20Manual%20(pre-released).pdf> | yes |
| `wabco_mm0112` | WABCO | ABS/ESC | MM0112 ABS/ESC E-version maintenance manual (05.2020) | <https://www.zf.com/products/media/automotive/cv/literature_downloads_wna/truck_solutions/abs_maintenance_manuals_/MM0112_web.pdf> | yes |
| `wabco_mm1719` | WABCO | ABS/ESC | MM1719 mBSP ABS/ESC maintenance manual (08.2018) | <https://www.zf.com/products/media/automotive/cv/literature_downloads_wna/truck_solutions/abs_maintenance_manuals_/MM1719_web.pdf> | yes |
| `yanmar_over56kw` | Yanmar | Engine ECU, Aftertreatment DCU | Troubleshooting manual, engines over 56 kW (2024) | <https://www.yanmar.com/media/news/2024/08/08065132/over_56kw_troubleshooting_manual.pdf> | yes |

## Dataset license

Both free samples are offered under ODbL v1.0; the full databases are available
under commercial license tiers (see README.md and the LICENSE file).


## Stable identity companions (since edition 2026.10)

Existing code_id, fault_id, fix_id and part_id values are preserved by a committed
allocation registry. IDs may be sparse and are scoped by domain/entity type.
Use qualified references such as `mechanicdb:v1:obd:fix:571`; the same integer
in HD or another table is a different identity. Numeric exports use permanent-ID
order; procedure display remains ascending probability_rank (numeric CAST for
Standard TEXT), with the existing I01 authored-order meaning.

`identity_metadata.json` identifies the immutable data release and artifact;
`identity_map.csv` / `.parquet` provide entitled references, decimal-text numeric
aliases, parent references, authored keys and content revision digests;
`identity_events.csv` provides relevant lifecycle information. The core SQLite
schema remains version 1. Public maps include only the authorized fixed samples.
Text, rank and component-name changes preserve intended identity. Retired or
withdrawn allocations are never reused; merge/split migration requires review.

Historical integers require an exact artifact or verified source release. Two
known September 2026 HD artifacts reused fault 571 for different entities; month
and number alone are ambiguous. Migration reports preserve original targets and
do not guess missing or changed historical procedure/part mappings. Paid
editions carry these companions from 2026.10.

Paid ZIPs carry the compact Parquet identity map; generated master directories
and public samples provide both CSV and Parquet maps. Content revision detectors
use the declared sha256-128 algorithm; full artifact/file/registry checksums use
SHA-256. CSV consumers can convert the companion with pandas.read_parquet().
