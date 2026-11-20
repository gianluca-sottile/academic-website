# Vetrina accademica — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Hugo Academic 4.8 site with a hand-built, bilingual (EN/IT) static showcase whose publications and package metadata refresh automatically, served by Netlify at gianlucasottile.rbind.io.

**Architecture:** YAML data files + one auto-generated `publications.json` are rendered by a small Python/Jinja2 build into plain HTML/CSS/JS under `site/` (EN at `/`, IT at `/it/`). A weekly GitHub Actions cron fetches ORCID→OpenAlex/Crossref and CRAN/GitHub metadata, commits changed JSON, and Netlify rebuilds on push. The old Hugo site is archived in `legacy/` and excluded from the build.

**Tech Stack:** Python 3.11, Jinja2, PyYAML, requests, pytest (+ `responses` for HTTP mocks); vanilla CSS (custom properties, light/dark) and vanilla JS (no framework); GitHub Actions; Netlify.

**Spec:** `_design/2026-11-20-vetrina-design.md` (read it first; it is in Italian).

## Global Constraints

- Repo: `github.com/gianluca-sottile/academic-website`. Work on branch `vetrina-2026`; `master` stays live until cutover. The local OneDrive folder has no `.git`: clone the repo into the scratch area, copy changes in, or ask Gianluca to run `git init`/`remote add` — never push without his OK.
- Domain stays `https://gianlucasottile.rbind.io/`. Netlify: `command = "pip install -r requirements.txt && python scripts/build.py"`, `publish = "site"`.
- Bilingual: EN at `/`, IT at `/it/`, reciprocal `<link rel="alternate" hreflang>` + `x-default`; switcher goes to the same page in the other language; browser-language *suggestion* banner only, never forced redirect. Text fields are `{en, it}`; a single-language string is shown in both versions with a language badge. Publication titles never translated.
- ORCID iD `0000-0001-9347-7251`. Publications source = ORCID list, enriched by OpenAlex (authors, venue, year, citations, OA link), Crossref fallback. Citation counts labelled "Source: OpenAlex" + link to Google Scholar `https://scholar.google.com/citations?user=qc0KUpwAAAAJ`.
- Exclude from site: preprints / working papers / anything not yet published; IS-Score, FCST, MERE; any editorial/referee work; `anonymous.4open.science` links; manuscript IDs.
- Software (closed list): islasso, Qest, qrcmNP, clustEff — each links to GitHub `github.com/gianluca-sottile/<repo>` and CRAN.
- Projects include PRIN 2022 "Spatio-temporal Functional Marked Point Processes for probabilistic forecasting of earthquakes", code 2022BN7CJP, PI G. Adelfio (Gianluca = participant), StatAtlas, From Data to Models with R, CoViSTAT19, PON AIM.
- Brand: wordmark "gianluca / *sottile*" (serif italic + 0.75px accent hairline) in header/footer; symbol "G + S-shaped quantile curve with data points" for favicon/avatar. Palette start: ink `#1F2A44`, paper `#F7F4EE`, accent `#D85A30`.
- WCAG 2.1 AA, responsive from 360px, light/dark, no client-side rendering of primary content (all text in pre-built HTML), total JS < 30 KB.
- Manual upkeep only for `news.yml` and `talks.yml`. A section whose data is empty is not rendered.
- Every Gianluca-facing text drafted by Claude is marked `draft: true` in YAML until he approves; the build prints a warning listing drafts.

## Review Focus

1. **ORCID/OpenAlex unreachable or rate-limited** → cron exits 0, keeps the previous `publications.json` untouched, logs a warning. (Task 3 test `test_fetch_failure_keeps_previous`)
2. **Duplicates**: same DOI in several ORCID groups, or preprint + published version of the same paper → one entry, the published one. (Task 3 `test_dedupe_doi_and_preprint`)
3. **Works without DOI or with HTML/LaTeX markup in titles** (`<i>`, `&amp;`, `$\ell_1$`) → kept, title sanitised to safe text, no raw tags rendered. (Task 3 `test_title_sanitising`, `test_no_doi_kept`)
4. **Missing Italian translation** → EN text shown on IT page with `EN` badge, never empty string or `None`. (Task 2 `test_i18n_fallback`)
5. **Old Hugo URLs** (`/publication/*`, `/talk/*`, `/courses/*`, `/project/*`, `/post/*`, `/CV_gianluca_sottile.pdf`) → 301 to new pages, PDFs keep working. (Task 8 `test_redirects`)

---

### Task 1: Repo restructure and build skeleton

