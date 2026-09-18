#!/usr/bin/env python3
"""
MechanicDB statistics page generator (`MechanicDB-public`).

Reads the FULL private dataset (the private pipeline's commercial_dataset/mechanicdb.sqlite,
never the public sample) and writes a citable, embeddable statistics page:

    stats/index.html          the page (URL /stats/)
    stats/charts/<slug>.svg   one standalone SVG per chart (for <img> embeds elsewhere)
    stats/data.json           every figure on the page, machine-readable

Only aggregates leave the private database -- no row-level data is written (the fix titles
and part names quoted are catalogue labels that repeat across hundreds of codes, not rows).
Every figure states its denominator. MechanicDB is a reference catalogue, not incidence
data: nothing here says how often a code is set on real vehicles, only how the catalogue
is built. Costs and labor hours are the dataset's editorial estimates, not quotes.

Re-run after each data refresh, then the private `scripts/generate_public_pages.py` (which
lists /stats/ in the sitemap) or insert the entry by hand, then `python scripts/i18n_common.py
build` and `... check`.

Usage:
    python scripts/generate_stats.py                 # ../../05_Automotive_OBD2_MechanicDB/commercial_dataset/mechanicdb.sqlite
    python scripts/generate_stats.py --db PATH       # or MECHANICDB_SQLITE=PATH
"""
import argparse
import datetime as dt
import os
import sqlite3
import statistics
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stats_common import (Site, esc, n, pct, data, svg_hbar, figure, table, section, toc, tiles,  # noqa: E402
                          article_ld, COPY_JS, STATS_CSS, write_outputs)

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "stats"
FIRST_PUBLISHED = "2026-09-18"
DEFAULT_DB = BASE_DIR.parent / "05_Automotive_OBD2_MechanicDB" / "commercial_dataset" / "mechanicdb.sqlite"

SITE = Site(base_url="https://mechanicdb.dataengineered.io", brand="MechanicDB",
            snippet_label="MechanicDB OBD-II fault code statistics",
            surface="#1b1e22", surface2="#24282e", ink="#f1efe8", muted="#9aa3ad", grid="#2e333a", accent="#ffb000",
            font="'Archivo', system-ui, -apple-system, 'Segoe UI', sans-serif",
            mono="'IBM Plex Mono', ui-monospace, Menlo, Consolas, monospace")

SYSTEMS = ["Powertrain", "Chassis", "Body", "Network"]
SYSTEM_LETTER = {"Powertrain": "P", "Chassis": "C", "Body": "B", "Network": "U"}
DIFFICULTY = ["Easy DIY", "Moderate DIY", "Professional Required"]
COST_BUCKETS = [("under $50", 0, 50), ("$50 to $99", 50, 100), ("$100 to $249", 100, 250), ("$250 to $499", 250, 500),
                ("$500 to $999", 500, 1000), ("$1,000 and above", 1000, None)]
LABOR_BUCKETS = [("0.5 h or less", 0, 0.5), ("0.6 to 1.0 h", 0.5, 1.0), ("1.1 to 2.0 h", 1.0, 2.0), ("2.1 to 4.0 h", 2.0, 4.0), ("over 4 h", 4.0, None)]


def usd(v):
    return f"${v:,.0f}" if float(v).is_integer() else f"${v:,.2f}"


def hours(v):
    return f"{v:g} h"


def family_name(key):
    return key.replace("_", " ")


# ---------------------------------------------------------------------------
# statistics
# ---------------------------------------------------------------------------

