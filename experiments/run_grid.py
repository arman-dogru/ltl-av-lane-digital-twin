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
    "cpsat_nodirect": lambda: CPSATDispatcher(direct=False), "cpsat_norepo": lambda: CPSATDispatcher(reposition=False),
}
BASE = ["human_only", "av_fixed", "greedy_av_first"]
GRIDS = {
    "baselines": [(sc, v, s) for sc in ("balanced", "imbalanced") for v in BASE for s in range(30)],
    "main": [(sc, "cpsat", s) for sc in ("balanced", "imbalanced") for s in range(10)],
    "ablations": [("balanced", v, s) for v in VARIANTS if v.startswith("cpsat_") for s in range(8)],
}

def run(cell):
    sc, v, seed = cell; t = time.time(); P = VARIANTS[v](); tw = Twin(scenario(sc), P, seed=seed).run()
    k = kpis(tw); st = getattr(P, "stats", {})
    return dict(scenario=sc, policy=v, seed=seed, runtime_s=round(time.time() - t, 1), **k,
                solves=st.get("solves", 0), solver_fallbacks=st.get("fallback", 0), solver_nonoptimal=st.get("feasible", 0))

if __name__ == "__main__":
    grid, workers = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4
    path = f"results/grid_{grid}.csv"; done = set()
    if os.path.exists(path):
        with open(path) as f: done = {(r["scenario"], r["policy"], int(r["seed"])) for r in csv.DictReader(f)}
    todo = [c for c in GRIDS[grid] if c not in done]; print(f"{grid}: {len(todo)} runs to do ({len(done)} cached)", flush=True)
    with ProcessPoolExecutor(workers) as ex:
        for fut in as_completed([ex.submit(run, c) for c in todo]):
            r = fut.result(); new = not os.path.exists(path)
            with open(path, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(r)); new and w.writeheader(); w.writerow(r)
            print(r["scenario"], r["policy"], r["seed"], r["runtime_s"], round(r["on_time"], 3), round(r["cost_per_pallet"], 2), flush=True)
