# Changelog

All notable changes to the MechanicDB dataset snapshots and this sample repository.

> All counts are **measured from the shipped artifacts** by the build pipeline
> (`build_report.json`) — never rounded up, never projected.

## Statistics page: each chart is announced with its own title — 2026-09-28

- /stats/: every chart's built-in title and description (what a screen reader announces for the
  chart) used the same two ids, t and d, repeated once per chart, so the page had duplicate ids
  and every chart was announced with the first chart's title. The ids now carry the chart's name
  (t-codes-by-system / d-codes-by-system, and so on) on the page and in the downloadable SVGs
  under /stats/charts/. scripts/stats_common.py is the current portfolio copy, which writes them
  on the next regeneration; the committed page and SVGs were patched to exactly what it writes,
  without regenerating (no figure, date or data.json changes).

## Homepage: current RecallDB recall count in "You might also need" — 2026-09-28

- The homepage's "You might also need" section (all five languages) introduced RecallDB with
  127,783 official U.S. recalls, the July 2026 edition's count. It now gives 128,936, the recall
  count of the RecallDB 2026.09 edition that buyers download today (built 2026-09-20). The rest of
  the sentence (five agencies, $49 one-time) is unchanged and still correct.

## README edition badge — 2026-09-28

- The README badge said "Snapshot 2026.07"; the Standard, OEM Complete and Heavy Duty ZIPs buyers
  download are edition 2026.09 (built 2026-09-27). The badge now says 2026.09. `claims.json` is
  unchanged: it is a byte copy of the private pipeline's file, and its `snapshot` value is not
  read by the build or the pages (the edition comes from the build date).

## Website: repository files no longer served — 2026-09-28

- The translation catalogs (`/locales/`), the build scripts (`/scripts/`), `i18n.config.json`,
  `README.md`, `vercel.json` and the dotfiles belong to this repository, not to the website, but
  the site served them as plain files. They now answer the site's normal 404 page (also when
  requested as `/locales%2Fes.json` or `//locales/es.json`) and stay available here on GitHub.
  Pages, data files, samples, `llms.txt` and the sitemap are unchanged (2026-09-28).

## Statistics page: chart embed links land on their chart — 2026-09-27

- /stats/: the copy-paste "Embed this chart" code of all nine charts linked
  /stats/#<chart-name> (e.g. #codes-by-system), which is no element on the page, so a visitor
  following an embedded chart landed at the top of the page. The links now point at the chart
  itself (/stats/#fig-codes-by-system, and the same for the other eight). Code already pasted
  elsewhere with the old link still opens the page, at the top.
- /stats/ also re-aligns a link to one of its sections or charts from another page once the web
  fonts have loaded (they load without blocking and move the sections when they swap in), unless
  the visitor has already scrolled or is reloading / going back. It uses the portfolio's shared
  section-links snippet (scripts/section_links.py); the page header is not sticky, so no scroll
  offset is added. The homepage keeps its own re-align from the entry below.
- scripts/stats_common.py is the current portfolio copy (it writes both changes on the next
  regeneration) and scripts/section_links.py is new next to it; the committed page was patched to
  exactly what they write, without regenerating it (no figure, chart, date or data.json changes).

## Homepage section links land on their section — 2026-09-27

- Links to a homepage section from another page (/#decoder, /#licensing, /#faq, in all five
  languages) now land on the section. The web fonts load without blocking the page, so they swap
  in after the browser has scrolled to the section and move the sections up (measured at 1280x800:
  #decoder 69 px, #licensing 144, #faq 175, #provenance 212), which left the heading above the
  screen (in Chrome, on a simulated first visit, #licensing ended 51 px above the screen; a browser
  without scroll anchoring would keep the whole shift). The homepage now re-aligns once the fonts
  have loaded, unless the visitor has already scrolled or is reloading / going back, where the
  browser's own restored position is kept; /#supportModal still just opens the inquiry form.
- The code decoder at the top of the homepage paints its first example at once instead of after a
  short delay, so the page no longer grows by a few hundred pixels (685 px on a phone) right after
  loading.

## Landing-page buy block, pricing heading, Heavy Duty inquiry topic — 2026-09-27

- Code and family pages (all five languages): the buy block under "Need all 15,886 codes as data?"
  now leads with "License OEM Complete · $149", the tier that has every code the heading promises,
  next to "Standard (SAE only) · $49"; it no longer sells the $49 SAE-only tier as the "full
  dataset". Its tier line names all three paid tiers: $49 Standard (9,249 SAE codes), $149 OEM
  Complete (all 15,886 codes, including 6,637 OEM codes across 32 makes) and $149 Heavy Duty (4,212
  J1939 fault pairs, linking the J1939 page), with prices and code/fault counts from claims.json and
  the OEM code and make counts from build_report.json. Links in that line now show in dark text
  (the amber was barely readable on the light box); the same applies on the J1939 pages.
- Homepage: the pricing heading reads "Five ways in" (it sits over five cards: the free sample and
  four paid options), and the inquiry form adds a "Heavy Duty (J1939) Commercial License ($149)"
  topic.

## Translated Dataset markup names its English original — 2026-09-27

- The Spanish, German, French and Portuguese pages' Dataset structured data (homepage,
  /obd2-dtc-database, /j1939-fault-code-database) names its English original in `sameAs`, so
  dataset search can tie the language copies to one canonical entry. The homepage Dataset's two
  parts (`hasPart`) are the English buyer pages' Datasets in every language. English pages and all
  visible text are unchanged.

## Page header and footer, sample labels, dated license terms — 2026-09-27

- Every generated page (code and family pages and the J1939 pages in all five languages, plus the
  English-only /license and /stats/): the header's "Decoder" link now opens the homepage decoder (/#decoder — it pointed at
  an anchor the homepage never had), the pricing link reads "Licensing" rather than a single $49
  price (there are three paid tiers), and the footer carries the homepage wording, "sample data
  under ODbL v1.0 · full dataset under commercial license", with a link to /license. The /stats/
  contact link opens the inquiry form, and the homepage breadcrumb's "Diagnostic Decoder" item
  points at /#decoder.
