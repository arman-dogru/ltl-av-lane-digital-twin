#!/usr/bin/env bash
# Follow-up pipeline for PR "Fixes #2" (resumable). WORKERS default 6 (8-core box, ~100 MB per worker).
set -e; cd "$(dirname "$0")"; P=.venv/bin/python; W=${WORKERS:-6}
exec > >(tee results/followup.log) 2>&1   # log: results/followup.log
$P experiments/run_grid.py review10 $W
$P experiments/run_grid.py sweeps $W
SEEDS=20 $P experiments/disruptions.py $W
$P experiments/summarize.py > /dev/null && $P experiments/plot_disruptions.py
echo FOLLOWUP_DONE
