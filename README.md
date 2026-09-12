# Prabowo speech corpus index

Local-first word-frequency, topic, and framing index built from Indonesian YouTube caption
tracks. The corpus is deduplicated by speech event and restricted to actual speeches: one
canonical source per event, so a speech reuploaded by seven channels is counted once, and
commentary shows, laugh compilations, and short excerpts are excluded.

Read `RESEARCH-PACK.md` for a single-file readable summary of every number below.

## Open the UI

Open `index.html` directly, or serve this directory:

```bash
python3 -m http.server 8765
```

The dashboard is self-contained; `data/expanded/analysis.json` is embedded into the HTML
at build time.

## Current corpus

```text
speech events        46    (unique, deduplicated)
caption uploads      80    (eligible items, duplicates folded in)
tokens         109.197
unique words    9.247
date range     2025-02-10 -> 2026-09-09
```

Fetch outcomes across all 160 selected candidates:

```text
caption retrieved                84
HTTP 429, reported as IpBlocked  30
subtitles genuinely disabled     3
no Indonesian caption track      14
not attempted yet                29
```

The 429 limit is measured rather than guessed; see
`data/expanded/ratelimit-observations.json`. The first block cleared after roughly 24 hours.
A second session at half the request rate was cut off after only 10 videos, so the allowance
looks cumulative rather than per-window.

Events by number of folded reuploads: 1 dup -> 7 events, 2 dup -> 10 events, 3 dup -> 1 events, 4 dup -> 1 events.

Multi-upload events:

- 2026-06-10 — [FULL] PIDATO PRESIDEN PRABOWO DI MUNAS HIPMI, SINGGUNG  — 5 uploads
- 2026-08-14 — [FULL] Pidato Presiden Prabowo-Puan Maharani soal RAPBN  — 4 uploads
- 2026-05-01 — Pidato Presiden Prabowo pada Peringatan Hari Buruh Inter — 3 uploads
- 2026-05-20 — Presiden Prabowo Sampaikan Pidato pada Rapat Paripurna D — 3 uploads
- 2026-06-23 — Pidato Lengkap Presiden Prabowo Subianto di Musyawarah U — 3 uploads
- 2026-06-24 — [FULL] Pidato Prabowo di PNKT XVII 2026: Australia Minta — 3 uploads
- 2026-07-01 — FULL! Pidato Prabowo di HUT ke-80 Bhayangkara: Hukum Tak — 3 uploads
- 2026-07-09 — [FULL] Pidato Prabowo Luncurkan Biodiesel B50: Indonesia — 3 uploads
- 2026-07-10 — Full Pidato Presiden Prabowo di Lombok, MBG KITA LANJUTK — 3 uploads
- 2026-07-30 — [FULL] Pidato Prabowo di Akad Rumah Subsidi: Singgung Pr — 3 uploads

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

### What counts as a speech

Media channels add clickbait adjectives ("Berapi-api!", "Bahas ...") to genuine full speeches,
so keyword filtering on those words discards real speeches. Instead two curated lists decide:

- rejected: statements by other people, arrival/departure clips, and commentary or
  compilation formats (`ada apa dengan`, `bikin tertawa`, `ngakak sampai`,
  `gemparkan satu ruangan`, `keceplosan saat pidato`, `saat prabowo bicara`,
  `ketika prabowo bertanya`) - each pattern came from a manual pass over every fetched title
- required: the title must describe a speech or remarks by Prabowo

## Selection pipeline

