from ltltwin.config import Config, HOUR
from ltltwin.sim import Twin, Shipment
from ltltwin.optimizer import CPSATDispatcher
from ltltwin.kpi import kpis
import math

def small(**kw): return Config(days=4, warmup_days=1, **kw)

def test_cpsat_conservation_capacity_and_solver_health():
    P = CPSATDispatcher(time_limit_s=0.3); tw = Twin(small(), P, seed=1).run()
    assert all(not math.isnan(s.delivered) for s in tw.shipments)
    assert all(t.pallets <= tw.cfg.trailer_pallets for t in tw.trips)
    assert P.stats["solves"] > 0 and P.stats["fallback"] / P.stats["solves"] < 0.1

def test_late_cost_monotone():
    P = CPSATDispatcher(late_fixed=300, late_per_h=50, buffer_min=0)
    assert P.late_cost(10, 20) == 0 and P.late_cost(20 + HOUR, 20) == 350 and P.late_cost(20 + 3 * HOUR, 20) > P.late_cost(20 + HOUR, 20)

def test_plan_respects_capacity_and_av_count():
    cfg = small(); tw = Twin(cfg, lambda *_: [], seed=0)
    pool = [Shipment(i, "DAL", "HOU", "HOU", 5, 0, 30 * HOUR) for i in range(12)]   # 60 pallets
    now = 6 * HOUR; ds = CPSATDispatcher(time_limit_s=1).plan(tw, now, "DAL", pool)
    assert all(sum(s.pallets for s in d.shipments) <= cfg.trailer_pallets for d in ds)
    assert sum(d.vehicle == "av" for d in ds) <= len(tw.idle_avs("DAL"))
    ids = [s.sid for d in ds for s in d.shipments]; assert len(ids) == len(set(ids))

def test_urgent_freight_ships_now():
    cfg = small(); tw = Twin(cfg, lambda *_: [], seed=0); now = 23 * HOUR    # AV not allowed at 23:00
    pool = [Shipment(0, "DAL", "HOU", "HOU", 3, 0, now + 5 * HOUR)]           # must leave now on a human truck
    ds = CPSATDispatcher(time_limit_s=1).plan(tw, now, "DAL", pool)
    assert len(ds) == 1 and ds[0].vehicle == "human"
