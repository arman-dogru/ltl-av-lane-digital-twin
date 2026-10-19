"""Render the README figures from committed result files only (no simulation runs).

Inputs : results/grid_*.csv (same merge/dedup as experiments/summarize.py), results/schedule_balanced_seed0.csv
Outputs: docs/figures/*.png
Usage  : .venv/bin/python scripts/make_figures.py
Means and 95% t-CIs use the same formula as experiments/summarize.py, so plotted values match the README tables.
"""
import glob
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"
plt.rcParams.update({"figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white", "font.size": 10,
                     "axes.titlesize": 11, "axes.titleweight": "bold", "axes.spines.top": False, "axes.spines.right": False})
COL = {"human_only": "#6e7781", "av_fixed": "#bf8700", "greedy_av_first": "#1f883d", "cpsat": "#0969da", "cpsat_noav": "#8250df"}
LAB = {"human_only": "human only", "av_fixed": "AV fixed headway", "greedy_av_first": "greedy AV-first", "cpsat": "CP-SAT", "cpsat_noav": "CP-SAT, no AVs"}
SRC = dict(fontsize=7.5, color="#555")

df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(ROOT / "results" / "grid_*.csv")))], ignore_index=True)
df = df.drop_duplicates(["scenario", "policy", "seed"])


def mci(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return x.mean(), stats.t.ppf(.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))


def paired(d, pol, col, scale=1.0, base="human_only"):
    g = d[d.policy == pol].set_index("seed"); b = d[d.policy == base].set_index("seed"); idx = g.index.intersection(b.index)
    return scale * (g.loc[idx, col] - b.loc[idx, col])


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=110, bbox_inches="tight", metadata={"Software": None}); plt.close(fig)
    print("wrote", (OUT / name).relative_to(ROOT))


