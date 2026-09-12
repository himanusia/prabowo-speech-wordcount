#!/usr/bin/env bash
# Scheduled gentle resume for a corpus profile whose candidates were rate limited.
#
# YouTube 429s the caption endpoint after a burst and the block clears on its own,
# so the leftovers need repeated small sessions rather than one long run. This runs
# one gentle session, stops at the first 429, and only rebuilds, commits and pushes
# when new captions actually arrive. A quiet tick prints nothing.
#
# Usage: scripts/auto_resume.sh [profile]        (default: prabowo)
#
# Always exits 0 on success, including when work was done: the Hermes scheduler
# treats any non-zero exit as a failure and raises an alert, so status is reported
# through stdout instead of the exit code. Exit 1 stays reserved for real failures.

set -uo pipefail

PROFILE="${1:-prabowo}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
DATA="$ROOT/data/$PROFILE"
RAW="$DATA/raw"
RUN_LOG="$DATA/auto-resume-run.log"

cd "$ROOT" || { echo "auto-resume: repo not found at $ROOT"; exit 1; }
[ -x "$PY" ] || { echo "auto-resume: venv python missing at $PY"; exit 1; }
[ -d "$DATA" ] || { echo "auto-resume: no data directory for profile '$PROFILE'"; exit 1; }

now() { date "+%Y-%m-%dT%H:%M:%S%z"; }
epoch() { date "+%s"; }
count_raw() { find "$RAW" -name '*.json' 2>/dev/null | wc -l | tr -d ' '; }

pending_total() {
  "$PY" - "$PROFILE" <<'PYEOF' 2>/dev/null || echo "?"
import json, sys
from pathlib import Path
path = Path("data") / sys.argv[1] / "pending.json"
if not path.exists():
    print("?")
else:
    items = json.loads(path.read_text(encoding="utf-8"))
    print(sum(1 for i in items if i["reason"] in {"IpBlocked", "never_attempted"}))
PYEOF
}

BEFORE=$(count_raw)
LEFT_BEFORE=$(pending_total)
START=$(epoch)
STARTED_AT=$(now)

# YouTube does not publish how long a 429 lasts, so instead of guessing a fixed
# interval the schedule probes on an exponential backoff and the log records where
# the window actually reopens: streak 1 -> 1h, 2 -> 2h, 3+ -> 4h (capped). A probe
# that returns captions proves the window opened and resets the streak. One blocked
# probe costs a single video, i.e. two HTTP requests.
BACKOFF_BASE_S=3600
BACKOFF_CAP_S=14400

BACKOFF_WAIT=$("$PY" - "$PROFILE" "$BACKOFF_BASE_S" "$BACKOFF_CAP_S" <<'PYEOF' 2>/dev/null || echo 0
import json, sys
from pathlib import Path
profile, base, cap = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
path = Path("data") / profile / "auto-resume-log.jsonl"
if not path.exists():
    print(0); raise SystemExit
rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
streak = 0
for row in reversed(rows):
    if row.get("new_captions", 0) > 0:
        break
    if row.get("blocked_hits", 0) >= 1:
        streak += 1
    else:
        break
print(0 if streak == 0 else min(base * 2 ** (streak - 1), cap))
PYEOF
)
BACKOFF_WAIT=${BACKOFF_WAIT:-0}

if [ "$BACKOFF_WAIT" -gt 0 ]; then
  LAST_TS=$("$PY" - "$PROFILE" <<'PYEOF' 2>/dev/null || echo ""
import json, sys
from pathlib import Path
path = Path("data") / sys.argv[1] / "auto-resume-log.jsonl"
rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
print(rows[-1]["started_at"] if rows else "")
PYEOF
)
  if [ -n "$LAST_TS" ]; then
    LAST_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$LAST_TS" "+%s" 2>/dev/null || echo 0)
    if [ "$LAST_EPOCH" -gt 0 ] && [ $(( START - LAST_EPOCH )) -lt "$BACKOFF_WAIT" ]; then
      exit 0   # still inside the backoff window: stay silent, spend nothing
    fi
  fi
fi

"$PY" scripts/collect.py --profile "$PROFILE" \
  --only-pending --pending-reasons IpBlocked,never_attempted \
  --stop-on-block --sleep 8 --pause-every 10 --pause-for 60 \
  > "$RUN_LOG" 2>&1
COLLECT_RC=$?

AFTER=$(count_raw)
NEW=$((AFTER - BEFORE))
BLOCKED=$(grep -c "IpBlocked" "$RUN_LOG" 2>/dev/null || true); BLOCKED=${BLOCKED:-0}
NO_TRACK=$(grep -c "^NO_INDONESIAN_TRACK\|Ikke\|no_indonesian" "$RUN_LOG" 2>/dev/null || true); NO_TRACK=${NO_TRACK:-0}
ELAPSED=$(( $(epoch) - START ))

"$PY" scripts/list_pending.py --profile "$PROFILE" > /dev/null 2>&1
LEFT_AFTER=$(pending_total)

