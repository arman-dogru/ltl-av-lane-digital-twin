Source files: grid_baselines.csv (human_only/av_fixed/greedy, seeds 0-29); grid_review.csv (balanced cpsat seeds 0-4 + floor/no-AV variants seeds 0-4); grid_review10.csv (floor/no-AV variants seeds 5-9); grid_main.csv (balanced cpsat seeds 5-9, imbalanced cpsat seeds 0-9); grid_ablations.csv (ablations seeds 0-4). The runner never re-runs a finished cell, so the balanced cpsat seeds are split: 0-4 in grid_review.csv, 5-9 in grid_main.csv.


### balanced

| policy | seeds | on-time | cost/pallet $ | cost+late/pallet $ | dwell h | AV fill | human fill | AV pallet share | AV util | human trips |
|---|---|---|---|---|---|---|---|---|---|---|
| human_only | 30 | 0.926 ± 0.002 | 33.81 ± 0.16 | 35.17 ± 0.18 | 1.79 ± 0.01 | — | 0.802 ± 0.004 | 0.000 ± 0.000 | 0.000 ± 0.000 | 402 ± 4 |
| av_fixed | 30 | 0.913 ± 0.002 | 32.60 ± 0.19 | 34.20 ± 0.21 | 2.36 ± 0.01 | 0.538 ± 0.017 | 0.840 ± 0.005 | 0.075 ± 0.002 | 0.313 ± 0.004 | 355 ± 3 |
| greedy_av_first | 30 | 0.919 ± 0.003 | 30.57 ± 0.19 | 32.06 ± 0.22 | 2.23 ± 0.02 | 0.882 ± 0.006 | 0.816 ± 0.006 | 0.173 ± 0.003 | 0.467 ± 0.006 | 327 ± 4 |
| cpsat | 10 | 0.904 ± 0.003 | 24.91 ± 0.18 | 26.69 ± 0.15 | 4.76 ± 0.09 | 0.961 ± 0.007 | 0.981 ± 0.008 | 0.217 ± 0.005 | 0.548 ± 0.004 | 257 ± 6 |
| cpsat_floor_av | 10 | 0.912 ± 0.002 | 24.68 ± 0.08 | 26.30 ± 0.09 | 6.20 ± 0.08 | 0.982 ± 0.004 | 0.986 ± 0.004 | 0.223 ± 0.003 | 0.554 ± 0.003 | 255 ± 5 |
| cpsat_floor_human | 10 | 0.908 ± 0.003 | 24.89 ± 0.09 | 26.59 ± 0.10 | 3.92 ± 0.04 | 0.961 ± 0.006 | 0.982 ± 0.005 | 0.218 ± 0.004 | 0.551 ± 0.003 | 257 ± 5 |
| cpsat_floor_x0.5 | 10 | 0.915 ± 0.003 | 24.97 ± 0.18 | 26.54 ± 0.14 | 6.12 ± 0.15 | 0.986 ± 0.003 | 0.975 ± 0.007 | 0.216 ± 0.006 | 0.540 ± 0.008 | 260 ± 8 |
| cpsat_floor_x1.5 | 10 | 0.907 ± 0.003 | 25.01 ± 0.13 | 26.71 ± 0.13 | 3.83 ± 0.10 | 0.955 ± 0.006 | 0.978 ± 0.007 | 0.217 ± 0.004 | 0.549 ± 0.003 | 258 ± 4 |
| cpsat_h12 | 5 | 0.906 ± 0.006 | 25.04 ± 0.12 | 26.77 ± 0.12 | 3.84 ± 0.08 | 0.929 ± 0.007 | 0.984 ± 0.009 | 0.211 ± 0.007 | 0.545 ± 0.003 | 257 ± 11 |
| cpsat_h4 | 5 | 0.904 ± 0.005 | 25.70 ± 0.21 | 27.47 ± 0.29 | 4.69 ± 0.10 | 0.966 ± 0.016 | 0.954 ± 0.010 | 0.209 ± 0.016 | 0.518 ± 0.024 | 266 ± 14 |
| cpsat_myopic | 5 | 0.901 ± 0.006 | 25.69 ± 0.31 | 27.51 ± 0.31 | 3.05 ± 0.10 | 0.979 ± 0.015 | 0.985 ± 0.007 | 0.153 ± 0.009 | 0.381 ± 0.015 | 275 ± 13 |
| cpsat_noav | 10 | 0.932 ± 0.003 | 32.40 ± 0.30 | 33.65 ± 0.28 | 2.57 ± 0.06 | — | 0.834 ± 0.008 | 0.000 ± 0.000 | 0.000 ± 0.000 | 386 ± 5 |
| cpsat_nodirect | 5 | 0.903 ± 0.003 | 24.86 ± 0.15 | 26.66 ± 0.17 | 4.77 ± 0.16 | 0.964 ± 0.012 | 0.982 ± 0.009 | 0.220 ± 0.009 | 0.551 ± 0.004 | 255 ± 12 |
| cpsat_norepo | 5 | 0.903 ± 0.003 | 24.87 ± 0.16 | 26.66 ± 0.18 | 4.77 ± 0.16 | 0.964 ± 0.012 | 0.982 ± 0.009 | 0.219 ± 0.009 | 0.551 ± 0.004 | 255 ± 12 |
| cpsat_warm | 5 | 0.900 ± 0.005 | 24.81 ± 0.11 | 26.65 ± 0.13 | 4.79 ± 0.11 | 0.961 ± 0.015 | 0.987 ± 0.008 | 0.219 ± 0.010 | 0.551 ± 0.007 | 254 ± 12 |

