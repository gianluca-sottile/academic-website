# Vetrina accademica a 360° — Gianluca Sottile
*Design doc · 20 novembre 2026 · stato: bozza da approvare*

## 1. Intento
Sostituire l'attuale sito Hugo Academic 4.8 (gianlucasottile.rbind.io, fermo al 2020, pubblicazioni ferme al 2023) con **una vetrina unica, da diffondere, da cui parte tutto**: ricerca, pubblicazioni, software, progetti, didattica, ruoli accademici. Deve essere *bella e invitante* — non "la classica pagina statica brutta" — e richiedere manutenzione minima.

**Successo:** un link da mettere in firma, su LinkedIn, nei CV e nelle slide; chi arriva (collega, commissione, studente, collaboratore) capisce in 10 secondi chi è Gianluca e trova in 2 click qualsiasi cosa faccia.

## 2. Obiettivi / Non-obiettivi / Anti-obiettivi
**Obiettivi**
- Home-vetrina con tutte le sezioni, ciascuna con rimando esaustivo (pagina dedicata o link esterno).
- Pubblicazioni **aggiornate automaticamente** (nessun inserimento manuale).
- **Progetti e Didattica** in primo piano (richiesta esplicita).
- Esperienze e ruoli accademici ben visibili (timeline).
- Tutti i pacchetti R con link a GitHub (e CRAN).
- Logo/monogramma personale al posto dell'avatar anonimo.

**Non-obiettivi**
- Blog, commenti, CMS, ricerca full-text.
- Paper in lavorazione o in revisione (esclusi per ora: IS-Score, FCST, MERE).

**Anti-obiettivi (fallimento anche se "funziona")**
- Aspetto da template accademico generico.
- Dipendenza da un framework che si rompe agli aggiornamenti.
- Qualsiasi contenuto riservato pubblicato (lavoro editoriale/referaggio, link anonimi di revisione, ID di manoscritti).
- Liste lunghe e piatte senza gerarchia.

## 3. Vincoli
- Sito statico, nessun server. Hosting gratuito.
- Aggiornamenti manuali **solo** per: news, congressi/talk (fatti da Gianluca o con Claude).
- Tutto il resto o automatico (pubblicazioni, metadati pacchetti) o in file dati che cambiano raramente (ruoli, corsi, progetti).
- Accessibile (WCAG AA), responsive (da 360 px), tema chiaro/scuro, veloce (nessun framework JS pesante).
- Indicizzabile: HTML pre-generato (non contenuto caricato solo via JS) per Google Scholar/motori di ricerca.

## 4. Approcci considerati
| | Approccio | Pro | Contro |
|---|---|---|---|
| **A ✔ scelto** | Sito su misura HTML/CSS/JS + dati in YAML + piccolo script di build | Libertà grafica totale, zero lock-in, durata nel tempo | Prima costruzione più onerosa |
| B | Hugo aggiornato (Hugo Blox) | Ecosistema noto | Di fatto riscrittura; look da template; rotture frequenti |
| C | Astro | Risultato curato | Toolchain Node non usata altrove, più manutenzione |

Quarto scartato: ottimo per documentazione, debole come vetrina. **Gianluca ha scelto A.**