record_result() {
  "$PY" - "$PROFILE" "$@" <<'PYEOF' 2>/dev/null || true
import json, sys
from pathlib import Path
profile = sys.argv[1]
keys = ["started_at", "elapsed_s", "new_captions", "blocked_hits", "no_track_hits",
        "pending_before", "pending_after", "published", "collect_rc", "note"]
row = dict(zip(keys, sys.argv[2:]))
for field in ("elapsed_s", "new_captions", "blocked_hits", "no_track_hits", "collect_rc"):
    row[field] = int(row[field])
for field in ("pending_before", "pending_after"):
    row[field] = int(row[field]) if row[field].isdigit() else None
row["published"] = row["published"] == "1"
path = Path("data") / profile / "auto-resume-log.jsonl"
with path.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
PYEOF
}

if [ "$NEW" -le 0 ]; then
  record_result "$STARTED_AT" "$ELAPSED" 0 "$BLOCKED" "$NO_TRACK" "$LEFT_BEFORE" "$LEFT_AFTER" 0 "$COLLECT_RC" "no_new_captions"
  if [ "$LEFT_AFTER" = "0" ]; then
    echo "Corpus '$PROFILE': all candidates handled, nothing left to fetch. This cron job can be removed."
  fi
  exit 0   # silent on a quiet tick
fi

for step in analyze export build_ui; do
  "$PY" "scripts/$step.py" --profile "$PROFILE" > /dev/null 2>&1 || {
    echo "auto-resume: $step failed for profile '$PROFILE'"; exit 1; }
done
"$PY" scripts/report.py --profile "$PROFILE" > /dev/null 2>&1 || true

EVENTS=$("$PY" - "$PROFILE" <<'PYEOF' 2>/dev/null || echo "?"
import json, sys
from pathlib import Path
t = json.loads((Path("data") / sys.argv[1] / "analysis.json").read_text(encoding="utf-8"))["totals"]
print(f"{t['unique_speech_events']} {t['total_tokens']}")
PYEOF
)

git add README.md "RESEARCH-PACK-$PROFILE.md" RESEARCH-PACK.md index.html "$PROFILE.html" \
        scripts data/"$PROFILE" > /dev/null 2>&1

"$PY" - "$PROFILE" <<'PYEOF'
import re, subprocess, sys
profile = sys.argv[1]
files = subprocess.check_output(["git","diff","--cached","--name-only","--diff-filter=ACMR"], text=True).splitlines()
patterns = [re.compile(r"ghp_[A-Za-z0-9_]{20,}"), re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
            re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), re.compile(r"sk-[A-Za-z0-9]{20,}")]
hits = [(n, p.pattern) for n in files for p in patterns
        if p.search(subprocess.check_output(["git","show",":"+n]).decode("utf-8","ignore"))]
bad = [n for n in files if "/raw/" in n or n.endswith("manifest.json") or n.endswith(".log") or n.endswith(".jsonl")]
if hits or bad:
    print(f"auto-resume: refusing to commit, hits={hits} bad={bad}")
    sys.exit(1)
PYEOF
if [ $? -ne 0 ]; then git reset > /dev/null 2>&1; echo "auto-resume: guard tripped, nothing published"; exit 1; fi

if git diff --cached --quiet; then
  record_result "$STARTED_AT" "$ELAPSED" "$NEW" "$BLOCKED" "$NO_TRACK" "$LEFT_BEFORE" "$LEFT_AFTER" 0 "$COLLECT_RC" "no_derived_change"
  echo "Corpus '$PROFILE': +${NEW} caption(s) but derived data unchanged."
  exit 0
fi

git -c user.name=himanusia -c user.email=19623185@std.stei.itb.ac.id commit -q \
  -m "chore(${PROFILE}): auto-resume fetch, ${NEW} new caption(s)

Collected by scripts/auto_resume.sh on a scheduled gentle session.
YouTube 429 stopped the run at the usual point; the script exits instead of
cooling down so the allowance recovers.
corpus now: ${EVENTS}" || { echo "auto-resume: commit failed"; exit 1; }

GIT_TERMINAL_PROMPT=0 git push -q origin HEAD:main 2>/dev/null
PUSHED=$?
record_result "$STARTED_AT" "$ELAPSED" "$NEW" "$BLOCKED" "$NO_TRACK" "$LEFT_BEFORE" "$LEFT_AFTER" \
  "$([ $PUSHED -eq 0 ] && echo 1 || echo 0)" "$COLLECT_RC" \
  "$([ $PUSHED -eq 0 ] && echo pushed || echo push_failed)"

if [ $PUSHED -ne 0 ]; then
  echo "Corpus '$PROFILE': +${NEW} caption(s), committed but push FAILED (check auth)"
  exit 1
fi
echo "Corpus '$PROFILE': +${NEW} caption(s) published. ${EVENTS} events, ${LEFT_AFTER} candidate(s) pending."
exit 0
