"""Why does a 24 h AV window cost MORE than the default 05-21 window under CP-SAT? (PR #3 review, finding 1)

Part A (committed CSVs, no rerun): paired 24 h - 16 h differences on the same seeds (common random numbers) for
cost/pallet, on-time, dwell, AV trips and human fill, at 5 and at 10 seeds.
Part B (rerun, CP-SAT, seeds 0,1,4, balanced): per run, after warm-up -
  * human (non-empty) trips carrying < 20 pallets,
  * AV departures and human fill by 3 h local-hour bucket,
  * idle AVs (parked at a terminal, not busy) sampled at every full hour, by local hour.
Writes results/av_hours_mechanism.md.  usage: python experiments/av_hours_mechanism.py [workers]"""
import glob, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ltltwin.scenarios import scenario
from ltltwin.sim import Twin, local_hour
from ltltwin.optimizer import CPSATDispatcher
from ltltwin.config import HOUR, DAY

H24, H16 = "balanced@av_hours=(0,24)", "balanced"
SMALL = 20; TRACE_SEEDS = (0, 1, 4)

def ci(x, k=2):
    x = np.asarray(x, float); h = stats.t.ppf(.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return f"{x.mean():+.{k}f} ± {h:.{k}f}"

def part_a():
    df = pd.concat([pd.read_csv(f) for f in glob.glob("results/grid_*.csv")]).drop_duplicates(["scenario", "policy", "seed"])
    c = df[df.policy == "cpsat"]; a = c[c.scenario == H24].set_index("seed"); b = c[c.scenario == H16].set_index("seed")
    seeds = sorted(a.index.intersection(b.index)); rows = []
    for n in (5, len(seeds)):
        s = [x for x in seeds if x < 5] if n == 5 else seeds
        d = lambda col, k=1.0: ci(k * (a.loc[s, col] - b.loc[s, col]), 2 if col != "fill_human" else 3)
        rows.append(f"| {len(s)} | {d('cost_per_pallet')} | {d('on_time', 100)} | {d('dwell_mean_h')} | {d('av_trips')} | {d('fill_human')} |")
    return ["## A. Paired 24 h − 16 h (CP-SAT, balanced, same seeds; mean ± 95% t-CI)", "",
            "| seeds | Δ cost/pallet $ | Δ on-time pp | Δ dwell h | Δ AV trips | Δ human fill |", "|---|---|---|---|---|---|", *rows]

def trace(cell):
    sc, seed = cell; tw = Twin(scenario(sc), CPSATDispatcher(), seed=seed); idle = []
    def probe():
        while True:
            yield tw.env.timeout(HOUR - (tw.env.now % HOUR) if tw.env.now % HOUR else HOUR)
            if tw.env.now >= tw.cfg.warmup_days * DAY:
                idle.append((int(local_hour(tw.env.now)) % 24, sum(len(tw.idle_avs(t)) for t in tw.cfg.terminals)))
    tw.env.process(probe()); tw.run()
    T = [t for t in tw.trips if not t.empty and t.depart >= tw.cfg.warmup_days * DAY]
    b = lambda t: int(local_hour(t.depart)) // 3
    av = np.bincount([b(t) for t in T if t.vehicle == "av"], minlength=8)
    hf = [np.mean([t.pallets / tw.cfg.trailer_pallets for t in T if t.vehicle == "human" and b(t) == k] or [np.nan]) for k in range(8)]
    ih = pd.DataFrame(idle, columns=["h", "n"]).groupby("h").n.mean()
    return dict(sc=sc, seed=seed, small=sum(t.vehicle == "human" and t.pallets < SMALL for t in T), av=av, hf=hf, idle=ih)

def part_b(workers):
    cells = [(sc, s) for sc in (H16, H24) for s in TRACE_SEEDS]
    with ProcessPoolExecutor(workers) as ex: R = list(ex.map(trace, cells))
    lab = {H16: "16 h (05–21)", H24: "24 h"}; out = ["", f"## B. Trace (CP-SAT, balanced, seeds {TRACE_SEEDS}, after warm-up; rerun, so CP-SAT time-limit noise applies)", "",
          f"Human trips with < {SMALL} pallets per run:", ""]
    for sc in (H16, H24): out.append(f"- {lab[sc]}: " + ", ".join(f"seed {r['seed']}: {r['small']}" for r in R if r["sc"] == sc))
    hdr = "| window | " + " | ".join(f"{3*k:02d}–{3*k+3:02d}" for k in range(8)) + " |"; sep = "|---" * 9 + "|"
    out += ["", "AV departures per 3 h local-hour bucket (sum over seeds):", "", hdr, sep]
    for sc in (H16, H24): out.append(f"| {lab[sc]} | " + " | ".join(str(v) for v in sum(r["av"] for r in R if r["sc"] == sc)) + " |")
    out += ["", "Human fill (mean pallets/26) by departure bucket (mean over seeds):", "", hdr, sep]
    for sc in (H16, H24): out.append(f"| {lab[sc]} | " + " | ".join(f"{v:.2f}" for v in np.nanmean([r["hf"] for r in R if r["sc"] == sc], axis=0)) + " |")
    out += ["", "Idle AVs (parked, not busy; of 2) sampled on the hour, mean by local hour:", "",
            "| window | " + " | ".join(f"{h:02d}" for h in range(0, 24, 2)) + " |", "|---" * 13 + "|"]
    for sc in (H16, H24):
        m = pd.concat([r["idle"] for r in R if r["sc"] == sc], axis=1).mean(axis=1)
        out.append(f"| {lab[sc]} | " + " | ".join(f"{m.get(h, np.nan):.2f}" for h in range(0, 24, 2)) + " |")
    return out

if __name__ == "__main__":
    lines = part_a() + part_b(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
    open("results/av_hours_mechanism.md", "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
