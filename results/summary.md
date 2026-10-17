
### balanced

| policy | seeds | on-time | cost/pallet $ | cost+late/pallet $ | dwell h | AV fill | human fill | AV pallet share | AV util | human trips |
|---|---|---|---|---|---|---|---|---|---|---|
| human_only | 30 | 0.926 ± 0.002 | 33.81 ± 0.16 | 35.17 ± 0.18 | 1.79 ± 0.01 | — | 0.802 ± 0.004 | 0.000 ± 0.000 | 0.000 ± 0.000 | 402 ± 4 |
| av_fixed | 30 | 0.913 ± 0.002 | 32.60 ± 0.19 | 34.20 ± 0.21 | 2.36 ± 0.01 | 0.538 ± 0.017 | 0.840 ± 0.005 | 0.075 ± 0.002 | 0.313 ± 0.004 | 355 ± 3 |
| greedy_av_first | 30 | 0.919 ± 0.003 | 30.57 ± 0.19 | 32.06 ± 0.22 | 2.23 ± 0.02 | 0.882 ± 0.006 | 0.816 ± 0.006 | 0.173 ± 0.003 | 0.467 ± 0.006 | 327 ± 4 |

Paired difference vs human_only (balanced; same seeds = same demand)

| policy | seeds | Δ on-time (pp) | Δ cost/pallet $ | Δ dwell h |
|---|---|---|---|---|
| av_fixed | 30 | -1.28 ± 0.13 | -1.21 ± 0.12 | 0.57 ± 0.01 |
| greedy_av_first | 30 | -0.68 ± 0.13 | -3.24 ± 0.12 | 0.44 ± 0.01 |

### imbalanced

| policy | seeds | on-time | cost/pallet $ | cost+late/pallet $ | dwell h | AV fill | human fill | AV pallet share | AV util | human trips |
|---|---|---|---|---|---|---|---|---|---|---|
| human_only | 30 | 0.924 ± 0.002 | 33.69 ± 0.18 | 35.09 ± 0.20 | 1.77 ± 0.01 | — | 0.803 ± 0.005 | 0.000 ± 0.000 | 0.000 ± 0.000 | 401 ± 5 |
| av_fixed | 30 | 0.915 ± 0.002 | 32.68 ± 0.20 | 34.24 ± 0.23 | 2.31 ± 0.02 | 0.546 ± 0.017 | 0.836 ± 0.005 | 0.076 ± 0.003 | 0.309 ± 0.004 | 356 ± 4 |
| greedy_av_first | 30 | 0.920 ± 0.002 | 31.11 ± 0.20 | 32.58 ± 0.21 | 2.16 ± 0.02 | 0.880 ± 0.007 | 0.813 ± 0.005 | 0.155 ± 0.004 | 0.420 ± 0.009 | 334 ± 4 |

Paired difference vs human_only (imbalanced; same seeds = same demand)

| policy | seeds | Δ on-time (pp) | Δ cost/pallet $ | Δ dwell h |
|---|---|---|---|---|
| av_fixed | 30 | -0.86 ± 0.12 | -1.01 ± 0.13 | 0.54 ± 0.01 |
| greedy_av_first | 30 | -0.39 ± 0.15 | -2.58 ± 0.13 | 0.40 ± 0.01 |