## 5. Architettura (scelta: A)
```
academic-website/
├── data/                 ← l'unica cosa che si tocca a mano
│   ├── profile.yml       bio, interessi, link (ORCID, Scholar, GitHub, LinkedIn…)
│   ├── roles.yml         ruoli accademici + esperienze (timeline)
│   ├── news.yml          news e notizie brevi            [manuale]
│   ├── talks.yml         congressi, talk, poster         [manuale]
│   ├── projects.yml      progetti di ricerca e divulgazione
│   ├── teaching.yml      corsi (titolo, CdS, CFU, a.a., lingua, link materiali)
│   ├── software.yml      pacchetti (nome, repo GitHub, CRAN, paper collegato)
│   ├── publications.overrides.yml  nascondi/metti in evidenza/aggiungi link codice
│   └── publications.json ← GENERATO dal cron, non si modifica
├── src/                  template HTML, CSS, JS, logo SVG
├── scripts/
│   ├── fetch_publications.py   ORCID → OpenAlex/Crossref → publications.json
│   ├── fetch_software.py       CRAN (versione, download) + GitHub (stelle, ultimo rilascio)
│   └── build.py                YAML/JSON + template → site/ (HTML statico)
├── static/               PDF (CV, poster, slide), immagini
├── site/                 output pubblicato (generato)
├── legacy/               vecchio sito Hugo archiviato (non pubblicato)
└── .github/workflows/
    ├── build.yml         build + deploy a ogni push
    └── refresh.yml       cron settimanale: aggiorna pubblicazioni e pacchetti, commit se cambia, ricostruisce
```
- **Build:** Python 3 + Jinja2 + PyYAML (unica dipendenza). Output HTML/CSS/JS puri.
- **JS lato client** solo per interazioni: filtri pubblicazioni (anno/tema/tipo), ricerca rapida, animazioni allo scroll, toggle tema.
- **Pubblicazioni:** ORCID 0000-0001-9347-7251 è la fonte autorevole dell'elenco; i DOI vengono arricchiti con OpenAlex (autori, rivista, citazioni, link open access) e Crossref come fallback. `publications.overrides.yml` permette di nascondere voci, marcarne alcune come "selected", aggiungere link a codice/pacchetto. Se una fonte non risponde il cron **non** cancella nulla: mantiene l'ultimo JSON valido.
- **Scopus:** non nella prima versione (richiede chiave API istituzionale); aggancio predisposto.

## 6. Struttura dei contenuti
**Home (vetrina, una pagina lunga con navigazione a sezioni)**
1. **Hero** — monogramma, nome, ruolo ("Associate Professor of Statistics, University of Palermo"), una frase sulla ricerca, link rapidi (CV, Scholar, ORCID, GitHub, email), contatori vivi (pubblicazioni, citazioni, pacchetti, corsi).
2. **About & temi di ricerca** — bio breve + temi come "card" cliccabili che filtrano le pubblicazioni.
3. **News** — ultime 4–5 voci (manuali), link a "tutte".
4. **Progetti** ★ — card grandi con immagine/anteprima: StatAtlas, From Data to Models with R, CoViSTAT19, PON AIM, progetti finanziati (es. PRIN 2022 – da confermare).
5. **Didattica** ★ — corsi attuali e passati (CdS, CFU, a.a., lingua, link materiali/pagina UniPA), risorse aperte.
6. **Pubblicazioni** — 5–6 "selected" + link alla pagina completa filtrabile.
7. **Software** — tutti i pacchetti con badge (CRAN, versione, GitHub), paper collegato.
8. **Percorso & ruoli** — timeline accademica (ruoli, posizioni, visiting, formazione, incarichi istituzionali, società scientifiche).
9. **Talk & congressi** — ultimi, link a elenco completo con PDF.
10. **Contatti** — email, ufficio, mappa leggera (link, non embed pesante).

**Pagine dedicate:** `/publications`, `/teaching` (+ eventuale pagina per corso), `/projects`, `/software`, `/talks`, `/cv`.

## 7. Contenuti iniziali noti
- **Software:** islasso, Qest, qrcmNP, clustEff (+ altri da confermare, es. cglasso se co-autore).
- **Progetti:** StatAtlas (github.com/gianluca-sottile/statatlas), From Data to Models with R (gianluca-sottile.github.io/An-R-Tutorial-for-Beginners), CoViSTAT19, PON AIM.
- **Didattica:** Statistical Machine Learning (LM Statistica e Data Science, EN, 42 h, a.a. 2026/27); Statistica (L-18 Economia e Amministrazione Aziendale, IT); Optimization for Statistical and Machine Learning; Financial Markets Laboratory; corsi passati di Statistica (Architettura, Biologia).
- **Esclusi:** IS-Score, FCST, MERE (in lavorazione); qualsiasi attività editoriale/referaggio.

## 8. Identità visiva
- Direzione: editoriale-scientifica, sobria ma viva. Tipografia di carattere (serif per titoli + sans leggibile), palette ristretta con un colore d'accento, molto spazio bianco, micro-animazioni discrete, grafica generativa leggera legata alla statistica (curve, percorsi di regolarizzazione, densità) come motivo ricorrente.
- **Logo:** monogramma "GS" SVG su misura che richiama un elemento statistico (es. percorso lasso / curva quantile). 2–3 proposte da scegliere tramite mockup.
- Guida di gusto: skill `frontend-design`; revisione con `design-critique` e `accessibility-review`.

