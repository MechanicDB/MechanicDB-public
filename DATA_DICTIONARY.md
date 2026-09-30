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

## 5. OEM coverage by make

<!-- COVERAGE:START -->
OEM (manufacturer-specific) codes number **6,637** across **32** makes, and are **not evenly distributed** — coverage is
strongest on US-market brands. The SAE-universal spine (9,249 codes) applies to
every vehicle regardless of make, so this table describes only the
manufacturer-controlled ranges (`P1`, `P30`–`P33`, `C1`/`C2`, `B1`/`B2`, `U1`/`U2`).

| Make | OEM codes | Make | OEM codes |
| :--- | ---: | :--- | ---: |
| Volkswagen | 528 | Plymouth | 113 |
| Ford | 413 | Dodge | 97 |
| Lincoln | 413 | Jeep | 97 |
| Mercury | 413 | Acura | 94 |
| Buick | 402 | Honda | 94 |
| Cadillac | 402 | Infiniti | 94 |
| Chevrolet | 402 | Subaru | 93 |
| GM | 402 | Kia | 76 |
| GMC | 402 | Nissan | 59 |
| Saturn | 402 | Lexus | 49 |
| Oldsmobile | 401 | Toyota | 45 |
| Chrysler | 282 | Mitsubishi | 33 |
| BMW | 250 | Mercedes-Benz | 32 |
| Mazda | 233 | Geo | 19 |
| Jaguar | 163 | Suzuki | 17 |
| Pontiac | 115 | Audi | 2 |
<!-- COVERAGE:END -->

---

## 6. Heavy Duty tier (J1939) — six tables

