# youtube-speech-corpus

Build a searchable word, topic, and framing index from any corpus of spoken YouTube
content — speeches, hearings, lectures, interviews — using the caption tracks YouTube
already provides. No transcription model, no API key, no cloud service.

A **profile** describes one corpus: what to search for, how to tell the material you
want from the clips and commentary around it, how to recognise the same event uploaded
several times, which policy signal to track, and which lexical categories count as
topics. Point the pipeline at a new profile and the whole toolchain follows.

`profiles/prabowo.json` ships as a worked example: Indonesian speeches by Prabowo
Subianto, 67 events, 153,699 tokens, 2024-08 to 2026-09. See `RESEARCH-PACK.md` for its
numbers. The code never hardcodes that speaker, language, or topic.

## Quickstart

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

```bash
cd scripts
../.venv/bin/python discover.py     --profile prabowo   # queries  -> candidate seeds
../.venv/bin/python collect.py      --profile prabowo   # seeds    -> caption tracks
../.venv/bin/python fetch_metadata.py --profile prabowo # upload dates, channels, durations
../.venv/bin/python analyze.py      --profile prabowo   # dedupe + counts + signals
../.venv/bin/python export.py       --profile prabowo   # CSV exports
../.venv/bin/python build_ui.py     --profile prabowo   # single-file dashboard
../.venv/bin/python report.py       --profile prabowo   # readable research pack
```

Step 1–3 are the only networked steps. Everything after runs offline from the fetched
files. Open `index.html` (or serve the directory with `python3 -m http.server 8765`) for
the dashboard.

## Writing a profile

`profiles/<name>.json` is the whole configuration. Every key the pipeline reads:

```jsonc
{
  "name": "prabowo",
  "display_name": "prabowo.speeches",        // dashboard title
  "description": "…",                        // one line, shown in the report
  "language_code": "id",                     // caption track to prefer

  "discovery": {
    "queries":       [{"label": "official_channel", "target": "https://www.youtube.com/@…/videos", "kind": "channel"},
                      {"label": "search_a", "target": "ytsearch100:…", "kind": "search"}],
    "extra_searches": [],                    // lower-priority sweeps
    "max_per_query": 100,
    "max_seeds": 200
  },

  "title_filters": {
    "speech_required": "…",                  // regex: title looks like the material you want
    "speaker_required": "…",                 // regex: the right person/topic is named
    "exclude_other_speakers": "…",           // someone else speaking
    "exclude_commentary": "…",               // commentary, compilations, excerpts, news about it
    "exclude_arrival": "…",                  // arrivals, departures, welcomes
    "arrival_exempt": "…"                    // …unless the title also promises a speech
  },

  "source_tiers": {
    "official_channel_exact":    ["…"],      // channel IS the speaker's own account
    "official_channel_or_title": ["…"],      // official media office, anywhere in channel+title
    "full_media_title_re": "…"               // full-length media upload
  },

  "dedup":    {"shingle_size": 4, "same_day_containment": 0.22, "cross_day_containment": 0.58},
  "canonical": {
    "opening_re": "…",                       // how a speech opens
    "padded_opening_fraction": 0.02,         // skip captures whose opening starts this late
    "complete_opening_fraction": 0.01,
    "score_title_bonus_re": "…", "score_live_penalty_re": "…"
  },

  "policy_signals": {                        // the one signal worth tracking explicitly
    "label": "MBG", "label_slug": "mbg",
    "exact_token": "mbg", "full_phrase_re": "…",
    "paired_terms": ["makan", "bergizi"], "context_token": "sppg",
    "context_terms": ["gizi", "bergizi", "makan", "anak"], "ambiguous_re": "…"
  },

  "topics": {"category": ["term", "…"]},     // overlapping lexical categories
  "topic_order": ["…"],
  "pronouns": ["saya", "kita", "kami", "mereka"],   // framing words
  "stopwords": ["…"],                        // hidden by the dashboard's "hide common words"
  "speech_windows": {"VIDEO_ID": [start, end]}      // hand-checked trims, optional
}
```

## How a corpus is built

```text
discover   profile queries            ->  unique uploads
score      title filters + speaker    ->  candidates
seed       priority order             ->  the work list
collect    caption tracks             ->  raw snippets per upload
metadata   upload date/channel/title  ->  no transcript needed
analyze    dedupe by event            ->  one canonical upload per speech event
export     CSV + JSON                 ->  word index, per-event counts, signals
```

