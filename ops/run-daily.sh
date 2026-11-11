#!/usr/bin/env bash
# Daily run on the Hetzner box (user: hrjobs). Reads the sources, rewrites the list of open listings, and
# writes the day's report and counts. It posts nowhere and sends no mail.
#
# Two modes, chosen by whether the box holds a deploy key for this repo (/home/hrjobs/.ssh/id_ed25519):
#   no key   collect only. Results go to /home/hrjobs/collected and stay on the box.
#   key      collect and publish. Results go into the repo and are pushed to GitHub.
#
# Halt:      touch /home/hrjobs/STOP     (the run exits quietly; remove the file to resume)
# Self-halt: if more than half the company boards fail to load, the collector exits 2, nothing is written,
#            and this script creates STOP itself so a person looks before the next run.
set -euo pipefail
cd "$(dirname "$0")/.."
HOME_DIR=${HOME:-/home/hrjobs}
STOP="$HOME_DIR/STOP"
KEPT="$HOME_DIR/collected"
if [ -e "$STOP" ]; then echo "STOP file present ($STOP); not running"; exit 0; fi

DATE=$(date -u +%F)
echo "== $(date -u +%FT%TZ) hr-jobs daily run for $DATE =="
git pull --rebase --quiet

if [ -e "$HOME_DIR/.ssh/id_ed25519" ] && [ "${HRJOBS_NO_PUBLISH:-0}" != "1" ]; then
  PUBLISH=1; OUT=.
  # first publishing run after a collect-only period: continue from what the box collected
  if [ -e "$KEPT/data/current/jobs.csv" ]; then
    cp "$KEPT/data/current/jobs.csv" data/current/jobs.csv
    mv "$KEPT" "$KEPT.merged-$DATE"
  fi
else
  PUBLISH=0; OUT="$KEPT"
  echo "collect-only mode: results stay in $KEPT"
  mkdir -p "$KEPT/data/current"
  # first collect-only run: continue from the list in the repo
  [ -e "$KEPT/data/current/jobs.csv" ] || cp data/current/jobs.csv "$KEPT/data/current/jobs.csv"
fi

rc=0
python3 -m hrjobs.collect --date "$DATE" --out "$OUT" || rc=$?
if [ "$rc" -eq 2 ]; then
  echo "self-halt: writing $STOP"
  date -u +"%FT%TZ collector exit 2 (more than half the boards failed)" > "$STOP"
  exit 0
elif [ "$rc" -ne 0 ]; then
  echo "collector failed with exit $rc"; exit "$rc"
fi

if [ "$PUBLISH" = "1" ]; then
  git add -- data/current/jobs.csv "data/summary/$DATE.json" "reports/$DATE.md" reports/latest.md
  if git diff --cached --quiet; then echo "nothing new to commit"; else
    git commit -q -m "Daily HR job collection $DATE (run on the Hetzner box)"
    git pull --rebase --quiet
    git push --quiet
    echo "pushed listings and report for $DATE"
  fi
fi
echo "== done $(date -u +%FT%TZ) =="
