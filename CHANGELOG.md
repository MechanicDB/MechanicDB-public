# Changelog

All notable changes to the MechanicDB dataset snapshots and this sample repository.

> All counts are **measured from the shipped artifacts** by the build pipeline
> (`build_report.json`) — never rounded up, never projected.

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
  [Kaggle](https://www.kaggle.com/datasets/ahtiticheamine/mechanicdb-automotive-obd2-repair-database).

Full dataset & updates: [mechanicdb](https://mechanicdb-public.pages.dev/)
