# xuguang-ai.github.io

Source of [xuguang-ai.github.io](https://xuguang-ai.github.io): one page built by a small Python script and published by GitHub Actions. There is one branch, `main`; every push to it publishes the site.

## Update the content

| To change | Edit |
| --- | --- |
| Headline, about text, timeline, peer-review venues, links, the "Latest" pill | `content/profile.yml` |
| Research interests, their ids and representative work | `content/research.yml` |
| Open-source projects | `content/software.yml` |
| Publications | `content/papers.bib` |

Add a paper by pasting its BibTeX into `content/papers.bib` with the publisher's full author list, a `doi` (or a `url` for preprints) and a `date` (`YYYY-MM` or `YYYY-MM-DD`, within the cited year; the list shows it as "Sep 2026"). The list is one sequence sorted by `date`, newest first, so file order does not matter. Preprints are `@misc` with `howpublished` (e.g. `arXiv:2607.07673`). Other site-only fields: `abbr` (short venue label used on the research cards), `venue` (label in the publication list, when the journal name is not the best label), `area` (the `id` of a research interest in `content/research.yml`; it files the paper under that interest for the publication filter, and may be left out), `equal` (the first N authors contributed equally; they get an asterisk), `preprint` (public preprint of an accepted paper). Each row has one "Link" button to the paper. Author lists show everyone up to the site owner (at least three names), then "et al."; the owner's name is highlighted. The first six rows show by default (`PUBS_VISIBLE` in `build.py`).

The publication list has a filter row, one button per research interest that has papers. The "N papers" link on a research card sets the same filter.

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
- `static/`: `css/site.css` (one light theme), `js/site.js`, images, favicon.
- `assets/img/my_profile.jpeg`: the original portrait; `static/img/portrait*.jpg` are resized copies.
- `.github/workflows/deploy.yml`: builds on every push and pull request, and deploys `main` to GitHub Pages.

## License

The code is under the MIT License (see `LICENSE`). The portrait and the written content of the site are © Xuguang Ai and are not covered by that license.
