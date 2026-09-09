# Prabowo speech word index

A small, local-first word-frequency index built from ten recent Indonesian YouTube caption tracks.

## Open the UI

Open `index.html` directly, or serve this directory:

```bash
python3 -m http.server 8765
```

The dashboard is self-contained: the current `data/analysis.json` is embedded into the HTML.

## Current corpus

All selected tracks are Indonesian and auto-generated. The public source catalog is
`data/source-catalog.json`. Raw caption snippets are intentionally local-only:
they are fetched into `data/transcripts/raw/` but are ignored by Git so the public
repository does not redistribute the caption text.

The ten uploads are:

- 2026-07-24 — [Pidato Prabowo di Harlah PKB](https://www.youtube.com/watch?v=vyp6JITYFM8) — KOMPASTV
- 2026-06-28 — [Pidato Penutupan Sarasehan Kebangsaan KSTI 2026](https://www.youtube.com/watch?v=xK61ktEglpc) — Pangkep TV
- 2026-06-26 — [Pembukaan Sarasehan Kebangsaan KSTI 2026](https://www.youtube.com/watch?v=hJybE-uF_qE) — Sekretariat Presiden
- 2026-05-01 — [Pidato pada Peringatan Hari Buruh Internasional](https://www.youtube.com/watch?v=rKpNQwecniM) — Prabowo Subianto
- 2026-03-11 — [Pidato di Tasyakuran HUT ke-1 Danantara](https://www.youtube.com/watch?v=VyPCSPnxbaE) — METRO TV
- 2026-02-28 — [Sambutan pada Perayaan Tahun Baru Imlek Nasional](https://www.youtube.com/watch?v=5OIq7GaU4sI) — Sekretariat Presiden
- 2025-10-24 — [Sambutan pada Puncak Peringatan Hari Santri](https://www.youtube.com/watch?v=02IcsjvhFGQ) — Sekretariat Presiden
- 2025-08-31 — [Pernyataan Menyikapi Aksi Demo](https://www.youtube.com/watch?v=3e_gu9rWwWQ) — Kompas.com
- 2025-08-07 — [KSTI Indonesia 2025](https://www.youtube.com/watch?v=E_doThSKS4E) — Sekretariat Presiden
- 2025-04-10 — [Pidato Kenegaraan di Hadapan Parlemen Turkiye](https://www.youtube.com/watch?v=CfnRESwOZKQ) — Sekretariat Presiden

## Method

- `youtube-transcript-api==1.2.4`
- Indonesian (`id`) caption track
- Manual track preferred if available; all selected tracks were auto-generated
- Approximate speech windows exclude obvious MC, opening, music, or closing material
- Bracketed caption events such as `[musik]` and `[tepuk tangan]` removed
- Unicode NFC + casefold + Unicode-aware tokenization
- No de-duplication: repeated spoken words remain counted
- Primary output is surface-form frequency; the UI's `filter kata umum` is an optional view

The counts describe the selected YouTube caption windows, not verified audio ground truth. Review names, numbers, acronyms, and the transcript against the source video before publishing a claim.

## Setup and reproducibility

Use Python 3.12+ and install the pinned dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The fetch step needs network access to YouTube. It writes raw captions and
`data/manifest.json` locally. The remaining analysis and UI build steps run
locally from those files.

## Outputs

- `index.html` — terminal-style interactive dashboard
- `data/analysis.json` — UI data and full per-speech count maps
- `data/word-frequency.csv` — all 2,403 aggregate surface forms
- `data/word-frequency-by-speech.csv` — per-speech counts
- `data/source-catalog.json` — public source IDs, dates, channels, links, and windows
- `data/manifest.json` — local source/fetch status; ignored by Git
- `data/transcripts/raw/*.json` — local-only untouched caption snippets plus track metadata
- `scripts/fetch_sources.py` — fetch the current ten source tracks
- `scripts/analyze_counts.py` — apply windows and deterministic tokenization
- `scripts/export_counts.py` — write CSVs
- `scripts/build_ui.py` — rebuild the embedded dashboard

## Rebuild

```bash
.venv/bin/python scripts/fetch_sources.py
.venv/bin/python scripts/analyze_counts.py
.venv/bin/python scripts/export_counts.py
.venv/bin/python scripts/build_ui.py
```

The scripts overwrite derived JSON/CSV/UI outputs when rerun. The public
snapshot remains usable without raw captions; rerunning `fetch_sources.py`
recreates the ignored local inputs from the source list in the script.

## Public-data and license note

The repository code is MIT-licensed. The YouTube videos and caption tracks are
third-party source material; the model does not grant rights to redistribute
their audiovisual or caption content. This repository publishes source links and
derived counts, while keeping raw caption text out of the public tree. Check
the rights and platform terms before republishing excerpts or monetizing a
video.
