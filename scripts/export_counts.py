from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "analysis.json"
OUT_DIR = ROOT / "data"


def main() -> None:
    data = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    sources = data["sources"]
    aggregate = Counter()
    for source in sources:
        aggregate.update(source["counts"])

    speech_count = {
        word: sum(1 for source in sources if source["counts"].get(word, 0))
        for word in aggregate
    }
    total = sum(aggregate.values())

    with (OUT_DIR / "word-frequency.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["word", "count", "per_1000_tokens", "speech_count"])
        for word, count in aggregate.most_common():
            writer.writerow([
                word,
                count,
                round(count / total * 1000, 4) if total else 0,
                speech_count[word],
            ])

    with (OUT_DIR / "word-frequency-by-speech.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["speech_id", "date", "title", "word", "count"])
        for source in sources:
            for word, count in sorted(
                source["counts"].items(), key=lambda item: (-item[1], item[0])
            ):
                writer.writerow([
                    source["id"],
                    source["date"],
                    source["title"],
                    word,
                    count,
                ])

    print(f"aggregate_rows={len(aggregate)}")
    print(f"speech_rows={sum(len(source['counts']) for source in sources)}")
    print(f"aggregate_tokens={total}")


if __name__ == "__main__":
    main()
