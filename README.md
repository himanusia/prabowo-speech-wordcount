# Prabowo speech corpus index

Local-first word-frequency, topic, and framing index built from Indonesian YouTube caption
tracks. The corpus is deduplicated by speech event: one canonical source per event, so a
speech reuploaded by seven channels is counted once.

## Open the UI

Open `index.html` directly, or serve this directory:

```bash
python3 -m http.server 8765
```

The dashboard is self-contained; `data/expanded/analysis.json` is embedded into the HTML
at build time.

## Current corpus

```text
speech events        45    (unique, deduplicated)
caption uploads      76    (eligible items, duplicates folded in)
tokens         106.246
unique words    9.007
date range     2025-02-10 → 2026-09-09
```

Fetch outcomes across all 160 selected candidates:

```text
caption retrieved               74
HTTP 429, reported as IpBlocked 31
subtitles genuinely disabled     3
no Indonesian caption track      13
not attempted yet                39
```

Events by number of folded reuploads: 1 dup -> 7 events, 2 dup -> 7 events, 3 dup -> 2 events, 4 dup -> 1 events.

Multi-upload events:

- 2026-05-01 — Pidato Presiden Prabowo pada Peringatan Hari Buruh Inter — 5 uploads
- 2026-06-10 — [FULL] PIDATO PRESIDEN PRABOWO DI MUNAS HIPMI, SINGGUNG  — 4 uploads
- 2026-08-14 — [FULL] Pidato Presiden Prabowo-Puan Maharani soal RAPBN  — 4 uploads
- 2026-06-23 — Pidato Lengkap Presiden Prabowo Subianto di Musyawarah U — 3 uploads
- 2026-06-24 — [FULL] Pidato Prabowo di PNKT XVII 2026: Australia Minta — 3 uploads
- 2026-07-01 — FULL! Pidato Prabowo di HUT ke-80 Bhayangkara: Hukum Tak — 3 uploads
- 2026-07-09 — [FULL] Pidato Prabowo Luncurkan Biodiesel B50: Indonesia — 3 uploads
- 2026-07-10 — Full Pidato Presiden Prabowo di Lombok, MBG KITA LANJUTK — 3 uploads
- 2026-08-14 — [FULL] Pidato Presiden Prabowo di Sidang Tahunan MPR RI  — 3 uploads
- 2026-08-31 — [FULL] PIDATO PRESIDEN PRABOWO DI PENUTUPAN MUKTAMAR KE- — 3 uploads

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

## Selection pipeline