def compute(db_path):
    con = sqlite3.connect(str(db_path))

    def q(sql, *a):
        return con.execute(sql, a).fetchall()

    def med(vals):
        return statistics.median(vals) if vals else 0

    s = {}
    s["snapshot_date"] = dt.date.fromtimestamp(Path(db_path).stat().st_mtime).isoformat()
    s["codes"] = q("select count(*) from dtc_codes")[0][0]
    s["sae_codes"] = q("select count(*) from dtc_codes where is_oem_specific=0")[0][0]
    s["oem_codes"] = q("select count(*) from dtc_codes where is_oem_specific=1")[0][0]
    s["makes"] = q("select count(distinct oem_make) from dtc_codes where is_oem_specific=1")[0][0]
    s["families"] = q("select count(distinct fault_family) from dtc_codes")[0][0]
    s["fixes"] = q("select count(*) from diagnostic_fixes")[0][0]
    s["parts"] = q("select count(*) from replacement_parts")[0][0]
    s["distinct_code_strings"] = q("select count(distinct dtc_code) from dtc_codes")[0][0]

    # 1. codes by system
    sysc = {(sc, oem): c for sc, oem, c in q("select system_category, is_oem_specific, count(*) from dtc_codes group by 1,2")}
    fams = dict(q("select system_category, count(distinct fault_family) from dtc_codes group by 1"))
    s["by_system"] = []
    for sc in SYSTEMS:
        sae, oem = sysc.get((sc, 0), 0), sysc.get((sc, 1), 0)
        s["by_system"].append(dict(system=sc, letter=SYSTEM_LETTER[sc], codes=sae + oem, share_pct=pct(sae + oem, s["codes"]), sae=sae, oem=oem, families=fams.get(sc, 0)))
    s["oem_systems"] = [sc for sc in SYSTEMS if sysc.get((sc, 1), 0)]

    # 2. OEM codes per make
    s["by_make"] = [(m, c, pct(c, s["oem_codes"])) for m, c in q("select oem_make, count(*) c from dtc_codes where is_oem_specific=1 group by 1 order by c desc, 1")]

    # 3. code strings defined by the most makes
    s["shared_codes"] = [(code, m, d) for code, m, d in q(
        "select dtc_code, count(distinct oem_make) m, count(distinct short_description) d from dtc_codes where is_oem_specific=1 group by 1 order by m desc, 1 limit 15")]
    s["oem_strings"] = q("select count(distinct dtc_code) from dtc_codes where is_oem_specific=1")[0][0]
    s["oem_strings_multi"] = q("select count(*) from (select dtc_code from dtc_codes where is_oem_specific=1 group by 1 having count(distinct oem_make) > 1)")[0][0]
    s["oem_overlap_sae"] = q("select count(*) from dtc_codes where is_oem_specific=1 and dtc_code in (select dtc_code from dtc_codes where is_oem_specific=0)")[0][0]

    # 4. fault families
    s["top_families"] = [(family_name(f), c, pct(c, s["codes"]), sc) for f, c, sc in q(
        "select fault_family, count(*) c, min(system_category) from dtc_codes group by 1 order by c desc, 1 limit 15")]
    s["top_first_steps"] = [(t, c) for t, c in q("select fix_title, count(*) c from diagnostic_fixes where probability_rank=1 group by 1 order by c desc, 1 limit 12")]
    fpc = dict(q("select n, count(*) from (select code_id, count(*) n from diagnostic_fixes group by 1) group by 1"))
    s["fixes_per_code"] = [(k, fpc[k], pct(fpc[k], s["codes"])) for k in sorted(fpc)]

    # 5. difficulty
    dall = dict(q("select difficulty_level, count(*) from diagnostic_fixes group by 1"))
    d1 = dict(q("select difficulty_level, count(*) from diagnostic_fixes where probability_rank=1 group by 1"))
    s["difficulty_all"] = [(d, dall.get(d, 0), pct(dall.get(d, 0), s["fixes"])) for d in DIFFICULTY]
    s["difficulty_rank1"] = [(d, d1.get(d, 0), pct(d1.get(d, 0), s["codes"])) for d in DIFFICULTY]
    ds = {}
    for sc, d, c in q("select c.system_category, f.difficulty_level, count(*) from diagnostic_fixes f join dtc_codes c using(code_id) group by 1,2"):
        ds.setdefault(sc, {})[d] = c
    s["difficulty_by_system"] = [(sc, {d: ds.get(sc, {}).get(d, 0) for d in DIFFICULTY}, sum(ds.get(sc, {}).values())) for sc in SYSTEMS]

    # 6. parts cost
    rows = q("select est_parts_cost_min_usd, est_parts_cost_max_usd, est_labor_hours, probability_rank, difficulty_level from diagnostic_fixes")
    s["fixes_with_cost"] = q("select count(*) from diagnostic_fixes where est_parts_cost_min_usd is not null and est_parts_cost_max_usd is not null")[0][0]
    s["fixes_with_labor"] = q("select count(*) from diagnostic_fixes where est_labor_hours is not null")[0][0]

    def cost_summary(label, sub):
        return dict(group=label, fixes=len(sub), median_min=med([r[0] for r in sub]), median_max=med([r[1] for r in sub]),
                    mean_max=round(statistics.mean([r[1] for r in sub]), 1) if sub else 0, median_labor=med([r[2] for r in sub]))
    s["cost_groups"] = [cost_summary("All fixes", rows), cost_summary("Most probable cause (rank 1)", [r for r in rows if r[3] == 1])]
    s["cost_groups"] += [cost_summary(d, [r for r in rows if r[4] == d]) for d in DIFFICULTY]
    bys = {}
    for sc, mn, mx, lh in q("select c.system_category, f.est_parts_cost_min_usd, f.est_parts_cost_max_usd, f.est_labor_hours from diagnostic_fixes f join dtc_codes c using(code_id)"):
        bys.setdefault(sc, []).append((mn, mx, lh))
    s["cost_by_system"] = [dict(system=sc, fixes=len(bys.get(sc, [])), median_min=med([r[0] for r in bys.get(sc, [])]), median_max=med([r[1] for r in bys.get(sc, [])]),
                                median_labor=med([r[2] for r in bys.get(sc, [])])) for sc in SYSTEMS]
    s["cost_buckets"] = []
    for label, lo, hi in COST_BUCKETS:
        c = sum(1 for r in rows if r[1] >= lo and (hi is None or r[1] < hi))
        s["cost_buckets"].append((label, c, pct(c, len(rows))))
    s["cost_max"] = max(r[1] for r in rows)
    s["cost_1000plus"] = sum(1 for r in rows if r[1] >= 1000)
    s["costliest"] = [(t, v, c) for t, v, c in q("select fix_title, est_parts_cost_max_usd, count(*) from diagnostic_fixes group by 1,2 order by 2 desc, 1 limit 8")]

    # 7. labor hours
    s["labor_buckets"] = []
    for label, lo, hi in LABOR_BUCKETS:
        c = sum(1 for r in rows if r[2] > lo and (hi is None or r[2] <= hi))
        s["labor_buckets"].append((label, c, pct(c, len(rows))))
    s["labor_median"] = med([r[2] for r in rows])
    s["labor_max"] = max(r[2] for r in rows)
    s["labor_by_difficulty"] = [(d, med([r[2] for r in rows if r[4] == d])) for d in DIFFICULTY]

    # 8. parts
    ppf = dict(q("select n, count(*) from (select fix_id, count(*) n from replacement_parts group by 1) group by 1"))
    s["parts_per_fix"] = [(k, ppf[k], pct(ppf[k], s["fixes"])) for k in sorted(ppf)]
    s["fixes_without_parts"] = q("select count(*) from diagnostic_fixes where fix_id not in (select fix_id from replacement_parts)")[0][0]
    s["parts_mean_per_fix"] = round(s["parts"] / s["fixes"], 2)
    s["distinct_parts"] = q("select count(distinct part_name) from replacement_parts")[0][0]
    s["top_parts"] = [(p, c, pct(c, s["fixes"])) for p, c in q("select part_name, count(*) c from replacement_parts group by 1 order by c desc, 1 limit 12")]
    con.close()
    return s