def fig_tradeoff():
    """Cost per pallet vs on-time per policy (mean ± 95% t-CI over seeds), balanced and imbalanced."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for ax, sc in zip(axes, ["balanced", "imbalanced"]):
        d = df[df.scenario == sc]
        for p in ["human_only", "av_fixed", "greedy_av_first", "cpsat", "cpsat_noav"]:
            g = d[d.policy == p]
            if g.empty: continue
            (x, xe), (y, ye) = mci(100 * g.on_time), mci(g.cost_per_pallet)
            ax.errorbar(x, y, xerr=xe, yerr=ye, fmt="o", ms=8, color=COL[p], capsize=3, lw=1.5)
            left = p == "av_fixed"
            ax.annotate(f"{LAB[p]} ({len(g)} seeds)\n${y:.2f}, {x:.1f}%", (x, y), textcoords="offset points",
                        xytext=(-10, -4) if left else ((8, 4) if p != "cpsat_noav" else (8, -18)), fontsize=8, color=COL[p],
                        ha="right" if left else "left", va="top" if left else "baseline")
        ax.set_title(f"{sc} demand"); ax.set_xlabel("on-time delivery [%]"); ax.grid(alpha=.25)
        ax.set_xlim(87.5, 95.2)
    axes[0].set_ylabel("cost per pallet [$] (lower is better)")
    fig.suptitle("CP-SAT buys the lowest cost with some service; the AVs make the saving", fontweight="bold", y=1.02)
    fig.text(0.01, -0.04, "Mean ± 95% t-CI over seeds; synthetic assumptions in ltltwin/config.py. Source: results/grid_*.csv", **SRC)
    save(fig, "cost_vs_ontime.png")


def fig_paired():
    """Per-seed paired Δ cost/pallet vs human_only (common random numbers)."""
    fig, ax = plt.subplots(figsize=(8, 3.8))
    rows = [("balanced", "greedy_av_first"), ("balanced", "cpsat_noav"), ("balanced", "cpsat"),
            ("imbalanced", "greedy_av_first"), ("imbalanced", "cpsat")]
    rng = np.random.default_rng(0)
    for i, (sc, p) in enumerate(rows):
        v = paired(df[df.scenario == sc], p, "cost_per_pallet").values
        ax.scatter(v, i + rng.uniform(-.15, .15, len(v)), s=16, color=COL[p], alpha=.55, lw=0)
        m, h = mci(v)
        ax.errorbar(m, i, xerr=h, fmt="D", color="black", ms=6, capsize=4, lw=1.6, zorder=3)
        ax.text(m, i - .32, f"{m:+.2f} ± {h:.2f}  (n={len(v)})", ha="center", fontsize=8)
    ax.axvline(0, color="#444", lw=.8)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"{LAB[p]}\n{sc}" for sc, p in rows], fontsize=8.5); ax.invert_yaxis()
    ax.set_xlabel("Δ cost per pallet vs human-only, same seed = same demand [$]")
    ax.set_title("Every seed agrees: paired per-seed savings vs human-only")
    ax.text(0, -0.2, "Dots: one seed each. Diamond: mean ± 95% t-CI. Source: results/grid_*.csv", transform=ax.transAxes, **SRC)
    save(fig, "paired_seed_deltas.png")


def fig_sweeps():
    """AV fleet size and AV cost-per-mile sweeps (balanced, seeds 0-4), paired vs human_only under the same setting."""
    base = df[(df.scenario == "balanced") & (df.seed < 5)]
    def setting(s): return base if s == "default" else df[(df.scenario == f"balanced@{s}") & (df.seed < 5)]
    fleets = [(0, "av_fleet=0"), (1, "av_fleet=1"), (2, "default"), (3, "av_fleet=3"), (4, "av_fleet=4"), (6, "av_fleet=6")]
    costs = [(1.2, "av_cost_per_mile=1.2"), (1.6, "default"), (2.0, "av_cost_per_mile=2.0"), (2.3, "av_cost_per_mile=2.3")]
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    for ax, xs, col, scale, ylab in [(axes[0], fleets, "cost_per_pallet", 1, "Δ cost/pallet vs human-only [$]"),
                                     (axes[1], fleets, "on_time", 100, "Δ on-time vs human-only [pp]"),
                                     (axes[2], costs, "cost_per_pallet", 1, "Δ cost/pallet vs human-only [$]")]:
        for p in ["greedy_av_first", "cpsat"]:
            pts = []
            for x, s in xs:
                v = paired(setting(s), p, col, scale).values
                pts.append((x, *mci(v)) if np.ptp(v) > 0 else (x, v.mean(), 0.0))
            x, m, h = map(np.array, zip(*pts))
            ax.errorbar(x, m, yerr=h, marker="o", color=COL[p], capsize=3, lw=1.8, label=LAB[p])
        ax.axhline(0, color="#444", lw=.8); ax.grid(alpha=.25); ax.set_ylabel(ylab)
    axes[0].set_xlabel("AV tractors in the fleet"); axes[1].set_xlabel("AV tractors in the fleet"); axes[2].set_xlabel("AV linehaul cost [$/mile]")
    axes[0].set_title("Savings grow with fleet, with diminishing returns"); axes[1].set_title("…at a service cost under CP-SAT")
    axes[2].set_title("Still saves at human per-mile parity ($2.30)")
    for ax in axes[:2]: ax.axvline(2, color="#bbb", ls="--", lw=1)
    axes[2].axvline(1.6, color="#bbb", ls="--", lw=1)
    axes[0].legend(frameon=False, fontsize=8.5)
    fig.text(0.01, -0.06, "Balanced, seeds 0-4, mean ± 95% t-CI of paired differences; dashed = default setting. Source: results/grid_sweeps.csv + default cells", **SRC)
    fig.tight_layout(); save(fig, "sensitivity_sweeps.png")


def fig_ablations():
    """CP-SAT variants (balanced) paired vs human_only: Δ cost and Δ on-time."""
    d = df[df.scenario == "balanced"]
    rows = [("cpsat", "default (8 h horizon)"), ("cpsat_myopic", "myopic (horizon 0)"), ("cpsat_h4", "horizon 4 h"),
            ("cpsat_h12", "horizon 12 h"), ("cpsat_warm", "warm start"), ("cpsat_nodirect", "no direct-to-3P"),
            ("cpsat_norepo", "no empty repositioning"), ("cpsat_floor_x0.5", "defer floor ×0.5"), ("cpsat_floor_x1.5", "defer floor ×1.5"),
            ("cpsat_floor_human", "defer floor = human rate"), ("cpsat_floor_av", "defer floor = AV rate"), ("cpsat_noav", "no AVs (control)")]
    rows = [(p, l) for p, l in rows if p in set(d.policy)]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True)
    for ax, col, scale, xl in [(axes[0], "cost_per_pallet", 1, "Δ cost/pallet vs human-only [$]"), (axes[1], "on_time", 100, "Δ on-time vs human-only [pp]")]:
        for i, (p, l) in enumerate(rows):
            v = paired(d, p, col, scale).values; m, h = mci(v)
            c = COL["cpsat_noav"] if p == "cpsat_noav" else (COL["cpsat"] if p == "cpsat" else "#54aeff")
            ax.barh(i, m, xerr=h, color=c, height=.6, capsize=2.5)
            ax.text((m + h + 0.1) if m >= 0 else 0.1, i, f"{m:+.2f} ± {h:.2f}", va="center", ha="left", fontsize=7.5)
        ax.axvline(0, color="#444", lw=.8); ax.set_xlabel(xl); ax.grid(axis="x", alpha=.25)
    axes[0].set_xlim(-10.5, 2.6); axes[1].set_xlim(-4, 2.3)
    n = {p: len(paired(d, p, "cost_per_pallet")) for p, _ in rows}
    axes[0].set_yticks(range(len(rows))); axes[0].set_yticklabels([f"{l}  (n={n[p]})" for p, l in rows], fontsize=8.5); axes[0].invert_yaxis()
    fig.suptitle("CP-SAT ablations: solver settings barely move the saving; removing the AVs does", fontweight="bold", y=1.0)
    fig.text(0.01, -0.03, "Balanced; mean ± 95% t-CI of paired per-seed differences; n = seeds. Source: results/grid_review*.csv, grid_main.csv, grid_ablations.csv", **SRC)
    fig.tight_layout(); save(fig, "cpsat_ablations.png")


def fig_gantt():
    """Gantt chart of every linehaul trip in a 48 h window of one simulated run (balanced, seed 0)."""
    S = pd.read_csv(ROOT / "results" / "schedule_balanced_seed0.csv")
    t0, t1 = 7 * 24, 9 * 24   # day 7 00:00 to day 9 00:00 (simulation clock, hours)
    fig, axes = plt.subplots(2, 1, figsize=(12, 6.4), sharex=True, gridspec_kw=dict(hspace=.35))
    for ax, p in zip(axes, ["greedy_av_first", "cpsat"]):
        d = S[(S.policy == p) & (S.arrive_h > t0) & (S.depart_h < t1)].sort_values("depart_h")
        labels, y = [], 0
        for aid in sorted(d[d.vehicle == "av"].av_id.dropna().unique()):
            for _, r in d[(d.vehicle == "av") & (d.av_id == aid)].iterrows():
                ax.barh(y, r.arrive_h - r.depart_h, left=r.depart_h, height=.7, color="#d0d7de" if r["empty"] else COL["cpsat"],
                        hatch="///" if r["empty"] else None, edgecolor="#8c959f" if r["empty"] else "white")
                if not r["empty"]: ax.text(r.depart_h + .15, y, f"{r.origin}→{r.stop} {r.pallets}", va="center", fontsize=6.5, color="white", clip_on=True)
            labels.append(f"AV tractor {int(aid)}"); y += 1
        lanes = []   # pack human trips into the fewest rows without overlap
        for _, r in d[d.vehicle == "human"].iterrows():
            k = next((i for i, end in enumerate(lanes) if end <= r.depart_h), None)
            if k is None: lanes.append(r.arrive_h); k = len(lanes) - 1
            else: lanes[k] = r.arrive_h
            ax.barh(y + k, r.arrive_h - r.depart_h, left=r.depart_h, height=.7, color=plt.cm.Oranges(.3 + .6 * r.pallets / 26), edgecolor="white")
        labels += ["human trucks" if i == len(lanes) // 2 else "" for i in range(len(lanes))]
        for day in (7, 8, 9):   # AV dispatch window 05:00-21:00: shade the closed hours
            for a, b in [(day * 24 - 3, day * 24 + 5)]:
                ax.axvspan(max(a, t0), min(b, t1), color="#f0f0f0", zorder=0)
        ax.set_yticks(range(y + len(lanes))); ax.set_yticklabels(labels, fontsize=8); ax.invert_yaxis(); ax.set_ylim(y + len(lanes) - .4, -.6)
        w = d[(d.depart_h >= t0) & (d.depart_h < t1)]
        ax.set_title(f"{LAB[p]}: {int(((w.vehicle == 'av') & (w["empty"] == 0)).sum())} loaded AV runs, {int((w.vehicle == 'human').sum())} human runs departing in this window", loc="left")
    ticks = np.arange(t0, t1 + 1, 6)
    axes[1].set_xticks(ticks); axes[1].set_xticklabels([f"day {int(t // 24)}\n{int(t % 24):02d}:00" for t in ticks], fontsize=8)
    axes[1].set_xlim(t0, t1)
    fig.legend(handles=[Patch(color=COL["cpsat"], label="AV, loaded (label: origin→stop, pallets)"), Patch(facecolor="#d0d7de", hatch="///", edgecolor="#8c959f", label="AV, empty reposition"),
                        Patch(color=plt.cm.Oranges(.75), label="human truck (darker = fuller, of 26 pallets)"), Patch(color="#f0f0f0", label="AV dispatch closed (21:00-05:00)")],
               loc="lower center", ncol=4, frameon=False, fontsize=8, bbox_to_anchor=(.5, -.04))
    fig.suptitle("Simulated linehaul schedule, balanced demand, seed 0 (48 h window)", fontweight="bold", y=.97)
    fig.text(0.01, -.07, "Each bar is one trip, from departure (after loading) to arrival; AV dispatch = start of loading. Human trucks are packed into rows. One simulated run, not an average. "
             "\n"
             "Source: results/schedule_balanced_seed0.csv (experiments/export_schedule.py)", **SRC)
    save(fig, "schedule_gantt.png")


if __name__ == "__main__":
    fig_tradeoff(); fig_paired(); fig_sweeps(); fig_ablations(); fig_gantt()
