#!/usr/bin/env bash
# Pubblica la nuova vetrina sul repo GitHub (una tantum).
# Uso:  cd ".../academic-website" && bash scripts/pubblica_su_github.sh
set -euo pipefail
REPO_URL="https://github.com/gianluca-sottile/academic-website.git"

echo "== 1/5 Ambiente Python"
VENV="$HOME/.venvs/academic-website"   # fuori da OneDrive
[ -d "$VENV" ] || python3 -m venv "$VENV"
source "$VENV/bin/activate"
pip install -q -r requirements.txt -r requirements-dev.txt

echo "== 2/5 Aggiornamento completo di pubblicazioni e pacchetti (serve internet)"
git checkout -q master
python scripts/fetch_publications.py
python scripts/fetch_software.py

echo "== 3/5 Test e build di produzione"
python -m pytest -q
BUILD_ENV=production python scripts/build.py
if ! git diff --quiet -- data/; then
  git add data/publications.json data/software.json
  git commit -qm "chore(data): first full refresh"
fi

echo "== 4/5 Allineamento con la storia del repo su GitHub"
git remote get-url origin >/dev/null 2>&1 || git remote add origin "$REPO_URL"
git fetch -q origin
DEFAULT=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
echo "   ramo principale su GitHub: $DEFAULT"
git checkout -q -B publish "origin/$DEFAULT"
git rm -rq --ignore-unmatch .            # svuota l'albero del vecchio sito (resta nella storia)
git checkout master -- .                 # porta dentro la nuova vetrina
git add -A
git commit -qm "New academic showcase: bilingual static site with automatic publications" || echo "   (niente da committare)"

echo "== 5/5 Push"
git push origin "publish:$DEFAULT"
git checkout -q master
echo "Fatto. Netlify ricostruisce gianlucasottile.rbind.io in 1-2 minuti."
