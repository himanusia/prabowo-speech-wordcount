from __future__ import annotations

import json
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from youtube_transcript_api import YouTubeTranscriptApi

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "transcripts" / "raw"
MANIFEST_PATH = ROOT / "data" / "manifest.json"

SOURCES = [
    {"id": "vyp6JITYFM8", "date": "2026-07-24", "title": "Pidato Prabowo di Harlah PKB", "channel": "KOMPASTV"},
    {"id": "xK61ktEglpc", "date": "2026-06-28", "title": "Pidato Penutupan Sarasehan Kebangsaan KSTI 2026", "channel": "Pangkep TV"},
    {"id": "hJybE-uF_qE", "date": "2026-06-26", "title": "Pembukaan Sarasehan Kebangsaan KSTI 2026", "channel": "Sekretariat Presiden"},
    {"id": "rKpNQwecniM", "date": "2026-05-01", "title": "Pidato Presiden Prabowo pada Peringatan Hari Buruh Internasional", "channel": "Prabowo Subianto"},
    {"id": "VyPCSPnxbaE", "date": "2026-03-11", "title": "Pidato Presiden Prabowo di Tasyakuran HUT ke-1 Danantara", "channel": "METRO TV"},
    {"id": "5OIq7GaU4sI", "date": "2026-02-28", "title": "Sambutan Presiden Prabowo pada Perayaan Tahun Baru Imlek Nasional", "channel": "Sekretariat Presiden"},
    {"id": "CfnRESwOZKQ", "date": "2025-04-10", "title": "Pidato Kenegaraan Presiden Prabowo di Hadapan Parlemen Turkiye", "channel": "Sekretariat Presiden"},
    {"id": "E_doThSKS4E", "date": "2025-08-07", "title": "Presiden Prabowo Hadiri KSTI Indonesia 2025", "channel": "Sekretariat Presiden"},
    {"id": "3e_gu9rWwWQ", "date": "2025-08-31", "title": "Pernyataan Presiden Prabowo Menyikapi Aksi Demo", "channel": "Kompas.com"},
    {"id": "02IcsjvhFGQ", "date": "2025-10-24", "title": "Sambutan Presiden Prabowo pada Puncak Peringatan Hari Santri", "channel": "Sekretariat Presiden"},
]

WORD_RE = re.compile(r"(?u)[^\W_]+(?:[-'][^\W_]+)*")


def tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFC", text).casefold()
    return [
        token for token in WORD_RE.findall(normalized)
        if any(char.isalpha() for char in token)
    ]


def choose_indonesian_track(api: YouTubeTranscriptApi, video_id: str):
    tracks = list(api.list(video_id))
    candidates = [track for track in tracks if track.language_code.startswith("id")]
    if not candidates:
        raise RuntimeError("no Indonesian transcript track")
    manual = [track for track in candidates if not track.is_generated]
    return (manual or candidates)[0], tracks


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    api = YouTubeTranscriptApi()
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "language": "id",
        "source_count_requested": len(SOURCES),
        "sources": [],
    }

    for source in SOURCES:
        video_id = source["id"]
        entry: dict[str, object] = {
            **source,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }
        try:
            track, available = choose_indonesian_track(api, video_id)
            fetched = track.fetch()
            snippets = fetched.to_raw_data()
            text = " ".join(item["text"] for item in snippets)
            item = {
                **entry,
                "status": "ok",
                "language": fetched.language,
                "language_code": fetched.language_code,
                "is_generated": fetched.is_generated,
                "is_translatable": track.is_translatable,
                "snippet_count": len(snippets),
                "raw_token_count": len(tokens(text)),
                "raw_snippets": snippets,
                "available_tracks": [
                    {
                        "language": t.language,
                        "language_code": t.language_code,
                        "is_generated": t.is_generated,
                        "is_translatable": t.is_translatable,
                    }
                    for t in available
                ],
            }
            out_path = RAW_DIR / f"{video_id}.json"
            out_path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
            entry.update({
                "status": "ok",
                "language": fetched.language,
                "language_code": fetched.language_code,
                "is_generated": fetched.is_generated,
                "snippet_count": len(snippets),
                "raw_token_count": len(tokens(text)),
                "raw_path": str(out_path.relative_to(ROOT)),
            })
            print(f"OK {video_id}: {len(snippets)} snippets, {len(tokens(text))} tokens")
        except Exception as exc:
            entry.update({"status": "error", "error_type": type(exc).__name__, "error": str(exc)})
            print(f"ERROR {video_id}: {type(exc).__name__}: {exc}")
        manifest["sources"].append(entry)
        time.sleep(0.35)

    manifest["source_count_ok"] = sum(1 for source in manifest["sources"] if source["status"] == "ok")
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Fetched {manifest['source_count_ok']}/{manifest['source_count_requested']} sources")


if __name__ == "__main__":
    main()