Paired difference vs human_only (balanced; same seeds = same demand)

| policy | seeds | Δ on-time (pp) | Δ cost/pallet $ | Δ dwell h |
|---|---|---|---|---|
| av_fixed | 30 | -1.28 ± 0.13 | -1.21 ± 0.12 | 0.57 ± 0.01 |
| greedy_av_first | 30 | -0.68 ± 0.13 | -3.24 ± 0.12 | 0.44 ± 0.01 |
| cpsat | 10 | -2.25 ± 0.28 | -8.81 ± 0.30 | 2.97 ± 0.09 |
| cpsat_floor_av | 10 | -1.39 ± 0.31 | -9.04 ± 0.31 | 4.41 ± 0.09 |
| cpsat_floor_human | 10 | -1.81 ± 0.21 | -8.83 ± 0.31 | 2.13 ± 0.04 |
| cpsat_floor_x0.5 | 10 | -1.13 ± 0.28 | -8.76 ± 0.29 | 4.33 ± 0.16 |
| cpsat_floor_x1.5 | 10 | -1.87 ± 0.28 | -8.72 ± 0.32 | 2.04 ± 0.10 |
| cpsat_h12 | 5 | -2.01 ± 0.61 | -8.71 ± 0.63 | 2.05 ± 0.10 |
| cpsat_h4 | 5 | -2.23 ± 0.46 | -8.05 ± 0.58 | 2.91 ± 0.11 |
| cpsat_myopic | 5 | -2.53 ± 0.73 | -8.07 ± 0.52 | 1.27 ± 0.12 |
| cpsat_noav | 10 | 0.62 ± 0.21 | -1.33 ± 0.34 | 0.78 ± 0.07 |
| cpsat_nodirect | 5 | -2.39 ± 0.43 | -8.89 ± 0.73 | 2.98 ± 0.18 |
| cpsat_norepo | 5 | -2.38 ± 0.43 | -8.88 ± 0.73 | 2.99 ± 0.18 |
| cpsat_warm | 5 | -2.63 ± 0.55 | -8.94 ± 0.66 | 3.01 ± 0.12 |

### imbalanced

| policy | seeds | on-time | cost/pallet $ | cost+late/pallet $ | dwell h | AV fill | human fill | AV pallet share | AV util | human trips |
|---|---|---|---|---|---|---|---|---|---|---|
| human_only | 30 | 0.924 ± 0.002 | 33.69 ± 0.18 | 35.09 ± 0.20 | 1.77 ± 0.01 | — | 0.803 ± 0.005 | 0.000 ± 0.000 | 0.000 ± 0.000 | 401 ± 5 |
| av_fixed | 30 | 0.915 ± 0.002 | 32.68 ± 0.20 | 34.24 ± 0.23 | 2.31 ± 0.02 | 0.546 ± 0.017 | 0.836 ± 0.005 | 0.076 ± 0.003 | 0.309 ± 0.004 | 356 ± 4 |
| greedy_av_first | 30 | 0.920 ± 0.002 | 31.11 ± 0.20 | 32.58 ± 0.21 | 2.16 ± 0.02 | 0.880 ± 0.007 | 0.813 ± 0.005 | 0.155 ± 0.004 | 0.420 ± 0.009 | 334 ± 4 |
| cpsat | 10 | 0.882 ± 0.006 | 25.38 ± 0.38 | 27.54 ± 0.31 | 5.11 ± 0.13 | 0.955 ± 0.008 | 0.970 ± 0.013 | 0.209 ± 0.005 | 0.535 ± 0.011 | 264 ± 6 |

Paired difference vs human_only (imbalanced; same seeds = same demand)

| policy | seeds | Δ on-time (pp) | Δ cost/pallet $ | Δ dwell h |
|---|---|---|---|---|
| av_fixed | 30 | -0.86 ± 0.12 | -1.01 ± 0.13 | 0.54 ± 0.01 |
| greedy_av_first | 30 | -0.39 ± 0.15 | -2.58 ± 0.13 | 0.40 ± 0.01 |
| cpsat | 10 | -3.69 ± 0.40 | -8.46 ± 0.36 | 3.35 ± 0.13 |

### CP-SAT solver health

