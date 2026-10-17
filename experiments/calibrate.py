"""Calibrate SLA window so the human-only baseline sits at ~90-95% on-time.
Uses seeds 1000-1004, disjoint from evaluation seeds (0-29), so calibration does not see eval demand."""
import sys, numpy as np, json
sys.path.insert(0, ".")
from ltltwin.config import Config
from ltltwin.sim import Twin
from ltltwin.policies import HumanOnly
from ltltwin.kpi import kpis
rows = []
for lo, hi in [(18, 30), (14, 30), (12, 28), (12, 24), (10, 24), (10, 20), (8, 20)]:
    k = [kpis(Twin(Config(sla_hours=(lo, hi)), HumanOnly(), seed=s).run()) for s in range(1000, 1005)]
    r = dict(sla=(lo, hi), on_time=round(float(np.mean([x["on_time"] for x in k])), 4), cost=round(float(np.mean([x["cost_per_pallet"] for x in k])), 2)); rows.append(r); print(r, flush=True)
json.dump(rows, open("results/calibration_sla.json", "w"), indent=1)
