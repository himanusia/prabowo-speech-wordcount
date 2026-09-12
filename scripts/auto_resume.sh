#!/usr/bin/env bash
# Auto-resume collection for the Prabowo speech corpus.
#
# YouTube rate limits the caption endpoint (HTTP 429, reported by
# youtube-transcript-api as IpBlocked). The block clears on its own after hours,
# so this script attempts a gentle session, stops at the first 429 instead of
# burning cooldowns, and only rebuilds + commits when new captions actually
# arrived. Intended to run from a Hermes cron job as a script-only (no_agent)
# task so a quiet tick costs nothing.
#
# Exit codes:  0 = fine (quiet when nothing new, otherwise a summary on stdout)
#              1 = hard failure (missing venv/scripts, rebuild, guard or push error)
#
# Always exit 0 on success, including when work was done: the Hermes scheduler
# treats any non-zero exit as a failure and raises an alert, so status is
# reported through stdout instead of the exit code.

set -uo pipefail

ROOT="/Users/mac/.hermes/workspace/prabowo-speech-wordcount"
PY="$ROOT/.venv/bin/python"
DATA="$ROOT/data/expanded"
RAW="$DATA/raw"
RUN_LOG="$DATA/auto-resume-run.log"

cd "$ROOT" || { echo "auto-resume: repo not found at $ROOT"; exit 1; }
[ -x "$PY" ] || { echo "auto-resume: venv python missing at $PY"; exit 1; }

now() { date "+%Y-%m-%dT%H:%M:%S%z"; }
epoch() { date "+%s"; }

count_raw() { find "$RAW" -name '*.json' 2>/dev/null | wc -l | tr -d ' '; }

pending_total() {
  "$PY" - <<'PYEOF' 2>/dev/null || echo "?"
import json
from pathlib import Path
p = Path("data/expanded/pending.json")
if not p.exists():
    print("?")
else:
    items = json.loads(p.read_text(encoding="utf-8"))
    wanted = {"IpBlocked", "never_attempted"}
    print(sum(1 for i in items if i["reason"] in wanted))
PYEOF
}

BEFORE=$(count_raw)
LEFT_BEFORE=$(pending_total)
START=$(epoch)
STARTED_AT=$(now)

# Gentle session: paced, and it stops on the first 429 instead of grinding.
"$PY" scripts/collect_expanded.py \
  --only-pending \
  --pending-reasons IpBlocked,never_attempted \
  --stop-on-block \
  --sleep 8 \
  --pause-every 10 \
  --pause-for 60 \
  > "$RUN_LOG" 2>&1
COLLECT_RC=$?

AFTER=$(count_raw)
NEW=$((AFTER - BEFORE))
BLOCKED=$(grep -c "IpBlocked" "$RUN_LOG" 2>/dev/null || true)
BLOCKED=${BLOCKED:-0}
NO_TRACK=$(grep -c "^NO_INDONESIAN_TRACK" "$RUN_LOG" 2>/dev/null || true)
NO_TRACK=${NO_TRACK:-0}
ELAPSED=$(( $(epoch) - START ))

# pending.json is the collector's own report; refresh it so LEFT is current.
"$PY" scripts/list_pending.py > /dev/null 2>&1
LEFT_AFTER=$(pending_total)

record_result() {
  "$PY" - "$@" <<'PYEOF' 2>/dev/null || true
import json, sys
from pathlib import Path
keys = ["started_at", "elapsed_s", "new_captions", "blocked_hits",
        "no_track_hits", "pending_before", "pending_after", "published",
        "collect_rc", "note"]
vals = sys.argv[1:]
row = dict(zip(keys, vals))
for field in ("elapsed_s", "new_captions", "blocked_hits", "no_track_hits", "collect_rc"):
    row[field] = int(row[field])
for field in ("pending_before", "pending_after"):
    row[field] = int(row[field]) if row[field].isdigit() else None
row["published"] = row["published"] == "1"
path = Path("data/expanded/auto-resume-log.jsonl")
with path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
PYEOF
}

