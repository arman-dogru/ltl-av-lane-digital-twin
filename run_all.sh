#!/usr/bin/env bash
# Full experiment pipeline (resumable). ~1 min per CP-SAT run per worker; baselines are seconds.
set -e; cd "$(dirname "$0")"; P=.venv/bin/python; W=${WORKERS:-4}
$P experiments/run_grid.py baselines $W
$P experiments/run_grid.py main $W
$P experiments/run_grid.py ablations $W
echo ALL_DONE
