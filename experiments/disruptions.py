"""Disruption case study (balanced scenario, day-7 events), paired against the undisturbed run of the same seed.

Cases: weather (AV hold 04:00-16:00), dock (DAL loses 4/6 doors 15:00-23:00, inbound peak),
surge (50% of day-7 pickups slip 2-6 h), combined (all three).
Metrics: on-time for freight created on days 7-8, peak excess backlog and excess pallet-hours vs the same seed undisturbed."""
import csv, os, sys, json
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ltltwin.config import DAY, HOUR
from ltltwin.scenarios import scenario
from ltltwin.sim import Twin
from ltltwin.policies import HumanOnly, GreedyAVFirst
from ltltwin.optimizer import CPSATDispatcher
from ltltwin.kpi import kpis, window_kpis

D = 7 * DAY
CASES = {
    "none": {},
    "weather": dict(weather_hold=((D + 4 * HOUR, D + 16 * HOUR),)),
    "dock": dict(dock_outage=(("DAL", D + 15 * HOUR, D + 23 * HOUR, 4),)),
    "surge": dict(late_pickup_prob=0.5, late_pickup_hours=(2, 6), late_pickup_window=(D, D + DAY)),
}
CASES["combined"] = {**CASES["weather"], **CASES["dock"], **CASES["surge"]}
POL = {"human_only": HumanOnly, "greedy_av_first": GreedyAVFirst, "cpsat": CPSATDispatcher}
SEEDS = range(int(os.environ.get("SEEDS", 8)))

def run(cell):
    case, pol, seed = cell
    tw = Twin(scenario("balanced", **CASES[case]), POL[pol](), seed=seed).run()
    w = window_kpis(tw, D, D + 2 * DAY); k = kpis(tw)
    tr = [(t, a + b) for t, a, b in tw.trace if D - DAY <= t < D + 3 * DAY]
    return dict(case=case, policy=pol, seed=seed, win_on_time=w["on_time"], win_late_hours=w["late_hours_total"], win_n=w["n"],
                on_time=k["on_time"], cost_per_pallet=k["cost_per_pallet"]), tr

if __name__ == "__main__":
    os.makedirs("results", exist_ok=True); cells = [(c, p, s) for c in CASES for p in POL for s in SEEDS]
    rows, traces = [], {}
    with ProcessPoolExecutor(int(sys.argv[1]) if len(sys.argv) > 1 else 3) as ex:
        for f in as_completed([ex.submit(run, c) for c in cells]):
            r, tr = f.result(); rows.append(r); traces[(r["case"], r["policy"], r["seed"])] = tr; print(r["case"], r["policy"], r["seed"], round(r["win_on_time"], 3), flush=True)
    # excess backlog vs same-seed undisturbed run (tick = cfg.tick_min minutes)
    for r in rows:
        base = np.array([b for _, b in traces[("none", r["policy"], r["seed"])]], float); cur = np.array([b for _, b in traces[(r["case"], r["policy"], r["seed"])]], float)
        n = min(len(base), len(cur)); ex_ = np.clip(cur[:n] - base[:n], 0, None)
        r["peak_excess_pallets"] = float(ex_.max()); r["excess_pallet_hours"] = float(ex_.sum() * 15 / 60)
    rows.sort(key=lambda r: (r["case"], r["policy"], r["seed"]))
    with open("results/disruptions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    # mean backlog trace per case/policy for plotting
    mt = {}
    for (c, p, s), tr in traces.items(): mt.setdefault(f"{c}|{p}", []).append([b for _, b in tr])
    json.dump({k: dict(t_hours=[(t - D) / HOUR for t, _ in traces[(k.split('|')[0], k.split('|')[1], 0)]], backlog=np.mean([v[:min(map(len, vs))] for v in vs], axis=0).tolist())
               for k, vs in mt.items()}, open("results/disruption_traces.json", "w"))
    print("DONE")
