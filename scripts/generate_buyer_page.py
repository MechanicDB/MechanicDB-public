#!/usr/bin/env python3
"""Build /obd2-dtc-database, the page aimed at people buying the dataset.

GSC (12 Sep) shows MechanicDB surfacing only for code-lookup intent --
"p0446 engine code", "what is code p0446" -- at average position 61.9,
against SERPs held by RepairPal, YourMechanic and AutoZone. Those are not
winnable and the people typing them are not buyers.

The buyer queries are a different, near-empty cluster: "obd2 dtc
database", "dtc code list csv", "trouble code dataset download". Nothing
on the site targeted them -- a grep for those phrases across every page
returned zero matches. The homepage comes closest but draws 0 impressions
and its title led with "The OBD-II Diagnostic & Repair Database", which
carries neither "DTC" nor any format or download word.

This page owns that cluster. Every figure in it is lifted from the claims
already on the homepage, so nothing new is asserted:
  15,886 codes (9,249 SAE + 6,637 OEM across 32 makes), 647 fault
  families, 56,561 ranked fixes, 75,055 parts mappings, four tables,
  CSV / Parquet / SQLite, $49 SAE and $149 OEM, 90-code free sample.

The page sits at the repo root, the same depth as index.html, so the
<style> block, font links and footer lifted from it work unchanged. The
header nav is rewritten to absolute anchors, since its section links
point at the homepage.

Run from the repo root:  python scripts/generate_buyer_page.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
OUT = ROOT / "obd2-dtc-database.html"
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://mechanicdb.dataengineered.io"

BEGIN = "<!-- BEGIN:buyer-link -->"
END = "<!-- END:buyer-link -->"

TITLE = "OBD-II DTC Database Download — CSV, Parquet, SQLite"
DESC = ("15,886 OBD-II trouble codes (9,249 SAE + 6,637 OEM) joined to 56,561 ranked "
        "repairs. Download as CSV, Parquet or SQLite. Free 90-code sample.")

# Homepage title/meta: led with framing rather than with anything anyone types.
HOME_TITLE_OLD = "<title>OBD-II DTC Database — 15,886 Trouble Codes &amp; Fixes | MechanicDB</title>"
HOME_TITLE_NEW = "<title>MechanicDB — 15,886 OBD-II Trouble Codes &amp; Ranked Fixes</title>"


def lifted_chrome(src):
    """Font links and the stylesheet block from the homepage."""
    head = src[: src.lower().find("</head>")]
    keep = [m.group(0) for m in re.finditer(r"<link[^>]+>", head, re.I)
            if re.search(r'rel="?(stylesheet|preconnect)', m.group(0), re.I)]
    keep += [m.group(0) for m in re.finditer(r"<style[^>]*>.*?</style>", head, re.S | re.I)]
    return "\n".join(keep)


def lifted_block(tag, src):
    m = re.search(r"<%s[^>]*>.*?</%s>" % (tag, tag), src, re.S | re.I)
    return m.group(0) if m else ""


BODY = """
<main class="wrap" style="padding-top:34px">

  <p class="crumb" style="font-family:var(--mono,monospace);font-size:.76rem;opacity:.6;margin-bottom:14px">
    <a href="/">MechanicDB</a> &rsaquo; OBD-II DTC database
  </p>

  <h1 style="max-width:20ch">The OBD-II trouble code database, as a file you can query.</h1>

  <p class="lede" style="max-width:66ch">
    15,886 diagnostic trouble codes joined to 56,561 ranked repair procedures, delivered as
    pipe-delimited CSV, Apache Parquet or a SQLite database. Built for OBD apps, scan-tool
    firmware, AI mechanic co-pilots and shop software &mdash; not a website you have to scrape.
  </p>

  <div class="cta-row" style="margin:26px 0 8px">
    <a class="btn btn-amber" href="/#licensing">See the tiers &mdash; $49 / $149</a>
    <a class="btn btn-ghost" href="https://github.com/MechanicDB/MechanicDB-public/releases/download/sample-latest/mechanicdb-sample-latest.zip">Download the free 90-code sample</a>
  </div>

  <h2 style="margin-top:44px">What you get in the download</h2>
  <div class="tablewrap" style="overflow-x:auto">
  <table style="width:100%;border-collapse:collapse;font-size:.94rem;min-width:520px">
    <tbody>
      <tr><td style="padding:9px 0"><b>15,886</b> trouble codes</td><td style="opacity:.75">9,249 SAE-standard (P0, P2, P34&ndash;P39, C0, B0, U0, U3) + 6,637 manufacturer-specific across 32 makes</td></tr>
      <tr><td style="padding:9px 0"><b>56,561</b> ranked fixes</td><td style="opacity:.75">3&ndash;5 per code, ordered by real-world likelihood, with difficulty tier, parts-cost range and labor hours</td></tr>
      <tr><td style="padding:9px 0"><b>75,055</b> parts mappings</td><td style="opacity:.75">Aftermarket part names per fix, with catalog search URLs</td></tr>
      <tr><td style="padding:9px 0"><b>647</b> fault families</td><td style="opacity:.75">Authored groupings that make the corpus navigable rather than a flat code list</td></tr>
    </tbody>
  </table>
  </div>

  <h2 style="margin-top:44px">Formats</h2>
  <p style="max-width:66ch;opacity:.85">
    Every tier ships all three. Pipe-delimited <b>CSV</b> (UTF-8 BOM, Excel-safe).
    <b>Apache Parquet</b> with Snappy compression &mdash; a measured 92.0% smaller.
    A <b>SQLite</b> database carrying all four tables with the join chain intact.
  </p>

  <h2 style="margin-top:44px">Schema</h2>
  <p style="max-width:66ch;opacity:.85">Four relational tables, normalized for databases and pre-joined for notebooks.</p>
  <div class="tablewrap" style="overflow-x:auto">
  <table style="width:100%;border-collapse:collapse;font-size:.9rem;min-width:520px">
    <thead><tr style="text-align:left;opacity:.6;font-size:.76rem;letter-spacing:.08em;text-transform:uppercase">
      <th style="padding:0 12px 8px 0">Table</th><th style="padding:0 12px 8px 0">Rows</th><th style="padding:0 0 8px">Holds</th></tr></thead>
    <tbody>
      <tr><td style="padding:9px 12px 9px 0"><code>dtc_codes</code></td><td style="padding:9px 12px 9px 0">15,886</td><td>Definition, system category, OEM flag and make, fault family, technical explanation</td></tr>
      <tr><td style="padding:9px 12px 9px 0"><code>diagnostic_fixes</code></td><td style="padding:9px 12px 9px 0">56,561</td><td>Ranked procedures with difficulty tier, parts cost min/max, labor hours, steps</td></tr>
      <tr><td style="padding:9px 12px 9px 0"><code>replacement_parts</code></td><td style="padding:9px 12px 9px 0">75,055</td><td>Aftermarket part names per fix, with catalog search URLs</td></tr>
      <tr><td style="padding:9px 12px 9px 0"><code>dtc_fixes_joined</code></td><td style="padding:9px 12px 9px 0">56,561</td><td>The flat analytical view &mdash; all 16 columns, one <code>read_csv</code> / <code>read_parquet</code></td></tr>
    </tbody>
  </table>
  </div>
  <p style="opacity:.7;font-size:.88rem;margin-top:10px">
    Join chain: <code>dtc_codes.code_id</code> &rarr; <code>diagnostic_fixes.code_id</code> &rarr; <code>replacement_parts.fix_id</code>
  </p>

  <h2 style="margin-top:44px">Coverage, stated honestly</h2>
  <p style="max-width:66ch;opacity:.85">
    The 9,249 SAE-universal codes apply to every vehicle regardless of make. OEM coverage is
    <b>not even</b> &mdash; it is strongest on US-market brands and some marques are thin. The full
    per-make breakdown is published on the <a href="/#coverage">homepage</a> so you can check the
    makes you care about <em>before</em> buying rather than after. Every published code traces to a
    committed source; a build gate rejects fabricated codes.
  </p>

  <h2 style="margin-top:44px">Licensing</h2>
  <p style="max-width:66ch;opacity:.85">
    The 90-code sample is free under ODbL v1.0. The full dataset ships under a commercial license
    &mdash; <b>$49</b> for the 9,249 SAE codes, <b>$149</b> for SAE plus all 6,637 OEM codes.
    Full terms and the per-make breakdown are on the <a href="/#licensing">homepage</a>.
  </p>

  <p style="margin:38px 0 10px;opacity:.85">
    Looking up one specific code instead? Browse the
    <a href="/landing/families">fault-family directory</a>.
  </p>

