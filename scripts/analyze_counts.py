from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "manifest.json"
OUTPUT_PATH = ROOT / "data" / "analysis.json"

# These windows remove obvious MC/opening/closing/event material where the
# YouTube upload is a whole event rather than a speech-only cut.
WINDOWS = {
    "vyp6JITYFM8": (61.6, 2865.0),
    "xK61ktEglpc": (0.0, 1050.0),
    "hJybE-uF_qE": (1161.6, 2850.0),
    "rKpNQwecniM": (20.2, 2262.0),
    "VyPCSPnxbaE": (34.4, 1020.0),
    "5OIq7GaU4sI": (0.0, 257.0),
    "CfnRESwOZKQ": (0.0, 923.0),
    "E_doThSKS4E": (1333.7, 1985.0),
    "3e_gu9rWwWQ": (0.0, 646.0),
    "02IcsjvhFGQ": (0.0, 175.0),
}

WORD_RE = re.compile(r"(?u)[^\W_]+(?:[-'][^\W_]+)*")
EVENT_RE = re.compile(r"\[[^\]]*\]|<[^>]*>")


def tokenize(text: str) -> list[str]:
    text = EVENT_RE.sub(" ", text)
    text = unicodedata.normalize("NFC", text).casefold()
    return [
        token
        for token in WORD_RE.findall(text)
        if any(char.isalpha() for char in token)
    ]


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": {
            "source": "YouTube Indonesian caption track",
            "primary_metric": "surface-form token count",
            "normalization": "Unicode NFC + casefold + Unicode-aware tokenization",
            "removed": "bracketed caption events such as [musik] and [tepuk tangan]",
            "deduplication": "none; repeated spoken words remain counted",
            "windows": "approximate speech windows manually selected per upload",
            "note": "Counts describe the selected caption windows, not a verified word-for-word ground truth of the audio.",
        },
        "totals": {},
        "sources": [],
    }

    corpus = Counter()
    included_snippets = 0
    event_only_snippets = 0

    for source in manifest["sources"]:
        if source["status"] != "ok":
            continue
        video_id = source["id"]
        raw = json.loads((ROOT / source["raw_path"]).read_text(encoding="utf-8"))
        window_start, window_end = WINDOWS[video_id]
        counts = Counter()
        selected = []
        event_removed = 0

        for snippet in raw["raw_snippets"]:
            start = float(snippet["start"])
            if start < window_start or start >= window_end:
                continue
            included_snippets += 1
            text = str(snippet["text"])
            cleaned = EVENT_RE.sub(" ", text).strip()
            if not cleaned:
                event_only_snippets += 1
                continue
            words = tokenize(text)
            if not words:
                event_only_snippets += 1
                continue
            selected.append(
                {
                    "start": start,
                    "duration": float(snippet["duration"]),
                    "text": text,
                }
            )
            counts.update(words)
            corpus.update(words)
            if EVENT_RE.search(text):
                event_removed += 1

        output["sources"].append(
            {
                "id": video_id,
                "date": source["date"],
                "title": source["title"],
                "channel": source["channel"],
                "url": source["url"],
                "language_code": raw["language_code"],
                "is_generated": raw["is_generated"],
                "window_start": window_start,
                "window_end": window_end,
                "full_snippet_count": raw["snippet_count"],
                "selected_snippet_count": len(selected),
                "event_marker_snippet_count": event_removed,
                "token_count": sum(counts.values()),
                "unique_word_count": len(counts),
                "counts": dict(counts),
            }
        )

    source_count = len(output["sources"])
    total_words = sum(corpus.values())
    top_words = []
    for word, count in corpus.most_common(100):
        speech_count = sum(
            1 for source in output["sources"] if source["counts"].get(word, 0)
        )
        top_words.append(
            {
                "word": word,
                "count": count,
                "per_1000": round(count / total_words * 1000, 2) if total_words else 0,
                "speech_count": speech_count,
            }
        )

    output["totals"] = {
        "video_count": source_count,
        "total_tokens": total_words,
        "unique_words": len(corpus),
        "caption_snippets_in_windows": included_snippets,
        "event_only_snippets_removed": event_only_snippets,
        "top_words": top_words,
    }

    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"analyzed {source_count} videos, {total_words} tokens, "
        f"{len(corpus)} unique words"
    )
    print("top 20:")
    for item in top_words[:20]:
        print(
            f"{item['word']}\t{item['count']}\t"
            f"{item['per_1000']}\t{item['speech_count']}"
        )


if __name__ == "__main__":
    main()
