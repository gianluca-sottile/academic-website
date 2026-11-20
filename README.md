# gianlucasottile.rbind.io

Vetrina accademica di Gianluca Sottile — sito statico bilingue (EN `/`, IT `/it/`).

## Build locale
```bash
pip install -r requirements.txt -r requirements-dev.txt
python scripts/build.py      # genera site/
python -m pytest             # test
python -m http.server -d site 8000
```

## Cosa si modifica a mano
Solo i file in `data/` (vedi `data/schema.md`). Le pubblicazioni (`data/publications.json`) e i dati dei pacchetti (`data/software.json`) si aggiornano da soli ogni settimana.

Il vecchio sito Hugo è archiviato in `legacy/` (non pubblicato).
