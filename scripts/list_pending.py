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
    entries = {entry["id"]: entry for entry in manifest["sources"]}

    pending = []
    for seed in seeds:
        video_id = seed["id"]
        entry = entries.get(video_id)
        if entry is None:
            reason = "never_attempted"
        elif entry.get("status") == "ok":
            continue
        elif entry.get("status") == "no_indonesian_track":
            reason = "no_indonesian_track"
        else:
            reason = entry.get("error_type", entry.get("status", "unknown"))
        meta = metadata.get(video_id, {})
        pending.append({
            "id": video_id,
            "reason": reason,
            "date": meta.get("upload_date", ""),
            "channel": meta.get("channel", ""),
            "title": meta.get("title", seed.get("title", "")),
        })

    ok = sum(1 for entry in entries.values() if entry.get("status") == "ok")
    print(f"seeds={len(seeds)} ok={ok} pending={len(pending)}")
    print(Counter(item["reason"] for item in pending))
    (EXPANDED / "pending.json").write_text(
        json.dumps(pending, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for item in pending:
        print(item["reason"], item["id"], item["date"], item["title"][:70])


if __name__ == "__main__":
    main()