## 9. Lasciato al builder
Scelta finale di font e palette (dopo mockup), dettagli di animazione, struttura interna dei template, formato preciso dei file YAML, test (build riproducibile, validazione link, controllo HTML).

## 10. Scelte fatte da Claude (correggibili)
- **Temi di ricerca sulle pubblicazioni:** etichettati a mano in `publications.overrides.yml` (pre-compilati da Claude per l'archivio attuale); le nuove pubblicazioni ricevono un tema suggerito dai "topics" di OpenAlex, sovrascrivibile. Una pubblicazione senza tema compare comunque nell'elenco completo.
- **Citazioni:** da OpenAlex, dichiarate come tali ("fonte: OpenAlex") con link al profilo Google Scholar (che non ha API gratuita e dà numeri più alti).
- **Migrazione contenuti:** si portano talk, poster/slide PDF, CV, progetti CoViSTAT19/AIM, esperienze; si eliminano post demo, slide d'esempio, cartelle "copia", widget inutilizzati.
- **Vecchi URL:** redirect dai percorsi Hugo (`/publication/…`, `/talk/…`, `/courses/…`) alle nuove pagine.
- **Repo:** il vecchio sito Hugo viene spostato in `legacy/` (escluso dal deploy); la vecchia cartella `data/` di Hugo finisce lì, liberando il nome.
- **Testi mancanti** (bio aggiornata, frasi sui temi, descrizioni progetti/corsi): bozze scritte da Claude a partire da sito attuale, CV e sessioni precedenti, da rivedere da Gianluca prima della pubblicazione. Nessuna sezione esce vuota: una sezione senza dati non viene mostrata.
- **Voci "da confermare"** (PRIN 2022, cglasso, altri pacchetti): escluse finché Gianluca non conferma.

## 11. Decisioni di Gianluca
- Lingua: **bilingue IT/EN con selettore** (accessibilità per studenti e colleghi italiani e stranieri). Implementazione (scelta di Claude): inglese alla radice `/`, italiano sotto `/it/`, `hreflang` reciproci, selettore che porta alla stessa pagina nell'altra lingua, lingua del browser suggerita alla prima visita (mai redirect forzato). Nei YAML i campi testuali sono `{en: …, it: …}`; se una news o un talk ha una sola lingua, viene mostrato in entrambe le versioni con un piccolo badge di lingua (così l'inserimento rapido resta semplice). Titoli delle pubblicazioni non tradotti.
- Logo: **combinazione D + B.** Firma tipografica "gianluca / *sottile*" in serif corsivo con linea sottilissima d'accento (header, footer, CV) + simbolo "G con curva quantile a S e punti dati" (favicon, avatar social, icona app). Palette di partenza: inchiostro #1F2A44, carta #F7F4EE, accento corallo #D85A30 (rifinibile nei mockup).
- **Stato: design approvato da Gianluca il 20/11/2026.**
- Pacchetti: islasso, Qest, qrcmNP, clustEff (lista chiusa finché non ce ne sono di nuovi).
- Progetti finanziati: aggiunto **PRIN 2022 "Spatio-temporal Functional Marked Point Processes for probabilistic forecasting of earthquakes"** (cod. 2022BN7CJP, PI G. Adelfio) — Gianluca partecipante; sito/link del progetto da fornire se esiste.
- Hosting / dominio / repo: **repo esistente github.com/gianluca-sottile/academic-website; Netlify resta e serve il sito su gianlucasottile.rbind.io.** Netlify costruisce dal repo (`netlify.toml` aggiornato: comando `python scripts/build.py`, publish `site/`); il cron settimanale gira su GitHub Actions e committa nel repo, Netlify ricostruisce automaticamente. Redirect dei vecchi URL tramite `_redirects` di Netlify. Il lavoro avviene su un branch dedicato, così il sito attuale resta online fino al passaggio.
- Elenco completo pacchetti e progetti finanziati: _da fornire_