</main>
"""


def build():
    src = INDEX.read_text(encoding="utf-8")
    page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{base}/obd2-dtc-database">
<link rel="alternate" hreflang="en" href="{base}/obd2-dtc-database">
<link rel="alternate" hreflang="x-default" href="{base}/obd2-dtc-database">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{base}/obd2-dtc-database">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Dataset","name":"MechanicDB OBD-II DTC Database","description":"{desc}","url":"{base}/obd2-dtc-database","creator":{{"@type":"Organization","name":"DataEngineered","url":"https://dataengineered.io"}},"distribution":[{{"@type":"DataDownload","encodingFormat":"text/csv"}},{{"@type":"DataDownload","encodingFormat":"application/vnd.apache.parquet"}},{{"@type":"DataDownload","encodingFormat":"application/x-sqlite3"}}],"variableMeasured":["diagnostic trouble code","system category","fault family","repair procedure","probability rank","difficulty tier","estimated parts cost","labor hours","replacement part name"]}}
</script>
{chrome}
</head>
<body>
{header}
{body}
{footer}
</body>
</html>
""".format(
        title=TITLE, desc=DESC, base=BASE,
        chrome=lifted_chrome(src),
        header=lifted_block("header", src).replace('href="#', 'href="/#'),
        body=BODY,
        footer=lifted_block("footer", src),
    )
    OUT.write_text(page, encoding="utf-8", newline="")


