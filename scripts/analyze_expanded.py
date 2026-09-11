from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE_DIR = ROOT / "data" / "transcripts" / "raw"
EXPANDED_DIR = ROOT / "data" / "expanded"
MANIFEST_PATH = EXPANDED_DIR / "manifest.json"
METADATA_PATH = EXPANDED_DIR / "metadata.json"
OUTPUT_PATH = EXPANDED_DIR / "analysis.json"
CATALOG_PATH = EXPANDED_DIR / "source-catalog.json"

BASELINE_WINDOWS = {
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
MBG_FULL_RE = re.compile(
    r"\b(?:program\s+)?makanan?\s+bergizi\s+gratis\b"
)
NON_SPEECH_RE = re.compile(
    r"(?i)(ustaz\s+adi\s+hidayat|mar(?:u|ú)f\s+amin|ketum\s+mui|"
    r"\bmui\b|mensesneg|menteri|minister|teddy|ahy|gibran|"
    r"momen|aksi|polemik|pakar|kroni|podcast|parodi|analisis|"
    r"komentari|survei|siswa|siswi|bocah|dapur|ayam|mahfud)"
)
ARRIVAL_RE = re.compile(
    r"(?i)(tiba|bertolak|keberangkatan|arriv|depart|disambut|welcome)"
)
SPEECH_RE = re.compile(
    r"(?i)(pidato|sambutan|speech|remarks|sidang|kenegaraan|"
    r"pernyataan|may day|hari buruh|muktamar|kongres|peringatan|"
    r"pelantikan|plenary|business summit|natal|waisak|imlek|"
    r"forum|rapat paripurna|pemerintahan|ucapan)"
)

STOPWORDS = set(
    """
yang dan di ke dari untuk dengan ini itu pada dalam adalah akan ada atau bagi
sebagai oleh para sudah sangat juga lebih tidak ya kan lagi hanya semua bisa
bahwa telah dapat atas terhadap menjadi secara karena namun maka kalau jika
ketika seperti tentang antara kepada daripada sampai serta pun lah kah
saya kita kami mereka kalian anda saudara saudara-saudara sekalian terima kasih
tapi jadi baik banyak besar hari sekarang tadi sama
""".split()
)

TOPIC_TERMS = {
    "pangan": {
        "pangan", "swasembada", "beras", "petani", "nelayan", "pupuk",
        "tebu", "gula", "jagung", "sawah", "ikan", "pertanian",
    },
    "ekonomi": {
        "ekonomi", "investasi", "industri", "hilirisasi", "pertumbuhan",
        "usaha", "pengusaha", "pajak", "anggaran", "rupiah", "perdagangan",
        "koperasi", "bumn", "umkm",
    },
    "pendidikan": {
        "pendidikan", "sekolah", "guru", "siswa", "universitas", "ilmu",
        "sains", "kampus", "pelajar",
    },
    "kesehatan_dan_gizi": {
        "kesehatan", "gizi", "bergizi", "nutrisi", "stunting", "anak",
        "dokter", "rumah", "sakit", "makanan", "sppg", "bgn",
    },
    "tata_kelola": {
        "korupsi", "kebocoran", "efisiensi", "pengawasan", "integritas",
        "suap", "hukuman", "hukum", "uang", "pemerintah", "reformasi",
    },
    "pertahanan_dan_keamanan": {
        "tni", "polri", "pertahanan", "militer", "perang", "keamanan",
        "prajurit", "kepolisian",
    },
    "nasional_dan_identitas": {
        "indonesia", "bangsa", "rakyat", "negara", "merah", "putih",
        "pancasila", "kemerdekaan", "kedaulatan", "tanah", "air",
    },
}

TOPIC_ORDER = list(TOPIC_TERMS)
PRONOUNS = ("saya", "kita", "kami", "mereka")


def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", EVENT_RE.sub(" ", text)).casefold()


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    return [
        token
        for token in WORD_RE.findall(normalized)
        if any(char.isalpha() for char in token)
    ]


def normalized_date(value: str) -> str:
    if not value:
        return ""
    if re.fullmatch(r"\d{8}", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return value


def source_tier(channel: str, title: str) -> str:
    lowered = f"{channel} {title}".casefold()
    if "sekretariat presiden" in lowered or channel.casefold().strip() == "prabowo subianto":
        return "official"
    if re.search(r"(?i)\bfull\b|\blengkap\b|\blive\b", title):
        return "full_media"
    return "media"


def snippet_items(raw_snippets: list[dict], window: tuple[float, float] | None):
    output = []
    for snippet in raw_snippets:
        start = float(snippet["start"])
        if window and not (window[0] <= start < window[1]):
            continue
        text = str(snippet["text"])
        words = tokenize(text)
        if words:
            output.append({
                "start": round(start, 3),
                "text": text,
                "tokens": words,
            })
    return output


def load_items() -> list[dict]:
    items = []
    seen = set()

    for path in sorted(BASELINE_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        video_id = raw["id"]
        if video_id not in BASELINE_WINDOWS:
            continue
        snippets = snippet_items(raw["raw_snippets"], BASELINE_WINDOWS[video_id])
        items.append({
            "id": video_id,
            "date": normalized_date(raw["date"]),
            "title": raw["title"],
            "channel": raw["channel"],
            "url": raw["url"],
            "duration": round(BASELINE_WINDOWS[video_id][1] - BASELINE_WINDOWS[video_id][0]),
            "source_kind": "baseline",
            "source_tier": source_tier(raw["channel"], raw["title"]),
            "snippets": snippets,
        })
        seen.add(video_id)

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    for entry in manifest["sources"]:
        video_id = entry["id"]
        if entry.get("status") != "ok" or video_id in seen:
            continue
        raw = json.loads((ROOT / entry["raw_path"]).read_text(encoding="utf-8"))
        meta = metadata.get(video_id, {})
        title = meta.get("title", entry.get("title", ""))
        channel = meta.get("channel", entry.get("channel", ""))
        items.append({
            "id": video_id,
            "date": normalized_date(meta.get("upload_date", "")),
            "title": title,
            "channel": channel,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "duration": meta.get("duration"),
            "source_kind": "expanded",
            "source_tier": source_tier(channel, title),
            "snippets": snippet_items(raw["raw_snippets"], None),
        })
        seen.add(video_id)

    return items


def is_eligible(item: dict) -> bool:
    title = item["title"]
    if NON_SPEECH_RE.search(title):
        return False
    if item["source_kind"] == "baseline":
        return True
    if not SPEECH_RE.search(title):
        return False
    if ARRIVAL_RE.search(title) and not re.search(
        r"(?i)(pidato|sambutan|speech|remarks|pernyataan)", title
    ):
        return False
    return bool(re.search(r"(?i)(prabowo|presiden|president)", title))


def shingle_set(tokens: list[str]) -> set[tuple[str, ...]]:
    return set(zip(tokens, tokens[1:], tokens[2:], tokens[3:]))


def duplicate_clusters(items: list[dict]) -> list[list[dict]]:
    shingles = [shingle_set(item["tokens"]) for item in items]
    parent = list(range(len(items)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        first, second = find(left), find(right)
        if first != second:
            parent[second] = first

    for index in range(len(items)):
        for other in range(index):
            left, right = shingles[index], shingles[other]
            if not left or not right:
                continue
            containment = len(left & right) / min(len(left), len(right))
            same_date = bool(items[index]["date"]) and (
                items[index]["date"] == items[other]["date"]
            )
            if containment >= 0.58 or (same_date and containment >= 0.22):
                union(index, other)

    groups = {}
    for index, item in enumerate(items):
        groups.setdefault(find(index), []).append(item)
    return list(groups.values())


def canonical_score(item: dict) -> tuple[int, int, int]:
    title = item["title"]
    score = 0
    if item["source_tier"] == "official":
        score += 5
    if re.search(r"(?i)(full|lengkap|pidato|sambutan|speech|remarks)", title):
        score += 3
    if re.search(r"(?i)\blive\b", title):
        score -= 1
    return score, len(item["tokens"]), item["duration"] or 0


def mbg_metrics(snippets: list[dict]) -> dict:
    exact = 0
    full_phrase = 0
    paired_terms = 0
    related = 0
    ambiguous = 0
    evidence = []

    for snippet in snippets:
        text = normalize_text(snippet["text"])
        words = snippet["tokens"]
        matched = []
        if "mbg" in words:
            if re.search(r"\bmbg\s+singkatan\s+mas\s+bahlil\s+ganteng\b", text):
                ambiguous += 1
                matched.append("ambiguous_acronym")
            else:
                exact += 1
                matched.append("mbg_exact")
        if MBG_FULL_RE.search(text):
            full_phrase += 1
            matched.append("full_phrase")
        if "makan" in words and "bergizi" in words:
            paired_terms += 1
            matched.append("makan_plus_bergizi")
        if "sppg" in words and any(
            term in words for term in ("gizi", "bergizi", "makan", "anak")
        ):
            related += 1
            matched.append("sppg_context")
        if matched:
            evidence.append({
                "start": snippet["start"],
                "matches": matched,
            })

    policy_mentions = exact + full_phrase + paired_terms + related - ambiguous
    return {
        "mbg_exact_count": exact,
        "mbg_full_phrase_count": full_phrase,
        "makan_plus_bergizi_count": paired_terms,
        "mbg_related_count": related,
        "mbg_ambiguous_count": ambiguous,
        "mbg_policy_signal_count": max(policy_mentions, 0),
        "mbg_present": bool(full_phrase or paired_terms or related or exact > ambiguous),
        "evidence": evidence[:30],
    }


def topic_counts(tokens: list[str], snippets: list[dict]) -> dict[str, int]:
    counts = Counter(tokens)
    output = {
        topic: sum(counts[word] for word in terms)
        for topic, terms in TOPIC_TERMS.items()
    }
    output["mbg"] = mbg_metrics(snippets)["mbg_policy_signal_count"]
    return output


def prepare_items() -> tuple[list[dict], list[list[dict]], int]:
    loaded = load_items()
    eligible = [item for item in loaded if is_eligible(item)]
    excluded = len(loaded) - len(eligible)
    for item in eligible:
        item["tokens"] = [
            token
            for snippet in item["snippets"]
            for token in snippet["tokens"]
        ]
    clusters = duplicate_clusters(eligible)
    return eligible, clusters, excluded


def main() -> None:
    eligible, clusters, excluded = prepare_items()
    canonical = []
    duplicate_groups = []

    for group_index, group in enumerate(clusters, start=1):
        chosen = max(group, key=canonical_score)
        chosen["duplicate_group"] = f"event-{group_index:03d}"
        chosen["duplicate_count"] = len(group) - 1
        chosen["mbg"] = mbg_metrics(chosen["snippets"])
        chosen["topics"] = topic_counts(chosen["tokens"], chosen["snippets"])
        chosen["token_count"] = len(chosen["tokens"])
        chosen["unique_word_count"] = len(set(chosen["tokens"]))
        canonical.append(chosen)
        duplicate_groups.append({
            "event_group": chosen["duplicate_group"],
            "canonical_id": chosen["id"],
            "member_ids": sorted(item["id"] for item in group),
        })

    canonical.sort(key=lambda item: (item["date"], item["id"]))
    corpus = Counter()
    topic_total = Counter()
    topic_coverage = Counter()
    pronoun_total = Counter()
    for item in canonical:
        corpus.update(item["tokens"])
        topic_total.update(item["topics"])
        for topic, count in item["topics"].items():
            if count:
                topic_coverage[topic] += 1
        pronoun_total.update(
            word for word in item["tokens"] if word in PRONOUNS
        )

    total_tokens = sum(corpus.values())
    top_words = []
    for word, count in corpus.most_common(100):
        top_words.append({
            "word": word,
            "count": count,
            "per_1000": round(count / total_tokens * 1000, 2)
            if total_tokens else 0,
            "speech_count": sum(
                1 for item in canonical if item["tokens"].count(word)
            ),
        })

    content_counter = Counter({
        word: count
        for word, count in corpus.items()
        if word not in STOPWORDS and len(word) > 2
    })
    top_content = []
    for word, count in content_counter.most_common(100):
        top_content.append({
            "word": word,
            "count": count,
            "per_1000": round(count / total_tokens * 1000, 2)
            if total_tokens else 0,
            "speech_count": sum(
                1 for item in canonical if item["tokens"].count(word)
            ),
        })

    topic_summary = []
    for topic in ["mbg", *TOPIC_ORDER]:
        topic_summary.append({
            "topic": topic,
            "matched_units": topic_total[topic],
            "per_1000_tokens": round(
                topic_total[topic] / total_tokens * 1000, 2
            ) if total_tokens else 0,
            "speech_count": topic_coverage[topic],
            "speech_share": round(
                topic_coverage[topic] / len(canonical) * 100, 1
            ) if canonical else 0,
        })

    framing = []
    for word in PRONOUNS:
        framing.append({
            "word": word,
            "count": pronoun_total[word],
            "per_1000_tokens": round(
                pronoun_total[word] / total_tokens * 1000, 2
            ) if total_tokens else 0,
            "speech_count": sum(
                1 for item in canonical if word in item["tokens"]
            ),
        })

    public_sources = []
    public_items = []
    canonical_ids = {item["id"] for item in canonical}
    public_variants = []
    for item in canonical:
        public_item = {
            key: item[key]
            for key in (
                "id", "date", "title", "channel", "url", "duration",
                "source_tier", "duplicate_group", "duplicate_count",
                "token_count", "unique_word_count", "topics", "mbg",
            )
        }
        public_item["counts"] = dict(Counter(item["tokens"]).most_common())
        public_sources.append(public_item)
        public_items.append({
            "event_group": item["duplicate_group"],
            "canonical_id": item["id"],
            "member_ids": next(
                group["member_ids"]
                for group in duplicate_groups
                if group["event_group"] == item["duplicate_group"]
            ),
        })

    for item in eligible:
        public_variants.append({
            "id": item["id"],
            "date": item["date"],
            "title": item["title"],
            "channel": item["channel"],
            "url": item["url"],
            "duration": item["duration"],
            "source_tier": item["source_tier"],
            "source_kind": item["source_kind"],
            "token_count": len(item["tokens"]),
            "is_canonical": item["id"] in canonical_ids,
            "event_group": next(
                group["event_group"]
                for group in duplicate_groups
                if item["id"] in group["member_ids"]
            ),
        })
    public_variants.sort(key=lambda row: (row["date"], row["id"]))
    word_index = [
        [word, count, sum(1 for item in canonical if word in item["tokens"])]
        for word, count in corpus.most_common()
    ]

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "method": {
            "source": "Indonesian YouTube caption tracks",
            "primary_metric": "surface-form token count for canonical speech events",
            "normalization": "Unicode NFC + casefold + Unicode-aware tokenization",
            "event_markers": "bracketed caption events removed",
            "deduplication": (
                "4-token shingle containment; one canonical source per event"
            ),
            "topic_layer": (
                "curated lexical signals; overlapping categories are allowed"
            ),
            "mbg_rule": (
                "exact MBG/full phrase or contextual makan+bergizi/SPPG signal; "
                "ambiguous acronym evidence is reported separately"
            ),
            "warning": (
                "caption windows/tracks are not verified audio ground truth; "
                "topic signals need spot review before publication"
            ),
        },
        "totals": {
            "input_caption_items": len(load_items()),
            "eligible_caption_items": len(eligible),
            "unique_speech_events": len(canonical),
            "duplicate_items_removed": sum(
                len(group) - 1 for group in clusters
            ),
            "excluded_items": excluded,
            "total_tokens": total_tokens,
            "unique_words": len(corpus),
            "top_words": top_words,
            "top_content_words": top_content,
            "topics": topic_summary,
            "framing": framing,
        },
        "sources": public_sources,
        "variants": public_variants,
        "word_index": word_index,
        "duplicate_groups": public_items,
    }
    OUTPUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    CATALOG_PATH.write_text(
        json.dumps({
            "description": (
                "Canonical speech-event catalog for the expanded local-first "
                "Indonesian caption index."
            ),
            "raw_captions_in_repository": False,
            "sources": public_sources,
            "duplicate_groups": public_items,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        f"input={len(load_items())} eligible={len(eligible)} "
        f"events={len(canonical)} duplicates_removed="
        f"{sum(len(group) - 1 for group in clusters)} tokens={total_tokens}"
    )


if __name__ == "__main__":
    main()