```text
discovery     4 yt-dlp queries -> 566 unique uploads
scoring       319 candidates passed the title parser -> 160 seeds
fetching      121 attempts logged -> 74 caption tracks retrieved
loading       80 items in the corpus input
eligibility   4 excluded as non-speech (MC, minister statements, arrival clips)
dedup         31 duplicate uploads folded in
canonical     45 speech events
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
- The corpus is not exhaustive: 31 candidates were rejected with HTTP 429 and 39 were never
  attempted. See `data/expanded/pending.json`.

## Headline numbers

Topic signals per 1,000 tokens and event coverage:

```text
mbg                        0.73   16/45
pangan                     4.14   32/45
ekonomi                    5.86   40/45
pendidikan                 2.67   33/45
kesehatan_dan_gizi         4.01   40/45
tata_kelola                3.72   38/45
pertahanan_dan_keamanan    3.73   36/45
nasional_dan_identitas    32.77   45/45
```

Top content words after removing function words and pronouns:

```text
indonesia         1118  events=44
rakyat             809  events=42
harus              715  events=42
negara             580  events=41
tahun              574  events=41
bangsa             568  events=44
enggak             442  events=30
menteri            342  events=36
presiden           341  events=42
ketua              325  events=30
apa                293  events=30
mau                285  events=33
seluruh            277  events=42
republik           269  events=40
hadir              263  events=38
```

Framing pronouns per 1,000 tokens:

```text
kita     38.49  (4.089 occurrences, 45/45 events)
saya     25.27  (2.685 occurrences, 44/45 events)
mereka    2.93
kami      1.67
```

`kita` leads `saya` across the full corpus. On the original ten-video sample the two were
nearly tied, so the smaller sample was misleading.

MBG: 17 of 45 events carry an MBG signal, 54 exact
`MBG` occurrences, 78 policy signals total.

## Per-event numbers

`dup` is how many additional uploads of the same event were folded into it.

| date | tokens | uniq | dup | tier | MBG | channel | title |
|---|---:|---:|---:|---|---:|---|---|
| 2025-02-10 | 1465 | 551 | 0 | full_media | 0 | BeritaSatu | (FULL) Pidato Presiden Prabowo Dalam Kongres ke-18 Muslima |
| 2025-04-10 | 807 | 335 | 0 | official | 0 | Sekretariat Presiden | Pidato Kenegaraan Presiden Prabowo di Hadapan Parlemen Tur |
| 2025-07-01 | 1102 | 424 | 0 | official | 2 | Prabowo Subianto | Full Pidato Presiden Prabowo di Upacara Peringatan ke 79 H |
| 2025-08-07 | 588 | 315 | 0 | official | 0 | Sekretariat Presiden | Presiden Prabowo Hadiri KSTI Indonesia 2025 |
| 2025-08-31 | 739 | 329 | 0 | media | 0 | Kompas.com | Pernyataan Presiden Prabowo Menyikapi Aksi Demo |
| 2025-09-29 | 5204 | 1385 | 0 | full_media | 4 | tvOneNews | [FULL] Pidato Lengkap Presiden Prabowo di Munas Ke-VI PKS  |
| 2025-10-24 | 236 | 144 | 0 | official | 0 | Sekretariat Presiden | Sambutan Presiden Prabowo pada Puncak Peringatan Hari Sant |
| 2025-12-25 | 213 | 120 | 0 | official | 0 | Sekretariat Presiden | Presiden Prabowo Sampaikan Ucapan Selamat Hari Natal 2025, |
| 2026-01-05 | 2952 | 830 | 0 | full_media | 11 | VIVA.CO.ID | (FULL) Pidato Presiden Prabowo di Perayaan Natal Nasional  |
| 2026-02-02 | 6257 | 1619 | 0 | full_media | 11 | METRO TV | [FULL] PIDATO PRESIDEN PRABOWO DI RAKORNAS PEMERINTAH PUSA |
| 2026-02-28 | 333 | 175 | 0 | official | 0 | Sekretariat Presiden | Sambutan Presiden Prabowo pada Perayaan Tahun Baru Imlek N |
| 2026-03-10 | 1388 | 559 | 1 | full_media | 0 | METRO TV | BREAKING NEWS - [FULL] Pidato Presiden Prabowo di Peringat |
| 2026-03-11 | 1205 | 459 | 0 | media | 0 | METRO TV | Pidato Presiden Prabowo di Tasyakuran HUT ke-1 Danantara |
| 2026-05-01 | 2044 | 691 | 4 | official | 5 | Prabowo Subianto | Pidato Presiden Prabowo pada Peringatan Hari Buruh Interna |
| 2026-05-13 | 2769 | 916 | 0 | full_media | 0 | METRO TV | BREAKING NEWS - [FULL] PIDATO PRESIDEN PRABOWO DI PENYERAH |
| 2026-05-16 | 3552 | 1104 | 0 | full_media | 9 | METRO TV | [FULL] BREAKING NEWS - PIDATO PRESIDEN PRABOWO DI PERESMIA |
| 2026-05-20 | 68 | 47 | 1 | official | 0 | Sekretariat Presiden | Presiden Prabowo Sampaikan Pidato pada Rapat Paripurna DPR |
| 2026-05-29 | 661 | 261 | 0 | full_media | 0 | Liputan6 | [FULL] Pidato Presiden Prabowo: Pujian untuk Macron Hingga |
| 2026-05-31 | 352 | 206 | 0 | official | 0 | Sekretariat Presiden | Sambutan Presiden Prabowo pada Puncak Peringatan Hari Tri  |
| 2026-06-01 | 1520 | 605 | 1 | full_media | 1 | CNN Indonesia | FULL Pidato Prabowo di Upacara Hari Lahir Pancasila |
| 2026-06-03 | 2386 | 730 | 1 | official | 3 | Sekretariat Presiden | Pidato Presiden RI pada Acara Building Indonesia's Future  |
| 2026-06-10 | 4297 | 1246 | 3 | full_media | 0 | METRO TV | [FULL] PIDATO PRESIDEN PRABOWO DI MUNAS HIPMI, SINGGUNG KR |
| 2026-06-23 | 2358 | 795 | 2 | full_media | 0 | BeritaSatu | Pidato Lengkap Presiden Prabowo Subianto di Musyawarah Ula |
| 2026-06-24 | 2990 | 901 | 2 | full_media | 4 | KOMPASTV | [FULL] Pidato Prabowo di PNKT XVII 2026: Australia Minta P |
| 2026-06-26 | 1619 | 617 | 0 | official | 0 | Sekretariat Presiden | Pembukaan Sarasehan Kebangsaan KSTI 2026 |
| 2026-06-28 | 1137 | 462 | 0 | media | 0 | Pangkep TV | Pidato Penutupan Sarasehan Kebangsaan KSTI 2026 |
| 2026-07-01 | 1822 | 679 | 2 | full_media | 2 | KOMPASTV | FULL! Pidato Prabowo di HUT ke-80 Bhayangkara: Hukum Tak B |
| 2026-07-09 | 2541 | 879 | 2 | full_media | 0 | KOMPASTV DEWATA | [FULL] Pidato Prabowo Luncurkan Biodiesel B50: Indonesia J |
| 2026-07-10 | 3129 | 948 | 2 | full_media | 7 | Tribun Lombok | Full Pidato Presiden Prabowo di Lombok, MBG KITA LANJUTKAN |
| 2026-07-16 | 1575 | 601 | 0 | full_media | 0 | KOMPASTV | FULL! Pidato Prabowo Resmikan Groundbreaking LNG Abadi Mas |
| 2026-07-17 | 2617 | 905 | 1 | full_media | 0 | KOMPASTV | [FULL] Pidato Presiden Prabowo di Panen Raya Tebu Serentak |
| 2026-07-20 | 5868 | 1482 | 0 | full_media | 3 | tvOneNews | [FULL] Pidato Presiden Prabowo Di Sidang Kabinet Paripurna |
| 2026-07-24 | 2730 | 900 | 0 | media | 0 | KOMPASTV | Pidato Prabowo di Harlah PKB |
| 2026-07-29 | 1616 | 604 | 0 | full_media | 0 | METRO TV | [FULL] Pidato Presiden Prabowo di Pelantikan Pamong Praja  |
| 2026-07-30 | 2412 | 834 | 1 | full_media | 0 | KOMPASTV | [FULL] Pidato Prabowo di Akad Rumah Subsidi: Singgung Pres |
| 2026-07-30 | 1414 | 601 | 0 | full_media | 0 | METRO TV | [FULL] BREAKING NEWS - PIDATO PRESIDEN PRABOWO SAAT RESMIK |
| 2026-08-06 | 1185 | 448 | 0 | full_media | 0 | KOMPASTV | [FULL] Pidato Prabowo Depan 150 Peneliti BRIN Soroti Pendi |
| 2026-08-07 | 2315 | 818 | 0 | full_media | 0 | KOMPASTV | FULL! Pidato Prabowo di Peluncuran Buku Bahlil: Swasembada |
| 2026-08-14 | 11989 | 2631 | 3 | full_media | 7 | KOMPASTV | [FULL] Pidato Presiden Prabowo-Puan Maharani soal RAPBN 20 |
| 2026-08-14 | 7750 | 1884 | 2 | full_media | 5 | Official iNews | [FULL] Pidato Presiden Prabowo di Sidang Tahunan MPR RI 20 |
| 2026-08-25 | 1388 | 576 | 0 | full_media | 0 | METRO TV | [FULL] PIDATO PRABOWO RESMIKAN PLTS DI BALI: BERI BINTANG  |
| 2026-08-27 | 1697 | 675 | 1 | full_media | 3 | KOMPASTV | [FULL] Pidato Presiden Prabowo Hadiri Muktamar ke-35 NU: S |
| 2026-08-31 | 1595 | 645 | 2 | full_media | 0 | METRO TV | [FULL] PIDATO PRESIDEN PRABOWO DI PENUTUPAN MUKTAMAR KE-35 |
| 2026-09-09 | 1123 | 439 | 0 | full_media | 0 | SUARANTBcom | [FULL] Pidato Presiden Prabowo Lepas Kontingen Indonesia M |
| 2026-09-09 | 3238 | 973 | 0 | full_media | 1 | KOMPASTV MADIUN | Pidato Lengkap Presiden Prabowo di HUT ke 25 Partai Demokr |

Machine-readable versions: `data/expanded/events.csv` (this table),
`data/expanded/word-frequency.csv` (all 9.007 aggregate surface forms),
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
- `data/expanded/analysis.json` — totals, word index, per-event counts, MBG evidence
- `data/expanded/word-frequency.csv` — aggregate surface forms
- `data/expanded/word-frequency-by-event.csv` — per-event counts
- `data/expanded/events.csv` — one row per canonical event with MBG columns
- `data/expanded/source-catalog.json` — canonical events and duplicate groups
- `data/expanded/candidate-seeds.json` — the discovery/selection list driving fetching
- `data/expanded/metadata.json` — upload dates, durations, channels
- `data/expanded/pending.json` — candidates not fetched yet, with the per-item reason
- `data/expanded/raw/*.json` — local-only caption snippets; ignored by Git
- `scripts/collect_expanded.py` — fetch the candidate set
- `scripts/list_pending.py` — report missing candidates and why
- `scripts/analyze_expanded.py` — dedupe events, count words, derive topics/framing/MBG
- `scripts/export_expanded.py` — write CSVs
- `scripts/build_ui_expanded.py` — rebuild the embedded dashboard

## Rebuild

```bash
.venv/bin/python scripts/collect_expanded.py
.venv/bin/python scripts/analyze_expanded.py
.venv/bin/python scripts/export_expanded.py
.venv/bin/python scripts/build_ui_expanded.py
```

Fetching is the only networked step. YouTube rate-limits it: after 74 videos in
about five minutes the caption endpoint began returning HTTP 429, which the library reports
as `IpBlocked`. `collect_expanded.py` records each failure instead of dropping it silently.

## Public-data and license note

The repository code is MIT-licensed. The YouTube videos and caption tracks are third-party
source material; nothing here grants rights to redistribute their audiovisual or caption
content. This repository publishes source links and derived counts while keeping raw caption
text out of the public tree.
