# Contributing to MechanicDB

Thanks for your interest! This repository is the **public showcase** for the
MechanicDB automotive diagnostic dataset — it holds a free sample and its
documentation. The data pipeline itself is not open source, so contributions
here focus on **data quality, docs, and examples**.

## Ways to help

### 🐛 Report a data issue
Spotted a wrong code definition, fix ranking, cost range, or repair step in the
sample? Open an issue with:

- the `dtc_code` (and `oem_make` if it's a manufacturer-specific row),
- what's wrong and what it should be,
- ideally a reference (service-manual excerpt, manufacturer TSB, or standard
  diagnostic practice) so we can re-verify.

**Safety-related errors are the highest priority** — if a repair step could be
dangerous as written (especially anything touching high-voltage hybrid/EV
systems or SRS/airbag components), please flag it immediately.

### ✏️ Improve docs or examples
Typos, clearer explanations, or better quickstart snippets are welcome via pull
request.

### 💡 Request a make or field
Want a column the dataset doesn't have, or coverage of a make we don't ship?
Open an issue describing the use case — it helps prioritize snapshots and
informs custom builds.

## Correction or removal requests

To request a record be corrected, email
**mechanicdb.urologist336@simplelogin.com** (or open an issue).

## Pull request guidelines

- Keep PRs focused and describe the *why*.
- Docs/examples only — please don't add pipeline or scraping code here.
- Data changes to the sample must preserve the schema in
  [DATA_DICTIONARY.md](DATA_DICTIONARY.md) (pipe-delimited, UTF-8 with BOM, no
  embedded linebreaks).

## Licensing of contributions

By contributing, you agree that your contributions are licensed under the same
terms as this repository: **ODbL v1.0** for dataset files, **CC BY 4.0** for
documentation (see [LICENSE](LICENSE)).

Questions? **mechanicdb.urologist336@simplelogin.com** · full dataset:
[mechanicdb](https://mechanicdb-public.pages.dev/)

*Repair steps are educational reference material, not professional repair advice.*
