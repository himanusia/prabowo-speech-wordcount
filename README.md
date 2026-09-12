# Prabowo speech corpus index

Local-first word-frequency, topic, and framing index built from Indonesian YouTube caption
tracks. The corpus is deduplicated by speech event and restricted to actual speeches: one
canonical source per event, so a speech reuploaded by seven channels is counted once, and
commentary shows, laugh compilations, and short excerpts are excluded.

`RESEARCH-PACK.md` is a single-file readable summary of every number below.

## Open the UI

Open `index.html` directly, or serve this directory:

```bash
python3 -m http.server 8765
```

The dashboard is self-contained; `data/expanded/analysis.json` is embedded into the HTML
at build time.

## Current corpus

```text
speech events        67    (unique, deduplicated)
caption uploads      128    (eligible items, duplicates folded in)
tokens         153.699
unique words    11.630
date range     2024-08-27 -> 2026-09-09
```

Fetch outcomes across all 160 selected candidates:

```text
caption retrieved                142
subtitles genuinely disabled     3
no Indonesian caption track      15
blocked by YouTube (HTTP 429)    0
not attempted yet                0
```

Every candidate has now been resolved. The 15 without an Indonesian track are Prabowo
speaking English at international forums (EEF Russia, APEC, ADF, SPIEF, Japan and US business
summits), so no Indonesian caption exists to fetch.

Events by number of folded reuploads: 1 dup -> 12 events, 2 dup -> 8 events, 3 dup -> 3 events, 4 dup -> 2 events, 5 dup -> 2 events, 6 dup -> 1 events.

Multi-upload events:

- 2026-08-14 — 🔴BREAKING NEWS - Pidato Kenegaraan Presiden Prabowo di S — 7 uploads
- 2026-06-23 — 🔴BREAKING NEWS - Pidato Presiden Prabowo di Penutupan Mu — 6 uploads
- 2026-09-09 — 🔴BREAKING NEWS - PIDATO PRESIDEN PRABOWO DI PERINGATAN H — 6 uploads
- 2026-06-10 — [FULL] PIDATO PRESIDEN PRABOWO DI MUNAS HIPMI, SINGGUNG  — 5 uploads
- 2026-08-31 — [FULL] Pidato Prabowo Tutup Muktamar NU: Umat Harus Hidu — 5 uploads
- 2026-07-01 — FULL! Pidato Prabowo di HUT ke-80 Bhayangkara: Hukum Tak — 4 uploads
- 2026-08-14 — [FULL] Berapi-api! Pidato Presiden Prabowo Sampaikan RAP — 4 uploads
- 2026-08-29 — Sambutan Presiden Republik Indonesia Prabowo Subianto |  — 4 uploads

## Method

- [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api), pinned to upstream commit `8f150ba8836da30a36bcd40e8fca226ed179ba72`
- Indonesian (`id`) caption track, manual preferred over auto-generated
- Bracketed caption events such as `[musik]` and `[tepuk tangan]` removed
- Unicode NFC + casefold + Unicode-aware tokenization
- No de-duplication of repeated words; every spoken occurrence counts
- Event dedup via 4-token shingle containment between uploads (same day >= 0.22, cross-day >= 0.58)
- One canonical source per event, preferring official channels, then longer transcripts
- Topic layer is curated lexical signals with overlapping categories allowed
- MBG signal counts exact `MBG`, the full `makan bergizi gratis` phrase, `makan` + `bergizi`
  in one caption, and SPPG context; ambiguous acronym hits are reported separately

### Two capture routes, verified identical

The caption endpoint (`/api/timedtext`) rate-limits this IP with HTTP 429 after a burst. The
transcript panel in the YouTube UI reads a different endpoint (`youtubei get_panel`) that is not
throttled, so the remaining uploads were captured through it. Cross-check on video `9rpZpKagShM`:
the API returned 628 snippets and the panel 255 segments, both **15.621 characters and 2.362
words**, normalized ratio 1.000, with identical opening and closing text. The capture route
therefore does not affect any word count.

