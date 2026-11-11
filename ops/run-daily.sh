#!/usr/bin/env bash
# Daily run on the Hetzner box (user: hrjobs). Reads the sources, rewrites data/current/jobs.csv, writes the
# day's report and counts, and pushes them to GitHub. It posts nowhere else and sends no mail.
#
# Halt:      touch /home/hrjobs/STOP     (the run exits quietly; remove the file to resume)
# Self-halt: if more than half the company boards fail to load, the collector exits 2, nothing is written,
#            and this script creates STOP itself so a person looks before the next run.
set -euo pipefail
cd "$(dirname "$0")/.."
HOME_DIR=${HOME:-/home/hrjobs}
STOP="$HOME_DIR/STOP"
if [ -e "$STOP" ]; then echo "STOP file present ($STOP); not running"; exit 0; fi

DATE=$(date -u +%F)
echo "== $(date -u +%FT%TZ) hr-jobs daily run for $DATE =="
git pull --rebase --quiet

rc=0
python3 -m hrjobs.collect --date "$DATE" || rc=$?
if [ "$rc" -eq 2 ]; then
  echo "self-halt: writing $STOP"
  date -u +"%FT%TZ collector exit 2 (more than half the boards failed)" > "$STOP"
  exit 0
elif [ "$rc" -ne 0 ]; then
  echo "collector failed with exit $rc"; exit "$rc"
fi

if [ "${HRJOBS_NO_PUBLISH:-0}" = "1" ]; then echo "HRJOBS_NO_PUBLISH=1: not committing"; exit 0; fi
git add -- data/current/jobs.csv "data/summary/$DATE.json" "reports/$DATE.md" reports/latest.md
if git diff --cached --quiet; then echo "nothing new to commit"; else
  git commit -q -m "Daily HR job collection $DATE (run on the Hetzner box)"
  git pull --rebase --quiet
  git push --quiet
  echo "pushed listings and report for $DATE"
fi
echo "== done $(date -u +%FT%TZ) =="