if [ "$NEW" -le 0 ]; then
  record_result "$STARTED_AT" "$ELAPSED" 0 "$BLOCKED" "$NO_TRACK" \
    "$LEFT_BEFORE" "$LEFT_AFTER" 0 "$COLLECT_RC" "no_new_captions"
  if [ "$LEFT_AFTER" = "0" ]; then
    echo "Prabowo corpus: all candidates handled, nothing left to fetch. This cron job can be removed."
  fi
  # Silent on a quiet tick: nothing new, so no one needs a message.
  exit 0
fi

# New captions arrived: rebuild the derived data.
"$PY" scripts/analyze_expanded.py > /dev/null 2>&1 || { echo "auto-resume: analyze failed"; exit 1; }
"$PY" scripts/export_expanded.py > /dev/null 2>&1 || { echo "auto-resume: export failed"; exit 1; }
"$PY" scripts/build_ui_expanded.py > /dev/null 2>&1 || { echo "auto-resume: ui build failed"; exit 1; }

EVENTS=$("$PY" - <<'PYEOF' 2>/dev/null || echo "?"
import json
from pathlib import Path
t = json.loads(Path("data/expanded/analysis.json").read_text(encoding="utf-8"))["totals"]
print(f"{t['unique_speech_events']} {t['total_tokens']}")
PYEOF
)

# Stage only derived outputs; raw captions and the run log stay ignored.
git add README.md RESEARCH-PACK.md index.html scripts/analyze_expanded.py \
        data/expanded/analysis.json data/expanded/events.csv \
        data/expanded/source-catalog.json data/expanded/pending.json \
        data/expanded/auto-resume-log.jsonl \
        data/expanded/word-frequency.csv data/expanded/word-frequency-by-event.csv \
        > /dev/null 2>&1

# Refuse to publish if anything forbidden or secret-shaped got staged.
"$PY" - <<'PYEOF'
import re, subprocess, sys
files = subprocess.check_output(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
    text=True,
).splitlines()
patterns = [
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
]
hits = [
    (name, pattern.pattern)
    for name in files
    for pattern in patterns
    if pattern.search(subprocess.check_output(["git", "show", ":" + name]).decode("utf-8", "ignore"))
]
bad = [n for n in files if "/raw/" in n or n.endswith("manifest.json") or n.endswith(".log")]
if hits or bad:
    print("auto-resume: refusing to commit, hits=%s bad=%s" % (hits, bad))
    sys.exit(1)
PYEOF
if [ $? -ne 0 ]; then
  git reset > /dev/null 2>&1
  echo "auto-resume: secret/path guard tripped, nothing published"
  exit 1
fi

if git diff --cached --quiet; then
  record_result "$STARTED_AT" "$ELAPSED" "$NEW" "$BLOCKED" "$NO_TRACK" \
    "$LEFT_BEFORE" "$LEFT_AFTER" 0 "$COLLECT_RC" "no_derived_change"
  echo "Prabowo corpus: +${NEW} caption(s) but derived data unchanged."
  exit 0
fi

git -c user.name=himanusia -c user.email=19623185@std.stei.itb.ac.id commit -q \
  -m "chore: auto-resume fetch, ${NEW} new caption(s)

Collected by scripts/auto_resume.sh on a scheduled gentle session.
YouTube 429 stopped the run at the usual point; the script exits instead
of cooling down so the allowance recovers.
corpus now: ${EVENTS}" || { echo "auto-resume: commit failed"; exit 1; }

GIT_TERMINAL_PROMPT=0 git push -q origin HEAD:main 2>/dev/null
PUSHED=$?
record_result "$STARTED_AT" "$ELAPSED" "$NEW" "$BLOCKED" "$NO_TRACK" \
  "$LEFT_BEFORE" "$LEFT_AFTER" "$([ $PUSHED -eq 0 ] && echo 1 || echo 0)" \
  "$COLLECT_RC" "$([ $PUSHED -eq 0 ] && echo pushed || echo push_failed)"

if [ $PUSHED -ne 0 ]; then
  echo "Prabowo corpus: +${NEW} caption(s), committed but push FAILED (check auth)"
  exit 1
fi

echo "Prabowo corpus: +${NEW} caption(s) published. ${EVENTS} events, ${LEFT_AFTER} candidate(s) still pending."
exit 0
