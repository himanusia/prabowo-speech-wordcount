from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPANDED = ROOT / "data" / "expanded"


def main() -> None:
    manifest = json.loads((EXPANDED / "manifest.json").read_text(encoding="utf-8"))
    metadata = {
        **json.loads((EXPANDED / "early-metadata.json").read_text(encoding="utf-8")),
        **json.loads((EXPANDED / "metadata.json").read_text(encoding="utf-8")),
    }
    seeds = json.loads((EXPANDED / "candidate-seeds.json").read_text(encoding="utf-8"))["selected"]
    status = {entry["id"]: entry.get("status") for entry in manifest["sources"]}

    pending = []
    for seed in seeds:
        video_id = seed["id"]
        if status.get(video_id) == "ok":
            continue
        meta = metadata.get(video_id, {})
        pending.append({
            "id": video_id,
            "status": status.get(video_id, "never_fetched"),
            "date": meta.get("upload_date", ""),
            "channel": meta.get("channel", ""),
            "title": meta.get("title", seed.get("title", "")),
        })

    print(f"seeds={len(seeds)} ok={sum(1 for value in status.values() if value == 'ok')} pending={len(pending)}")
    print(Counter(item["status"] for item in pending))
    (EXPANDED / "pending.json").write_text(
        json.dumps(pending, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for item in pending:
        print(item["status"], item["id"], item["date"], item["title"][:70])


if __name__ == "__main__":
    main()