Panel capture is driven by a browser session, so it is not part of the cron/CLI pipeline:
`scripts/import_panel.py` folds its JSONL output into `manifest.json`.

### What counts as a speech

Media channels add clickbait adjectives ("Berapi-api!", "Bahas ...") to genuine full speeches,
so keyword filtering on those words discards real speeches. Instead a curated list decides, and
every pattern came from a manual pass over all fetched titles:

- rejected: statements by other people, arrival/departure clips, commentary or compilation
  formats, and news items about Prabowo rather than Prabowo speaking
- required: the title must describe a speech or remarks by Prabowo

### Padded livestream captures

A livestream often opens on floor noise, introductions, or unrelated chatter before the speech
starts. Because the canonical picker used to prefer the longest transcript, such a capture could
win and pull thousands of non-speech tokens into the corpus. `pick_canonical()` now measures
where the speech opening formula first appears as a fraction of the transcript and disregards
candidates that start too late, but only when another upload of the same event does start at the
top. Measured on the 2026-08-14 Sidang Tahunan cluster: the padded capture reached its opening at
token 2.058 of 30.742 (6,7%), while the five genuine uploads opened at token 0-11.

## Selection pipeline

```text
discovery     4 yt-dlp queries -> 566 unique uploads
scoring       319 candidates passed the title parser -> 160 seeds
fetching      160 candidates resolved -> 142 caption tracks retrieved
loading       148 items in the corpus input
eligibility   20 excluded as non-speech, clip, or padded capture
dedup         61 duplicate uploads folded in
canonical     67 speech events
```

## Caveats before quoting a number

- All counts are surface forms. `mbg` and `MBG` are the same token after casefolding, but
  `asing` and `masing-masing` are different tokens.
- Caption tracks are not verified audio ground truth. Names, numbers, acronyms, and repeated
  phrases are the usual failure points.
- Speech windows were applied only to ten hand-checked uploads where the recording includes
  MC, music, or closing material. The remaining events use the full caption track, so a few
  still include non-speech material.
- Topic categories are lexical proxies, not classifications. `anak` counts toward
  `kesehatan_dan_gizi` in every context, including ones unrelated to the nutrition program.
- Per-event token counts range from 68 to 7,900. The five longest events supply
  20.4% of all tokens.
- The 67 events are not a random sample. Long speeches at large events are likelier to surface
  in search, so the mix is biased toward state occasions and large mass organisations.
- Only 12 of 67 events use an official channel; the rest are media uploads, so titles and
  durations follow whatever those channels published.

## Headline numbers

Topic signals per 1,000 tokens and event coverage:

```text
mbg                        0.57   24/67
pangan                     3.72   45/67
ekonomi                    5.64   60/67
pendidikan                 3.55   50/67
kesehatan_dan_gizi         3.48   61/67
tata_kelola                3.62   57/67
pertahanan_dan_keamanan    3.64   58/67
nasional_dan_identitas    32.52   67/67
```

Top content words after removing function words and pronouns:

```text
indonesia         1688  events=66
rakyat            1081  events=63
harus              991  events=64
bangsa             863  events=64
negara             795  events=62
tahun              708  events=60
enggak             604  events=49
menteri            548  events=59
ketua              503  events=48
presiden           501  events=64
republik           398  events=62
mau                397  events=53
seluruh            393  events=63
apa                378  events=49
hadir              368  events=61
```

Framing pronouns per 1,000 tokens:

```text
kita     38.59  (5.931 occurrences, 67/67 events)
saya     26.65  (4.096 occurrences, 66/67 events)
mereka    3.38
kami      1.93
```

`kita` leads `saya` across the full corpus. On the original ten-video sample the two were
nearly tied, so the smaller sample was misleading.

