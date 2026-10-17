import sys, json, time
from ltltwin.config import Config
from ltltwin.sim import Twin
from ltltwin.policies import HumanOnly, AVFixed, GreedyAVFirst
from ltltwin.kpi import kpis
for P in (HumanOnly, AVFixed, GreedyAVFirst):
    t = time.time(); k = kpis(Twin(Config(), P(), seed=0).run())
    print(P.name, f"{time.time()-t:.1f}s", {a: round(b, 3) if isinstance(b, float) else b for a, b in k.items()})
