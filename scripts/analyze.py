#!/usr/bin/env python3
"""Build the analysis for one corpus profile.

Reads the fetched caption tracks plus their metadata, drops non-speech and
duplicate uploads, picks one canonical upload per speech event, then produces the
word index, topic signals, policy-signal evidence, and framing counts.

Every domain decision comes from the profile (see profiles/*.json) — no speaker,
language, or topic is hardcoded here.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from corpus import REPO_ROOT, Corpus, add_profile_argument, load_profile

WORD_RE = re.compile(r"(?u)[^\W_]+(?:[-'][^\W_]+)*")
EVENT_RE = re.compile(r"\[[^\]]*\]|<[^>]*>")


class Analyzer:
    def __init__(self, profile: dict, corpus: Corpus):
        self.profile = profile
        self.corpus = corpus

        filters = profile["title_filters"]
        self.speech_re = re.compile(filters["speech_required"])
        self.non_speech_re = re.compile(filters["exclude_other_speakers"])
        self.commentary_re = re.compile(filters["exclude_commentary"])
        self.arrival_re = re.compile(filters["exclude_arrival"])
        self.speaker_re = re.compile(filters["speaker_required"])
        self.arrival_exempt_re = re.compile(filters["arrival_exempt"])

        tiers = profile["source_tiers"]
        self.official_exact = [c.casefold().strip() for c in tiers["official_channel_exact"]]
        self.official_anywhere = [c.casefold() for c in tiers["official_channel_or_title"]]
        self.full_media_re = re.compile(tiers["full_media_title_re"])

        dedup = profile["dedup"]
        self.shingle_size = dedup["shingle_size"]
        self.same_day = dedup["same_day_containment"]
        self.cross_day = dedup["cross_day_containment"]

        canonical = profile["canonical"]
        self.opening_re = re.compile(canonical["opening_re"])
        self.padded_fraction = canonical["padded_opening_fraction"]
        self.complete_fraction = canonical["complete_opening_fraction"]
        self.score_bonus_re = re.compile(canonical["score_title_bonus_re"])
        self.score_live_re = re.compile(canonical["score_live_penalty_re"])

        signal = profile["policy_signals"]
        self.signal_label = signal["label"]
        self.signal_slug = signal.get("label_slug", signal["label"].casefold())
        self.signal_exact = signal["exact_token"]
        self.signal_full_re = re.compile(signal["full_phrase_re"])
        self.signal_paired = tuple(signal["paired_terms"])
        self.signal_context_token = signal["context_token"]
        self.signal_context_terms = tuple(signal["context_terms"])
        self.signal_ambiguous_re = re.compile(signal["ambiguous_re"])

        self.topics = {name: set(words) for name, words in profile["topics"].items()}
        self.topic_order = list(profile["topic_order"])
        self.pronouns = tuple(profile["pronouns"])
        self.stopwords = set(profile["stopwords"])
        self.speech_windows = {
            video_id: tuple(window)
            for video_id, window in profile.get("speech_windows", {}).items()
        }

    # ---------------------------------------------------------------- text

    def normalize_text(self, text: str) -> str:
        return unicodedata.normalize("NFC", EVENT_RE.sub(" ", text)).casefold()

    def tokenize(self, text: str) -> list[str]:
        normalized = self.normalize_text(text)
        return [
            token
            for token in WORD_RE.findall(normalized)
            if any(char.isalpha() for char in token)
        ]

    @staticmethod
    def normalized_date(value: str) -> str:
        if not value:
            return ""
        if re.fullmatch(r"\d{8}", value):
            return f"{value[:4]}-{value[4:6]}-{value[6:]}"
        return value

    def source_tier(self, channel: str, title: str) -> str:
        # An exact channel match means the upload IS the speaker's own channel; a
        # substring match on channel+title catches official media-office channels
        # even when the title carries the programme name.
        resolved = channel.casefold().strip()
        if any(name == resolved for name in self.official_exact):
            return "official"
        combined = f"{channel} {title}".casefold()
        if any(name in combined for name in self.official_anywhere):
            return "official"
        if self.full_media_re.search(title):
            return "full_media"
        return "media"

    # --------------------------------------------------------------- items

    def snippet_items(self, raw_snippets: list[dict], window: tuple[float, float] | None):
        output = []
        for snippet in raw_snippets:
            start = float(snippet["start"])
            if window and not (window[0] <= start < window[1]):
                continue
            text = str(snippet["text"])
            words = self.tokenize(text)
            if words:
                output.append({"start": round(start, 3), "text": text, "tokens": words})
        return output

    def load_items(self) -> list[dict]:
        manifest = self.corpus.read_manifest()
        metadata = self.corpus.read_json(self.corpus.metadata, {})
        items = []
        for entry in manifest.get("sources", []):
            if entry.get("status") != "ok":
                continue
            video_id = entry["id"]
            raw_path = REPO_ROOT / entry["raw_path"]
            if not raw_path.exists():
                continue
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            meta = metadata.get(video_id, {})
            title = meta.get("title") or entry.get("title", "")
            channel = meta.get("channel") or entry.get("channel", "")
            items.append({
                "id": video_id,
                "date": self.normalized_date(meta.get("upload_date", "")),
                "title": title,
                "channel": channel,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "duration": meta.get("duration"),
                "fetch_method": entry.get("fetch_method", "caption_api"),
                "source_tier": self.source_tier(channel, title),
                "snippets": self.snippet_items(
                    raw["raw_snippets"], self.speech_windows.get(video_id)
                ),
            })
        return items

    def is_eligible(self, item: dict) -> bool:
        title = item["title"]
        if self.non_speech_re.search(title) or self.commentary_re.search(title):
            return False
        if item["id"] in self.speech_windows:
            return True
        if not self.speech_re.search(title):
            return False
        if self.arrival_re.search(title) and not self.arrival_exempt_re.search(title):
            return False
        return bool(self.speaker_re.search(title))

    # ---------------------------------------------------------- duplicates

    def shingle_set(self, tokens: list[str]) -> set[tuple[str, ...]]:
        size = self.shingle_size
        return set(zip(*(tokens[offset:] for offset in range(size))))

    def duplicate_clusters(self, items: list[dict]) -> list[list[dict]]:
        shingles = [self.shingle_set(item["tokens"]) for item in items]
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
                if containment >= self.cross_day or (same_date and containment >= self.same_day):
                    union(index, other)

        groups: dict[int, list[dict]] = {}
        for index, item in enumerate(items):
            groups.setdefault(find(index), []).append(item)
        return list(groups.values())

    # ----------------------------------------------------------- canonical

    def opening_fraction(self, item: dict) -> float | None:
        total = len(item["tokens"])
        if not total:
            return None
        seen = 0
        for snippet in item["snippets"]:
            match = self.opening_re.search(snippet["text"])
            if match:
                prefix = len(self.tokenize(snippet["text"][: match.start()]))
                return (seen + prefix) / total
            seen += len(snippet["tokens"])
        return None

    def canonical_score(self, item: dict) -> tuple[int, int, int]:
        score = 0
        if item["source_tier"] == "official":
            score += 5
        if self.score_bonus_re.search(item["title"]):
            score += 3
        if self.score_live_re.search(item["title"]):
            score -= 1
        return score, len(item["tokens"]), item["duration"] or 0

    def pick_canonical(self, group: list[dict]) -> dict:
        candidates = group
        complete = [
            item for item in group
            if (fraction := self.opening_fraction(item)) is not None
            and fraction <= self.complete_fraction
        ]
        if complete:
            unpadded = [
                item for item in group
                if (fraction := self.opening_fraction(item)) is None
                or fraction <= self.padded_fraction
            ]
            if unpadded:
                candidates = unpadded
        return max(candidates, key=self.canonical_score)

    # ------------------------------------------------------------- signals

    def policy_signal_metrics(self, snippets: list[dict]) -> dict:
        exact = full_phrase = paired = context = ambiguous = 0
        evidence = []
        for snippet in snippets:
            text = self.normalize_text(snippet["text"])
            words = snippet["tokens"]
            matched = []
            if self.signal_exact in words:
                if self.signal_ambiguous_re.search(text):
                    ambiguous += 1
                    matched.append("ambiguous")
                else:
                    exact += 1
                    matched.append("exact_token")
            if self.signal_full_re.search(text):
                full_phrase += 1
                matched.append("full_phrase")
            if all(term in words for term in self.signal_paired):
                paired += 1
                matched.append("paired_terms")
            if self.signal_context_token in words and any(
                term in words for term in self.signal_context_terms
            ):
                context += 1
                matched.append("context")
            if matched:
                evidence.append({"start": snippet["start"], "matches": matched})

        total = exact + full_phrase + paired + context - ambiguous
        return {
            "label": self.signal_label,
            "exact_token_count": exact,
            "full_phrase_count": full_phrase,
            "paired_terms_count": paired,
            "context_count": context,
            "ambiguous_count": ambiguous,
            "policy_signal_count": max(total, 0),
            "present": bool(full_phrase or paired or context or exact > ambiguous),
            "evidence": evidence[:30],
        }

    def topic_counts(self, tokens: list[str], snippets: list[dict]) -> dict[str, int]:
        counts = Counter(tokens)
        output = {
            topic: sum(counts[word] for word in words)
            for topic, words in self.topics.items()
        }
        output[self.signal_slug] = self.policy_signal_metrics(snippets)["policy_signal_count"]
        return output

    # ---------------------------------------------------------------- main

    def prepare_items(self) -> tuple[list[dict], list[list[dict]], int]:
        loaded = self.load_items()
        eligible = [item for item in loaded if self.is_eligible(item)]
        excluded = len(loaded) - len(eligible)
        for item in eligible:
            item["tokens"] = [
                token for snippet in item["snippets"] for token in snippet["tokens"]
            ]
        return eligible, self.duplicate_clusters(eligible), excluded

    def fetch_stats(self) -> dict:
        manifest = self.corpus.read_manifest()
        entries = {entry["id"]: entry for entry in manifest.get("sources", [])}
        stats = {
            "ok": 0, "ip_blocked": 0, "transcripts_disabled": 0,
            "no_indonesian_track": 0, "never_attempted": 0,
        }
        for seed in self.corpus.read_json(self.corpus.seeds, {"selected": []})["selected"]:
            entry = entries.get(seed["id"])
            if entry is None:
                stats["never_attempted"] += 1
            elif entry.get("status") == "ok":
                stats["ok"] += 1
            elif entry.get("status") == "no_indonesian_track":
                stats["no_indonesian_track"] += 1
            elif entry.get("error_type") == "IpBlocked":
                stats["ip_blocked"] += 1
            elif entry.get("error_type") == "TranscriptsDisabled":
                stats["transcripts_disabled"] += 1
            else:
                stats["never_attempted"] += 1
        return stats


def build(analyzer: Analyzer) -> dict:
    eligible, clusters, excluded = analyzer.prepare_items()
    stats = analyzer.fetch_stats()
    canonical = []
    duplicate_groups = []
    for index, group in enumerate(clusters, start=1):
        chosen = analyzer.pick_canonical(group)
        chosen["duplicate_group"] = f"event-{index:03d}"
        chosen["duplicate_count"] = len(group) - 1
        chosen["policy_signals"] = analyzer.policy_signal_metrics(chosen["snippets"])
        chosen["topics"] = analyzer.topic_counts(chosen["tokens"], chosen["snippets"])
        chosen["token_count"] = len(chosen["tokens"])
        chosen["unique_word_count"] = len(set(chosen["tokens"]))
        canonical.append(chosen)
        duplicate_groups.append({
            "event_group": chosen["duplicate_group"],
            "canonical_id": chosen["id"],
            "member_ids": sorted(item["id"] for item in group),
        })

    canonical.sort(key=lambda item: (item["date"], item["id"]))
    corpus: Counter = Counter()
    topic_total: Counter = Counter()
    topic_coverage: Counter = Counter()
    pronoun_total: Counter = Counter()
    for item in canonical:
        corpus.update(item["tokens"])
        topic_total.update(item["topics"])
        for topic, count in item["topics"].items():
            if count:
                topic_coverage[topic] += 1
        pronoun_total.update(word for word in item["tokens"] if word in analyzer.pronouns)

    total_tokens = sum(corpus.values())
    event_count = len(canonical)

    def word_rows(counter: Counter, limit: int) -> list[dict]:
        rows = []
        for word, count in counter.most_common(limit):
            rows.append({
                "word": word,
                "count": count,
                "per_1000": round(count / total_tokens * 1000, 2) if total_tokens else 0,
                "speech_count": sum(1 for item in canonical if word in item["tokens"]),
            })
        return rows

    top_words = word_rows(corpus, 100)
    content = Counter({
        word: count for word, count in corpus.items()
        if word not in analyzer.stopwords and len(word) > 2
    })
    top_content = word_rows(content, 100)

    topic_summary = []
    for topic in [analyzer.signal_slug, *analyzer.topic_order]:
        topic_summary.append({
            "topic": topic,
            "matched_units": topic_total[topic],
            "per_1000_tokens": round(topic_total[topic] / total_tokens * 1000, 2) if total_tokens else 0,
            "speech_count": topic_coverage[topic],
            "speech_share": round(topic_coverage[topic] / event_count * 100, 1) if event_count else 0,
        })

    framing = []
    for word in analyzer.pronouns:
        framing.append({
            "word": word,
            "count": pronoun_total[word],
            "per_1000_tokens": round(pronoun_total[word] / total_tokens * 1000, 2) if total_tokens else 0,
            "speech_count": sum(1 for item in canonical if word in item["tokens"]),
        })

    canonical_ids = {item["id"] for item in canonical}
    group_of = {
        member: group["event_group"]
        for group in duplicate_groups for member in group["member_ids"]
    }
    public_sources = []
    for item in canonical:
        public_item = {
            key: item[key]
            for key in (
                "id", "date", "title", "channel", "url", "duration", "source_tier",
                "fetch_method", "duplicate_group", "duplicate_count",
                "token_count", "unique_word_count", "topics", "policy_signals",
            )
        }
        public_item["counts"] = dict(Counter(item["tokens"]).most_common())
        public_sources.append(public_item)

    public_groups = [
        {"event_group": group["event_group"], "canonical_id": group["canonical_id"],
         "member_ids": group["member_ids"]}
        for group in duplicate_groups
    ]

    public_variants = [
        {
            "id": item["id"], "date": item["date"], "title": item["title"],
            "channel": item["channel"], "url": item["url"], "duration": item["duration"],
            "source_tier": item["source_tier"], "fetch_method": item["fetch_method"],
            "token_count": len(item["tokens"]),
            "is_canonical": item["id"] in canonical_ids,
            "event_group": group_of[item["id"]],
        }
        for item in eligible
    ]
    public_variants.sort(key=lambda row: (row["date"], row["id"]))

    word_index = [
        [word, count, sum(1 for item in canonical if word in item["tokens"])]
        for word, count in corpus.most_common()
    ]

    signal = analyzer.profile["policy_signals"]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": {
            "name": analyzer.profile["name"],
            "description": analyzer.profile.get("description", ""),
            "language_code": analyzer.profile.get("language_code", ""),
        },
        "method": {
            "source": "YouTube caption tracks (caption API, and the transcript panel where the API is rate limited)",
            "primary_metric": "surface-form token count for canonical speech events",
            "normalization": "Unicode NFC + casefold + Unicode-aware tokenization",
            "event_markers": "bracketed caption events removed",
            "deduplication": (
                f"{analyzer.shingle_size}-token shingle containment "
                f"(same day >= {analyzer.same_day}, cross day >= {analyzer.cross_day}); "
                "one canonical source per event"
            ),
            "canonical_rule": (
                "official channel first, then title cues, then length; padded livestream "
                f"captures are skipped when another upload of the same event opens at the top "
                f"(opening fraction > {analyzer.padded_fraction})"
            ),
            "topic_layer": "curated lexical signals; overlapping categories are allowed",
            "policy_signal_rule": (
                f"{signal['label']}: exact token, full phrase, paired terms "
                f"{' + '.join(signal['paired_terms'])}, or {signal['context_token']} context; "
                "ambiguous evidence is reported separately and subtracted from the total"
            ),
            "warning": (
                "caption tracks are not verified audio ground truth; "
                "topic signals need spot review before publication"
            ),
        },
        "totals": {
            "input_caption_items": len(analyzer.load_items()),
            "eligible_caption_items": len(eligible),
            "unique_speech_events": event_count,
            "duplicate_items_removed": sum(len(group) - 1 for group in clusters),
            "excluded_items": excluded,
            "fetch_ok": stats["ok"],
            "fetch_ip_blocked": stats["ip_blocked"],
            "fetch_transcripts_disabled": stats["transcripts_disabled"],
            "fetch_no_indonesian_track": stats["no_indonesian_track"],
            "fetch_never_attempted": stats["never_attempted"],
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
        "duplicate_groups": public_groups,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse one corpus profile.")
    add_profile_argument(parser)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    corpus = Corpus(profile)
    analyzer = Analyzer(profile, corpus)
    output = build(analyzer)
    corpus.analysis.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    corpus.catalog.write_text(
        json.dumps({
            "description": f"Canonical speech-event catalog for the '{profile['name']}' corpus.",
            "raw_captions_in_repository": False,
            "sources": output["sources"],
            "duplicate_groups": output["duplicate_groups"],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    totals = output["totals"]
    print(
        f"profile={profile['name']} input={totals['input_caption_items']} "
        f"eligible={totals['eligible_caption_items']} events={totals['unique_speech_events']} "
        f"duplicates_removed={totals['duplicate_items_removed']} tokens={totals['total_tokens']}"
    )


if __name__ == "__main__":
    main()
