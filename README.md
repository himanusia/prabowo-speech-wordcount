# Prabowo speech corpus index

Local-first word-frequency, topic, and framing index built from Indonesian YouTube
caption tracks. The corpus is deduplicated by speech event: one canonical source per
event, so a speech reuploaded by six channels is counted once.

## Open the UI

Open `index.html` directly, or serve this directory:

```bash
python3 -m http.server 8765
```

The dashboard is self-contained; the current `data/expanded/analysis.json` is embedded
into the HTML at build time.

## Current corpus

```text
speech events        44   (unique, deduplicated)
caption uploads      75   (eligible items fetched, duplicates removed)
tokens          105,507
unique words      8,969
date range   2025-02 → 2026-09
```

Every track used is the Indonesian (`id`) auto-generated caption track.

Dedup matters here: the 2026-08-14 MPR annual session was uploaded by seven channels,
and the June 2026 HIPMI congress by four. Without dedup the long speeches would dominate
every count.

The canonical catalog is `data/expanded/source-catalog.json`, the machine-readable
per-event table is `data/expanded/events.csv`, and the raw list of fetched uploads
(including duplicates) is `data/expanded/variants` in `analysis.json`.

Raw caption text is intentionally local-only: it is fetched into
`data/transcripts/raw/` and `data/expanded/raw/`, both ignored by Git, so the public
repository redistributes source links and derived counts rather than caption text.

## Method

- [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api), pinned to upstream commit `8f150ba8836da30a36bcd40e8fca226ed179ba72`
- Indonesian (`id`) caption track, manual preferred over auto-generated
- Bracketed caption events such as `[musik]` and `[tepuk tangan]` removed
- Unicode NFC + casefold + Unicode-aware tokenization
- No de-duplication of repeated words; every spoken occurrence counts
- Event dedup via 4-token shingle containment between uploads (same day: 0.22, cross-day: 0.58)
- One canonical source per event, preferring official channels, then longer transcripts
- Topic layer is curated lexical signals with overlapping categories allowed
- MBG signal counts exact `MBG`, the full `makan bergizi gratis` phrase, `makan` + `bergizi`
  in one caption, and SPPG context; ambiguous acronym hits are reported separately

Ordering caveats worth knowing before quoting a number:

- All counts are surface forms. `mbg` and `MBG` are the same token after casefolding, but
  `asing` and `masing-masing` are different tokens.
- Caption tracks are not verified audio ground truth. Names, numbers, acronyms, and
  repeated phrases are the usual failure points.
- Speech windows were applied only to ten hand-checked uploads where the recording includes
  MC, music, or closing material. The remaining events use the full caption track, so a few
  of them still include non-speech material.
- Topic categories are lexical proxies, not classifications. `anak` counts toward
  `kesehatan_dan_gizi` in every context, including ones unrelated to the nutrition program.

## Headline numbers

Top content words, after removing function words and pronouns:

```text
indonesia   1112      rakyat 803      harus 710
tahun        573      negara 572      bangsa 567
```

Topic signals per 1,000 tokens and event coverage:

```text
nasional_dan_identitas      32.78   44/44 events
ekonomi                      5.90   39/44
pangan                       4.17   32/44
kesehatan_dan_gizi           4.03   39/44
pertahanan_dan_keamanan      3.72   35/44
tata_kelola                  3.66   37/44
pendidikan                   2.69   33/44
mbg                          0.74   16/44
```

MBG appears in 16 of 44 events, with 54 exact `MBG` occurrences and 78 policy signals in
total. Its density rises from early 2026 onward.

Framing pronouns per 1,000 tokens:

```text
kita    38.59  (4,071 occurrences, 44/44 events)
saya    25.33  (2,673 occurrences, 43/44 events)
mereka   2.91
kami     1.65
```

`kita` leads `saya` across the full corpus. On the original ten-video sample the two were
nearly tied, so the smaller sample was misleading.

## Setup and reproducibility

Use Python 3.12+ and install the pinned dependencies:

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

Fetching needs network access to YouTube and writes the ignored raw caption files. The
analysis, export, and build steps run offline from those files.

## Outputs

- `index.html` — terminal-style interactive dashboard
- `data/expanded/analysis.json` — embedded UI data: totals, word index, per-event counts, MBG evidence
- `data/expanded/word-frequency.csv` — all 8,969 aggregate surface forms
- `data/expanded/word-frequency-by-event.csv` — per-event counts
- `data/expanded/events.csv` — one row per canonical event with MBG columns
- `data/expanded/source-catalog.json` — public catalog of canonical events and duplicate groups
- `data/expanded/candidate-seeds.json` — the discovery/selection list that drives fetching
- `data/expanded/metadata.json` — upload dates, durations, channels for the candidate set
- `data/expanded/pending.json` — candidates that are not fetched yet, with the per-item reason
- `data/expanded/raw/*.json` — local-only caption snippets; ignored by Git
- `data/transcripts/raw/*.json` — local-only caption snippets for the hand-windowed uploads
- `scripts/fetch_sources.py` — fetch the ten hand-windowed uploads
- `scripts/collect_expanded.py` — fetch the expanded candidate set
- `scripts/list_pending.py` — report which candidates are still missing and why
- `scripts/analyze_expanded.py` — deduplicate events, count words, derive topics, framing, and MBG signals
- `scripts/export_expanded.py` — write CSVs
- `scripts/build_ui_expanded.py` — rebuild the embedded dashboard

## Rebuild

```bash
.venv/bin/python scripts/fetch_sources.py
.venv/bin/python scripts/collect_expanded.py
.venv/bin/python scripts/analyze_expanded.py
.venv/bin/python scripts/export_expanded.py
.venv/bin/python scripts/build_ui_expanded.py
```

Reruns overwrite the derived JSON, CSV, and HTML outputs. Fetching is the only networked
step and is rate-limited by YouTube; `collect_expanded.py` skips uploads already fetched and
records `ip_blocked`, `transcripts_disabled`, or `no_indonesian_track` per item instead of
silently dropping them. On this run 31 of the remaining candidates were rejected with
`IpBlocked`, so the corpus is not yet exhaustive for 2024-10 to 2025-12.

## Public-data and license note

The repository code is MIT-licensed. The YouTube videos and caption tracks are third-party
source material; nothing here grants rights to redistribute their audiovisual or caption
content. This repository publishes source links and derived counts while keeping raw caption
text out of the public tree. Check the rights and platform terms before republishing excerpts
or monetizing a video.
