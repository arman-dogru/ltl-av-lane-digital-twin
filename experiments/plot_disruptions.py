"""Mean total backlog (pallets waiting at both terminals) around the day-7 disruptions -> results/disruption_backlog.png"""
import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
T = json.load(open("results/disruption_traces.json")); cases = ["none", "weather", "dock", "surge", "combined"]
fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
for ax, p in zip(axes, ["human_only", "greedy_av_first", "cpsat"]):
    for c in cases:
        k = f"{c}|{p}"
        if k in T: ax.plot(T[k]["t_hours"][:len(T[k]["backlog"])], T[k]["backlog"], label=c, lw=1.6 if c != "none" else 2.4, color="k" if c == "none" else None)
    ax.axvspan(0, 24, color="grey", alpha=.1); ax.set_title(p); ax.set_xlabel("hours from day-7 00:00"); ax.grid(alpha=.3)
axes[0].set_ylabel("pallets waiting (mean over seeds)"); axes[-1].legend(); fig.tight_layout(); fig.savefig("results/disruption_backlog.png", dpi=120)
