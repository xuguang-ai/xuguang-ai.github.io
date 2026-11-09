# xuguang-ai.github.io

Source of [xuguang-ai.github.io](https://xuguang-ai.github.io): one page built by a small Python script and published by GitHub Actions. There is one branch, `main`; every push to it publishes the site.

## Update the content

| To change | Edit |
| --- | --- |
| Headline, about text, timeline, links, the "Latest" pill | `content/profile.yml` |
| Research directions and their representative work | `content/research.yml` |
| Selected research (which papers, short titles, takeaways) | `content/selected.yml` |
| Open-source projects | `content/software.yml` |
| Publications | `content/papers.bib` |

Add a paper by pasting its BibTeX into `content/papers.bib` with the publisher's full author list and a `doi`. Optional fields: `abbr` (short venue label), `pdf` (a link checked to return a PDF), `code`, `note`. Papers are grouped by year in file order, newest first. The site owner's name is highlighted automatically.

To offer a CV download, put the PDF in `static/` and set `cv_pdf` in `content/profile.yml`.

## Build and preview

```bash
python3 -m pip install -r requirements.txt   # Jinja2, PyYAML
python3 build.py --check                     # writes _site/ and runs the checks CI runs
python3 -m http.server --directory _site 8000
```

Then open <http://localhost:8000>. The checks fail on in-page links to missing ids, missing local files, links nested in links, papers without the owner or a DOI, and leftover template text.

## Layout

- `build.py`: reads `content/`, renders `templates/` with Jinja2, copies `static/`, and writes `_site/` (index, 404, redirects from the old `/publications/`, `/cv/`, `/repositories/` and `/news/` pages, sitemap, robots.txt).
- `templates/`: page templates; `partials/visuals.html` holds the three animated research illustrations.
- `static/`: `css/site.css` (light theme by default, dark after the visitor toggles it), `js/site.js`, images, favicon.
- `assets/img/my_profile.jpeg`: the original portrait; `static/img/portrait*.jpg` are resized copies.
- `.github/workflows/deploy.yml`: builds on every push and pull request, and deploys `main` to GitHub Pages.
