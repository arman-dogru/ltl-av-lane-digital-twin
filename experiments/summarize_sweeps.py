"""Sensitivity sweeps (balanced, seeds 0-4): per setting, mean ± 95% t-CI and paired Δ vs human_only under the SAME setting.
The default setting (av_fleet=2, av_hours=(5,21), av $1.60/mi, demand 1.0) is taken from the main grids (seeds 0-4)."""
import glob, numpy as np, pandas as pd
from scipy import stats
df = pd.concat([pd.read_csv(f) for f in glob.glob("results/grid_*.csv")]).drop_duplicates(["scenario", "policy", "seed"])
base = df[(df.scenario == "balanced") & (df.seed < 5) & df.policy.isin(["human_only", "greedy_av_first", "cpsat"])].copy(); base["scenario"] = "balanced@default"
d = pd.concat([df[df.scenario.str.startswith("balanced@") & (df.seed < 5)], base]); d["setting"] = d.scenario.str.split("@").str[1]
def ci(x, k=2):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 2: return "—"
    return f"{x.mean():.{k}f} ± {stats.t.ppf(.975, len(x)-1) * x.std(ddof=1) / np.sqrt(len(x)):.{k}f}"
order = ["av_fleet=0", "av_fleet=1", "default", "av_fleet=3", "av_fleet=4", "av_fleet=6", "av_hours=(6,18)", "av_hours=(0,24)",
         "av_cost_per_mile=1.2", "av_cost_per_mile=2.0", "av_cost_per_mile=2.3", "demand=0.7", "demand=1.3"]
out = ["| setting | policy | seeds | on-time | cost/pallet $ | AV pallet share | Δ cost/pallet vs human_only $ | Δ on-time vs human_only pp |", "|---|---|---|---|---|---|---|---|"]
for st in [o for o in order if o in set(d.setting)]:
    g = d[d.setting == st]; h = g[g.policy == "human_only"].set_index("seed")
    for p in ("human_only", "greedy_av_first", "cpsat"):
        x = g[g.policy == p].set_index("seed")
        if x.empty: continue
        idx = x.index.intersection(h.index)
        dc = ci(x.loc[idx, "cost_per_pallet"] - h.loc[idx, "cost_per_pallet"]) if p != "human_only" else "—"
        do = ci(100 * (x.loc[idx, "on_time"] - h.loc[idx, "on_time"])) if p != "human_only" else "—"
        out.append(f"| {st} | {p} | {len(x)} | {ci(x.on_time, 3)} | {ci(x.cost_per_pallet)} | {ci(x.av_share_pallets, 3)} | {dc} | {do} |")
open("results/sweeps.md", "w").write("\n".join(out) + "\n"); print("\n".join(out))
