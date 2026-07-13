#!/usr/bin/env python3
"""
MechanicDB Static Diagnostic Monograph & Category Hub Generator
Transforms dtc_codes.csv, diagnostic_fixes.csv, and replacement_parts.csv into:
  1. ~90+ standalone OBD-II code pages (landing/<dtc_code>.html)
  2. 4 system category index hubs (landing/<system>.html)
  3. Complete sitemap.xml (~100 clean URLs)
"""

import os
import csv
import json
import html
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANDING_DIR = os.path.join(BASE_DIR, "landing")
DTC_CSV = os.path.join(BASE_DIR, "dtc_codes.csv")
FIXES_CSV = os.path.join(BASE_DIR, "diagnostic_fixes.csv")
PARTS_CSV = os.path.join(BASE_DIR, "replacement_parts.csv")
SITEMAP_XML = os.path.join(BASE_DIR, "sitemap.xml")

DOMAIN = "https://mechanicdb-public.pages.dev"


def clean_url(fname):
    """Cloudflare Pages serves <name>.html at the extensionless clean URL and
    308-redirects the .html form; public URLs must use the clean final form
    (a service worker may not answer a navigation with a redirected response)."""
    return fname[:-5] if fname.endswith(".html") else fname

def load_data():
    dtc_map = {} # code_id -> dtc dict
    dtc_by_code = {} # dtc_code -> dtc dict

    if os.path.exists(DTC_CSV):
        with open(DTC_CSV, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter="|")
            for row in reader:
                cid = row["code_id"].strip()
                code = row["dtc_code"].strip()
                row["fixes"] = []
                dtc_map[cid] = row
                dtc_by_code[code] = row

    parts_map = {} # fix_id -> list of part dicts
    if os.path.exists(PARTS_CSV):
        with open(PARTS_CSV, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter="|")
            for row in reader:
                fid = row["fix_id"].strip()
                parts_map.setdefault(fid, []).append(row)

    if os.path.exists(FIXES_CSV):
        with open(FIXES_CSV, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter="|")
            for row in reader:
                cid = row["code_id"].strip()
                fid = row["fix_id"].strip()
                row["parts"] = parts_map.get(fid, [])
                if cid in dtc_map:
                    dtc_map[cid]["fixes"].append(row)

    # Sort fixes by probability_rank
    for cid, dtc in dtc_map.items():
        dtc["fixes"].sort(key=lambda x: int(x["probability_rank"]) if x["probability_rank"].isdigit() else 99)

    return dtc_by_code

def chip_class(diff):
    if diff == "Easy DIY": return "chip chip-easy"
    if diff == "Moderate DIY": return "chip chip-mod"
    return "chip chip-pro"

def chip_color(diff):
    if diff == "Easy DIY": return "#4caf6d"
    if diff == "Moderate DIY": return "#e8a13d"
    return "#d65454"

