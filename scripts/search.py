#!/usr/bin/env python3
"""Find terms in a corpus and show their context.

Counts alone mislead: an auto-generated caption can spell a word oddly, and a bare
hit says nothing about who it was aimed at. This prints each term's totals plus the
surrounding words so a claim can be checked against the actual line.

    scripts/search.py --profile prabowo --terms "antek,asing"
    scripts/search.py --profile prabowo --terms "goblok|bodoh|tolol" --regex
    scripts/search.py --profile prabowo --terms "asing" --context 12 --snippets 8
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict

from corpus import Corpus, add_profile_argument, load_profile


def load_canonical(corpus: Corpus) -> tuple[list[dict], dict[str, list[dict]]]:
    data = corpus.read_json(corpus.analysis, None)
    if data is None:
        raise SystemExit(f"no analysis at {corpus.analysis}; run scripts/analyze.py first")
    sources = data["sources"]
    raws: dict[str, list[dict]] = {}
    for source in sources:
        path = corpus.raw_dir / f"{source['id']}.json"
        if path.exists():
            raws[source["id"]] = json.loads(path.read_text(encoding="utf-8"))["raw_snippets"]
    return sources, raws


def main() -> None:
    parser = argparse.ArgumentParser(description="Search a corpus with context.")
    add_profile_argument(parser)
    parser.add_argument("--terms", required=True,
                        help="Comma-separated terms. Interpreted as regex with --regex.")
    parser.add_argument("--regex", action="store_true",
                        help="Treat each term as a regular expression.")
    parser.add_argument("--substring", action="store_true",
                        help="Match inside longer words too. Without this, a search for "
                             "'asing' will not match 'masing-masing'.")
    parser.add_argument("--context", type=int, default=10,
                        help="Words of context to show on each side.")
    parser.add_argument("--snippets", type=int, default=4,
                        help="Context lines to show per term (0 hides them).")
    parser.add_argument("--min-events", type=int, default=1)
    args = parser.parse_args()

    profile = load_profile(args.profile)
    corpus = Corpus(profile)
    sources, raws = load_canonical(corpus)
    total_tokens = sum(source["token_count"] for source in sources)

    terms = [t.strip() for t in args.terms.split(",") if t.strip()]
    print(f"profile={profile['name']} events={len(sources)} tokens={total_tokens:,}".replace(",", "."))
    mode = 'regex' if args.regex else ('substring' if args.substring else 'whole word')
    print(f"searching: {', '.join(terms)}  ({mode})")
    print()

    for term in terms:
        if args.regex:
            pattern = re.compile(term, re.I)
        elif args.substring:
            pattern = re.compile(re.escape(term), re.I)
        else:
            pattern = re.compile(r"(?<![\w-])" + re.escape(term) + r"(?![\w-])", re.I)
        per_event: dict[str, int] = defaultdict(int)
        contexts: list[str] = []
        for source in sources:
            snippets = raws.get(source["id"])
            if not snippets:
                continue
            for snippet in snippets:
                text = snippet["text"]
                hits = pattern.findall(text)
                if not hits:
                    continue
                per_event[source["id"]] += len(hits)
                if len(contexts) < args.snippets:
                    words = text.split()
                    match = pattern.search(text)
                    if match:
                        before = len(text[: match.start()].split())
                        lo = max(0, before - args.context)
                        hi = min(len(words), before + args.context)
                        contexts.append(
                            f'{source["date"]} {" ".join(words[lo:before])} ▸{" ".join(words[before:before + len(match.group(0).split())])}◂ {" ".join(words[before + len(match.group(0).split()):hi])}'
                        )

        count = sum(per_event.values())
        events = len(per_event)
        rate = count / total_tokens * 1000 if total_tokens else 0
        if events < args.min_events:
            print(f'{term!r:<28} 0 hit')
            continue
        print(f'{term!r:<28} {count:>5} hit  {rate:>6.2f}/1k  {events:>2}/{len(sources)} event  '
              f'({events / len(sources) * 100:.0f}%)')
        top = sorted(per_event.items(), key=lambda kv: -kv[1])[:5]
        by_id = {s["id"]: s for s in sources}
        for video_id, hits in top:
            source = by_id[video_id]
            print(f'      {hits:>3}x  {source["date"]}  {source["title"][:60]}')
        for line in contexts[: args.snippets]:
            print(f'      …{line}')
        print()


if __name__ == "__main__":
    main()