# ---------------------------------------------------------------------------
# page
# ---------------------------------------------------------------------------

CSS = """
    :root { --bg-paper: #1b1e22; --bg-paper-2: #24282e; --text-ink: #f1efe8; --text-muted: #9aa3ad;
            --rule-color: #2e333a; --accent: #ffb000; --radius: 6px;
            --mono: 'IBM Plex Mono', ui-monospace, monospace; --disp: 'Saira Condensed', sans-serif; --body: 'Archivo', system-ui, sans-serif; }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: var(--bg-paper); color: var(--text-ink); font-family: var(--body); font-size: 16px; line-height: 1.6; }
    a { color: var(--accent); text-decoration: none; } a:hover { text-decoration: underline; }
    .wrap { max-width: 1080px; margin: 0 auto; padding: 0 24px; }
    header.bar { border-bottom: 1px solid var(--rule-color); padding: 18px 0; }
    .bar-inner { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
    .wordmark { font-family: var(--disp); font-weight: 700; font-size: 1.35rem; text-transform: uppercase; color: #fff; display: flex; align-items: center; gap: 10px; }
    .mil { width: 22px; height: 16px; background: var(--accent); display: inline-block; }
    .bar-nav { font-family: var(--mono); font-size: .82rem; display: flex; gap: 20px; flex-wrap: wrap; }
    .stats-wrap { max-width: 1000px; margin: 0 auto; padding: 44px 24px 64px; }
    .stats-wrap h1 { font-family: var(--disp); font-size: clamp(2rem, 4vw, 3rem); line-height: 1.08; margin: 0 0 8px; color: #fff; text-transform: uppercase; letter-spacing: .03em; }
    .stats-wrap h2 { font-family: var(--disp); font-size: 1.6rem; margin: 0; color: #fff; text-transform: uppercase; letter-spacing: .02em; }
    .stats-wrap h3 { font-size: 1.05rem; margin: 24px 0 0; color: #fff; }
    .stats-wrap .lede { font-size: 1.05rem; margin-top: 12px; max-width: 76ch; color: var(--text-muted); }
    .crumb { font-family: var(--mono); font-size: .78rem; margin: 0 0 1rem; color: var(--text-muted); }
    .crumb a { color: var(--text-muted); } .crumb span { color: var(--accent); }
    .eyebrow { font-family: var(--mono); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.14em; color: var(--accent); margin-bottom: 10px; }
    .tiles strong { font-family: var(--mono); color: #fff; }
    .cta-inline { margin-top: 56px; padding: 28px; border: 1px solid var(--rule-color); border-radius: var(--radius); background: var(--bg-paper-2); }
    .cta-inline p { color: var(--text-muted); margin: 8px 0 16px; }
    .btn-amber { display: inline-block; background: var(--accent); color: #1b1500; font-family: var(--mono); font-weight: 600; padding: 12px 28px; border-radius: 4px; text-transform: uppercase; }
    .btn-amber:hover { background: #ffbe2e; text-decoration: none; }
    footer { border-top: 1px solid var(--rule-color); margin-top: 60px; padding: 30px 0; font-family: var(--mono); font-size: .76rem; text-align: center; color: var(--text-muted); }
"""