MechanicDB Heavy Duty is a **standalone** commercial product, `$149`, sold and delivered separately
from the OBD-II Standard/OEM Complete tiers above (on sale since 2026-09-24, see [README.md](README.md) and the
[J1939 fault code database](https://mechanicdb.dataengineered.io/j1939-fault-code-database) page). It maps SAE J1939 SPN+FMI fault pairs drawn from published OEM fault tables (Eaton,
WABCO, Bendix, John Deere, Navistar, Cummins, Caterpillar, PSI, Perkins, Yanmar) to authored
short descriptions, fault families, explanations, ranked fixes and part mappings — currently **4,212
fault pairs, 870 distinct SPNs, 16,998 ranked fixes and 5,904 part mappings across 10 OEMs and 16
official-host sources**, measured at build time. It follows the same physical conventions as the
tables above: pipe-delimited CSV, `utf-8-sig`, no embedded `\r`/`\n` (replaced with ` • `), Parquet
Snappy, one SQLite.

**This is not the SAE J1939 Digital Annex and contains no SAE text.** Every row carries its own
`source_url` to the OEM's published fault table; the parameter/failure-mode facts (SPN, FMI, OEM code)
are reported, but `short_description`, `spn_name`, `fmi_name` and the explanation text are our own
words, never a copy of the source document. The on-highway engine fault lists of Cummins, Detroit,
PACCAR, Volvo/Mack and Cat *trucks* are dealer-gated and are not in this tier.

**Natural key:** (`source_id`, `spn`, `fmi`, `oem_code`) identifies a distinct OEM-published fault row.
The same SPN+FMI pair recurs across OEMs by design — exactly as the same `dtc_code` recurs across
makes in `dtc_codes` above — because each OEM publishes and controls its own fault table; `fault_id`
is the single join key for the other tables.

**Editorial-estimate note:** as with `diagnostic_fixes` above, `difficulty_level`,
`est_parts_cost_min_usd`, `est_parts_cost_max_usd` and `est_labor_hours` in this tier's
`diagnostic_fixes` rows are editorial estimates — here, for **US independent heavy-duty / fleet
shops**, not dealer rates and not a quote. They are not sourced from the OEM documents.

**Free sample:** [`samples/heavyduty/`](samples/heavyduty/) in this repository ships 100 of the 4,212
faults (deterministically sampled across the full spine, so every one of the 10 OEMs is represented),
their referenced SPNs, ranked fixes, part mappings, and the complete 32-row FMI register — same
schema, same ODbL v1.0 terms as the OBD-II sample above (see [LICENSE](LICENSE)); its source documents are listed in [SOURCES.md](SOURCES.md#heavy-duty-sample-j1939).

### 6.1 `j1939_fmi` (Failure Mode Identifier register, 32 rows)

Authored paraphrase of the 32 SAE J1939 Failure Mode Identifiers, cross-checked against public
technical explainers — never SAE text.

| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `fmi` | Integer (PK) | The FMI value, 0–31. | `3` |
| `fmi_name` | String | Our paraphrase of the failure mode. | `Circuit voltage high / short to supply` |
| `failure_class` | String | Normalized failure-mode class used to drive fix ordering (see 6.9 below). One of: `range_high`, `range_low`, `erratic`, `circuit_high`, `circuit_low`, `open_circuit`, `short_ground`, `mechanical`, `frequency`, `update_rate`, `rate_of_change`, `unknown_cause`, `device`, `calibration`, `special`, `network_error`, `drift_high`, `drift_low`, `reserved`, `condition`. | `circuit_high` |
| `is_reserved` | Integer | `1` for FMI 22–30 (SAE-reserved; some OEMs assign proprietary meanings), `0` otherwise. | `0` |

### 6.2 `j1939_spn` (Suspect Parameter Number register — one row per (`spn`, `oem_make`))

**Key:** `j1939_spn` is keyed on (`spn`, `oem_make`), not on `spn` alone. SPNs below `516096` are
standard SAE parameters: one row, `oem_make` empty, a neutral name shared across every OEM that
references the SPN. SPNs `>= 516096` fall in the OEM-controlled naming range — this covers both the
OEM-naming band `516096`–`520191` (OEM-published but not SAE-reserved-proprietary) and the
proprietary range `>= 520192` — and get **one row per OEM that uses the SPN**, each named from that
OEM's own document; the same SPN can therefore appear once per OEM with a different `spn_name` in
each row. `j1939_faults.detailed_technical_explanation` renders `{spn_name}` for a standard SPN
from the shared neutral name and, for `spn >= 516096`, from the fault's own source document,
never another OEM's; when two documents of the same OEM name an SPN differently, this table
keeps the name from the first `source_id` (sorted) and each fault keeps its own document's name.

**In the free sample,** [`samples/heavyduty/j1939_spn.csv`](samples/heavyduty/j1939_spn.csv) holds
every full-tier row for each SPN number the sampled faults reference, so an OEM-range SPN can also
appear under an OEM that has no fault in the sample; `source_count` is the full tier's value, so it
can exceed the number of sources visible in the sample's `j1939_faults.csv`.

| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `spn` | Integer (PK part 1) | The J1939 Suspect Parameter Number. | `110` |
| `spn_name` | String | Our paraphrase of the parameter. For a standard SPN, one neutral name shared by every OEM. For `spn >= 516096`, this OEM's own name for the parameter, read from this OEM's document. When the source documents do not state a role for the SPN, the name says so rather than guessing: `Parameter <spn> (role not stated by the OEM tables)` for a standard SPN, `<OEM> parameter <spn> (role not stated)` for an OEM-range SPN. | `Engine coolant temperature` |
| `is_proprietary` | Integer | `1` when `spn >= 520192` (the SAE-reserved proprietary SPN block), `0` otherwise — including for the `516096`–`520191` OEM-naming band, which is OEM-published but not SAE-reserved-proprietary. | `0` |
| `oem_make` | String | Part 2 of the composite key. Empty string for a standard SPN (`spn < 516096`); for `spn >= 516096`, the `oem_make` (same values as `j1939_faults.oem_make`) of the OEM whose document uses the SPN. | `` |
| `system_category` | String | Fixed vocabulary: `Engine`, `Fuel`, `Air Intake`, `Aftertreatment`, `Cooling`, `Lubrication`, `Electrical`, `Transmission`, `Brakes/ABS`, `Body/Cab`, `Network`, `Instrument`. | `Cooling` |
| `source_count` | Integer | Number of distinct `source_id` values behind this row: every source that references the SPN for a standard SPN, that OEM's sources for an OEM-range row. | `4` |

### 6.3 `j1939_faults` (Master Fault Registry — this tier's spine, analogue of `dtc_codes`)

One row per extracted OEM SPN+FMI fault pair.

| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `fault_id` | Integer (PK) | Primary key, assigned after sorting rows by (`oem_make`, `controller`, `spn`, `fmi`, `oem_code`). | `280` |
| `spn` | Integer (FK, with `oem_make` below, → `j1939_spn`) | Join to `j1939_spn` on `spn` plus `oem_make` when `spn >= 516096` (this fault's own OEM row, see 6.2), and on `spn` with an empty `oem_make` below `516096`; joining on `spn` alone repeats a fault once per OEM that uses an OEM-range SPN. | `110` |
| `fmi` | Integer (FK → `j1939_fmi.fmi`) | | `3` |
| `oem_make` | String | One of `Eaton`, `WABCO`, `Bendix`, `John Deere`, `Navistar`, `Cummins`, `Caterpillar`, `PSI`, `Perkins`, `Yanmar`. | `Caterpillar` |
| `oem_code` | String | The OEM's own code for this fault as printed in its document; empty string when the source document does not print one. | `110-3` |
| `controller` | String | Fixed vocabulary: `Engine ECU`, `Aftertreatment DCU`, `Transmission`, `ABS/ESC`, `Body controller`. | `Engine ECU` |
| `short_description` | String | Authored, our words, ≤ 120 characters. Never a copy of OEM text. | `Engine coolant temperature sensor circuit voltage above normal (short to supply)` |
| `fault_family` | String | Slug of the authored fault family that groups this fault with others sharing a diagnosis/repair path; joins `diagnostic_fixes` via the family's authored fixes. | `hde_coolant_temp_sensor` |
| `detailed_technical_explanation` | String | Authored explanation, rendered from the family's template — never OEM prose. | `SPN 110 (Engine coolant temperature) with FMI 3 (Circuit voltage high / short to supply) is set by the Engine ECU when the engine coolant temperature sensor signal leaves its plausible window...` |
| `source_id` | String | Register key for the OEM document this row's fact was read from; listed in [SOURCES.md](SOURCES.md#heavy-duty-sample-j1939). | `cat_c10882888` |
| `source_url` | String | The official OEM document URL this row's fact was read from. | `https://s7d2.scene7.com/is/content/Caterpillar/C10882888` |
| `source_page` | String | Page/section marker within the source document, when the source format carries one. | `102` |
| `source_doc` | String | Human-readable document title/ID. | `1200 Series marine auxiliary engines troubleshooting guide` |

### 6.4 `diagnostic_fixes`

Same shape and column names as the OBD-II tier's `diagnostic_fixes` (section 2 above), except the
foreign key is `fault_id` (this tier has no `code_id`). Difficulty and fix ranking are re-authored for
this tier — see 6.7/6.9 below.

| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `fix_id` | Integer (PK) | Primary key. | `101` |
| `fault_id` | Integer (FK → `j1939_faults.fault_id`) | | `1` |
| `fix_title` | String | Actionable title of the recommended inspection or repair. | `Inspect coolant temperature sensor connector` |
| `probability_rank` | Integer | `1` = most likely fix for this fault, `2` = next, etc. Order is FMI-driven — see 6.9. | `1` |
| `difficulty_level` | String | Fixed vocabulary for this tier — see 6.7. | `Fleet technician` |
| `est_parts_cost_min_usd` | Float | Editorial estimate, US independent heavy-duty shop. | `35.00` |
| `est_parts_cost_max_usd` | Float | Editorial estimate, US independent heavy-duty shop. | `120.00` |
| `est_labor_hours` | Float | Editorial estimate, US independent heavy-duty shop. | `0.75` |
| `step_by_step_instructions` | String | Bulleted, ` • `-separated. | `1. Disconnect ECU harness connector • 2. Inspect pins for corrosion...` |

### 6.5 `replacement_parts`

Same shape and column names as section 3 above, keyed to this tier's `fix_id`. `amazon_search_query`
is filled only where the part is plausibly retail/aftermarket; dealer-only or fabricated-to-order parts
get an empty string (NULL over guess).

| Column Name | Data Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `part_id` | Integer (PK) | | `501` |
| `fix_id` | Integer (FK → `diagnostic_fixes.fix_id`) | | `101` |
| `part_name` | String | | `Engine Coolant Temperature Sensor` |
| `amazon_search_query` | String | Direct catalog search URL; empty string when the part is dealer-only. | `https://www.amazon.com/s?k=heavy+duty+diesel+coolant+temperature+sensor` |

### 6.6 `j1939_fixes_joined` (Pre-Joined Analytical View)

A denormalized flat table combining `j1939_faults` and `diagnostic_fixes` (joined on `fault_id`) —
every column from both tables in one row, for ML ingestion and instant frontend rendering, mirroring
`dtc_fixes_joined` above.

### 6.7 Difficulty vocabulary (this tier only)

The Standard/OEM tiers' DIY-oriented scale (`Easy DIY`, `Moderate DIY`, `Professional Required`) is
wrong for heavy-duty trucks — most fixes require shop tooling, air-brake certification or an OEM
service tool, and "DIY" is not a meaningful buyer segment. This tier's `difficulty_level` uses instead:

| Value | Meaning |
| :--- | :--- |
| `Driver check` | A pre-trip/roadside check any driver can do without tools (visual inspection, connector reseat, DPF regen prompt). |
| `Fleet technician` | Requires shop tools and diagnostic software but not dealer-level equipment; typical in-house fleet maintenance scope. |
| `Dealer / specialist` | Requires OEM service tools, calibration equipment or specialist certification (air brake, aftertreatment); typically outsourced to a dealer. |

### 6.8 Controller and system vocabularies

`controller` (on `j1939_faults`) identifies which vehicle ECU/module owns the fault: `Engine ECU`,
`Aftertreatment DCU`, `Transmission`, `ABS/ESC`, `Body controller`.

`system_category` (on `j1939_spn`) classifies the parameter itself, independent of which controller
reported it: `Engine`, `Fuel`, `Air Intake`, `Aftertreatment`, `Cooling`, `Lubrication`, `Electrical`,
`Transmission`, `Brakes/ABS`, `Body/Cab`, `Network`, `Instrument`.

### 6.9 FMI-driven fix ordering

Unlike the OBD-II tiers, where `probability_rank` is purely an authored per-family order, this tier's
ranking is **fact-driven by the FMI**: the FMI already states the failure mode (a short to ground is
diagnosed differently from a value out of range), so fix order follows it rather than guesswork. Every
fault gets at least one fix (the family default), so — as with the OBD-II tiers — fixes exist for
100% of faults.