def retitle_homepage():
    src = INDEX.read_text(encoding="utf-8")
    changed = []
    if HOME_TITLE_OLD in src:
        src = src.replace(HOME_TITLE_OLD, HOME_TITLE_NEW, 1)
        changed.append("title")
    # Link the new page so it is reachable, not sitemap-only.
    block = ('%s<a href="/obd2-dtc-database" class="btn btn-ghost">Get the database &mdash; '
             'CSV, Parquet, SQLite</a>%s' % (BEGIN, END))
    if BEGIN in src and END in src:
        src = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), lambda _: block, src, flags=re.DOTALL)
        changed.append("link (refreshed)")
    else:
        m = re.search(r'<div class="cta-row">', src)
        if not m:
            sys.exit("could not find the hero CTA row to link the new page from")
        end = m.end()
        src = src[:end] + "\n  " + block + src[end:]
        changed.append("link")
    INDEX.write_text(src, encoding="utf-8", newline="")
    return changed


def update_sitemap():
    src = SITEMAP.read_text(encoding="utf-8")
    loc = "%s/obd2-dtc-database" % BASE
    if "<loc>%s</loc>" % loc in src:
        return False
    src = src.replace("</urlset>",
                      "  <url>\n    <loc>%s</loc>\n    <changefreq>monthly</changefreq>\n"
                      "    <priority>0.9</priority>\n  </url>\n</urlset>" % loc, 1)
    SITEMAP.write_text(src, encoding="utf-8", newline="")
    return True


if __name__ == "__main__":
    build()
    print("wrote obd2-dtc-database.html")
    print("homepage: %s" % (", ".join(retitle_homepage()) or "unchanged"))
    print("sitemap: %s" % ("added" if update_sitemap() else "already present"))
