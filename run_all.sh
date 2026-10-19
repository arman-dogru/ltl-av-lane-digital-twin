#!/usr/bin/env bash
# Full experiment pipeline (resumable; re-run to continue). Baselines take seconds, CP-SAT ~1-3 min per run per worker.
# The review/main/ablations grids share one CSV per grid; summarize.py merges them (deduplicated by scenario, policy, seed).
set -e; cd "$(dirname "$0")"; P=.venv/bin/python; W=${WORKERS:-4}
$P experiments/run_grid.py baselines $W
$P experiments/run_grid.py review $W
$P experiments/run_grid.py main $W
$P experiments/run_grid.py ablations $W
$P experiments/disruptions.py $W
$P experiments/summarize.py > /dev/null && $P experiments/plot_disruptions.py
$P experiments/export_schedule.py
$P scripts/make_figures.py
echo ALL_DONE
