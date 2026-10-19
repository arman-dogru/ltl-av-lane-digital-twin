"""Export every linehaul trip of one simulated run per policy -> results/schedule_balanced_seed0.csv (input of the README Gantt chart).

usage: .venv/bin/python experiments/export_schedule.py   (~30 s; CP-SAT has a 1 s time limit per solve, so a re-export can differ
       slightly from the committed CSV; the grid CSVs, not this file, are the source of every reported KPI)
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ltltwin.scenarios import scenario
from ltltwin.sim import Twin
from ltltwin.policies import GreedyAVFirst
from ltltwin.optimizer import CPSATDispatcher
from ltltwin.kpi import kpis
from ltltwin.config import HOUR

class TracedTwin(Twin):
    """Twin that also records which AV tractor drove each trip (the base Trip record has no vehicle id)."""
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.av_of = {}
    def _run(self, d, av):
        g = super()._run(d, av); val = None
        while True:   # delegate step by step: any trip appended while this generator runs is this generator's trip
            n = len(self.trips)
            try: ev = g.send(val)
            except StopIteration: return
            for tr in self.trips[n:]: self.av_of[id(tr)] = av.aid if av is not None else ""
            val = yield ev

SCEN, SEED, OUT = "balanced", 0, "results/schedule_balanced_seed0.csv"
rows = []
for name, mk in [("greedy_av_first", GreedyAVFirst), ("cpsat", CPSATDispatcher)]:
    tw = TracedTwin(scenario(SCEN), mk(), seed=SEED).run(); k = kpis(tw)
    print(f"{name}: on_time={k['on_time']:.4f} cost/pallet={k['cost_per_pallet']:.2f} trips={len(tw.trips)}")
    for t in tw.trips:
        rows.append(dict(policy=name, vehicle=t.vehicle, av_id=tw.av_of.get(id(t), ""), origin=t.origin, stop=t.stop,
                         depart_h=round(t.depart / HOUR, 4), arrive_h=round(t.arrive / HOUR, 4), pallets=t.pallets, empty=int(t.empty)))
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("wrote", OUT, len(rows), "trips")
