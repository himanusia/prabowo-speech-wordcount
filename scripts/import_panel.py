#!/usr/bin/env python3
"""Import transcripts collected through the YouTube transcript panel.

The caption endpoint (/api/timedtext) rate-limits this IP, but the panel in the
web UI reads youtubei get_panel and is not throttled. Text output is identical:
a side-by-side check on video 9rpZpKagShM gave 15621 chars / 2362 words from
both routes with a normalized ratio of 1.000.

Reads the JSONL progress file written by the browser collector and folds the
results into manifest.json so the rest of the pipeline sees them as normal
sources.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPANDED = ROOT / "data" / "expanded"
MANIFEST_PATH = EXPANDED / "manifest.json"
SEEDS_PATH = EXPANDED / "candidate-seeds.json"
PROGRESS_PATH = Path(
    "/Users/mac/.hermes/workspace/prabowo-corpus-artifacts/_panel_progress.jsonl"
)
TEST_PROGRESS_PATH = Path(
    "/Users/mac/.hermes/workspace/prabowo-corpus-artifacts/_panel_test.jsonl"
)


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for path in (TEST_PROGRESS_PATH, PROGRESS_PATH):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = {item["id"]: item for item in manifest["sources"]}
    seeds = {
        item["id"]: item
        for item in json.loads(SEEDS_PATH.read_text(encoding="utf-8"))["selected"]
    }

    rows = load_rows()
    ok = 0
    skipped = 0
    for row in rows:
        video_id = row["id"]
        status = row.get("status")
        if status != "ok":
            entry = entries.get(video_id) or {
                "id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": row.get("title", ""),
                "channel": "",
            }
            if status == "no_indonesian_track":
                entry.update({"status": "no_indonesian_track",
                              "error_type": "NoIndonesianTrack",
                              "fetch_method": "transcript_panel"})
                entries[video_id] = entry
                skipped += 1
            continue

        raw_path = EXPANDED / "raw" / f"{video_id}.json"
        if not raw_path.exists():
            print(f"missing raw file, skipping: {video_id}")
            continue
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        entry = entries.get(video_id) or {
            "id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": raw.get("title") or seeds.get(video_id, {}).get("title", ""),
            "channel": raw.get("channel") or seeds.get(video_id, {}).get("channel", ""),
            "selection_reason": seeds.get(video_id, {}).get("selection_reason", ""),
            "discovery_origins": seeds.get(video_id, {}).get("discovery_origins", []),
        }
        entry.update({
            "status": "ok",
            "language": raw.get("language", "Indonesian (auto-generated)"),
            "language_code": raw.get("language_code", "id"),
            "is_generated": raw.get("is_generated", True),
            "is_translatable": True,
            "snippet_count": raw.get("snippet_count", len(raw.get("raw_snippets", []))),
            "raw_path": str(raw_path.relative_to(ROOT)),
            "fetch_method": "transcript_panel",
            "panel_segments": row.get("segments"),
        })
        entry.pop("error_type", None)
        entry.pop("error", None)
        entries[video_id] = entry
        ok += 1

    manifest["sources"] = list(entries.values())
    manifest["source_count_ok"] = sum(
        1 for item in entries.values() if item.get("status") == "ok"
    )
    manifest["source_count_no_indonesian_track"] = sum(
        1 for item in entries.values() if item.get("status") == "no_indonesian_track"
    )
    manifest["source_count_error"] = sum(
        1 for item in entries.values() if item.get("status") == "error"
    )
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"imported_ok={ok} no_indonesian_track={skipped} "
          f"manifest_ok={manifest['source_count_ok']} "
          f"manifest_errors={manifest['source_count_error']}")


if __name__ == "__main__":
    main()
