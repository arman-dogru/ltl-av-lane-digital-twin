# Dallas–Houston autonomous LTL lane digital twin

**Status: in progress (session 1 of several).** The simulator core, the three baseline policies and the invariant tests are done. The optimizing dispatcher, the disruption experiments, the sweeps and the full write-up come next (see `/workspace/projects/progress.md`).

This is a SimPy discrete-event model of an LTL network around one autonomous linehaul lane (Dallas ↔ Houston terminals plus 3P endpoints). It is used to compare policies for deciding which consolidated freight rides an AV truck and which rides a human-driven one. All parameters are explicit assumptions in `ltltwin/config.py`, not Waabi, Volvo or Warp figures. The context is the [Volvo × Waabi customer operations with Warp on Dallas–Houston](https://waabi.ai/insights/volvo-and-waabi-kick-off-customer-operations-in-texas-starting-with-warp) (Oct 5, 2026).

## Layout
- `ltltwin/config.py`: every assumption (network, docks, AV hours and fleet, costs, demand profile, SLAs, disruptions).
- `ltltwin/sim.py`: shipments → inbound dock (door contention) → pool → linehaul (AV or human, direct-to-3P allowed) → destination dock or final mile.
- `ltltwin/policies.py`: `HumanOnly`, `AVFixed` (fixed headway), `GreedyAVFirst` (fill threshold plus empty repositioning).
- `ltltwin/kpi.py`: on-time %, dwell, trailer fill, AV utilization and share, cost per pallet (with and without late penalty).
- `tests/`: conservation, trailer capacity, AV operating window and weather hold, determinism, and that AV fleet = 0 reduces to human-only.

## Preliminary baselines (20 seeds, common random numbers, mean ± 95% CI)
| KPI | human_only | av_fixed (4 h) | greedy_av_first |
|---|---|---|---|
| on-time | 0.984 ± 0.001 | 0.974 ± 0.001 | 0.979 ± 0.001 |
| cost / pallet ($) | 30.70 ± 0.08 | 29.94 ± 0.13 | 28.12 ± 0.14 |
| AV trailer fill | — | 0.66 | 0.93 |
| AV share of pallets | 0 | 9.5% | 18.3% |
| mean dwell (h) | 1.90 | 2.63 | 2.51 |

These are preliminary: the SLA and demand defaults are not yet calibrated (human-only on-time is near the ceiling).

```bash
uv venv .venv && uv pip install --python .venv/bin/python simpy numpy pandas scipy ortools pytest
.venv/bin/python -m pytest -q tests
.venv/bin/python experiments/baselines.py 20
```
