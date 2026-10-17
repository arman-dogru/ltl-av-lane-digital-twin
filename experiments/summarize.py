"""Tables (mean ± 95% t-CI over seeds) and paired differences vs human_only, from results/grid_*.csv -> results/summary.md.
Only completed cells are reported, with their seed counts."""
import glob, numpy as np, pandas as pd
from scipy import stats
df = pd.concat([pd.read_csv(f) for f in glob.glob("results/grid_*.csv")], ignore_index=True).drop_duplicates(["scenario", "policy", "seed"])
K = [("on_time", "on-time", 3), ("cost_per_pallet", "cost/pallet $", 2), ("cost_incl_late_per_pallet", "cost+late/pallet $", 2), ("dwell_mean_h", "dwell h", 2),
     ("fill_av", "AV fill", 3), ("fill_human", "human fill", 3), ("av_share_pallets", "AV pallet share", 3), ("av_util", "AV util", 3), ("human_trips", "human trips", 0)]
def ci(x, d):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 2: return "—"
    h = stats.t.ppf(.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)); return f"{x.mean():.{d}f} ± {h:.{d}f}"
order = ["human_only", "av_fixed", "greedy_av_first", "cpsat"]; out = []
for sc in ("balanced", "imbalanced"):
    d = df[df.scenario == sc]; pols = [p for p in order if p in set(d.policy)] + sorted(p for p in set(d.policy) if p not in order)
    out += [f"\n### {sc}\n", "| policy | seeds | " + " | ".join(k[1] for k in K) + " |", "|---" * (len(K) + 2) + "|"]
    for p in pols:
        g = d[d.policy == p]; out.append(f"| {p} | {len(g)} | " + " | ".join(ci(g[k], r) for k, _, r in K) + " |")
    base = d[d.policy == "human_only"].set_index("seed")
    out += [f"\nPaired difference vs human_only ({sc}; same seeds = same demand)\n", "| policy | seeds | Δ on-time (pp) | Δ cost/pallet $ | Δ dwell h |", "|---|---|---|---|---|"]
    for p in pols:
        if p == "human_only": continue
        g = d[d.policy == p].set_index("seed"); idx = g.index.intersection(base.index)
        if len(idx) < 2: continue
        out.append(f"| {p} | {len(idx)} | {ci(100 * (g.loc[idx, 'on_time'] - base.loc[idx, 'on_time']), 2)} | {ci(g.loc[idx, 'cost_per_pallet'] - base.loc[idx, 'cost_per_pallet'], 2)} | {ci(g.loc[idx, 'dwell_mean_h'] - base.loc[idx, 'dwell_mean_h'], 2)} |")
s = df[df.policy.str.startswith("cpsat")]
if len(s):
    out += ["\n### CP-SAT solver health\n", "| variant | runs | solves | time-limited (feasible, not proven optimal) | fallbacks to greedy |", "|---|---|---|---|---|"]
    for p, g in s.groupby("policy"):
        n = int(g.solves.sum()); out.append(f"| {p} | {len(g)} | {n} | {g.solver_nonoptimal.sum() / n:.1%} | {g.solver_fallbacks.sum() / n:.2%} |")
# vs greedy (the strongest heuristic) for CP-SAT variants
for sc in ("balanced", "imbalanced"):
    d = df[df.scenario == sc]; base = d[d.policy == "greedy_av_first"].set_index("seed"); ps = [p for p in sorted(set(d.policy)) if p.startswith("cpsat")]
    if not ps or base.empty: continue
    out += [f"\nPaired difference vs greedy_av_first ({sc})\n", "| policy | seeds | Δ on-time (pp) | Δ cost/pallet $ | Δ dwell h |", "|---|---|---|---|---|"]
    for p in ps:
        g = d[d.policy == p].set_index("seed"); idx = g.index.intersection(base.index)
        if len(idx) >= 2: out.append(f"| {p} | {len(idx)} | {ci(100 * (g.loc[idx, 'on_time'] - base.loc[idx, 'on_time']), 2)} | {ci(g.loc[idx, 'cost_per_pallet'] - base.loc[idx, 'cost_per_pallet'], 2)} | {ci(g.loc[idx, 'dwell_mean_h'] - base.loc[idx, 'dwell_mean_h'], 2)} |")
# disruption case study
import os
if os.path.exists("results/disruptions.csv"):
    z = pd.read_csv("results/disruptions.csv")
    out += ["\n## Disruption case study (balanced, day-7 events; freight created days 7-8; paired vs same seed undisturbed)\n",
            "| case | policy | seeds | window on-time | Δ vs undisturbed (pp) | peak excess backlog (pallets) | excess pallet-hours |", "|---|---|---|---|---|---|---|"]
    for c in ["none", "weather", "dock", "surge", "combined"]:
        for p in ["human_only", "greedy_av_first", "cpsat"]:
            g = z[(z.case == c) & (z.policy == p)].set_index("seed"); b = z[(z.case == "none") & (z.policy == p)].set_index("seed")
            if g.empty: continue
            idx = g.index.intersection(b.index)
            out.append(f"| {c} | {p} | {len(g)} | {ci(g.win_on_time, 3)} | {ci(100 * (g.loc[idx, 'win_on_time'] - b.loc[idx, 'win_on_time']), 2) if c != 'none' else '—'} | {ci(g.peak_excess_pallets, 0) if c != 'none' else '—'} | {ci(g.excess_pallet_hours, 0) if c != 'none' else '—'} |")
open("results/summary.md", "w").write("\n".join(out) + "\n"); print("\n".join(out))
