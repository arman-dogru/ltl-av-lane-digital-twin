"""Run (scenario, policy-variant, seed) cells in parallel; append one CSV row per run (resumable).
Common random numbers: a given seed produces identical demand for every policy within a scenario.

usage: python experiments/run_grid.py <grid-name> [workers]"""
import csv, os, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ltltwin.scenarios import scenario
from ltltwin.sim import Twin
from ltltwin.policies import HumanOnly, AVFixed, GreedyAVFirst
from ltltwin.optimizer import CPSATDispatcher
from ltltwin.kpi import kpis

VARIANTS = {
    "human_only": lambda: HumanOnly(), "av_fixed": lambda: AVFixed(), "greedy_av_first": lambda: GreedyAVFirst(),
    "cpsat": lambda: CPSATDispatcher(),
    "cpsat_h4": lambda: CPSATDispatcher(horizon_h=4), "cpsat_h12": lambda: CPSATDispatcher(horizon_h=12),
    "cpsat_myopic": lambda: CPSATDispatcher(horizon_h=0),          # only 'leave now' slots: no waiting to consolidate
    "cpsat_reopt30": lambda: CPSATDispatcher(reopt_min=30), "cpsat_reopt120": lambda: CPSATDispatcher(reopt_min=120),
    "cpsat_buf0": lambda: CPSATDispatcher(buffer_min=0), "cpsat_buf90": lambda: CPSATDispatcher(buffer_min=90),
    "cpsat_late150": lambda: CPSATDispatcher(late_fixed=150, late_per_h=25), "cpsat_late1500": lambda: CPSATDispatcher(late_fixed=1500, late_per_h=250),
    "cpsat_warm": lambda: CPSATDispatcher(warm_start=True), "cpsat_noav": lambda: CPSATDispatcher(),
    "cpsat_floor_x0.5": lambda: CPSATDispatcher(defer_scale=0.5), "cpsat_floor_x1.5": lambda: CPSATDispatcher(defer_scale=1.5),
    "cpsat_floor_human": lambda: CPSATDispatcher(defer_floor="human"), "cpsat_floor_av": lambda: CPSATDispatcher(defer_floor="av"),
    "cpsat_nodirect": lambda: CPSATDispatcher(direct=False), "cpsat_norepo": lambda: CPSATDispatcher(reposition=False),
}
CFG = {"cpsat_noav": dict(av_fleet=0)}   # per-variant scenario overrides (no-AV control: same dispatcher, no AV trucks)
BASE = ["human_only", "av_fixed", "greedy_av_first"]
GRIDS = {
    "baselines": [(sc, v, s) for sc in ("balanced", "imbalanced") for v in BASE for s in range(30)],
    # reviewer-blocking evidence first: default vs defer-floor sweep vs no-AV control (balanced, seeds 0-4)
    "review": [("balanced", v, s) for v in ("cpsat", "cpsat_floor_x0.5", "cpsat_floor_x1.5", "cpsat_floor_human", "cpsat_floor_av", "cpsat_noav") for s in range(5)],
    # issue #2 minor 2: floor sweep + no-AV control extended to the same 10 seeds as `main`
    "review10": [("balanced", v, s) for v in ("cpsat_floor_x0.5", "cpsat_floor_x1.5", "cpsat_floor_human", "cpsat_floor_av", "cpsat_noav") for s in range(5, 10)],
    # PR #3 review: 24 h AV window at 10 seeds for the paired 24 h - 16 h comparison
    "hours24_10": [("balanced@av_hours=(0,24)", "cpsat", s) for s in range(5, 10)],
    # step 4 sensitivity sweeps (balanced, seeds 0-4, common random numbers); ';'-separated overrides, demand scales volume
    "sweeps": [(f"balanced@{o}", v, s) for o in
               [f"av_fleet={n}" for n in (0, 1, 3, 4, 6)] + ["av_hours=(0,24)", "av_hours=(6,18)"] +
               [f"av_cost_per_mile={c}" for c in (1.2, 2.0, 2.3)] + ["demand=0.7", "demand=1.3"]
               for v in ("human_only", "greedy_av_first", "cpsat") for s in range(5)],
    "main": [(sc, "cpsat", s) for sc in ("balanced", "imbalanced") for s in range(10)],
    # reviewer-requested horizon checks + controls first; 5 seeds (paired with the same seeds of `main`)
    "ablations": [("balanced", v, s) for v in ("cpsat_myopic", "cpsat_h4", "cpsat_h12", "cpsat_warm", "cpsat_norepo", "cpsat_nodirect") for s in range(5)],
    "ablations_more": [("balanced", v, s) for v in ("cpsat_buf0", "cpsat_buf90", "cpsat_late150", "cpsat_late1500", "cpsat_reopt30", "cpsat_reopt120") for s in range(5)],
}

def run(cell):
    sc, v, seed = cell; t = time.time(); P = VARIANTS[v](); tw = Twin(scenario(sc, **CFG.get(v, {})), P, seed=seed).run()
    k = kpis(tw); st = getattr(P, "stats", {})
    return dict(scenario=sc, policy=v, seed=seed, runtime_s=round(time.time() - t, 1), **k,
                solves=st.get("solves", 0), solver_fallbacks=st.get("fallback", 0), solver_nonoptimal=st.get("feasible", 0))

if __name__ == "__main__":
    grid, workers = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4
    path = f"results/grid_{grid}.csv"; done = set()
    import glob   # a cell finished in ANY grid is reused (CP-SAT with a time limit is not bit-deterministic, so never run a cell twice)
    for other in glob.glob("results/grid_*.csv"):
        with open(other) as f: done |= {(r["scenario"], r["policy"], int(r["seed"])) for r in csv.DictReader(f)}
    todo = [c for c in GRIDS[grid] if c not in done]; print(f"{grid}: {len(todo)} runs to do ({len(done)} cached)", flush=True)
    with ProcessPoolExecutor(workers) as ex:
        for fut in as_completed([ex.submit(run, c) for c in todo]):
            r = fut.result(); new = not os.path.exists(path)
            with open(path, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(r)); new and w.writeheader(); w.writerow(r)
            print(r["scenario"], r["policy"], r["seed"], r["runtime_s"], round(r["on_time"], 3), round(r["cost_per_pallet"], 2), flush=True)