def generate_code_page(code, dtc):
    code_esc = html.escape(code)
    short_esc = html.escape(dtc.get("short_description", code))
    explain_esc = html.escape(dtc.get("detailed_technical_explanation", ""))
    sys_cat = dtc.get("system_category", "Powertrain")
    is_oem = dtc.get("is_oem_specific", "0") == "1"
    oem_make = dtc.get("oem_make", "")
    family = dtc.get("fault_family", "")

    page_url = f"{DOMAIN}/landing/{code}"

    sys_file_map = {
        "Powertrain": "powertrain.html",
        "Chassis": "chassis.html",
        "Body": "body.html",
        "Network": "network.html"
    }
    sys_url = f"{DOMAIN}/landing/{clean_url(sys_file_map.get(sys_cat, 'powertrain.html'))}"

    # Build repair procedures HTML
    fixes_html = ""
    for f in dtc["fixes"]:
        rank = html.escape(f.get("probability_rank", "-"))
        title = html.escape(f.get("fix_title", "Repair Procedure"))
        diff = f.get("difficulty_level", "Moderate DIY")
        min_c = html.escape(f.get("est_parts_cost_min_usd", "0"))
        max_c = html.escape(f.get("est_parts_cost_max_usd", "0"))
        hrs = html.escape(f.get("est_labor_hours", "1.0"))
        steps_raw = f.get("step_by_step_instructions", "")
        
        steps_list = [s.strip() for s in steps_raw.split("•") if s.strip()]
        if not steps_list:
            steps_list = [steps_raw] if steps_raw else []

        steps_html = "<ol class='step-list'>" + "".join(f"<li>{html.escape(s)}</li>" for s in steps_list) + "</ol>"

        parts_html = ""
        if f["parts"]:
            parts_links = []
            for p in f["parts"]:
                pname = html.escape(p.get("part_name", "Part"))
                purl = html.escape(p.get("amazon_search_query", "#"))
                parts_links.append(f"<a href='{purl}' target='_blank' rel='noopener noreferrer' class='part-link'>🔧 {pname}</a>")
            parts_html = "<div class='parts-req'><b>Required Replacement Parts:</b> " + " · ".join(parts_links) + "</div>"

        fixes_html += f"""
        <div class="fix-card">
          <div class="fix-header">
            <span class="rank-badge">Rank #{rank}</span>
            <h3 class="fix-title">{title}</h3>
            <span class="{chip_class(diff)}" style="background: {chip_color(diff)}25; color: {chip_color(diff)}; border: 1px solid {chip_color(diff)};">{html.escape(diff)}</span>
          </div>
          <div class="fix-meta">
            <span>Parts Estimate: <b>${min_c}–${max_c} USD</b></span>
            <span>Labor Estimate: <b>{hrs} Shop Hours</b></span>
          </div>
          <div class="fix-body">
            {steps_html}
            {parts_html}
          </div>
        </div>
        """

    if not fixes_html:
        fixes_html = "<p style='color: var(--trace);'>Exact repair procedures for this diagnostic trouble code are accessible within the full SQL/Parquet database release.</p>"

    # JSON-LD schemas
    json_ld_article = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": f"OBD-II Code {code}: {dtc.get('short_description', '')}",
        "description": dtc.get("detailed_technical_explanation", ""),
        "url": page_url,
        "author": {"@type": "Organization", "name": "MechanicDB"},
        "publisher": {"@type": "Organization", "name": "MechanicDB", "url": DOMAIN},
        "about": {
            "@type": "Thing",
            "name": f"Automotive Diagnostic Trouble Code {code}",
            "description": f"OBD-II {sys_cat} Fault: {dtc.get('short_description', '')}"
        }
    }

    json_ld_breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN},
            {"@type": "ListItem", "position": 2, "name": f"{sys_cat} System ({code[0]}-Codes)", "item": sys_url},
            {"@type": "ListItem", "position": 3, "name": f"Code {code}", "item": page_url}
        ]
    }

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Code {code_esc} — {short_esc} — MechanicDB OBD-II Diagnostic Guide</title>
<meta name="description" content="Detailed diagnostic explanation and probability-ranked repair procedures for OBD-II Code {code_esc} ({short_esc}). DIY difficulty tiers, parts cost ranges (${min_c}–${max_c} USD), and labor estimates.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{page_url}">
<link rel="alternate" hreflang="en" href="{page_url}">
<link rel="alternate" hreflang="x-default" href="{page_url}">
<meta property="og:title" content="Code {code_esc} — {short_esc} — MechanicDB">
<meta property="og:description" content="{explain_esc[:180]}...">
<meta property="og:url" content="{page_url}">
<meta property="og:type" content="article">