def build_page(s, charts):
    site = SITE
    snap = s["snapshot_date"]
    src_note = f"Source: MechanicDB, mechanicdb.dataengineered.io/stats · build {snap} · CC BY 4.0"
    sections = []

    # 1. by system
    bs = s["by_system"]
    charts["codes-by-system"] = svg_hbar(site, "OBD-II fault codes by vehicle system", f"{n(s['codes'])} codes (SAE standard + manufacturer-specific) by first letter",
                                         [(f"{r['system']} ({r['letter']}-codes)", r["codes"], f"{n(r['codes'])} ({r['share_pct']}%)") for r in bs], src_note, label_w=190)
    pw = bs[0]
    sections.append(section(
        site, "systems", "Fault codes by vehicle system",
        f"<strong>{pw['share_pct']}%</strong> of the {n(s['codes'])} catalogued codes are {data(pw['system'].lower())} codes ({data('P')}-codes): {n(pw['sae'])} SAE-standard and {n(pw['oem'])} manufacturer-specific. "
        f"{data('Network')} ({data('U')}) holds {n(bs[3]['codes'])}, {data('Chassis')} ({data('C')}) {n(bs[1]['codes'])} and {data('Body')} ({data('B')}) {n(bs[2]['codes'])}. "
        f"All {n(s['oem_codes'])} manufacturer-specific codes in the catalogue are {', '.join(data(x.lower()) for x in s['oem_systems'])} codes.",
        figure(site, "codes-by-system", charts["codes-by-system"], "OBD-II fault codes by vehicle system", f"{n(s['codes'])} codes"),
        table(["System", "Letter", "Codes", "Share", "SAE standard", "Manufacturer-specific", "Fault families"],
              [(r["system"], r["letter"], n(r["codes"]), f"{r['share_pct']}%", n(r["sae"]), n(r["oem"]), n(r["families"])) for r in bs], {2, 3, 4, 5, 6}),
        f"One row per code definition: SAE rows are unique by code string, manufacturer rows by make and code string, so a P1xxx string defined by several makes counts once per make. "
        f"The system is the code's first letter as defined by SAE J2012 / ISO 15031-6. {n(s['codes'])} definitions cover {n(s['distinct_code_strings'])} distinct code strings."))

    # 2. makes
    bm = s["by_make"]
    charts["oem-codes-by-make"] = svg_hbar(site, "Manufacturer-specific codes per make", f"Top 15 of {n(s['makes'])} makes, {n(s['oem_codes'])} manufacturer-specific codes",
                                           [(m, c, f"{n(c)} ({p}%)") for m, c, p in bm[:15]], src_note, label_w=130)
    sections.append(section(
        site, "makes", "Which makes have the most manufacturer-specific codes",
        f"{data(bm[0][0])} has the most manufacturer-specific codes in the catalogue with <strong>{n(bm[0][1])}</strong> ({bm[0][2]}% of {n(s['oem_codes'])}), followed by {data(bm[1][0])}, {data(bm[2][0])} and {data(bm[3][0])} with {n(bm[1][1])} each. "
        f"The {n(s['makes'])} makes range from {n(bm[0][1])} down to {n(bm[-1][1])} codes ({data(bm[-1][0])}).",
        figure(site, "oem-codes-by-make", charts["oem-codes-by-make"], "Manufacturer-specific codes per make", f"top 15 of {n(s['makes'])} makes"),
        table(["Make", "Manufacturer-specific codes", "Share of OEM codes"], [(m, n(c), f"{p}%") for m, c, p in bm], {1, 2}),
        "Counts describe the catalogue's coverage of each make's published code list, not how often the codes occur on the road. "
        "Sister brands that share a platform (for example the GM divisions, or Ford, Lincoln and Mercury) publish the same list and therefore show identical counts."))

    # 3. shared code strings
    sc = s["shared_codes"]
    charts["codes-shared-across-makes"] = svg_hbar(site, "Code strings defined by the most makes", f"Top 15 of {n(s['oem_strings'])} manufacturer-specific code strings",
                                                   [(code, m, f"{n(m)} makes") for code, m, d in sc], src_note, label_w=90)
    sections.append(section(
        site, "shared-codes", "Code strings that mean different things per make",
        f"<strong>{data(sc[0][0])}</strong> and {data(sc[1][0])} are each defined by {n(sc[0][1])} of the {n(s['makes'])} makes, with {n(sc[0][2])} and {n(sc[1][2])} distinct meanings respectively. "
        f"{n(s['oem_strings_multi'])} of the {n(s['oem_strings'])} manufacturer-specific code strings ({pct(s['oem_strings_multi'], s['oem_strings'])}%) are defined by more than one make"
        + (", and none of them reuses an SAE-standard string." if s["oem_overlap_sae"] == 0 else f"; {n(s['oem_overlap_sae'])} also exist as SAE-standard codes."),
        figure(site, "codes-shared-across-makes", charts["codes-shared-across-makes"], "Code strings defined by the most makes", f"top 15 of {n(s['oem_strings'])} strings"),
        table(["Code", "Makes defining it", "Distinct meanings"], [(code, n(m), n(d)) for code, m, d in sc], {1, 2}),
        "The P1xxx, P3xxx and higher ranges are reserved for manufacturers, so the same string carries a different definition per make; a generic code reader that shows only the string cannot tell them apart. "
        "Distinct meanings counts distinct short descriptions in the catalogue; makes that publish the same wording count once."))

    # 4. families and first steps
    tf = s["top_families"]
    charts["fault-families"] = svg_hbar(site, "Fault families with the most codes", f"Top 15 of {n(s['families'])} hand-authored families, {n(s['codes'])} codes",
                                        [(f, c, f"{n(c)} ({p}%)") for f, c, p, sc_ in tf], src_note, label_w=250)
    fs = s["top_first_steps"]
    fpc = s["fixes_per_code"]
    sections.append(section(
        site, "families", "Which fault families hold the most codes",
        f"<strong>{data(tf[0][0])}</strong> is the largest of the {n(s['families'])} fault families with {n(tf[0][1])} codes ({tf[0][2]}%), followed by {data(tf[1][0])} ({n(tf[1][1])}) and {data(tf[2][0])} ({n(tf[2][1])}). "
        f"Every code carries {fpc[0][0]} to {fpc[-1][0]} ranked fixes ({', '.join(f'{n(c)} codes with {k}' for k, c, p in fpc)}); the most frequent most-probable first step, {data(fs[0][0])}, is ranked first for {n(fs[0][1])} codes.",
        figure(site, "fault-families", charts["fault-families"], "Fault families with the most codes", f"top 15 of {n(s['families'])} families"),
        table(["Fault family", "Codes", "Share", "System"], [(f, n(c), f"{p}%", sc_) for f, c, p, sc_ in tf], {1, 2})
        + "<h3>Most frequent most-probable first step</h3>"
        + table(["Rank-1 fix title", "Codes where it is ranked first"], [(t, n(c)) for t, c in fs], {1}),
        "A fault family groups codes that share a failure mechanism and repair set; every code belongs to exactly one family. "
        "Rank 1 is the most probable root cause in the family's ranked repair set, so a family's first step is ranked first for every code in that family."))

    # 5. difficulty
    da, d1 = s["difficulty_all"], s["difficulty_rank1"]
    charts["difficulty-all-fixes"] = svg_hbar(site, "DIY difficulty of all ranked fixes", f"{n(s['fixes'])} ranked repair procedures",
                                              [(d, c, f"{n(c)} ({p}%)") for d, c, p in da], src_note, label_w=190)
    charts["difficulty-first-fix"] = svg_hbar(site, "DIY difficulty of the most probable fix per code", f"{n(s['codes'])} rank-1 fixes",
                                              [(d, c, f"{n(c)} ({p}%)") for d, c, p in d1], src_note, label_w=190)
    easy1 = next(p for d, c, p in d1 if d == "Easy DIY")
    pro1 = next(p for d, c, p in d1 if d == "Professional Required")
    dbs = s["difficulty_by_system"]
    sections.append(section(
        site, "difficulty", "How much of the repair work is DIY",
        f"Across all {n(s['fixes'])} ranked fixes, <strong>{da[0][2]}%</strong> are {data('Easy DIY')}, {da[1][2]}% {data('Moderate DIY')} and {da[2][2]}% {data('Professional Required')}. "
        f"Looking only at the most probable cause of each code, <strong>{easy1}%</strong> of the {n(s['codes'])} rank-1 fixes are Easy DIY and {pro1}% need a professional. "
        f"{data('Body')} codes have the highest professional share among rank-1 fixes; see the table.",
        figure(site, "difficulty-all-fixes", charts["difficulty-all-fixes"], "DIY difficulty of all ranked fixes", f"{n(s['fixes'])} fixes")
        + figure(site, "difficulty-first-fix", charts["difficulty-first-fix"], "DIY difficulty of the most probable fix per code", f"{n(s['codes'])} rank-1 fixes"),
        table(["System", "Fixes"] + DIFFICULTY, [(sc_, n(t)) + tuple(f"{n(d[k])} ({pct(d[k], t)}%)" for k in DIFFICULTY) for sc_, d, t in dbs], {1, 2, 3, 4}),
        "difficulty_level is assigned per fix by the editorial pipeline: Easy DIY (basic hand tools, no lifting or programming), Moderate DIY (specialty tools or partial disassembly), "
        "Professional Required (programming, high-voltage, SRS, internal transmission or engine work). The rank-1 fix is the first item of each code's probability-ranked repair set."))

    # 6. cost
    cg, cb = s["cost_groups"], s["cost_buckets"]
    charts["parts-cost-ranges"] = svg_hbar(site, "Upper parts-cost estimate per fix", f"{n(s['fixes'])} fixes by est_parts_cost_max_usd",
                                           [(lbl, c, f"{n(c)} ({p}%)") for lbl, c, p in cb], src_note, label_w=140)
    allc, r1 = cg[0], cg[1]
    sections.append(section(
        site, "repair-cost", "What the repairs are estimated to cost",
        f"Every one of the {n(s['fixes'])} fixes carries a parts-cost range ({pct(s['fixes_with_cost'], s['fixes'])}% coverage). The median range is <strong>{usd(allc['median_min'])} to {usd(allc['median_max'])}</strong> in parts; "
        f"for the most probable fix per code it is {usd(r1['median_min'])} to {usd(r1['median_max'])}. "
        f"{cb[0][2]}% of fixes top out under $50 and {pct(s['cost_1000plus'], s['fixes'])}% ({n(s['cost_1000plus'])}) at $1,000 or more; the highest upper estimate is {usd(s['cost_max'])} ({data(s['costliest'][0][0])}).",
        figure(site, "parts-cost-ranges", charts["parts-cost-ranges"], "Upper parts-cost estimate per fix", f"{n(s['fixes'])} fixes"),
        table(["Group", "Fixes", "Median lower estimate", "Median upper estimate", "Mean upper estimate", "Median labor"],
              [(g["group"], n(g["fixes"]), usd(g["median_min"]), usd(g["median_max"]), usd(g["mean_max"]), hours(g["median_labor"])) for g in cg], {1, 2, 3, 4, 5})
        + "<h3>By vehicle system</h3>"
        + table(["System", "Fixes", "Median lower estimate", "Median upper estimate", "Median labor"],
                [(g["system"], n(g["fixes"]), usd(g["median_min"]), usd(g["median_max"]), hours(g["median_labor"])) for g in s["cost_by_system"]], {1, 2, 3, 4})
        + "<h3>Highest upper estimates</h3>"
        + table(["Fix", "Upper estimate", "Fixes"], [(t, usd(v), n(c)) for t, v, c in s["costliest"]], {1, 2}),
        "est_parts_cost_min_usd and est_parts_cost_max_usd are the dataset's editorial aftermarket parts estimates in US dollars at build time; they are not quotes, exclude labor and vary by vehicle and region. "
        "Medians are computed over fixes, so a family with 397 codes weighs 397 times. Compare groups within this page, not against a shop invoice."))

    # 7. labor
    lb = s["labor_buckets"]
    charts["labor-hours"] = svg_hbar(site, "Estimated labor hours per fix", f"{n(s['fixes'])} fixes by est_labor_hours",
                                     [(lbl, c, f"{n(c)} ({p}%)") for lbl, c, p in lb], src_note, label_w=130)
    lbd = s["labor_by_difficulty"]
    sections.append(section(
        site, "labor", "How long the repairs are estimated to take",
        f"The median fix is estimated at <strong>{hours(s['labor_median'])}</strong> of labor; {lb[0][2]}% of fixes are {lb[0][0]} and {lb[-1][2]}% are {lb[-1][0]}, with a maximum of {hours(s['labor_max'])}. "
        f"By difficulty the medians are {hours(lbd[0][1])} ({data(lbd[0][0])}), {hours(lbd[1][1])} ({data(lbd[1][0])}) and {hours(lbd[2][1])} ({data(lbd[2][0])}).",
        figure(site, "labor-hours", charts["labor-hours"], "Estimated labor hours per fix", f"{n(s['fixes'])} fixes"),
        table(["Labor estimate", "Fixes", "Share"], [(lbl, n(c), f"{p}%") for lbl, c, p in lb], {1, 2})
        + "<h3>Median labor by difficulty</h3>"
        + table(["Difficulty", "Median labor"], [(d, hours(v)) for d, v in lbd], {1}),
        f"est_labor_hours is the dataset's editorial estimate of hands-on time for a shop, present on {pct(s['fixes_with_labor'], s['fixes'])}% of fixes; diagnosis time before the repair is not included."))

    # 8. parts
    tp = s["top_parts"]
    ppf = s["parts_per_fix"]
    charts["parts-most-mapped"] = svg_hbar(site, "Parts and supplies mapped to the most fixes", f"Top 12 of {n(s['distinct_parts'])} catalogue items, {n(s['parts'])} mappings",
                                           [((p[:40].rstrip() + "…") if len(p) > 41 else p, c, f"{n(c)}") for p, c, sh in tp], src_note, label_w=300)
    sections.append(section(
        site, "parts", "Which parts and supplies the fixes call for",
        f"The {n(s['fixes'])} fixes map to <strong>{n(s['parts'])}</strong> replacement-part entries, {s['parts_mean_per_fix']} per fix on average ({', '.join(f'{p}% with {k}' for k, c, p in ppf)}), "
        f"drawn from {n(s['distinct_parts'])} distinct catalogue items. {data(tp[0][0])} is mapped to the most fixes ({n(tp[0][1])}, {tp[0][2]}%), ahead of {data(tp[1][0])} ({n(tp[1][1])}) and {data(tp[2][0])} ({n(tp[2][1])}).",
        figure(site, "parts-most-mapped", charts["parts-most-mapped"], "Parts and supplies mapped to the most fixes", f"top 12 of {n(s['distinct_parts'])} items"),
        table(["Part or supply", "Fixes mapped", "Share of fixes"], [(p, n(c), f"{sh}%") for p, c, sh in tp], {1, 2}),
        f"Each replacement_parts row links one fix to one catalogue item with a search query, not a part number; {n(s['fixes_without_parts'])} fixes have no mapping. "
        f"Tools and consumables (wiring kits, contact cleaner, multimeters) are catalogue items too, which is why they lead the count."))

    contents = toc([("systems", "Codes by vehicle system"), ("makes", "Codes per make"), ("shared-codes", "Code strings shared across makes"),
                    ("families", "Fault families and first steps"), ("difficulty", "DIY difficulty"), ("repair-cost", "Repair cost estimates"),
                    ("labor", "Labor hours"), ("parts", "Parts and supplies"), ("method", "Method, reuse and citation")])
    tile_html = tiles([("Fault codes", n(s["codes"])), ("SAE standard", n(s["sae_codes"])), ("Manufacturer-specific", n(s["oem_codes"])), ("Makes", n(s["makes"])),
                       ("Ranked fixes", n(s["fixes"])), ("Fault families", n(s["families"])), ("Parts mappings", n(s["parts"])), ("Build", snap)], date_labels=("Build",))
    title_tag = f"OBD-II Fault Code Statistics {snap[:4]} — Codes by System, Repair Cost, DIY Share | MechanicDB"
    desc = (f"OBD-II diagnostic trouble codes in numbers: {n(s['codes'])} codes across {n(s['makes'])} makes and {n(s['fixes'])} ranked fixes. Codes by vehicle system and make, "
            f"code strings shared across makes, fault families, DIY difficulty ({easy1}% of most-probable fixes are Easy DIY), parts-cost and labor estimates, most-mapped parts. Free to cite and embed.")
    ld = article_ld(site, "OBD-II fault codes in numbers: statistics from the MechanicDB catalogue", desc, FIRST_PUBLISHED,
                    f"{site.base_url}/assets/kaggle-cover.png", ["OBD-II", "diagnostic trouble codes", "car repair", "DIY", "automotive diagnostics"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title_tag)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{site.page_url}">
<link rel="alternate" hreflang="en" href="{site.page_url}">
<meta property="og:title" content="OBD-II fault codes in numbers — MechanicDB statistics {snap[:4]}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{site.page_url}">
<meta property="og:image" content="{site.base_url}/assets/kaggle-cover.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1b1e22">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@500;600;700&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" media="print" onload="this.media='all'"><noscript><link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@500;600;700&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet"></noscript>
{ld}
<style>{CSS}{STATS_CSS}</style>
</head>
<body>
<header class="bar">
  <div class="wrap bar-inner">
    <a href="/" class="wordmark"><span class="mil" aria-hidden="true"></span>MechanicDB</a>
    <nav class="bar-nav" aria-label="Site">
      <a href="/#interactive">Decoder</a>
      <a href="/#licensing">Dataset License ($49)</a>
      <a href="/landing/families">Fault families</a>
      <a href="/#faq">FAQ</a>
    </nav>
  </div>
</header>
<main class="stats-wrap">
  <p class="crumb"><a href="/">Home</a> / <span>Statistics</span></p>
  <p class="eyebrow">Catalogue statistics · build {esc(snap)}</p>
  <h1>OBD-II fault codes in numbers</h1>
  <p class="lede">Aggregate statistics computed from the full MechanicDB dataset: {n(s['codes'])} diagnostic trouble codes ({n(s['sae_codes'])} SAE-standard, {n(s['oem_codes'])} manufacturer-specific across {n(s['makes'])} makes) mapped to {n(s['fixes'])} probability-ranked repair procedures with difficulty, parts-cost and labor estimates. These figures describe the catalogue, not how often codes are set on the road. Every figure states its denominator and is free to cite, quote and embed with a link to this page.</p>
  <ul class="tiles">{tile_html}</ul>
  <nav class="toc" aria-label="Contents"><strong>On this page</strong><ol>{contents}</ol></nav>

{"".join(sections)}

  <section class="stat" id="method">
    <h2>Method, reuse and citation</h2>
    <ul class="method">
      <li><strong>Source.</strong> The full MechanicDB build of {snap}: {n(s['codes'])} code definitions, {n(s['fixes'])} ranked fixes and {n(s['parts'])} part mappings in {n(s['families'])} hand-authored fault families. Code definitions originate in SAE J2012 / ISO 15031-6 via an MIT-licensed upstream compilation; the repair content is original editorial material from a deterministic, test-gated pipeline. See <a href="/SOURCES.md">Sources</a> and the <a href="/DATA_DICTIONARY.md">data dictionary</a>.</li>
      <li><strong>Catalogue, not incidence.</strong> MechanicDB records what each code means and how it is repaired. No figure on this page measures how often a code appears on real vehicles; "most common" here always means most common within the catalogue, and each section says which denominator it uses.</li>
      <li><strong>Estimates are estimates.</strong> Parts costs (USD) and labor hours are the dataset's editorial values at build time, useful for comparison between fixes, not quotes. Difficulty is an editorial tier. Repair steps are educational reference material, not professional repair advice; high-voltage and SRS/airbag work requires qualified technicians.</li>
      <li><strong>Refresh.</strong> MechanicDB is curated; this page and its charts are regenerated with each new build, so figures move. Cite the build date.</li>
      <li><strong>Reuse.</strong> The figures and charts on this page are published under <a href="https://creativecommons.org/licenses/by/4.0/" rel="license">CC BY 4.0</a>: use them in forum posts, articles, slides and videos with a link to <span translate="no">{site.page_url}</span>. The machine-readable version is <a href="/stats/data.json">data.json</a>. The row-level dataset is a separate <a href="/#licensing">commercial product</a>; a free 90-code sample is in the <a href="https://github.com/MechanicDB/MechanicDB-public">public repository</a>.</li>
      <li><strong>Suggested citation.</strong> <span translate="no">MechanicDB ({snap[:4]}). <em>OBD-II fault codes in numbers</em>, build {snap}. DataEngineered. {site.page_url}</span></li>
      <li><strong>Questions or corrections:</strong> <a href="/#contact">contact form</a> or mechanicdb@dataengineered.io.</li>
    </ul>
  </section>

  <div class="cta-inline">
    <h3 style="margin:0">Need the code-level records behind these numbers?</h3>
    <p>Every code with its ranked fixes, difficulty, parts-cost range, labor hours, step-by-step instructions and part mappings, as CSV, Parquet and SQLite.</p>
    <a class="btn-amber" href="/#licensing">License the dataset · from $49</a>
  </div>
</main>
<footer><div class="wrap"><span>MechanicDB &middot; The OBD-II Diagnostic &amp; Repair Database &middot; ODbL v1.0 / Commercial License</span>
<div class="catalog-line" style="text-align:center; margin-top:14px; font-size:0.85rem; opacity:0.85;"><a href="https://dataengineered.io/">Part of the DataEngineered catalog &rarr;</a> &middot; <a href="https://dataengineered.io/about">About</a> &middot; <a href="https://dataengineered.io/terms">Terms</a> &middot; <a href="https://dataengineered.io/privacy">Privacy</a> &middot; <a href="https://dataengineered.io/refund-policy">Refund policy</a></div></div></footer>
{COPY_JS}
</body>
</html>
"""


def build_data_json(s):
    return {
        "dataset": SITE.brand, "page": SITE.page_url, "generated": dt.date.today().isoformat(), "build": s["snapshot_date"],
        "license": "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) - attribute with a link to the page",
        "note": "Catalogue statistics: nothing here measures how often a code is set on real vehicles. Costs and labor hours are editorial estimates, not quotes.",
        "totals": {k: s[k] for k in ("codes", "sae_codes", "oem_codes", "makes", "families", "fixes", "parts", "distinct_code_strings")},
        "by_system": s["by_system"],
        "oem_codes_by_make": [dict(make=m, codes=c, share_pct=p) for m, c, p in s["by_make"]],
        "code_strings_shared_across_makes": {"oem_strings": s["oem_strings"], "defined_by_more_than_one_make": s["oem_strings_multi"], "overlapping_sae": s["oem_overlap_sae"],
                                             "top": [dict(code=c, makes=m, distinct_meanings=d) for c, m, d in s["shared_codes"]]},
        "fault_families": {"top": [dict(family=f, codes=c, share_pct=p, system=sc) for f, c, p, sc in s["top_families"]],
                           "fixes_per_code": [dict(fixes=k, codes=c, share_pct=p) for k, c, p in s["fixes_per_code"]],
                           "top_rank1_fix_titles": [dict(title=t, codes=c) for t, c in s["top_first_steps"]]},
        "difficulty": {"all_fixes": [dict(level=d, fixes=c, share_pct=p) for d, c, p in s["difficulty_all"]],
                       "rank1_fixes": [dict(level=d, fixes=c, share_pct=p) for d, c, p in s["difficulty_rank1"]],
                       "by_system": [dict(system=sc, fixes=t, **{k.lower().replace(" ", "_"): v for k, v in d.items()}) for sc, d, t in s["difficulty_by_system"]]},
        "parts_cost_usd": {"fixes_with_range": s["fixes_with_cost"], "groups": s["cost_groups"], "by_system": s["cost_by_system"],
                           "upper_estimate_buckets": [dict(bucket=b, fixes=c, share_pct=p) for b, c, p in s["cost_buckets"]],
                           "max_upper_estimate": s["cost_max"], "highest": [dict(fix=t, upper_estimate=v, fixes=c) for t, v, c in s["costliest"]]},
        "labor_hours": {"fixes_with_estimate": s["fixes_with_labor"], "median": s["labor_median"], "max": s["labor_max"],
                        "buckets": [dict(bucket=b, fixes=c, share_pct=p) for b, c, p in s["labor_buckets"]],
                        "median_by_difficulty": [dict(level=d, median_hours=v) for d, v in s["labor_by_difficulty"]]},
        "parts": {"mappings": s["parts"], "distinct_items": s["distinct_parts"], "mean_per_fix": s["parts_mean_per_fix"], "fixes_without_mapping": s["fixes_without_parts"],
                  "per_fix": [dict(parts=k, fixes=c, share_pct=p) for k, c, p in s["parts_per_fix"]],
                  "most_mapped": [dict(item=p, fixes=c, share_pct=sh) for p, c, sh in s["top_parts"]]},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--db", default=os.environ.get("MECHANICDB_SQLITE", str(DEFAULT_DB)))
    args = ap.parse_args()
    db = Path(args.db)
    if not db.is_file():
        raise SystemExit(f"SQLite dataset not found: {db}")
    s = compute(db)
    charts = {}
    page = build_page(s, charts)
    write_outputs(OUT_DIR, page, charts, build_data_json(s))
    print(f"stats/index.html + {len(charts)} charts + data.json  (build {s['snapshot_date']}, {s['codes']:,} codes)")


if __name__ == "__main__":
    main()