MBG: 25 of 67 events carry an MBG signal, 50 exact `MBG` occurrences,
88 policy signals total.

## Per-event numbers

`dup` is how many additional uploads of the same event were folded into it.

| date | tokens | uniq | dup | tier | MBG | channel | title |
|---|---:|---:|---:|---|---:|---|---|
| 2024-08-27 | 2648 | 823 | 0 | media | 0 | KOMPASTV SUKABUMI | Kocak! Pidato Prabowo Subianto di Penutupan Kongres III Na |
| 2024-10-09 | 3315 | 1112 | 0 | full_media | 2 | KOMPASTV | [FULL] Pidato Prabowo di Investor Summit: Bocorkan Susunan |
| 2024-10-20 | 3655 | 1174 | 1 | full_media | 1 | BeritaSatu | [FULL] Pidato Perdana Presiden RI Ke-8 Prabowo Subianto /  |
| 2024-11-29 | 1788 | 598 | 0 | full_media | 1 | KOMPASTV DEWATA | [FULL] Pidato Presiden Prabowo Subianto Umumkan Kenaikan G |
| 2024-12-04 | 3552 | 1120 | 1 | full_media | 3 | METRO TV | [FULL] Pidato Presiden Prabowo di Pembukaan Sidang Tanwir  |
| 2024-12-19 | 2388 | 761 | 0 | full_media | 0 | Kompas.com | [FULL] Pidato Prabowo di Kairo: Singgung Gus Dur, Hitung K |
| 2024-12-28 | 1564 | 574 | 1 | full_media | 0 | Kompas.com | [FULL] Pidato Prabowo pada Perayaan Natal Nasional 2024 |
| 2025-02-10 | 1465 | 551 | 0 | full_media | 0 | BeritaSatu | (FULL) Pidato Presiden Prabowo Dalam Kongres ke-18 Muslima |
| 2025-04-10 | 807 | 335 | 0 | official | 0 | Sekretariat Presiden | Pidato Kenegaraan Presiden Prabowo di Hadapan Parlemen Tur |
| 2025-05-01 | 1687 | 586 | 0 | full_media | 0 | Kompas TV Biro Makassar | [FULL]  PIDATO PRESIDEN PRABOWO DI PERINGATAN MAY DAY 2025 |
| 2025-06-02 | 1324 | 493 | 0 | full_media | 0 | KOMPASTV | [FULL] Berapi-api! Pidato Presiden Prabowo Upacara Hari La |
| 2025-06-11 | 1321 | 573 | 0 | full_media | 0 | METRO TV | [FULL] Pidato Presiden Prabowo di Indo Defence Expo and Fo |
| 2025-07-01 | 1102 | 424 | 0 | official | 2 | Prabowo Subianto | Full Pidato Presiden Prabowo di Upacara Peringatan ke 79 H |
| 2025-07-21 | 3288 | 1132 | 0 | media | 1 | KOMPASTV JAWA TENGAH | Pidato Presiden Prabowo di Kongres PSI 2025 |
| 2025-07-23 | 649 | 281 | 0 | full_media | 0 | KOMPASTV | [FULL] Pidato Menggelegar Presiden Prabowo! Beri Amanat di |
| 2025-08-07 | 588 | 315 | 0 | official | 0 | Sekretariat Presiden | Presiden Prabowo Hadiri KSTI Indonesia 2025 |
| 2025-08-15 | 5764 | 1638 | 0 | full_media | 8 | Kompas.com | [FULL] Pidato Kenegaraan Presiden Prabowo pada Sidang Tahu |
| 2025-08-31 | 739 | 329 | 0 | media | 0 | Kompas.com | Pernyataan Presiden Prabowo Menyikapi Aksi Demo |
| 2025-09-29 | 5204 | 1385 | 0 | full_media | 4 | tvOneNews | [FULL] Pidato Lengkap Presiden Prabowo di Munas Ke-VI PKS  |
| 2025-10-23 | 863 | 322 | 0 | full_media | 0 | METRO TV | [FULL] Pidato Presiden Prabowo di Pertemuan Diplomatik Ind |
| 2025-10-24 | 236 | 144 | 0 | official | 0 | Sekretariat Presiden | Sambutan Presiden Prabowo pada Puncak Peringatan Hari Sant |
| 2025-11-06 | 1708 | 581 | 0 | full_media | 0 | KOMPASTV | [FULL] Pidato Prabowo Resmikan Pabrik Kimia di Cilegon: Ne |
| 2025-11-28 | 1404 | 577 | 0 | full_media | 0 | CNN Indonesia | LIVE Pidato Presiden Prabowo di Pertemuan Tahunan Bank Ind |
| 2025-11-28 | 2258 | 775 | 2 | full_media | 1 | KOMPASTV | [FULL] Pidato Presiden Prabowo di Peringatan Hari Guru Nas |
| 2025-12-05 | 1316 | 536 | 0 | full_media | 0 | METRO TV | [FULL] Pidato Presiden Prabowo untuk Atlet Sea Games 2025: |
| 2025-12-25 | 213 | 120 | 0 | official | 0 | Sekretariat Presiden | Presiden Prabowo Sampaikan Ucapan Selamat Hari Natal 2025, |
| 2026-01-05 | 2952 | 830 | 0 | full_media | 11 | VIVA.CO.ID | (FULL) Pidato Presiden Prabowo di Perayaan Natal Nasional  |
| 2026-01-12 | 1055 | 551 | 0 | media | 0 | tvOneNews | Sambutan Presiden Prabowo di Sekolah Rakyat Banjarbaru / B |
| 2026-02-02 | 6257 | 1619 | 0 | full_media | 11 | METRO TV | [FULL] PIDATO PRESIDEN PRABOWO DI RAKORNAS PEMERINTAH PUSA |
| 2026-02-28 | 333 | 175 | 0 | official | 0 | Sekretariat Presiden | Sambutan Presiden Prabowo pada Perayaan Tahun Baru Imlek N |
| 2026-03-10 | 1388 | 559 | 1 | full_media | 0 | METRO TV | BREAKING NEWS - [FULL] Pidato Presiden Prabowo di Peringat |
| 2026-03-11 | 1205 | 459 | 0 | media | 0 | METRO TV | Pidato Presiden Prabowo di Tasyakuran HUT ke-1 Danantara |
| 2026-04-18 | 543 | 258 | 0 | media | 0 | KOMPASTV | Pidato Presiden Prabowo di Retret Ketua DPRD se-Indonesia: |
| 2026-05-01 | 2044 | 691 | 2 | official | 5 | Prabowo Subianto | Pidato Presiden Prabowo pada Peringatan Hari Buruh Interna |
| 2026-05-13 | 2666 | 886 | 1 | official | 0 | Prabowo Subianto | Pidato Presiden Prabowo di Kejagung saat Penyerahan Denda  |
| 2026-05-16 | 3552 | 1104 | 0 | full_media | 9 | METRO TV | [FULL] BREAKING NEWS - PIDATO PRESIDEN PRABOWO DI PERESMIA |
| 2026-05-20 | 68 | 47 | 2 | official | 0 | Sekretariat Presiden | Presiden Prabowo Sampaikan Pidato pada Rapat Paripurna DPR |
| 2026-05-29 | 661 | 261 | 0 | full_media | 0 | Liputan6 | [FULL] Pidato Presiden Prabowo: Pujian untuk Macron Hingga |
| 2026-05-31 | 352 | 206 | 0 | official | 0 | Sekretariat Presiden | Sambutan Presiden Prabowo pada Puncak Peringatan Hari Tri  |
| 2026-06-01 | 1989 | 788 | 2 | media | 1 | KOMPASTV JAWA BARAT | BREAKING NEWS: Pidato Presiden Prabowo Peringatan Hari Lah |
| 2026-06-03 | 2386 | 730 | 1 | official | 3 | Sekretariat Presiden | Pidato Presiden RI pada Acara Building Indonesia's Future  |
| 2026-06-10 | 4297 | 1246 | 4 | full_media | 0 | METRO TV | [FULL] PIDATO PRESIDEN PRABOWO DI MUNAS HIPMI, SINGGUNG KR |
| 2026-06-23 | 4808 | 1668 | 5 | media | 0 | KOMPASTV | 🔴BREAKING NEWS - Pidato Presiden Prabowo di Penutupan Muna |
| 2026-06-24 | 2990 | 901 | 2 | full_media | 4 | KOMPASTV | [FULL] Pidato Prabowo di PNKT XVII 2026: Australia Minta P |
| 2026-06-26 | 1619 | 617 | 0 | official | 0 | Sekretariat Presiden | Pembukaan Sarasehan Kebangsaan KSTI 2026 |
| 2026-06-28 | 3303 | 765 | 1 | media | 0 | KOMPASTV | 🔴BREAKING NEWS - Pidato Presiden Prabowo Tutup Sarasehan K |
| 2026-07-01 | 1822 | 679 | 3 | full_media | 2 | KOMPASTV | FULL! Pidato Prabowo di HUT ke-80 Bhayangkara: Hukum Tak B |
| 2026-07-09 | 2541 | 879 | 2 | full_media | 0 | KOMPASTV DEWATA | [FULL] Pidato Prabowo Luncurkan Biodiesel B50: Indonesia J |
| 2026-07-10 | 3129 | 948 | 2 | full_media | 7 | Tribun Lombok | Full Pidato Presiden Prabowo di Lombok, MBG KITA LANJUTKAN |
| 2026-07-12 | 3715 | 1117 | 1 | media | 0 | CNN Indonesia | BREAKING NEWS Pidato Presiden Prabowo di Puncak Peringatan |
| 2026-07-16 | 1575 | 601 | 0 | full_media | 0 | KOMPASTV | FULL! Pidato Prabowo Resmikan Groundbreaking LNG Abadi Mas |
| 2026-07-17 | 2617 | 905 | 1 | full_media | 0 | KOMPASTV | [FULL] Pidato Presiden Prabowo di Panen Raya Tebu Serentak |
| 2026-07-20 | 5868 | 1482 | 1 | full_media | 3 | tvOneNews | [FULL] Pidato Presiden Prabowo Di Sidang Kabinet Paripurna |
| 2026-07-24 | 2730 | 900 | 1 | media | 0 | KOMPASTV | Pidato Prabowo di Harlah PKB |
| 2026-07-29 | 1616 | 604 | 0 | full_media | 0 | METRO TV | [FULL] Pidato Presiden Prabowo di Pelantikan Pamong Praja  |
| 2026-07-30 | 2412 | 834 | 2 | full_media | 0 | KOMPASTV | [FULL] Pidato Prabowo di Akad Rumah Subsidi: Singgung Pres |
| 2026-07-30 | 1414 | 601 | 0 | full_media | 0 | METRO TV | [FULL] BREAKING NEWS - PIDATO PRESIDEN PRABOWO SAAT RESMIK |
| 2026-07-31 | 2501 | 913 | 0 | media | 1 | tvOneNews | [Breaking News] Pidato Presiden Prabowo di Pertemuan denga |
| 2026-08-06 | 1185 | 448 | 0 | full_media | 0 | KOMPASTV | [FULL] Pidato Prabowo Depan 150 Peneliti BRIN Soroti Pendi |
| 2026-08-07 | 2315 | 818 | 0 | full_media | 0 | KOMPASTV | FULL! Pidato Prabowo di Peluncuran Buku Bahlil: Swasembada |
| 2026-08-14 | 7900 | 1910 | 6 | media | 5 | KOMPASTV JAWA TENGAH | 🔴BREAKING NEWS - Pidato Kenegaraan Presiden Prabowo di Sid |
| 2026-08-14 | 5554 | 1582 | 3 | full_media | 1 | KOMPASTV | [FULL] Berapi-api! Pidato Presiden Prabowo Sampaikan RAPBN |
| 2026-08-25 | 1388 | 576 | 0 | full_media | 0 | METRO TV | [FULL] PIDATO PRABOWO RESMIKAN PLTS DI BALI: BERI BINTANG  |
| 2026-08-29 | 1700 | 673 | 3 | media | 1 | KRAPYAK TV | Sambutan Presiden Republik Indonesia Prabowo Subianto / Mu |
| 2026-08-31 | 1520 | 616 | 4 | full_media | 0 | MerdekaDotCom | [FULL] Pidato Prabowo Tutup Muktamar NU: Umat Harus Hidup  |
| 2026-09-09 | 3310 | 1011 | 5 | media | 1 | Seputar iNews RCTI | 🔴BREAKING NEWS - PIDATO PRESIDEN PRABOWO DI PERINGATAN HUT |
| 2026-09-09 | 1573 | 632 | 1 | media | 0 | Pangkep TV | [FUUL] Sambutan Presiden Prabowo Lepas Kontingen Indonesia |