**Files:**
- Move: everything Hugo (`config/ content/ layouts/ themes/ resources/ public/ assets/ data/ static/admin index.Rmd index.html ac_website.Rproj`) → `legacy/`
- Keep in place: PDFs from `static/` → `static/files/` (CV, posters, slides); `static/img/` → `static/img/`
- Create: `requirements.txt`, `scripts/build.py`, `src/templates/base.html`, `src/templates/index.html`, `tests/test_build.py`, `.gitignore` (`site/`, `__pycache__/`), new `README.md` (how to add a news/talk, how to build locally)

**Interfaces:**
- Produces: `build(data_dir: Path, out_dir: Path) -> list[Path]` (returns written files); `LANGS = ("en", "it")`; `url_for(page: str, lang: str) -> str` (`url_for("publications","it") == "/it/publications/"`, `url_for("index","en") == "/"`).

- [ ] Step 1: Write `tests/test_build.py::test_build_writes_both_languages` — build with a minimal fixture data dir; assert `site/index.html` and `site/it/index.html` exist, each contains `hreflang="it"`, `hreflang="en"`, `hreflang="x-default"`, and `<html lang="en">` / `<html lang="it">`.
- [ ] Step 2: `pytest tests/test_build.py -v` → FAIL (no module).
- [ ] Step 3: Implement `build`, `url_for` in `scripts/build.py` (Jinja2 `Environment(autoescape=True)`; copies `static/` and `src/assets/` into `site/`).
- [ ] Step 4: `pytest -v` → PASS; `python scripts/build.py` exits 0.
- [ ] Step 5: Commit `chore: archive Hugo site in legacy/ and add static build skeleton`.

### Task 2: Data layer, i18n and validation

**Files:**
- Create: `scripts/data.py`, `data/schema.md` (one table per YAML file: field, type, required, example), `tests/test_data.py`, `tests/fixtures/data/*.yml`

**Interfaces:**
- Produces: `load_all(data_dir: Path) -> SiteData` (dataclass with `profile, roles, news, talks, projects, teaching, software, publications`); `tr(value: str | dict, lang: str) -> Localized` where `Localized = NamedTuple(text: str, lang: str)`; `validate(data: SiteData) -> list[str]` (error messages; build aborts if non-empty); `drafts(data) -> list[str]`.
- YAML item keys (all files): `id` (slug, unique per file), `draft` (bool, default false), text fields `{en, it}` or plain string. Specific required keys: news `date, text`; talks `date, title, event, place, kind (talk|poster|invited), files[]`; projects `title, summary, role, period, links[], kind (funded|open-resource|research)`; teaching `title, programme, level (BSc|MSc|PhD|open), ects, language, years, current (bool), links[]`; roles `title, org, start, end?, kind (position|visiting|service|education|membership)`; software `name, repo, cran, paper_doi?`.

- [ ] Step 1: Tests: `test_i18n_fallback` (`tr({"en":"Hi"}, "it") == ("Hi","en")`; `tr("Ciao","en").text == "Ciao"`; `tr({"en":"a","it":"b"},"it") == ("b","it")`), `test_validate_missing_required` (talk without `date` → error naming file and id), `test_duplicate_ids`, `test_forbidden_content` (any string containing `anonymous.4open.science`, `IS-Score`, `MERE-D-`, `Lorenz` → error), `test_empty_section_ok` (empty `news.yml` validates).
- [ ] Step 2: Run → FAIL.
- [ ] Step 3: Implement `scripts/data.py`; wire `validate` and `drafts` warning into `build`.
- [ ] Step 4: Run → PASS.
- [ ] Step 5: Commit `feat: data loader with i18n fallback and content guards`.

### Task 3: Publication fetcher (ORCID → OpenAlex/Crossref)

**Files:**
- Create: `scripts/fetch_publications.py`, `data/publications.overrides.yml`, `tests/test_fetch_publications.py`, `tests/fixtures/orcid_works.json`, `tests/fixtures/openalex_*.json`

**Interfaces:**
- Produces: `data/publications.json` = `{"updated": ISO date, "source": "ORCID+OpenAlex", "items": [Publication]}`; `Publication` keys: `id` (DOI lower-case or `orcid-<put-code>`), `title`, `authors: [str]`, `venue`, `year: int`, `type (article|chapter|proceedings|book)`, `doi?`, `url`, `oa_url?`, `citations: int|null`, `themes: [str]`, `selected: bool`, `links: [{label,url}]`.
- `fetch(orcid: str, session) -> list[Publication]`; `merge_overrides(items, overrides) -> list`; `main() -> int` (always 0 unless the overrides file is invalid).
- Overrides YAML: `hide: [doi]`, `selected: [doi]`, `themes: {doi: [theme-id]}`, `links: {doi: [{label,url}]}`, `extra: [Publication]` (manual additions). Theme ids come from `profile.yml: research_themes[].id`; unknown theme → validation error.
- Untagged new paper: `themes` suggested from OpenAlex `primary_topic` mapped via `profile.yml: research_themes[].openalex_keywords`; no match → `[]`.
- APIs: `https://pub.orcid.org/v3.0/{orcid}/works` (Accept JSON), `https://api.openalex.org/works/doi:{doi}?mailto=…`, `https://api.crossref.org/works/{doi}`. Polite `User-Agent` with repo URL; timeout 20 s; 3 retries with backoff.

