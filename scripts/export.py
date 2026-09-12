#!/usr/bin/env python3
"""Write the CSV exports for one corpus profile."""

from __future__ import annotations

import argparse
import csv
import json

from corpus import Corpus, add_profile_argument, load_profile


def main() -> None:
    parser = argparse.ArgumentParser(description="Export CSVs for one corpus profile.")
    add_profile_argument(parser)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    corpus = Corpus(profile)
    if not corpus.analysis.exists():
        raise SystemExit(f"no analysis at {corpus.analysis}; run scripts/analyze.py first")

    data = json.loads(corpus.analysis.read_text(encoding="utf-8"))
    totals = data["totals"]
    total_tokens = totals["total_tokens"]
    label = profile["policy_signals"]["label"]

    with corpus.word_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["word", "count", "per_1000_tokens", "event_count"])
        for word, count, event_count in data["word_index"]:
            writer.writerow([
                word,
                count,
                round(count / total_tokens * 1000, 4) if total_tokens else 0,
                event_count,
            ])

    with corpus.word_by_event_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["event_group", "date", "title", "channel", "word", "count"])
        for source in data["sources"]:
            for word, count in source["counts"].items():
                writer.writerow([
                    source["duplicate_group"], source["date"],
                    source["title"], source["channel"], word, count,
                ])

    with corpus.events_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([
            "event_group", "date", "title", "channel", "url", "token_count",
            "duplicate_count", "source_tier", "fetch_method",
            f"{label}_exact", f"{label}_full_phrase", f"{label}_signals", f"{label}_ambiguous",
        ])
        for source in data["sources"]:
            signals = source["policy_signals"]
            writer.writerow([
                source["duplicate_group"], source["date"], source["title"],
                source["channel"], source["url"], source["token_count"],
                source["duplicate_count"], source["source_tier"],
                source.get("fetch_method", ""),
                signals["exact_token_count"], signals["full_phrase_count"],
                signals["policy_signal_count"], signals["ambiguous_count"],
            ])

    print(f"aggregate_rows={len(data['word_index'])}")
    print(f"event_rows={len(data['sources'])}")
    print(f"variant_rows={len(data['variants'])}")
    print(f"tokens={total_tokens}")


if __name__ == "__main__":
    main()
