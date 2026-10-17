"""Baseline comparison over N seeds (common random numbers: same seed -> same demand for every policy).
Reports mean and 95% t-CI; paired differences vs human_only."""
import json, sys, numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, ".")
from ltltwin.config import Config
from ltltwin.sim import Twin
from ltltwin.policies import HumanOnly, AVFixed, GreedyAVFirst
from ltltwin.kpi import kpis
N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
rows = [dict(policy=P.name, seed=s, **kpis(Twin(Config(), P(), seed=s).run())) for s in range(N) for P in (HumanOnly, AVFixed, GreedyAVFirst)]
df = pd.DataFrame(rows); df.to_csv("results/baselines_runs.csv", index=False)
cols = ["on_time", "dwell_mean_h", "fill_av", "fill_human", "av_share_pallets", "av_util", "human_trips", "cost_per_pallet", "cost_incl_late_per_pallet"]
def ci(x): x = np.asarray(x, float); x = x[~np.isnan(x)]; h = stats.t.ppf(.975, len(x)-1) * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else np.nan; return f"{x.mean():.3f} ± {h:.3f}"
tab = df.groupby("policy")[cols].agg(ci).T; print(tab.to_string())
base = df[df.policy == "human_only"].set_index("seed")
for p in ("av_fixed", "greedy_av_first"):
    d = df[df.policy == p].set_index("seed")
    print(p, "paired Δon_time", ci(d.on_time - base.on_time), "Δcost/pallet", ci(d.cost_per_pallet - base.cost_per_pallet))