- [ ] Step 1: Tests (all HTTP mocked with `responses`): `test_parses_orcid_groups`, `test_dedupe_doi_and_preprint` (preprint type or `arxiv`/`biorxiv`/`ssrn` DOI dropped when a published DOI with same normalised title exists; lone preprints dropped too), `test_excludes_unpublished` (ORCID type `working-paper`/`preprint`/`other` → excluded), `test_title_sanitising` (`"A <i>new</i> &amp; test"` → `"A new & test"`; LaTeX `$...$` kept as text), `test_no_doi_kept` (uses ORCID data, `citations` null), `test_overrides_apply` (hide/selected/themes/links/extra), `test_fetch_failure_keeps_previous` (ORCID 503 → file bytes unchanged, return 0), `test_sorted_year_desc_then_title`.
- [ ] Step 2: Run → FAIL.
- [ ] Step 3: Implement. Write the JSON only if content (ignoring `updated`) changed.
- [ ] Step 4: Run → PASS. Then run live once: `python scripts/fetch_publications.py`; compare count with the 13 legacy publications + 2024–25 news items; report missing ones to Gianluca (they must be added to ORCID, or to `extra`).
- [ ] Step 5: Pre-fill `themes` and `selected` (5–6 items, include the two JRSS-C 2024/2025 papers and islasso) in overrides, `draft: true`. Commit `feat: automatic publication list from ORCID/OpenAlex`.

### Task 4: Software metadata fetcher

**Files:**
- Create: `scripts/fetch_software.py`, `data/software.yml`, `tests/test_fetch_software.py`

**Interfaces:**
- Produces: `data/software.json` = `{name: {cran_version, cran_published, downloads_last_month, gh_stars, gh_url}}`; same keep-previous-on-failure rule as Task 3.
- Sources: `https://crandb.r-pkg.org/{pkg}`, `https://cranlogs.r-pkg.org/downloads/total/last-month/{pkg}`, `https://api.github.com/repos/{owner}/{repo}` (uses `GITHUB_TOKEN` if set).
- `software.yml`: islasso (`gianluca-sottile/islasso`, paper doi `10.1177/0962280219842890`), Qest (`gianluca-sottile/Qest`, paper DOI resolved from the ScienceDirect link `S0167947322000512` in `legacy/content/home/software_andrea.md`), qrcmNP (paper `10.1177/1471082X19825523`), clustEff (paper `10.1007/s00180-018-0817-8`). Verify qrcmNP/clustEff repo names exist on GitHub; if not, link CRAN only and list them for Gianluca.

- [ ] Steps 1–5 as Task 3 pattern: tests `test_parses_sources`, `test_partial_failure_keeps_old_fields`, `test_unknown_pkg_reported`; implement; pass; commit `feat: CRAN/GitHub package metadata`.

### Task 5: Content migration and bilingual drafts

**Files:**
- Create: `data/profile.yml`, `data/roles.yml`, `data/news.yml`, `data/talks.yml`, `data/projects.yml`, `data/teaching.yml`
- Read: `legacy/content/authors/admin/_index.md`, `legacy/content/home/experience_andrea.md`, `legacy/content/home/talks2.md`, `legacy/content/talk/*/index.md`, `static/files/CV_gianluca_sottile.pdf`

**Interfaces:** schema from Task 2.

- [ ] Step 1: Populate YAML from the legacy sources and CV. Role title is **Associate Professor of Statistics** (fix legacy "Tenure-Track" inconsistency; confirm start date from CV). Teaching: Statistical Machine Learning (LM Statistics & Data Science, EN, 2026/27, current), Statistica (L-18 Economia e Amministrazione Aziendale, IT, current), Optimization for Statistical and Machine Learning, Financial Markets Laboratory, past Statistics courses (Architecture, Biology); open resource "From Data to Models with R". Talks from `legacy/content/talk/*` with their PDFs; news from the "Breaking news" block (3 articles + ICSDS 2025). All Claude-written prose `draft: true`.
- [ ] Step 2: `python scripts/build.py` → validation passes; drafts list printed.
- [ ] Step 3: Run `grep -riE "IS-Score|MERE-D|Lorenz|anonymous\.4open" data/` → no output.
- [ ] Step 4: Produce `_design/contenuti-da-rivedere.md` listing every draft item (IT+EN side by side) and every fact needing Gianluca's confirmation (dates, CFU, links). Commit `content: migrate and draft bilingual content`.

