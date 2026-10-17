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

def test_deferral_is_not_free():
    """Deferring must cost at least the pallet share of a full linehaul at the marginal rate (PR #1 review)."""
    cfg = small(); tw = Twin(cfg, lambda *_: [], seed=0); P = CPSATDispatcher()
    s = Shipment(0, "DAL", "HOU", "HOU", 6, 0, 100 * HOUR)          # far from due: no lateness component
    av_rate = cfg.lane_miles * cfg.av_cost_per_mile / cfg.trailer_pallets
    assert P.defer_cost(tw, s, 0.0, av_share=1.0) >= 6 * av_rate > 0

def test_defer_rate_is_human_rate_without_av_capacity():
    """No AV slot in the horizon -> deferral priced at the human rate (PR #1 re-review, finding 1)."""
    cfg = small(); tw = Twin(cfg, lambda *_: [], seed=0); P = CPSATDispatcher()
    hu = (cfg.lane_miles * cfg.human_cost_per_mile + cfg.human_dispatch_fixed) / cfg.trailer_pallets
    av = cfg.lane_miles * cfg.av_cost_per_mile / cfg.trailer_pallets
    assert abs(P.defer_rate(tw, 0.0) - hu) < 1e-9 and abs(P.defer_rate(tw, 1.0) - av) < 1e-9 and av < P.defer_rate(tw, 0.5) < hu

def _full_trailer_case(av_fleet):
    cfg = small(av_fleet=av_fleet); tw = Twin(cfg, lambda *_: [], seed=0); now = 8 * HOUR
    pool = [Shipment(i, "DAL", "HOU", "HOU", 13, 0, now + 60 * HOUR) for i in range(2)]   # 26 pallets, due in 60 h
    return cfg, tw, now, pool

def test_full_trailer_ships_now_on_human_truck_when_no_av():
    """Only option now is a human truck: a full trailer must ship within the horizon, and by a non-marginal margin."""
    cfg, tw, now, pool = _full_trailer_case(av_fleet=0); P = CPSATDispatcher(time_limit_s=2)
    ds = P.plan(tw, now, "DAL", pool)
    assert ds and all(d.vehicle == "human" for d in ds) and sum(len(d.shipments) for d in ds) == 2
    trip = cfg.lane_miles * cfg.human_cost_per_mile + cfg.human_dispatch_fixed
    margin = sum(P.defer_cost(tw, s, now, av_share=0.0) for s in pool) - trip
    assert margin >= 100, margin       # holding cost over the horizon, not a $2 tie-break

def test_full_trailer_ships_on_idle_av():
    cfg, tw, now, pool = _full_trailer_case(av_fleet=2); P = CPSATDispatcher(time_limit_s=2)
    ds = P.plan(tw, now, "DAL", pool)
    assert ds and ds[0].vehicle == "av" and sum(len(d.shipments) for d in ds) == 2

def test_warm_start_runs_and_conserves():
    P = CPSATDispatcher(time_limit_s=0.3, warm_start=True); tw = Twin(small(), P, seed=2).run()
    assert all(not math.isnan(s.delivered) for s in tw.shipments) and P.stats["fallback"] == 0 and len(P._prev) >= 0

def test_noav_control_uses_no_av():
    tw = Twin(small(av_fleet=0), CPSATDispatcher(time_limit_s=0.3), seed=0).run()
    assert not any(t.vehicle == "av" for t in tw.trips)
