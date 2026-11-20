# Schema dei file dati

Regole comuni: ogni voce ha un `id` univoco (slug). I testi possono essere una stringa semplice oppure `{en: ..., it: ...}`: se manca una lingua, il sito mostra l'altra con un'etichetta di lingua. `draft: true` = bozza non ancora approvata (non pubblicata in produzione).

| File | Campi obbligatori | Campi facoltativi |
|---|---|---|
| `news.yml` | `id`, `date` (AAAA-MM-GG), `text` | `link`, `draft` |
| `talks.yml` | `id`, `date`, `title`, `event`, `place`, `kind` (talk/poster/invited/keynote) | `files: [{label, url}]`, `link` |
| `projects.yml` | `id`, `title`, `summary`, `role`, `period`, `kind` (funded/open-resource/research) | `links: [{label, url}]`, `image`, `funder`, `code`, `featured` |
| `teaching.yml` | `id`, `title`, `programme`, `level` (BSc/MSc/PhD/open), `language`, `years` | `ects`, `hours`, `current`, `links`, `summary` |
| `roles.yml` | `id`, `title`, `org`, `start`, `kind` (position/visiting/service/education/membership) | `end`, `place`, `description` |
| `software.yml` | `id`, `name`, `repo` (owner/name) | `cran`, `paper_doi`, `summary` |
| `profile.yml` | `name`, `role`, `research_themes[] {id, label, openalex_keywords}` | `bio`, `links`, `contact` |
| `publications.overrides.yml` | — | `hide`, `selected`, `themes`, `links`, `extra` |

### Esempio: aggiungere una news
```yaml
- id: icsds-2026
  date: 2026-12-15
  text:
    en: Talk at ICSDS 2026 in Seville
    it: Intervento a ICSDS 2026 a Siviglia
  link: https://example.org
```
