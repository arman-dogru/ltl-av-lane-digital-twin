"""Seed-stability check: how the paired estimate and its 95% CI evolve with the number of seeds.
Uses the 30-seed baseline grid (greedy - human_only, both scenarios) and the 10-seed CP-SAT runs (cpsat - human_only).
Writes results/seed_stability.md and results/seed_stability.png."""
import glob, numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
df = pd.concat([pd.read_csv(f) for f in glob.glob("results/grid_*.csv")]).drop_duplicates(["scenario", "policy", "seed"])
df = df[~df.scenario.str.contains("@")]
def paired(sc, p, metric, scale=1.0):
    a = df[(df.scenario == sc) & (df.policy == p)].set_index("seed")[metric]; b = df[(df.scenario == sc) & (df.policy == "human_only")].set_index("seed")[metric]
    idx = sorted(a.index.intersection(b.index)); return scale * (a.loc[idx] - b.loc[idx]).to_numpy()
def path(d):
    out = []
    for n in range(3, len(d) + 1):
        x = d[:n]; h = stats.t.ppf(.975, n - 1) * x.std(ddof=1) / np.sqrt(n); out.append((n, x.mean(), h))
    return out
rows, fig = [], plt.figure(figsize=(12, 4)); axes = fig.subplots(1, 2)
for j, (metric, lab, scale) in enumerate([("cost_per_pallet", "Δ cost/pallet $", 1.0), ("on_time", "Δ on-time pp", 100.0)]):
    for sc in ("balanced", "imbalanced"):
        for p in ("greedy_av_first", "cpsat"):
            d = paired(sc, p, metric, scale)
            if len(d) < 3: continue
            P = path(d); n, m, h = zip(*P); full_m, full_h = m[-1], h[-1]
            # first n after which the running mean stays inside the final CI
            stable = next((n[i] for i in range(len(n)) if all(abs(mm - full_m) <= full_h for mm in m[i:])), n[-1])
            rows.append(dict(metric=lab, scenario=sc, policy=p, seeds=len(d), final=f"{full_m:.2f} ± {full_h:.2f}",
                             at_5=f"{m[2]:.2f} ± {h[2]:.2f}" if len(m) > 2 else "—", at_10=f"{m[7]:.2f} ± {h[7]:.2f}" if len(m) > 7 else "—", stable_from_n=stable))
            axes[j].plot(n, m, label=f"{p} / {sc}"); axes[j].fill_between(n, np.array(m) - h, np.array(m) + h, alpha=.15)
    axes[j].set_xlabel("seeds"); axes[j].set_ylabel(lab + " vs human_only"); axes[j].grid(alpha=.3)
axes[0].legend(fontsize=8); fig.tight_layout(); fig.savefig("results/seed_stability.png", dpi=110)
t = pd.DataFrame(rows); md = "| metric | scenario | policy | seeds | final (mean ± 95% CI) | at 5 seeds | at 10 seeds | running mean inside final CI from n = |\n|---|---|---|---|---|---|---|---|\n"
md += "\n".join(f"| {r.metric} | {r.scenario} | {r.policy} | {r.seeds} | {r.final} | {r.at_5} | {r.at_10} | {r.stable_from_n} |" for r in t.itertuples())
open("results/seed_stability.md", "w").write(md + "\n"); print(md)