- Structured data: every free-sample download in the Dataset markup (homepage, /obd2-dtc-database,
  /j1939-fault-code-database) is named as the free sample it is — e.g. "Free 90-code OBD-II sample
  — dtc_codes (CSV)", "Free 100-fault Heavy Duty sample — j1939_faults (Parquet)" — and marked free.
  The homepage Dataset's two parts are now full Dataset entries repeating each buyer page's own name
  and description (Google's Rich Results Test flagged the bare links as invalid). The /j1939/<oem>
  pages name the J1939 database page as the one they belong to (isPartOf) instead of nesting an
  incomplete copy of its Dataset, which the Rich Results Test rejected for its missing description.
- /license states the terms version, 2026-09-25: the date the current terms took effect (the Heavy
  Duty Section 3 rewrite). The terms themselves are unchanged; the paid downloads are re-issued with
  the same line in their COMMERCIAL_LICENSE.md, and the page's structured data states the version.

## Homepage Dataset markup describes the paid collection — 2026-09-27

- The homepage's Dataset structured data (all five languages) no longer calls the full paid database
  free and ODbL-licensed: `license` now points at the commercial terms (/license) and
  `isAccessibleForFree` is false; its downloads are the free OBD-II sample the homepage offers (CSV and
  Parquet), each marked ODbL v1.0; `hasPart` links the two buyer pages (/obd2-dtc-database and
  /j1939-fault-code-database), whose Datasets already followed this rule and list their own samples;
  the creator is DataEngineered. Name, description and visible page text are unchanged.
- README: the license badge reads "Sample License: ODbL v1.0" (it covers the free samples only).

## Heavy Duty wording and licensing docs — 2026-09-27

- Heavy Duty paid snapshot re-issued (label unchanged): 39 fault `short_description`s and the SPN 2209
  parameter name reworded in our own words — they repeated, or differed by one word from, the OEM's own
  fault text — plus the one explanation and the `j1939_fixes_joined` rows that repeat them. Counts,
  fault_ids, fix_ids, families and joins are unchanged. The automated copy checks now ignore case,
  punctuation and the ` - ` separator, and also catch a description that contains a whole OEM fault
  sentence.
- `samples/heavyduty/`: fault_id 1 (Bendix SPN 154 / FMI 13) `short_description` rewritten in our own
  words (it repeated the OEM's phrase). No counts, fault_ids or other rows change; the J1939 database
  page and /j1939/bendix show the new text.
- /license, the homepage pricing note and llms.txt no longer say the terms are simply "the same" for
  every tier: the grant, restrictions, warranty and termination are shared by Standard, OEM Complete
  and Heavy Duty, while each tier's copy names its own product and use cases and its Section 3 names
  that tier's sources. Homepage note translated into es/de/fr/pt-br.
- /license contact is the homepage inquiry form (/#supportModal, which now opens the form on arrival)
  instead of a mailto: link.
- LICENSE and SOURCES.md now cover the Heavy Duty sample (ODbL v1.0; register of the tier's 16 source
  documents, 15 of them with rows in the free sample). README: the licensing-form link pointed at a
  `#pricing` anchor the site never had; the three paid tiers and both samples are named.

## Deutz sources withdrawn from Heavy Duty — 2026-09-26

- The five Deutz documents (serdia.deutz.com) are no longer part of the Heavy Duty tier. The paid
  tier now measures **4,212 fault pairs · 884 SPN rows (870 distinct SPNs) · 16,998 ranked fixes · 5,904 part mappings
  across 10 OEMs and 16 official-host sources** (was 6,502 · 1,536 · 25,608 · 8,365, 11 OEMs, 21
  sources); `fault_id`, `fix_id` and `part_id` are renumbered, so join editions on
  (`source_id`, `spn`, `fmi`, `oem_code`).
- **Free sample** regenerated: 100 of the 4,212 faults, every one of the 10 OEMs represented, no
  Deutz rows. FMI register unchanged.
- **/j1939/deutz** and its es/de/fr/pt-br copies removed (they now return 404) and dropped from the
  sitemap; the homepage, the J1939 database page, the other OEM pages, README, DATA_DICTIONARY and
  llms.txt carry the new counts and OEM list.
- An edge cache kept serving the deleted /j1939/deutz pages after the deploy (the zone purge
  does not reach it), so functions/_middleware.js now answers those five paths itself with the
  locale's 404 page and a real 404 status.

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