<script type="application/ld+json">{json.dumps(json_ld_article)}</script>
<script type="application/ld+json">{json.dumps(json_ld_breadcrumb)}</script>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@500;600;700&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
<noscript><link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@500;600;700&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet"></noscript>
<style>
  :root {{
    --steel: #1b1e22; --steel-2: #24282e; --steel-3: #2e333a;
    --paper: #f1efe8; --ink: #22252a; --trace: #9aa3ad;
    --amber: #ffb000; --amber-deep: #cc8a00;
    --easy: #4caf6d; --mod: #e8a13d; --pro: #d65454;
    --mono: 'IBM Plex Mono', ui-monospace, monospace;
    --disp: 'Saira Condensed', sans-serif;
    --body: 'Archivo', system-ui, sans-serif;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--steel); color: var(--trace); font-family: var(--body); font-size: 16px; line-height: 1.6; }}
  a {{ color: var(--amber); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .wrap {{ max-width: 1080px; margin: 0 auto; padding: 0 24px; }}
  header.bar {{ border-bottom: 1px solid var(--steel-3); padding: 18px 0; }}
  .bar-inner {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }}
  .wordmark {{ font-family: var(--disp); font-weight: 700; font-size: 1.35rem; text-transform: uppercase; color: #fff; display: flex; align-items: center; gap: 10px; }}
  .mil {{ width: 22px; height: 16px; background: var(--amber); display: inline-block; }}
  
  .breadcrumb {{ font-family: var(--mono); font-size: 0.78rem; margin: 24px 0 16px; }}
  .breadcrumb a {{ color: var(--trace); }}
  .breadcrumb span {{ color: var(--amber); }}

  .monograph-head {{ background: var(--steel-2); border: 1px solid var(--steel-3); border-radius: 8px; padding: 32px; margin-bottom: 36px; box-shadow: 0 14px 40px rgba(0,0,0,0.35); }}
  .badges {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }}
  .badge {{ font-family: var(--mono); font-size: 0.74rem; padding: 4px 10px; border-radius: 3px; background: var(--steel); border: 1px solid var(--steel-3); color: var(--amber); text-transform: uppercase; letter-spacing: 0.08em; }}
  h1 {{ font-family: var(--disp); font-size: clamp(2.2rem, 5vw, 3.4rem); color: #fff; line-height: 1.1; margin-bottom: 18px; text-transform: uppercase; letter-spacing: 0.03em; }}
  .explain-box {{ background: var(--steel); border-left: 4px solid var(--amber); padding: 20px; border-radius: 4px; font-size: 1.05rem; color: #fff; line-height: 1.6; margin-top: 20px; }}
  .explain-title {{ font-family: var(--mono); font-size: 0.78rem; color: var(--amber); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }}

  h2.sec-title {{ font-family: var(--disp); font-size: 1.8rem; color: #fff; text-transform: uppercase; margin: 40px 0 20px; border-bottom: 1px solid var(--steel-3); padding-bottom: 10px; }}
  
  .fix-card {{ background: var(--steel-2); border: 1px solid var(--steel-3); border-radius: 6px; padding: 24px; margin-bottom: 24px; }}
  .fix-header {{ display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; margin-bottom: 14px; }}
  .rank-badge {{ font-family: var(--mono); font-size: 0.76rem; background: var(--amber); color: #1b1500; padding: 3px 10px; border-radius: 3px; font-weight: 700; }}
  .fix-title {{ font-family: var(--disp); font-size: 1.35rem; color: #fff; flex: 1; min-width: 240px; text-transform: uppercase; }}
  .chip {{ font-family: var(--mono); font-size: 0.74rem; font-weight: 600; padding: 4px 10px; border-radius: 3px; }}
  .fix-meta {{ display: flex; gap: 24px; font-family: var(--mono); font-size: 0.82rem; color: #d7dce2; background: var(--steel); padding: 10px 14px; border-radius: 4px; margin-bottom: 16px; flex-wrap: wrap; }}
  .fix-meta b {{ color: var(--amber); }}
  
  .step-list {{ margin-left: 20px; color: #d7dce2; line-height: 1.7; font-size: 0.96rem; }}
  .step-list li {{ margin-bottom: 8px; }}
  .parts-req {{ margin-top: 18px; padding-top: 14px; border-top: 1px dashed var(--steel-3); font-size: 0.92rem; }}
  .part-link {{ display: inline-block; background: var(--steel); border: 1px solid var(--steel-3); padding: 4px 10px; border-radius: 4px; margin: 4px 4px 0 0; color: #fff; }}
  .part-link:hover {{ border-color: var(--amber); color: var(--amber); }}

  .cta-footer {{ background: var(--paper); color: var(--ink); border-radius: 8px; padding: 36px; text-align: center; margin: 60px 0 40px; }}
  .cta-footer h3 {{ font-family: var(--disp); font-size: 2rem; text-transform: uppercase; margin-bottom: 10px; }}
  .btn-amber {{ display: inline-block; background: var(--amber); color: #1b1500; font-family: var(--mono); font-weight: 600; padding: 12px 28px; border-radius: 4px; margin-top: 16px; text-transform: uppercase; }}
  .btn-amber:hover {{ background: #ffbe2e; text-decoration: none; }}

  footer {{ border-top: 1px solid var(--steel-3); padding: 30px 0; font-family: var(--mono); font-size: 0.76rem; text-align: center; }}
</style>
</head>
<body>

<header class="bar">
  <div class="wrap bar-inner">
    <a href="/" class="wordmark"><span class="mil" aria-hidden="true"></span>MechanicDB</a>
    <nav style="font-family: var(--mono); font-size: 0.82rem; display: flex; gap: 20px;">
      <a href="/#interactive">Decoder</a>
      <a href="/#licensing">Dataset License ($49)</a>
      <a href="/#faq">FAQ</a>
    </nav>
  </div>
</header>

<div class="wrap">
  <div class="breadcrumb">
    <a href="/">Home</a> / <a href="/#interactive">Diagnostic Decoder</a> / <a href="{clean_url(sys_file_map.get(sys_cat, 'powertrain.html'))}">{sys_cat} System</a> / <span>Code {code_esc}</span>
  </div>

  <div class="monograph-head">
    <div class="badges">
      <span class="badge">System: {html.escape(sys_cat)} ({code_esc[0]}-Code)</span>
      <span class="badge">Coverage: {"OEM Specific (" + html.escape(oem_make) + ")" if is_oem else "SAE Standard (Generic)"}</span>
      <span class="badge">Fault Family: {html.escape(family)}</span>
    </div>
    <h1>Code {code_esc}: {short_esc}</h1>
    <div class="explain-box">
      <div class="explain-title">Diagnostic &amp; Technical Explanation</div>
      {explain_esc if explain_esc else "Standard automotive diagnostic trouble code logged when the powertrain, chassis, or body module detects a circuit or sensor performance deviation."}
    </div>
  </div>

  <h2 class="sec-title">Probability-Ranked Repair Procedures ({len(dtc['fixes'])} Ranked Fixes)</h2>
  {fixes_html}

  <div class="cta-footer">
    <h3>Need All 15,886 OBD-II Codes &amp; 56,561 Fixes?</h3>
    <p>Download the complete commercial MechanicDB dataset instantly. Includes CSV, Apache Parquet tables, and a relational SQLite database with commercial application rights.</p>
    <a href="https://buy.stripe.com/5kQ3cw7Be9b88rNfuU38403" class="btn-amber">License Full Dataset · Instant Download ($49)</a>
  </div>
</div>

<footer>
  <div class="wrap">
    <span>MechanicDB · The OBD-II Diagnostic &amp; Repair Database · ODbL v1.0 / Commercial License</span>
  </div>
</footer>

</body>
</html>
"""
    with open(os.path.join(LANDING_DIR, f"{code}.html"), "w", encoding="utf-8") as f:
        f.write(content)

def generate_category_hub(sys_cat, filename, title, codes_list):
    page_url = f"{DOMAIN}/landing/{clean_url(filename)}"
    
    # Sort codes alphabetically
    codes_list.sort(key=lambda x: x["dtc_code"])

    rows_html = ""
    for c in codes_list:
        code = html.escape(c["dtc_code"])
        desc = html.escape(c.get("short_description", code))
        family = html.escape(c.get("fault_family", ""))
        num_fixes = len(c.get("fixes", []))
        is_oem = c.get("is_oem_specific", "0") == "1"
        badge_txt = f"OEM ({html.escape(c.get('oem_make', ''))})" if is_oem else "SAE Standard"

        rows_html += f"""
        <tr>
          <td><a href="{code}" style="font-family: var(--mono); font-weight: 700; font-size: 1.1rem; color: var(--amber);">{code}</a></td>
          <td style="color: #fff; font-weight: 500;">{desc}</td>
          <td><span style="font-family: var(--mono); font-size: 0.74rem; background: var(--steel); padding: 3px 8px; border-radius: 3px;">{family}</span></td>
          <td><span style="font-family: var(--mono); font-size: 0.78rem; color: #d7dce2;">{badge_txt}</span></td>
          <td style="text-align: right; font-family: var(--mono); color: #86e8a7;">{num_fixes} fixes</td>
        </tr>
        """

    json_ld_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": title,
        "description": f"Automotive OBD-II diagnostic trouble codes for the {sys_cat} system.",
        "url": page_url,
        "numberOfItems": len(codes_list),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": idx + 1,
                "name": f"Code {c['dtc_code']} ({c.get('short_description', '')})",
                "url": f"{DOMAIN}/landing/{c['dtc_code']}"
            }
            for idx, c in enumerate(codes_list[:50])
        ]
    }

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} — MechanicDB OBD-II Directory</title>
<meta name="description" content="Browse verified {html.escape(sys_cat)} OBD-II diagnostic trouble codes with probability-ranked repair procedures, DIY difficulty ratings, and parts cost estimates.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{page_url}">
<link rel="alternate" hreflang="en" href="{page_url}">
<link rel="alternate" hreflang="x-default" href="{page_url}">
<script type="application/ld+json">{json.dumps(json_ld_list)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@500;600;700&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" media="print" onload="this.media='all'">
<noscript><link href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@500;600;700&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet"></noscript>
<style>
  :root {{ --steel: #1b1e22; --steel-2: #24282e; --steel-3: #2e333a; --paper: #f1efe8; --ink: #22252a; --trace: #9aa3ad; --amber: #ffb000; --mono: 'IBM Plex Mono', monospace; --disp: 'Saira Condensed', sans-serif; --body: 'Archivo', sans-serif; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--steel); color: var(--trace); font-family: var(--body); font-size: 16px; line-height: 1.6; }}
  a {{ color: var(--amber); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .wrap {{ max-width: 1080px; margin: 0 auto; padding: 0 24px; }}
  header.bar {{ border-bottom: 1px solid var(--steel-3); padding: 18px 0; }}
  .bar-inner {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }}
  .wordmark {{ font-family: var(--disp); font-weight: 700; font-size: 1.35rem; text-transform: uppercase; color: #fff; display: flex; align-items: center; gap: 10px; }}
  .mil {{ width: 22px; height: 16px; background: var(--amber); display: inline-block; }}
  
  .breadcrumb {{ font-family: var(--mono); font-size: 0.78rem; margin: 24px 0 16px; }}
  h1 {{ font-family: var(--disp); font-size: clamp(2.2rem, 5vw, 3.2rem); color: #fff; line-height: 1.1; margin-bottom: 14px; text-transform: uppercase; }}
  
  table.code-table {{ width: 100%; border-collapse: collapse; margin-top: 24px; background: var(--steel-2); border-radius: 6px; overflow: hidden; }}
  table.code-table th {{ background: var(--steel-3); color: #fff; font-family: var(--mono); font-size: 0.8rem; text-transform: uppercase; text-align: left; padding: 14px 18px; letter-spacing: 0.05em; }}
  table.code-table td {{ padding: 14px 18px; border-bottom: 1px solid var(--steel-3); font-size: 0.95rem; }}
  table.code-table tr:hover {{ background: rgba(255,176,0,0.04); }}
</style>
</head>
<body>

<header class="bar">
  <div class="wrap bar-inner">
    <a href="/" class="wordmark"><span class="mil" aria-hidden="true"></span>MechanicDB</a>
    <nav style="font-family: var(--mono); font-size: 0.82rem; display: flex; gap: 20px;">
      <a href="/#interactive">Decoder</a>
      <a href="/#licensing">Dataset License ($49)</a>
      <a href="/#faq">FAQ</a>
    </nav>
  </div>
</header>

<div class="wrap" style="padding-top: 30px; padding-bottom: 60px;">
  <div class="breadcrumb"><a href="/">Home</a> / <span>{html.escape(sys_cat)} System Directory</span></div>
  <h1>{html.escape(title)}</h1>
  <p style="color: #d7dce2; max-width: 70ch;">Complete diagnostic directory of verified {html.escape(sys_cat)} trouble codes. Click any code below for full technical anatomy, DIY safety analysis, probability-ranked repair procedures, parts cost estimates, and required aftermarket parts.</p>

  <table class="code-table">
    <thead>
      <tr>
        <th>Code</th>
        <th>Description</th>
        <th>Fault Family</th>
        <th>Standard</th>
        <th style="text-align: right;">Repairs</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>

</body>
</html>
"""
    with open(os.path.join(LANDING_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content)

def generate_sitemap(codes_list):
    try:
        from datetime import timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    except AttributeError:
        today = datetime.utcnow().strftime("%Y-%m-%d")
    urls = [
        f"""  <url>
    <loc>{DOMAIN}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>"""
    ]

    for hub in ["powertrain", "chassis", "body", "network"]:
        urls.append(f"""  <url>
    <loc>{DOMAIN}/landing/{hub}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>""")

    for c in codes_list:
        urls.append(f"""  <url>
    <loc>{DOMAIN}/landing/{c['dtc_code']}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{"\n".join(urls)}
</urlset>
"""
    with open(SITEMAP_XML, "w", encoding="utf-8") as f:
        f.write(sitemap_content)

def main():
    os.makedirs(LANDING_DIR, exist_ok=True)
    dtc_by_code = load_data()
    
    print(f"Loaded {len(dtc_by_code)} distinct DTC codes from CSV.")

    # Group by system category
    by_sys = {"Powertrain": [], "Chassis": [], "Body": [], "Network": []}
    
    for code, dtc in dtc_by_code.items():
        generate_code_page(code, dtc)
        cat = dtc.get("system_category", "Powertrain")
        if cat in by_sys:
            by_sys[cat].append(dtc)
        else:
            by_sys.setdefault("Powertrain", []).append(dtc)

    # Generate hubs
    generate_category_hub("Powertrain", "powertrain.html", "⚡ Powertrain System Diagnostic Trouble Codes (P-Codes)", by_sys["Powertrain"])
    generate_category_hub("Chassis", "chassis.html", "🛑 Chassis & ABS System Diagnostic Trouble Codes (C-Codes)", by_sys["Chassis"])
    generate_category_hub("Body", "body.html", "🚗 Body & SRS System Diagnostic Trouble Codes (B-Codes)", by_sys["Body"])
    generate_category_hub("Network", "network.html", "📡 CAN Network & Communication Trouble Codes (U-Codes)", by_sys["Network"])

    # Generate sitemap
    generate_sitemap(list(dtc_by_code.values()))
    
    print(f"Successfully generated {len(dtc_by_code)} diagnostic code monographs in landing/*.html, 4 category hubs, and sitemap.xml!")

if __name__ == "__main__":
    main()