### Task 6: Brand assets

**Files:**
- Create: `src/assets/brand/wordmark.svg`, `wordmark-dark.svg`, `symbol.svg`, `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png` (180), `og-image.png` (1200×630), `site.webmanifest`

- [ ] Step 1: Draw SVGs per Global Constraints (symbol must read at 16px: thicken curve, 3 dots max at small sizes; wordmark uses a self-hosted serif, outlined to paths so no font dependency).
- [ ] Step 2: Rasterise PNGs (`cairosvg` or `rsvg-convert`); check favicon at 16/32 px visually.
- [ ] Step 3: Commit `feat: brand wordmark and quantile symbol`.

### Task 7: Visual design — home mockup gate, then design system and home

**Files:**
- Create: `src/assets/css/tokens.css`, `base.css`, `components.css`; `src/assets/js/site.js` (theme toggle, lang suggestion, scroll reveal, nav highlight); `src/templates/partials/{header,footer,hero,about,news,projects,teaching,publications_selected,software,timeline,talks,contact}.html`

**Interfaces:**
- Consumes: `SiteData`, `tr`, `url_for`, brand assets.
- Each partial receives `(data, lang, t)` where `t(key)` returns UI strings from `src/i18n/{en,it}.yml`.

- [ ] Step 1: Load `frontend-design` skill. Build a static home mockup with real data, publish/screenshot it, and **stop for Gianluca's approval** of the look (typography, palette, hero, section rhythm). Iterate until approved.
- [ ] Step 2: Implement tokens (light + dark via `prefers-color-scheme` and `[data-theme]`), components and partials. Hero: wordmark, role, one-line research statement, quick links (CV, Scholar, ORCID, GitHub, email), live counters (publications, citations*, packages, courses; *with "OpenAlex" note). Projects and Teaching use large cards; timeline for roles; empty sections not rendered.
- [ ] Step 3: Tests in `tests/test_build.py`: `test_empty_section_hidden`, `test_counters_match_data`, `test_no_draft_in_production` (with `BUILD_ENV=production`, drafts render nothing and build warns), `test_no_external_runtime_fetch` (no `fetch(` to third-party hosts in `site.js`).
- [ ] Step 4: Run tests → PASS; screenshot at 360, 768, 1280 px, light and dark.
- [ ] Step 5: Commit `feat: home page design`.

### Task 8: Inner pages, language switcher, redirects

**Files:**
- Create: `src/templates/{publications,teaching,projects,software,talks,cv}.html`, `src/assets/js/pubs.js` (filter by year/theme/type + text search, URL-hash state), `static/_redirects`, `tests/test_pages.py`

- [ ] Step 1: Tests: `test_all_pages_both_langs` (6 pages × 2 langs exist), `test_switcher_targets_same_page`, `test_pubs_page_works_without_js` (full list present in HTML), `test_redirects` (each legacy pattern in Review Focus #5 has a `301` rule; `/CV_gianluca_sottile.pdf` → `/files/CV_gianluca_sottile.pdf`), `test_internal_links_resolve` (every internal href in `site/` points to an existing file).
- [ ] Step 2: Run → FAIL. Step 3: Implement. Step 4: Run → PASS.
- [ ] Step 5: Commit `feat: inner pages, filters, redirects`.

### Task 9: CI, cron and Netlify

**Files:**
- Create: `.github/workflows/ci.yml` (on push/PR: install, `pytest`, build), `.github/workflows/refresh.yml` (cron `17 5 * * 1` + `workflow_dispatch`: run both fetchers, commit `data/*.json` if changed with message `chore(data): weekly refresh`, push)
- Modify: `netlify.toml` (build command/publish per Global Constraints, `PYTHON_VERSION = "3.11"`); remove Hugo env vars

- [ ] Step 1: `act`-free check: `python -m yaml` lint of workflows; build locally with the exact Netlify command.
- [ ] Step 2: Commit `ci: tests, weekly data refresh, Netlify build`.
- [ ] Step 3: With Gianluca: push branch, open Netlify deploy preview, verify; then merge to `master` (cutover).

### Task 10: Final QA

- [ ] Step 1: Run `design:design-critique` on screenshots and `design:accessibility-review` on the built pages; fix blocking issues.
- [ ] Step 2: Link check of all external links (`scripts/check_links.py`, report only); HTML validation (`html5validator` or `vnu`) with zero errors.
- [ ] Step 3: Performance: home page HTML+CSS+JS < 150 KB excl. images; images lazy-loaded, WebP/AVIF.
- [ ] Step 4: Deliver `_design/contenuti-da-rivedere.md` and a short "how to add a news / talk" in `README.md` (IT).