| variant | runs | solves | time-limited (feasible, not proven optimal) | fallbacks to greedy |
|---|---|---|---|---|
| cpsat | 20 | 13505 | 0.4% | 0.00% |
| cpsat_floor_av | 10 | 6847 | 0.5% | 0.00% |
| cpsat_floor_human | 10 | 6809 | 0.2% | 0.00% |
| cpsat_floor_x0.5 | 10 | 6866 | 0.7% | 0.00% |
| cpsat_floor_x1.5 | 10 | 6772 | 1.9% | 0.00% |
| cpsat_h12 | 5 | 3375 | 0.4% | 0.00% |
| cpsat_h4 | 5 | 3370 | 0.0% | 0.00% |
| cpsat_myopic | 5 | 3389 | 0.0% | 0.00% |
| cpsat_noav | 10 | 6462 | 0.0% | 0.00% |
| cpsat_nodirect | 5 | 3416 | 0.1% | 0.00% |
| cpsat_norepo | 5 | 3416 | 0.1% | 0.00% |
| cpsat_warm | 5 | 3415 | 0.1% | 0.00% |

Paired difference vs greedy_av_first (balanced)

| policy | seeds | Δ on-time (pp) | Δ cost/pallet $ | Δ dwell h |
|---|---|---|---|---|
| cpsat | 10 | -1.43 ± 0.18 | -5.69 ± 0.44 | 2.54 ± 0.10 |
| cpsat_floor_av | 10 | -0.58 ± 0.25 | -5.92 ± 0.45 | 3.98 ± 0.10 |
| cpsat_floor_human | 10 | -0.99 ± 0.26 | -5.71 ± 0.41 | 1.70 ± 0.05 |
| cpsat_floor_x0.5 | 10 | -0.32 ± 0.18 | -5.63 ± 0.40 | 3.90 ± 0.15 |
| cpsat_floor_x1.5 | 10 | -1.05 ± 0.25 | -5.60 ± 0.45 | 1.61 ± 0.11 |
| cpsat_h12 | 5 | -1.10 ± 0.42 | -5.71 ± 0.94 | 1.62 ± 0.13 |
| cpsat_h4 | 5 | -1.33 ± 0.38 | -5.05 ± 0.82 | 2.47 ± 0.10 |
| cpsat_myopic | 5 | -1.63 ± 0.51 | -5.07 ± 0.92 | 0.83 ± 0.15 |
| cpsat_noav | 10 | 1.44 ± 0.23 | 1.80 ± 0.42 | 0.34 ± 0.09 |
| cpsat_nodirect | 5 | -1.48 ± 0.41 | -5.89 ± 0.99 | 2.55 ± 0.20 |
| cpsat_norepo | 5 | -1.48 ± 0.40 | -5.89 ± 1.00 | 2.55 ± 0.20 |
| cpsat_warm | 5 | -1.72 ± 0.46 | -5.94 ± 0.89 | 2.57 ± 0.12 |

Paired difference vs greedy_av_first (imbalanced)

| policy | seeds | Δ on-time (pp) | Δ cost/pallet $ | Δ dwell h |
|---|---|---|---|---|
| cpsat | 10 | -3.32 ± 0.45 | -5.77 ± 0.39 | 2.96 ± 0.13 |

## Disruption case study (balanced, day-7 events; freight created days 7-8; paired vs same seed undisturbed)

| case | policy | seeds | window on-time | Δ vs undisturbed (pp) | peak excess backlog (pallets) | excess pallet-hours |
|---|---|---|---|---|---|---|
| none | human_only | 8 | 0.930 ± 0.006 | — | — | — |
| none | greedy_av_first | 8 | 0.917 ± 0.009 | — | — | — |
| none | cpsat | 8 | 0.905 ± 0.013 | — | — | — |
| weather | human_only | 8 | 0.930 ± 0.006 | 0.00 ± 0.00 | 0 ± 0 | 0 ± 0 |
| weather | greedy_av_first | 8 | 0.914 ± 0.010 | -0.30 ± 0.65 | 53 ± 10 | 292 ± 63 |
| weather | cpsat | 8 | 0.917 ± 0.010 | 1.25 ± 0.89 | 38 ± 15 | 448 ± 186 |
| dock | human_only | 8 | 0.930 ± 0.006 | -0.03 ± 0.08 | 35 ± 7 | 55 ± 15 |
| dock | greedy_av_first | 8 | 0.917 ± 0.009 | -0.00 ± 0.27 | 50 ± 14 | 120 ± 45 |
| dock | cpsat | 8 | 0.904 ± 0.013 | -0.10 ± 0.29 | 44 ± 16 | 262 ± 190 |
| surge | human_only | 8 | 0.900 ± 0.013 | -3.02 ± 1.66 | 50 ± 3 | 602 ± 74 |
| surge | greedy_av_first | 8 | 0.895 ± 0.014 | -2.14 ± 1.74 | 68 ± 12 | 782 ± 190 |
| surge | cpsat | 8 | 0.882 ± 0.016 | -2.27 ± 2.33 | 87 ± 14 | 1109 ± 468 |
| combined | human_only | 8 | 0.899 ± 0.013 | -3.12 ± 1.65 | 52 ± 6 | 592 ± 70 |
| combined | greedy_av_first | 8 | 0.890 ± 0.011 | -2.66 ± 1.56 | 77 ± 13 | 876 ± 182 |
| combined | cpsat | 8 | 0.884 ± 0.014 | -2.02 ± 2.00 | 94 ± 12 | 1097 ± 395 |
