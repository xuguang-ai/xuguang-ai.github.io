#!/usr/bin/env python3
"""Build the website from content/, templates/ and static/ into _site/.

    python build.py            build into _site/
    python build.py --check    build, then run the consistency checks (CI runs this)

Preview locally with:  python -m http.server --directory _site 8000
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "_site"
SITE_URL = "https://xuguang-ai.github.io"
OWNER = ("Ai", "Xuguang")  # family and given name of the site owner, highlighted in author lists

# Old URLs of the previous site that other pages may link to; each becomes a small redirect page.
REDIRECTS = {
    "publications/": "/#publications",
    "cv/": "/#about",
    "repositories/": "/#open-source",
    "news/": "/",
}

LANG_COLORS = {"Python": "#3572a5", "R": "#198ce7", "Swift": "#f05138", "TypeScript": "#3178c6"}
ALL_AUTHORS_UP_TO = 5  # lists with at most this many authors are shown in full
PUBS_VISIBLE = 6       # publications shown before "Show all"; the rest are in the page but collapsed
FORBIDDEN = ["Einstein", "al-folio", "example_pdf", "Lorem ipsum", "TODO"]


# ---------------------------------------------------------------- BibTeX

def _closing_brace(text: str, start: int) -> int:
    """Index just past the brace that closes the group opened right before `start`."""
    depth, i = 1, start
    while depth:
        if i >= len(text):
            raise ValueError("unbalanced braces in papers.bib")
        depth += (text[i] == "{") - (text[i] == "}")
        i += 1
    return i


def parse_bib(text: str) -> list[dict]:
    """Parse a small hand-maintained BibTeX file whose field values are all brace-delimited."""
    entries, pos = [], 0
    head = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")
    field = re.compile(r"(\w+)\s*=\s*\{")
    while m := head.search(text, pos):
        end = _closing_brace(text, m.end())
        body, fields, j = text[m.end():end - 1], {}, 0
        while f := field.search(body, j):
            k = _closing_brace(body, f.end())
            fields[f.group(1).lower()] = " ".join(body[f.end():k - 1].split())
            j = k
        entries.append({"type": m.group(1).lower(), "key": m.group(2), "fields": fields})
        pos = end
    return entries


def tex(s: str) -> str:
    """The little LaTeX the bibliography uses, as plain text."""
    for a, b in (("---", "—"), ("--", "–"), ("``", "“"), ("''", "”"), ("\\&", "&"), ("~", " ")):
        s = s.replace(a, b)
    return s.replace("{", "").replace("}", "")


def initials(given: str) -> str:
    """'Thaddaeus Wai Soon' -> 'TWS', 'Yih-Chung' -> 'Y-C', 'R. Andrew' -> 'RA'."""
    return "".join("-".join(p[0] for p in word.split("-") if p) for word in given.replace(".", " ").split())


def author_line(authors: list[tuple[str, str]], owner: int, equal: int) -> str:
    """'Family Initials' from the first author through the site owner (at least three), then 'et al.'.

    Short lists are shown in full. The first `equal` authors contributed equally and get an asterisk.
    """
    def name(i: int) -> str:
        fam, giv = authors[i]
        text = html.escape(f"{fam} {initials(giv)}".strip()) + ("*" if i < equal else "")
        return f'<b class="me">{text}</b>' if i == owner else text

    n = len(authors)
    shown = n if n <= ALL_AUTHORS_UP_TO else max(3, owner + 1)
    line = ", ".join(name(i) for i in range(shown))
    return line + (", et al." if shown < n else "")


def load_papers() -> list[dict]:
    """All publications, newest first.

    Sorted by the `date` field (YYYY-MM or YYYY-MM-DD; the year alone if missing). A month-only date
    sorts after dated entries of the same month; ties keep file order.
    """
    papers = []
    for entry in parse_bib((CONTENT / "papers.bib").read_text(encoding="utf-8")):
        f, kind = entry["fields"], entry["type"]
        authors = []
        for a in f["author"].split(" and "):
            fam, _, giv = a.partition(",")
            authors.append((tex(fam.strip()), tex(giv.strip())))
        owner = next((i for i, a in enumerate(authors) if a == OWNER), -1)
        equal = int(f.get("equal", 0))
        doi_url = f"https://doi.org/{f['doi']}" if f.get("doi") else None
        # Short venue label for the left column: an explicit `venue`, else the journal, else `abbr`.
        venue_name = tex(f.get("venue") or (f.get("journal") if kind == "article" else None)
                         or f.get("abbr") or f.get("booktitle") or f.get("howpublished", "Preprint"))
        status = "Accepted" if f.get("note") == "Accepted" else ("Abstract" if f.get("kind") == "abstract" else "")
        papers.append({
            "key": entry["key"],
            "title": tex(f["title"]),
            "year": f["year"],
            "date": f.get("date", f["year"]),
            "abbr": f.get("abbr", ""),
            "venue_name": venue_name,
            "status": status,
            "url": doi_url or f.get("url") or f.get("preprint"),
            "link_label": "Paper" if (doi_url or f.get("url")) else "Preprint",
            "owner_position": owner + 1,
            "authors_html": author_line(authors, owner, equal),
        })
    return sorted(papers, key=lambda p: p["date"], reverse=True)


# ---------------------------------------------------------------- Build

def load_yaml(name: str):
    return yaml.safe_load((CONTENT / name).read_text(encoding="utf-8"))


def asset_url(path: str) -> str:
    """URL of a file under static/, with a content hash so browsers fetch new versions."""
    digest = hashlib.sha256((STATIC / path).read_bytes()).hexdigest()[:10]
    return f"/static/{path}?v={digest}"


def build() -> dict:
    profile = load_yaml("profile.yml")
    papers = load_papers()
    by_key = {p["key"]: p for p in papers}

    research = load_yaml("research.yml")
    for direction in research:
        for item in direction["work"]:
            if "key" in item:
                paper = by_key[item["key"]]
                item.setdefault("href", paper["url"])
                item.setdefault("venue", f"{paper['abbr']} {paper['year']}")

    software = load_yaml("software.yml")
    for project in software:
        project.setdefault("install", None)
        project.setdefault("links", [])
        project["lang_items"] = [{"name": n, "color": LANG_COLORS.get(n)} for n in project.get("langs", [])]

    for rank, p in enumerate(papers):
        p["collapsed"] = rank >= PUBS_VISIBLE

    person = {
        "@context": "https://schema.org", "@type": "Person", "name": profile["name"], "url": SITE_URL + "/",
        "jobTitle": profile["role"], "worksFor": {"@type": "Organization", "name": profile["affiliation"]},
        "image": SITE_URL + "/static/img/portrait.jpg", "sameAs": list(profile["links"].values()),
    }

    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "xml"]),
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    env.globals.update(asset=asset_url, site_url=SITE_URL, year=dt.date.today().year,
                       person_jsonld=json.dumps(person, ensure_ascii=False).replace("</", "<\\/"))
    ctx = {"profile": profile, "research": research, "software": software,
           "papers": papers, "pubs_visible": PUBS_VISIBLE}

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT / "static")
    (OUT / "index.html").write_text(env.get_template("index.html").render(**ctx, path="/"), encoding="utf-8")
    (OUT / "404.html").write_text(env.get_template("404.html").render(**ctx, path="/404.html"), encoding="utf-8")
    for old, target in REDIRECTS.items():
        page = OUT / old / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(env.get_template("redirect.html").render(target=target), encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE_URL}/</loc><lastmod>{dt.date.today().isoformat()}</lastmod></url>\n"
        "</urlset>\n", encoding="utf-8")
    return {"papers": papers}


# ---------------------------------------------------------------- Checks

class _Scan(HTMLParser):
    """Collect ids, links, asset references and nesting errors of one page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.hrefs, self.srcs, self.uses, self.errors, self.open_a = set(), [], [], [], [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a":
            if self.open_a:
                self.errors.append("a link nested inside another link")
            self.open_a += 1
            self.hrefs.append(a.get("href", ""))
        if tag == "button" and self.open_a:
            self.errors.append("a button inside a link")
        if tag == "use":
            self.uses.append(a.get("href", ""))
        for attr in ("src", "href"):
            if tag in ("img", "script", "link") and a.get(attr):
                self.srcs.append(a[attr])

    def handle_endtag(self, tag):
        if tag == "a":
            self.open_a -= 1


def check(result: dict) -> list[str]:
    problems = []
    page = (OUT / "index.html").read_text(encoding="utf-8")
    scan = _Scan()
    scan.feed(page)
    problems += scan.errors
    for href in scan.hrefs + scan.uses:
        if href.startswith(("#", "/#")):
            anchor = href.split("#", 1)[1]
            if anchor and anchor not in scan.ids:
                problems.append(f"in-page link to a missing id: {href}")
    for ref in scan.srcs + scan.hrefs:
        if ref.startswith("/") and not ref.startswith("//"):
            local = OUT / ref.split("?")[0].split("#")[0].lstrip("/")
            if ref.split("#")[0] not in ("/", "") and not local.exists():
                problems.append(f"missing local file: {ref}")
    for p in result["papers"]:
        if p["owner_position"] < 1:
            problems.append(f"{p['key']}: the site owner is not among the authors")
        if not p["url"]:
            problems.append(f"{p['key']}: no DOI or URL")
        if not p["date"].startswith(p["year"]):
            problems.append(f"{p['key']}: date {p['date']} is not in its year {p['year']}")
    for word in FORBIDDEN:
        for f in OUT.rglob("*.html"):
            if word in f.read_text(encoding="utf-8"):
                problems.append(f"leftover text '{word}' in {f.relative_to(OUT)}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="run consistency checks after building")
    args = ap.parse_args()
    result = build()
    print(f"built {OUT.relative_to(ROOT)}/: {len(result['papers'])} papers")
    if args.check:
        problems = check(result)
        for p in problems:
            print("CHECK FAILED:", p)
        if problems:
            return 1
        print("checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