Machine-readable versions: `data/expanded/events.csv` (this table),
`data/expanded/word-frequency.csv` (all 11.630 aggregate surface forms),
`data/expanded/word-frequency-by-event.csv` (per-event word counts).

## Setup and reproducibility

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

Fetching needs network access to YouTube and writes the ignored raw caption files. The
analysis, export, and build steps run offline from those files.

## Outputs

- `index.html` — terminal-style interactive dashboard
- `RESEARCH-PACK.md` — readable single-file summary of the current numbers
- `data/expanded/analysis.json` — totals, word index, per-event counts, MBG evidence
- `data/expanded/word-frequency.csv` — aggregate surface forms
- `data/expanded/word-frequency-by-event.csv` — per-event counts
- `data/expanded/events.csv` — one row per canonical event with MBG columns
- `data/expanded/source-catalog.json` — canonical events and duplicate groups
- `data/expanded/candidate-seeds.json` — the discovery/selection list driving fetching
- `data/expanded/metadata.json` — upload dates, durations, channels
- `data/expanded/pending.json` — candidates not fetched, with the per-item reason
- `data/expanded/ratelimit-observations.json` — measured 429 behaviour and recovery time
- `data/expanded/raw/*.json` — local-only caption snippets; ignored by Git
- `scripts/collect_expanded.py` — fetch the candidate set through the caption API
- `scripts/fetch_metadata.py` — fill upload dates, channels, durations via yt-dlp
- `scripts/import_panel.py` — fold panel-captured transcripts into the manifest
- `scripts/list_pending.py` — report missing candidates and why
- `scripts/analyze_expanded.py` — dedupe events, count words, derive topics/framing/MBG
- `scripts/export_expanded.py` — write CSVs
- `scripts/build_ui_expanded.py` — rebuild the embedded dashboard

## Rebuild

```bash
.venv/bin/python scripts/collect_expanded.py
.venv/bin/python scripts/fetch_metadata.py
.venv/bin/python scripts/analyze_expanded.py
.venv/bin/python scripts/export_expanded.py
.venv/bin/python scripts/build_ui_expanded.py
```

The caption API is the network step and it is rate limited. It stops at the first 429 instead of
grinding through cooldowns:

```bash
.venv/bin/python scripts/collect_expanded.py --only-pending --stop-on-block --sleep 8
```

## Public-data and license note

The repository code is MIT-licensed. The YouTube videos and caption tracks are third-party
source material; nothing here grants rights to redistribute their audiovisual or caption
content. This repository publishes source links and derived counts while keeping raw caption
text out of the public tree.