**One event, one row.** The same speech gets re-uploaded by many channels. Uploads are
clustered by 4-token shingle containment — same-day uploads merge at 0.22, cross-day at
0.58 — and one canonical upload represents each cluster. Without this, a speech uploaded
seven times counts seven times and long speeches dominate every frequency count.

**Canonical choice.** Official channel first, then title cues (`full`, `lengkap`,
`pidato`), then length. A livestream capture is skipped when another upload of the same
event opens at the top: the picker measures where the speech opening formula first
appears as a fraction of the transcript, and a capture that starts too late is treated as
padding. Measured on one cluster, the padded capture reached its opening at token 2,058
of 30,742 (6.7%) while the five genuine uploads opened at token 0–11.

**What counts as the material.** Media channels paste clickbait adjectives onto genuine
speeches, so filtering on those words deletes real speeches. The profile instead carries
a curated exclusion list — other speakers, arrivals, commentary formats, compilations,
short excerpts, and news *about* the speaker rather than the speaker talking.

## Two capture routes, verified identical

The caption endpoint (`/api/timedtext`) rate-limits a busy IP with HTTP 429. The
transcript panel in the YouTube web UI reads a **different** endpoint (`youtubei
get_panel`) that is not throttled, so a rate-limited corpus can still be completed:

- `scripts/collect.py` — the caption API. Fast, scriptable, part of the CLI pipeline.
- transcript panel + `scripts/import_panel.py` — needs a browser session, covers whatever
  the API refuses.

The text is the same. Cross-checked on one video: the API returned 628 snippets and the
panel 255 segments, both **15,621 characters and 2,362 words**, normalized ratio 1.000,
identical opening and closing text. Every manifest entry records which route it used in
`fetch_method`.

## Rate limiting, measured

`IpBlocked` is the library's name for HTTP 429 on the caption endpoint. Observed on one
IP: 74 videos fetched in 5 minutes before the first 429; the block was still active after
53 minutes and had cleared 23h40m later; a second session at **half** the request rate was
cut off after only 10 videos. Slowing down did not help — the allowance looks cumulative,
not per-window. One blocked probe costs a single video, i.e. two HTTP requests.

`scripts/collect.py --only-pending --stop-on-block` exits at the first 429 instead of
grinding through cooldowns, and `scripts/auto_resume.sh` wraps that in an exponential
backoff (1h → 2h → 4h, capped) so a schedule probes for the window instead of guessing it.
See `data/prabowo/ratelimit-observations.json` for the raw measurements.

## Outputs

For a profile named `<name>`, into `data/<name>/`:

| file | contents |
|---|---|
| `analysis.json` | source of truth: totals, word index, per-event counts, signal evidence |
| `word-frequency.csv` | every surface form with count, rate, and event coverage |
| `word-frequency-by-event.csv` | per-event word counts |
| `events.csv` | one row per canonical event with signal columns |
| `source-catalog.json` | canonical events and their duplicate groups |
| `candidate-seeds.json` | the discovery output that drives fetching |
| `metadata.json` | upload dates, channels, titles, durations |
| `pending.json` | candidates with no transcript yet, and why |
| `ratelimit-observations.json` | measured 429 behaviour on this machine |
| `raw/` | caption snippets — **not published** |

Plus `index.html` (dashboard), `RESEARCH-PACK.md` (readable summary), and
`data/<name>/auto-resume-log.jsonl` when the scheduled resume is used.

Raw caption text stays out of the repository: YouTube captions are third-party material.
The repo publishes source links and derived counts.

## Caveats that apply to any corpus built this way

- Captions are auto-generated by YouTube, not verified audio. Names, numbers, acronyms,
  and repeated phrases are the usual failure points.
- Frequency is surface-form. Casefolding merges `MBG`/`mbg`; it does not merge `asing` and
  `masing-masing`.
- Topic categories are lexical proxies, not classification. A term listed under one topic
  counts every time it appears, whatever the surrounding context.
- A corpus assembled from search is **not a random sample** of anything. Whatever the
  search surfaces easiest — long speeches, big events — is over-represented.
- Long material concentrates token mass. Report rates per 1,000 tokens and event coverage
  alongside raw counts.

## License

MIT for the code. The videos and caption tracks are third-party source material; nothing
here grants rights to redistribute their audiovisual or caption content.