```text
discovery     4 yt-dlp queries -> 566 unique uploads
scoring       319 candidates passed the title parser -> 160 seeds
fetching      160 attempts logged -> 84 caption tracks retrieved
loading       90 items in the corpus input
eligibility   10 excluded as non-speech or clip/commentary
dedup         34 duplicate uploads folded in
canonical     46 speech events
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
- The corpus is not exhaustive: 30 candidates were rejected with HTTP 429 and
  29 were never attempted. The largest gap is 2024-10 to 2025-12.
- Per-event token counts range from 68 to 11,989. The five longest events supply
  33.9% of all tokens, so aggregate frequency partly reflects those five
  speeches rather than the whole period.
- The 46 events are not a random sample. Long speeches at large events are likelier to surface
  in search, so the mix is biased toward state occasions and large mass organisations.

## Headline numbers

Topic signals per 1,000 tokens and event coverage:

```text
mbg                        0.72   17/46
pangan                     4.10   33/46
ekonomi                    5.91   41/46
pendidikan                 2.60   33/46
kesehatan_dan_gizi         3.94   41/46
tata_kelola                3.67   39/46
pertahanan_dan_keamanan    3.83   37/46
nasional_dan_identitas    32.54   46/46
```

Top content words after removing function words and pronouns:

```text
indonesia         1152  events=45
rakyat             808  events=42
harus              724  events=43
negara             593  events=42
tahun              586  events=42
bangsa             585  events=45
enggak             456  events=31
ketua              387  events=32
menteri            371  events=38
presiden           356  events=43
apa                296  events=31
mau                294  events=34
seluruh            284  events=43
republik           272  events=40
hadir              270  events=40
```

Framing pronouns per 1,000 tokens:

```text
kita     38.16  (4.167 occurrences, 46/46 events)
saya     24.99  (2.729 occurrences, 45/46 events)
mereka    2.87
kami      1.62
```

`kita` leads `saya` across the full corpus. On the original ten-video sample the two were
nearly tied, so the smaller sample was misleading.

MBG: 18 of 46 events carry an MBG signal, 54 exact
`MBG` occurrences, 79 policy signals total.

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
| 2026-05-01 | 2044 | 691 | 2 | official | 5 | Prabowo Subianto | Pidato Presiden Prabowo pada Peringatan Hari Buruh Interna |
| 2026-05-13 | 2769 | 916 | 0 | full_media | 0 | METRO TV | BREAKING NEWS - [FULL] PIDATO PRESIDEN PRABOWO DI PENYERAH |
| 2026-05-16 | 3552 | 1104 | 0 | full_media | 9 | METRO TV | [FULL] BREAKING NEWS - PIDATO PRESIDEN PRABOWO DI PERESMIA |
| 2026-05-20 | 68 | 47 | 2 | official | 0 | Sekretariat Presiden | Presiden Prabowo Sampaikan Pidato pada Rapat Paripurna DPR |
| 2026-05-29 | 661 | 261 | 0 | full_media | 0 | Liputan6 | [FULL] Pidato Presiden Prabowo: Pujian untuk Macron Hingga |
| 2026-05-31 | 352 | 206 | 0 | official | 0 | Sekretariat Presiden | Sambutan Presiden Prabowo pada Puncak Peringatan Hari Tri  |
| 2026-06-01 | 1520 | 605 | 1 | full_media | 1 | CNN Indonesia | FULL Pidato Prabowo di Upacara Hari Lahir Pancasila |
| 2026-06-03 | 2386 | 730 | 1 | official | 3 | Sekretariat Presiden | Pidato Presiden RI pada Acara Building Indonesia's Future  |
| 2026-06-10 | 4297 | 1246 | 4 | full_media | 0 | METRO TV | [FULL] PIDATO PRESIDEN PRABOWO DI MUNAS HIPMI, SINGGUNG KR |
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
| 2026-07-30 | 2412 | 834 | 2 | full_media | 0 | KOMPASTV | [FULL] Pidato Prabowo di Akad Rumah Subsidi: Singgung Pres |
| 2026-07-30 | 1414 | 601 | 0 | full_media | 0 | METRO TV | [FULL] BREAKING NEWS - PIDATO PRESIDEN PRABOWO SAAT RESMIK |
| 2026-07-31 | 2501 | 913 | 0 | media | 1 | tvOneNews | [Breaking News] Pidato Presiden Prabowo di Pertemuan denga |
| 2026-08-06 | 1185 | 448 | 0 | full_media | 0 | KOMPASTV | [FULL] Pidato Prabowo Depan 150 Peneliti BRIN Soroti Pendi |
| 2026-08-07 | 2315 | 818 | 0 | full_media | 0 | KOMPASTV | FULL! Pidato Prabowo di Peluncuran Buku Bahlil: Swasembada |
| 2026-08-14 | 11989 | 2631 | 3 | full_media | 7 | KOMPASTV | [FULL] Pidato Presiden Prabowo-Puan Maharani soal RAPBN 20 |
| 2026-08-14 | 7750 | 1884 | 2 | full_media | 5 | Official iNews | [FULL] Pidato Presiden Prabowo di Sidang Tahunan MPR RI 20 |
| 2026-08-25 | 1388 | 576 | 0 | full_media | 0 | METRO TV | [FULL] PIDATO PRABOWO RESMIKAN PLTS DI BALI: BERI BINTANG  |
| 2026-08-27 | 1697 | 675 | 1 | full_media | 3 | KOMPASTV | [FULL] Pidato Presiden Prabowo Hadiri Muktamar ke-35 NU: S |
| 2026-08-31 | 1595 | 645 | 2 | full_media | 0 | METRO TV | [FULL] PIDATO PRESIDEN PRABOWO DI PENUTUPAN MUKTAMAR KE-35 |
| 2026-09-09 | 3238 | 973 | 1 | full_media | 1 | KOMPASTV MADIUN | Pidato Lengkap Presiden Prabowo di HUT ke 25 Partai Demokr |
| 2026-09-09 | 1573 | 632 | 1 | media | 0 | Pangkep TV | [FUUL] Sambutan Presiden Prabowo Lepas Kontingen Indonesia |

Machine-readable versions: `data/expanded/events.csv` (this table),
`data/expanded/word-frequency.csv` (all 9.247 aggregate surface forms),
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
- `data/expanded/pending.json` — candidates not fetched yet, with the per-item reason
- `data/expanded/ratelimit-observations.json` — measured 429 behaviour and recovery time
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

Fetching is the only networked step and it is rate limited. Resume the missing candidates
without grinding through the limit:

```bash
.venv/bin/python scripts/collect_expanded.py --only-pending --stop-on-block --sleep 8
```

`--stop-on-block` exits at the first 429 instead of cooling down and burning the allowance.

## Public-data and license note

The repository code is MIT-licensed. The YouTube videos and caption tracks are third-party
source material; nothing here grants rights to redistribute their audiovisual or caption
content. This repository publishes source links and derived counts while keeping raw caption
text out of the public tree.
