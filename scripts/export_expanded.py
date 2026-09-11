from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "expanded" / "analysis.json"
OUT_DIR = ROOT / "data" / "expanded"


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    totals = data["totals"]
    total_tokens = totals["total_tokens"]

    with (OUT_DIR / "word-frequency.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["word", "count", "per_1000_tokens", "event_count"])
        for word, count, event_count in data["word_index"]:
            writer.writerow([
                word,
                count,
                round(count / total_tokens * 1000, 4) if total_tokens else 0,
                event_count,
            ])

    with (OUT_DIR / "word-frequency-by-event.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["event_group", "date", "title", "channel", "word", "count"])
        for source in data["sources"]:
            for word, count in source["counts"].items():
                writer.writerow([
                    source["duplicate_group"],
                    source["date"],
                    source["title"],
                    source["channel"],
                    word,
                    count,
                ])

    with (OUT_DIR / "events.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow([
            "event_group", "date", "title", "channel", "url", "token_count",
            "duplicate_count", "mbg_exact", "mbg_full_phrase", "mbg_signals",
            "mbg_ambiguous",
        ])
        for source in data["sources"]:
            writer.writerow([
                source["duplicate_group"],
                source["date"],
                source["title"],
                source["channel"],
                source["url"],
                source["token_count"],
                source["duplicate_count"],
                source["mbg"]["mbg_exact_count"],
                source["mbg"]["mbg_full_phrase_count"],
                source["mbg"]["mbg_policy_signal_count"],
                source["mbg"]["mbg_ambiguous_count"],
            ])

    print(f"aggregate_rows={len(data['word_index'])}")
    print(f"event_rows={len(data['sources'])}")
    print(f"variant_rows={len(data['variants'])}")
    print(f"tokens={total_tokens}")


if __name__ == "__main__":
    main()
