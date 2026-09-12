"""Corpus profile loading and path resolution.

A profile is a JSON file under `profiles/` that describes one corpus: what to
search for, how to tell a speech from a clip, how to recognise duplicates, which
policy signal to track, and which lexical categories count as topics. Everything
that used to be hardcoded for one speaker lives here, so pointing the pipeline at
a different corpus is a matter of adding a profile.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = REPO_ROOT / "profiles"
DATA_DIR = REPO_ROOT / "data"
DEFAULT_PROFILE = "prabowo"


def available_profiles() -> list[str]:
    return sorted(path.stem for path in PROFILES_DIR.glob("*.json"))


def add_profile_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help=(
            "corpus profile to operate on, matching profiles/<name>.json "
            f"(default: {DEFAULT_PROFILE}; available: {', '.join(available_profiles()) or 'none'})"
        ),
    )


def load_profile(name: str) -> dict:
    path = PROFILES_DIR / f"{name}.json"
    if not path.exists():
        raise SystemExit(
            f"unknown profile '{name}'. available: {', '.join(available_profiles()) or 'none'}"
        )
    profile = json.loads(path.read_text(encoding="utf-8"))
    profile.setdefault("name", name)
    if profile["name"] != name:
        raise SystemExit(
            f"profile file {path.name} declares name '{profile['name']}', expected '{name}'"
        )
    return profile


class Corpus:
    """Resolved file locations for one profile."""

    def __init__(self, profile: dict):
        self.profile = profile
        self.name = profile["name"]
        self.dir = DATA_DIR / self.name
        self.raw_dir = self.dir / "raw"
        self.manifest = self.dir / "manifest.json"
        self.metadata = self.dir / "metadata.json"
        self.seeds = self.dir / "candidate-seeds.json"
        self.discovery = self.dir / "discovery.json"
        self.pending = self.dir / "pending.json"
        self.analysis = self.dir / "analysis.json"
        self.catalog = self.dir / "source-catalog.json"
        self.events_csv = self.dir / "events.csv"
        self.word_csv = self.dir / "word-frequency.csv"
        self.word_by_event_csv = self.dir / "word-frequency-by-event.csv"
        self.ratelimit = self.dir / "ratelimit-observations.json"
        self.resume_log = self.dir / "auto-resume-log.jsonl"
        self.resume_run_log = self.dir / "auto-resume-run.log"
        self.panel_progress = self.dir / "panel-progress.jsonl"
        self.report = REPO_ROOT / (
            "RESEARCH-PACK.md" if self.name == DEFAULT_PROFILE
            else f"RESEARCH-PACK-{self.name}.md"
        )
        self.dashboard = REPO_ROOT / (
            "index.html" if self.name == DEFAULT_PROFILE else f"{self.name}.html"
        )

    def ensure_dirs(self) -> None:
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def read_manifest(self) -> dict:
        if self.manifest.exists():
            return json.loads(self.manifest.read_text(encoding="utf-8"))
        return {"generated_at": None, "sources": []}

    def read_json(self, path: Path, default):
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return default


def resolve(name: str) -> tuple[dict, Corpus]:
    profile = load_profile(name)
    return profile, Corpus(profile)
