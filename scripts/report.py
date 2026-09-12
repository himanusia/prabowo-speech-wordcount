#!/usr/bin/env python3
"""Generate the readable research pack for one corpus profile.

Everything is derived from analysis.json, so the report can never drift from the
data it describes.
"""

from __future__ import annotations

import argparse
from collections import Counter

from corpus import REPO_ROOT, Corpus, add_profile_argument, load_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the research pack for one profile.")
    add_profile_argument(parser)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    corpus = Corpus(profile)
    data = corpus.read_json(corpus.analysis, None)
    if data is None:
        raise SystemExit(f"no analysis at {corpus.analysis}; run scripts/analyze.py first")

    totals = data["totals"]
    sources = data["sources"]
    events = totals["unique_speech_events"]
    tokens = totals["total_tokens"]
    words = totals["unique_words"]
    framing = {row["word"]: row for row in totals["framing"]}
    topics = {row["topic"]: row for row in totals["topics"]}

    def group(n: int) -> str:
        return f"{n:,}".replace(",", ".")

    dates = sorted(source["date"] for source in sources)
    token_counts = sorted((source["token_count"] for source in sources), reverse=True)
    top5 = sum(token_counts[:5])
    signal = profile["policy_signals"]
    slug = signal.get("label_slug", signal["label"].casefold())
    label = signal["label"]
    signal_rows = [
        source for source in sources
        if source["policy_signals"]["policy_signal_count"] or source["policy_signals"]["ambiguous_count"]
    ]
    signal_total = sum(source["policy_signals"]["policy_signal_count"] for source in sources)
    signal_exact = sum(source["policy_signals"]["exact_token_count"] for source in sources)
    months = "\n".join(
        f"{month}  {count:>2}"
        for month, count in sorted(Counter(s["date"][:7] for s in sources).items())
    )
    topic_order = [slug, *profile["topic_order"]]
    topic_rows = "\n".join(
        f"{name:<24} {topics[name]['per_1000_tokens']:>6.2f}   {topics[name]['speech_count']:>2}/{events}"
        for name in topic_order if name in topics
    )
    top_words = "\n".join(
        f'{row["word"]:<18} {row["count"]:>5}  {row["per_1000"]:>6.2f}/1k  {row["speech_count"]:>2}/{events}'
        for row in totals["top_content_words"][:20]
    )
    fetch_total = (
        totals["fetch_ok"] + totals["fetch_transcripts_disabled"]
        + totals["fetch_no_indonesian_track"] + totals["fetch_ip_blocked"]
        + totals["fetch_never_attempted"]
    )
    tiers = ", ".join(f"{k} {v}" for k, v in Counter(s["source_tier"] for s in sources).most_common())
    framing_rows = "\n".join(
        f"{w:<8} {framing[w]['count']:>6}  {framing[w]['per_1000_tokens']:>6.2f}/1k  "
        f"{framing[w]['speech_count']:>2}/{events} event"
        for w in profile["pronouns"] if w in framing
    )
    official_events = sum(1 for s in sources if s["source_tier"] == "official")
    methods = "\n".join(
        f"{name:<18} {count:>4} unggahan"
        for name, count in Counter(s.get("fetch_method", "caption_api") for s in data["variants"]).most_common()
    )

    report = f"""# Research pack — {profile.get('display_name', profile['name'])}

{profile.get('description', '')}

Setiap angka di bawah berasal dari `{corpus.analysis.relative_to(REPO_ROOT)}`; tidak ada
teks caption mentah yang disertakan.

```text
event (unik)             {events}
unggahan                 {totals['eligible_caption_items']}
token                    {group(tokens)}
kata unik (surface form) {group(words)}
rentang                  {dates[0]} → {dates[-1]}
```

Tier sumber: {tiers}

## Sebaran per bulan

```text
{months}
```

## Distribusi token per pidato

```text
terpanjang   {token_counts[0]:>6}
median       {token_counts[len(token_counts) // 2]:>6}
terpendek    {token_counts[-1]:>6}
5 teratas    {top5:>6}  ({100 * top5 / tokens:.1f}% dari seluruh token)
```

## Kata isi teratas (fungsi kata dan pronomina dibuang)

```text
{top_words}
```

## Sinyal topik (leksikal, per 1.000 token)

```text
{topic_rows}
```

Kategori boleh tumpang tindih dan ini proksi leksikal, bukan klasifikasi.

## Framing pronomina

```text
{framing_rows}
```

## {label}

```text
{label} eksak (token)         {signal_exact}
sinyal kebijakan total    {signal_total}
pidato memuat {label}         {len(signal_rows)} dari {events} ({100 * len(signal_rows) / events:.0f}%)
```

Aturan sinyal: {label} eksak, frasa penuh, pasangan
{" + ".join(signal["paired_terms"])}, atau konteks {signal["context_token"]}. Kasus ambigu
dihitung terpisah dan dikurangi dari total, jadi angka eksak itu lantai.

## Cara transkrip diambil

```text
{methods}
```

Sebagian lewat caption API (`/api/timedtext`), sisanya lewat panel transcript YouTube
(endpoint `youtubei get_panel`) ketika API-nya kena rate limit. Kedua jalur sudah
diverifikasi menghasilkan teks identik, jadi pilihan jalur tidak memengaruhi hitungan kata.
Setiap entri di manifest punya penanda `fetch_method`.

Satu unggahan hanya diambil lewat satu jalur. Status pengambilan dari {fetch_total} kandidat:

```text
berhasil                 {totals['fetch_ok']}
tanpa track yang diminta {totals['fetch_no_indonesian_track']}
subtitle dimatikan       {totals['fetch_transcripts_disabled']}
kena rate limit          {totals['fetch_ip_blocked']}
belum dicoba             {totals['fetch_never_attempted']}
```

## Batasan yang wajib dibaca sebelum mengutip angka

1. Semua caption auto-generated, bukan ground truth audio. Nama, angka, dan akronim adalah
   titik gagal paling sering.
2. Pemotongan jendela pidato hanya diterapkan pada unggahan yang dicek manual. Sisanya
   memakai track penuh, jadi beberapa event masih membawa MC, musik, atau penutup.
3. Hitungan adalah surface form: `mbg` dan `MBG` sama setelah casefold, tapi `asing` dan
   `masing-masing` berbeda token.
4. {events} event ini bukan sampel acak. Materi panjang di acara besar lebih mudah muncul di
   pencarian, jadi komposisinya bias ke acara besar.
5. Hanya {official_events} dari {events} event memakai kanal resmi; sisanya kanal media, jadi judul dan durasi
   ikut apa yang diunggah kanal tersebut.

## Berkas data

- `analysis.json` — sumber kebenaran
- `word-frequency.csv` — {group(words)} surface form agregat
- `word-frequency-by-event.csv` — hitungan per pidato
- `events.csv` — satu baris per pidato dengan kolom sinyal
- `README.md` — metodologi dan cara rebuild
"""
    corpus.report.write_text(report, encoding="utf-8")
    print(f"wrote {corpus.report} ({len(report)} bytes)")


if __name__ == "__main__":
    main()
