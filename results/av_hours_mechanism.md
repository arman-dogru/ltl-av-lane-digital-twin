## A. Paired 24 h − 16 h (CP-SAT, balanced, same seeds; mean ± 95% t-CI)

| seeds | Δ cost/pallet $ | Δ on-time pp | Δ dwell h | Δ AV trips | Δ human fill |
|---|---|---|---|---|---|
| 5 | +1.18 ± 0.71 | +1.02 ± 0.70 | -0.35 ± 0.23 | +10.20 ± 1.04 | -0.071 ± 0.030 |
| 10 | +0.71 ± 0.48 | +0.56 ± 0.50 | -0.19 ± 0.17 | +10.60 ± 0.60 | -0.053 ± 0.019 |

## B. Trace (CP-SAT, balanced, seeds (0, 1, 4), after warm-up; rerun, so CP-SAT time-limit noise applies)

Human trips with < 20 pallets per run:

- 16 h (05–21): seed 0: 12, seed 1: 9, seed 4: 6
- 24 h: seed 0: 49, seed 1: 43, seed 4: 53

AV departures per 3 h local-hour bucket (sum over seeds):

| window | 00–03 | 03–06 | 06–09 | 09–12 | 12–15 | 15–18 | 18–21 | 21–24 |
|---|---|---|---|---|---|---|---|---|
| 16 h (05–21) | 0 | 23 | 55 | 1 | 74 | 0 | 71 | 1 |
| 24 h | 35 | 34 | 37 | 28 | 32 | 29 | 32 | 28 |

Human fill (mean pallets/26) by departure bucket (mean over seeds):

| window | 00–03 | 03–06 | 06–09 | 09–12 | 12–15 | 15–18 | 18–21 | 21–24 |
|---|---|---|---|---|---|---|---|---|
| 16 h (05–21) | 1.00 | 0.98 | 0.66 | 0.91 | 0.99 | 1.00 | 1.00 | 1.00 |
| 24 h | 0.98 | 0.78 | 0.51 | 0.66 | 0.92 | 0.97 | 1.00 | 1.00 |

Idle AVs (parked, not busy; of 2) sampled on the hour, mean by local hour:

| window | 00 | 02 | 04 | 06 | 08 | 10 | 12 | 14 | 16 | 18 | 20 | 22 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 16 h (05–21) | 0.29 | 1.98 | 2.00 | 0.27 | 0.27 | 0.27 | 1.71 | 0.33 | 0.33 | 0.73 | 0.42 | 0.40 |
| 24 h | 0.49 | 0.58 | 0.42 | 0.60 | 0.53 | 0.60 | 0.62 | 0.69 | 0.67 | 0.62 | 0.64 | 0.62 |
