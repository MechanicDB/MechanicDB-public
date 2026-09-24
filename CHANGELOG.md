# Changelog

All notable changes to the MechanicDB dataset snapshots and this sample repository.

> All counts are **measured from the shipped artifacts** by the build pipeline
> (`build_report.json`) — never rounded up, never projected.

## Heavy Duty SEO pages — 2026-09-24

- New page **/j1939-fault-code-database**: the Heavy Duty tier in full — six tables with row counts,
  coverage by OEM and by system, the 32-entry J1939 FMI reference, one sample row per OEM, three FAQ
  answers, buy button; Dataset, Product, FAQPage and BreadcrumbList structured data.
- One page per manufacturer under **/j1939/** (Bendix, Caterpillar, Cummins, Deutz, Eaton, John Deere,
  Navistar, Perkins, PSI, WABCO, Yanmar): source documents, pairs by system, largest fault families,
  FMI breakdown, standard vs OEM-assigned SPNs and that OEM's rows from the free sample. Counts,
  names and sample rows only; ranked fixes, costs, labour, steps and parts stay in the paid dataset.
- Homepage: title, meta and social descriptions now name the J1939 tier; the Dataset, FAQPage and
  Product structured data carry it (all three tiers are listed as offers, and the two Heavy Duty FAQ
  answers are in the FAQ schema as well as on the page). The coverage table links each OEM to its page.
- README, DATA_DICTIONARY and llms.txt no longer say "release pending"; the OBD-II buyer page links the
  J1939 page. All new copy translated into es/de/fr/pt-br; i18n check 0 errors.

## Heavy Duty coverage table restyled — 2026-09-24

- The homepage `#coverage-hd` table (OEM / controller / fault pairs / source document) now uses the site's paper spec-sheet styling (`.cov-table`, matching the per-make coverage grid and the specifications sheet): mono uppercase headers, amber fault-pair counts, manufacturer groups ruled off, and a stacked card layout under 640px. No data or counts changed; es/de/fr/pt-br homepages rebuilt.

## Heavy Duty tier released — 2026-09-24

- The Heavy Duty card now carries the buy button (Stripe payment link, `client_reference_id=mechanicdb_<lang>_pricing`) instead of the early-access request; `claims.json["heavyduty"]` is `released: true` with `launch_date` 2026-09-24. Instant download through the delivery worker.

## Heavy Duty (J1939) tier — release pending — 2026-09-21

- **New standalone tier, MechanicDB Heavy Duty ($149, sold and delivered separately from
  Standard/OEM Complete):** SAE J1939 SPN+FMI fault pairs read from published OEM fault
  tables — Eaton, WABCO, Bendix, Deutz, John Deere, Navistar, Cummins, Caterpillar, PSI,
  Perkins, Yanmar — mapped to authored short descriptions, fault families, explanations,
  ranked fixes and part mappings across six tables (`j1939_fmi`, `j1939_spn`,
  `j1939_faults`, `diagnostic_fixes`, `replacement_parts`, `j1939_fixes_joined`). Currently
  measures **6,502 fault pairs · 1,536 SPN rows (per OEM for proprietary SPNs) · 25,608 ranked fixes · 8,365 part
  mappings across 11 OEMs and 21 official-host sources**. Documented in
  [DATA_DICTIONARY.md](DATA_DICTIONARY.md) section 6.
- **This is not the SAE J1939 Digital Annex and contains no SAE text** — every row carries
  its own `source_url` to the OEM's published fault table; descriptions, names and
  explanations are our own words. The on-highway engine fault lists of Cummins, Detroit,
  PACCAR, Volvo/Mack and Cat *trucks* are dealer-gated and are not in this tier.
- New `difficulty_level` vocabulary for this tier only (`Driver check`, `Fleet technician`,
  `Dealer / specialist`) — the Standard/OEM tiers' DIY-oriented scale doesn't fit
  heavy-duty trucks.
- **Free sample:** 100 of the 6,502 faults (deterministically sampled so every one of the
  11 OEMs is represented), their SPNs, ranked fixes, part mappings and the full 32-row FMI
  register, added to this repository under [`samples/heavyduty/`](samples/heavyduty/) —
  same ODbL v1.0 terms as the existing OBD-II sample.
- Shopfront (mechanicdb.dataengineered.io): new "Heavy Duty" pricing card, a J1939
  OEM/controller/pairs coverage table, and two new FAQ entries ("Is this the SAE J1939
  Digital Annex?" and "Which truck engines are covered?").
- **Release pending:** `claims.json["heavyduty"]["released"]` is `false` — no Stripe link
  yet. The shopfront shows an "Ask for early access" call-to-action (support form) instead of a
  buy button until the tier launches.

## Site update — 2026-09-20

- **Sale attribution**: every Stripe buy link carries `?client_reference_id=<brand>_<lang>_<surface>` (`home` / `landing`); the i18n build swaps the language token per locale and the delivery worker prints the id in the order email. Stripe does not store UTM parameters, so this is the only per-page attribution that reaches the order record (2026-09-20).

## 2026.07 (v2 — "OEM Complete") — 2026-07-12

- **+6,637 manufacturer-specific (OEM) codes across 32 makes** merged into the
  dataset: Acura, Audi, BMW, Buick, Cadillac, Chevrolet, Chrysler, Dodge, Ford,
  Geo, GM, GMC, Honda, Infiniti, Jaguar, Jeep, Kia, Lexus, Lincoln, Mazda,
  Mercedes-Benz, Mercury, Mitsubishi, Nissan, Oldsmobile, Plymouth, Pontiac,
  Saturn, Subaru, Suzuki, Toyota, Volkswagen — totals now
  **15,886 codes · 56,561 ranked fixes · 75,055 parts mappings · 647 fault
  families**.
- OEM rows carry `is_oem_specific = 1` and `oem_make`; the natural key for OEM
  rows is `(oem_make, dtc_code)` (manufacturer code numbers legitimately recur
  across brands). Badge-engineered marques keep per-marque rows so
  make-filtered lookups return complete results.
- Free sample grew from 75 to **90 codes** (75 SAE + 15 OEM) so the OEM columns
  are populated and testable here.
- SAE-standard rows are byte-identical to v1 — a frozen-checksum test gate
  guarantees the OEM merge changed nothing in the universal spine.
- 2026-07-13: both paid tiers became **self-serve** — Stripe checkout with
  instant automated delivery ([Standard $49](https://buy.stripe.com/5kQ3cw7Be9b88rNfuU38403),
  [OEM Complete $149](https://buy.stripe.com/28EfZicVy0ECdM796w38404)).

## 2026.07 (v1) — 2026-07-07

- Initial public release.
- **9,249** SAE-standard OBD-II trouble codes mapped to **32,767** ranked repair
  procedures and **44,588** aftermarket parts mappings across hand-authored
  fault families.
- Every fix carries a difficulty rating (`Easy DIY` / `Moderate DIY` /
  `Professional Required`), a parts-cost range (USD), labor hours, and
  step-by-step instructions.
- Code definitions compiled from an MIT-licensed SAE J2012-derived public
  compilation (see [SOURCES.md](SOURCES.md)); repair content is original
  authored material produced by a deterministic, test-gated pipeline.
- Free 75-code sample published here and on
  [Kaggle](https://www.kaggle.com/datasets/dataengineered/mechanicdb-automotive-obd2-repair-database).

Full dataset & updates: [mechanicdb](https://mechanicdb.dataengineered.io/)
