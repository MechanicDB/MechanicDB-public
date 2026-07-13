# MechanicDB Relational Data Dictionary

MechanicDB is structured around three core normalized tables (`dtc_codes`, `diagnostic_fixes`, `replacement_parts`) and one pre-joined analytical view (`dtc_fixes_joined`). All string fields are guaranteed to have zero embedded linebreaks (`\r` or `\n` are replaced by ` • `) to ensure exact physical row parity in pipe-delimited (`|`) CSVs and PyArrow Parquet files. CSVs are encoded as `utf-8-sig` (UTF-8 with BOM).

**Row identity:** `dtc_code` alone is unique only within the SAE-universal rows (`is_oem_specific = 0`). For manufacturer-specific rows (`is_oem_specific = 1`), the natural key is the composite `(oem_make, dtc_code)` — the same `dtc_code` value can legitimately recur under different `oem_make` values. This is expected: manufacturer-controlled code ranges (`P1`, `P30–P33`, `C1/C2`, `B1/B2`, `U1/U2`) are assigned per-brand, not globally unique. `code_id` remains the single surface-level primary key for joins.

**Badge-engineering duplication:** marques that share engineering platforms (GM's seven marques, Ford/Mercury/Lincoln, Honda/Acura, and other shared-platform groups — see [SOURCES.md](SOURCES.md)) frequently share the same code definitions verbatim across brands. Rows are kept per marque rather than deduplicated across the group, so make-filtered lookups return complete results for the brand a buyer queries. This sample includes 15 OEM codes (of the full dataset's 6,637) so the OEM columns are populated and testable here too.

---

## 1. `dtc_codes` (Master Code Registry)

Contains definitions for both universal SAE-standard OBD-II trouble codes and manufacturer-specific (OEM) trouble codes, distinguished by `is_oem_specific` and `oem_make`.

| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `code_id` | Integer (PK) | Primary key unique identifier for the trouble code record. | `1` |
| `dtc_code` | String (5) | Standardized 5-character OBD-II trouble code. Unique alone for SAE rows; unique only in combination with `oem_make` for OEM rows. | `P0171` |
| `system_category` | String | Automotive system classification (`Powertrain`, `Chassis`, `Body`, `Network`). | `Powertrain` |
| `is_oem_specific` | Integer | Boolean flag: `0` for universal SAE standard, `1` for manufacturer-specific. | `0` |
| `oem_make` | String | Vehicle manufacturer make name (`Ford`, `Toyota`, `BMW`) for OEM rows, or empty string for SAE-universal rows. | `` |
| `fault_family` | String | Slug of the authored fault family grouping codes that share a diagnosis and repair path. | `maf_circuit` |
| `short_description` | String | Concise summary title of the trouble code. | `System Too Lean (Bank 1)` |
| `detailed_technical_explanation` | String | In-depth technical explanation of sensor telemetry and ECM detection logic. | `The engine control module (ECM) detects too much oxygen...` |

---

## 2. `diagnostic_fixes` (Ranked Repair Procedures & Cost Matrix)

Maps diagnostic trouble codes to actionable repair procedures, ranked by statistical likelihood and accompanied by aftermarket cost matrices.

| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `fix_id` | Integer (PK) | Primary key unique identifier for the repair procedure. | `101` |
| `code_id` | Integer (FK) | Foreign key referencing `dtc_codes.code_id`. | `1` |
| `fix_title` | String | Actionable title of the recommended diagnostic inspection or repair procedure. | `Clean or Replace MAF Sensor` |
| `probability_rank` | Integer | Statistical likelihood rank (`1` = most common root cause, `2` = secondary cause). | `1` |
| `difficulty_level` | String | Skill requirement rating (`Easy DIY`, `Moderate DIY`, `Professional Required`). | `Easy DIY` |
| `est_parts_cost_min_usd` | Float | Estimated minimum aftermarket replacement parts cost in US dollars. | `15.00` |
| `est_parts_cost_max_usd` | Float | Estimated maximum aftermarket replacement parts cost in US dollars. | `45.00` |
| `est_labor_hours` | Float | Average professional mechanic labor hours required to complete the procedure. | `0.5` |
| `step_by_step_instructions` | String | Bulleted step-by-step diagnostic and repair instructions (separated by ` • `). | `1. Disconnect battery • 2. Spray sensor...` |

---

## 3. `replacement_parts` (Aftermarket Part Mappings)

Maps diagnostic repair procedures to common aftermarket replacement parts and catalog search queries.

| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `part_id` | Integer (PK) | Primary key unique identifier for the replacement part record. | `501` |
| `fix_id` | Integer (FK) | Foreign key referencing `diagnostic_fixes.fix_id`. | `101` |
| `part_name` | String | Descriptive name or title of the replacement sensor, component, or repair kit. | `Mass Airflow Sensor (MAF) Cleaner & Sensor Kit` |
| `amazon_search_query` | String | Direct catalog search URL for acquiring the replacement part on Amazon or auto parts catalogs. | `https://www.amazon.com/s?k=EVAP+purge+solenoid+valve+automotive` |

---

## 4. `dtc_fixes_joined` (Pre-Joined Analytical View)

A denormalized analytical table combining code definitions, ranked fixes, and cost estimation matrices into a single flat file for rapid machine learning ingestion and instant frontend rendering. Contains all columns from `dtc_codes` (including `fault_family`) and `diagnostic_fixes` joined on `code_id`.
