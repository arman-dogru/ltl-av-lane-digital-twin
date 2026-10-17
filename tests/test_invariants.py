import math, pytest
from ltltwin.config import Config, DAY, HOUR
from ltltwin.sim import Twin, local_hour
from ltltwin.policies import HumanOnly, AVFixed, GreedyAVFirst
from ltltwin.kpi import kpis

def small(**kw): return Config(days=5, warmup_days=1, **kw)
POLICIES = [HumanOnly, AVFixed, GreedyAVFirst]

@pytest.mark.parametrize("P", POLICIES)
def test_conservation_and_capacity(P):
    tw = Twin(small(), P(), seed=1).run()
    assert all(not math.isnan(s.delivered) for s in tw.shipments)              # every shipment delivered
    assert all(s.delivered >= s.departed >= s.in_pool >= s.ready for s in tw.shipments)
    assert all(t.pallets <= tw.cfg.trailer_pallets for t in tw.trips)
    sent = sum(t.pallets for t in tw.trips); assert sent == sum(s.pallets for s in tw.shipments)

@pytest.mark.parametrize("P", [AVFixed, GreedyAVFirst])
def test_av_respects_hours_and_weather(P):
    hold = ((2 * DAY, 2 * DAY + 12 * HOUR),)
    tw = Twin(small(weather_hold=hold), P(), seed=2).run()
    a, b = tw.cfg.av_hours
    for t in tw.trips:
        if t.vehicle == "av" and not t.empty:
            # decision time is within window; loading may push actual departure slightly later
            dec = t.depart - t.pallets * tw.cfg.load_min_per_pallet
            assert a <= local_hour(dec) + 1e-6 and local_hour(dec) < b + 1, local_hour(dec)
            assert not (hold[0][0] <= dec < hold[0][1] - 1e-6)

def test_human_only_uses_no_av():
    tw = Twin(small(), HumanOnly(), seed=0).run(); assert not any(t.vehicle == "av" for t in tw.trips)

def test_deterministic_per_seed():
    k1 = kpis(Twin(small(), GreedyAVFirst(), seed=7).run()); k2 = kpis(Twin(small(), GreedyAVFirst(), seed=7).run())
    assert k1 == k2

def test_no_av_fleet_equals_human_only():
    k1 = kpis(Twin(small(av_fleet=0), GreedyAVFirst(), seed=3).run()); k2 = kpis(Twin(small(av_fleet=0), HumanOnly(), seed=3).run())
    assert k1["on_time"] == k2["on_time"] and k1["human_trips"] == k2["human_trips"]

def test_seed_reproduces_frozen_baseline_row():
    """Guards against RNG-stream changes: must equal the committed grid row for (balanced, human_only, seed 0)."""
    import csv
    from ltltwin.scenarios import scenario
    from pathlib import Path
    csv_path = Path(__file__).resolve().parent.parent / "results" / "grid_baselines.csv"
    row = next(r for r in csv.DictReader(open(csv_path)) if r["scenario"] == "balanced" and r["policy"] == "human_only" and r["seed"] == "0")
    k = kpis(Twin(scenario("balanced"), HumanOnly(), seed=0).run())
    assert abs(k["on_time"] - float(row["on_time"])) < 1e-9 and abs(k["cost_per_pallet"] - float(row["cost_per_pallet"])) < 1e-9

def test_late_pickup_window_only_affects_window():
    from ltltwin.config import DAY
    tw = Twin(small(late_pickup_prob=1.0, late_pickup_window=(2 * DAY, 3 * DAY)), HumanOnly(), seed=0).run()
    for s in tw.shipments:
        assert (s.ready > s.created) == (2 * DAY <= s.created < 3 * DAY)

@pytest.mark.parametrize("P", POLICIES)
def test_zero_demand_does_not_crash(P):
    """Issue #2: zero demand must yield NaN ratios / zero counts, not a ZeroDivisionError."""
    from ltltwin.kpi import window_kpis
    tw = Twin(small(shipments_per_day={"DAL": 0, "HOU": 0}), P(), seed=0).run(); k = kpis(tw)
    assert k["shipments"] == 0 and k["human_trips"] == 0 and math.isnan(k["on_time"]) and math.isnan(k["cost_per_pallet"])
    assert math.isnan(window_kpis(tw, 0, DAY)["on_time"])

def test_zero_demand_cpsat():
    from ltltwin.optimizer import CPSATDispatcher
    k = kpis(Twin(small(shipments_per_day={"DAL": 0, "HOU": 0}), CPSATDispatcher(time_limit_s=0.2), seed=0).run())
    assert k["shipments"] == 0 and math.isnan(k["on_time"])

def test_hos_limit_is_validated():
    with pytest.raises(ValueError):
        Twin(small(lane_miles=900.0), HumanOnly(), seed=0)

def test_sweep_hours_come_from_config():
    a = kpis(Twin(small(human_sweep_hours=(22, 2)), HumanOnly(), seed=4).run()); b = kpis(Twin(small(human_sweep_hours=(20,)), HumanOnly(), seed=4).run())
    assert a != b


# --- config validation (PR #3 review, finding 3) ----------------------------------------------------
import pytest as _pt
from ltltwin.config import Config as _C


@_pt.mark.parametrize("kw", [
    dict(av_hours=(5, 5)), dict(av_hours=(-1, 21)), dict(av_hours=(5, 25)),
    dict(pallets_per_shipment=(30, 30)), dict(pallets_per_shipment=(0, 6)), dict(pallets_per_shipment=(6, 1)),
    dict(trailer_pallets=0), dict(av_fleet=-1), dict(tick_min=0), dict(tick_min=-15),
    dict(human_mph=0), dict(av_mph=-1), dict(doors=0), dict(sla_hours=(28, 12)),
    dict(shipments_per_day={"DAL": -1, "HOU": 90}), dict(days=2, warmup_days=2),
])
def test_bad_config_raises(kw):
    with _pt.raises(ValueError, match="invalid Config"):
        _C(**kw)


def test_mutated_config_rechecked_by_twin():
    from ltltwin.sim import Twin
    from ltltwin.policies import HumanOnly
    cfg = _C(); cfg.tick_min = 0
    with _pt.raises(ValueError, match="tick_min"):
        Twin(cfg, HumanOnly(), seed=0)


def test_overnight_av_window_wraps_midnight():
    from ltltwin.sim import Twin, local_hour
    from ltltwin.policies import GreedyAVFirst
    cfg = _C(days=4, warmup_days=1, av_hours=(21, 5))
    assert cfg.av_window_open(22) and cfg.av_window_open(2) and not cfg.av_window_open(12) and not cfg.av_window_open(5)
    tw = Twin(cfg, GreedyAVFirst(), seed=0).run()
    av = [t for t in tw.trips if t.vehicle == "av"]
    assert av, "overnight window must allow AV trips"
    # the window gates the dispatch decision; Trip.depart is after door queue + loading (<= 26 x 2.5 min), so allow a lag
    assert not [t for t in av if 8 <= local_hour(t.depart) < 20], "AV dispatched outside the overnight window"


def test_day_window_unchanged_by_wraparound_support():
    c = _C()   # (5, 21)
    assert [h for h in range(24) if c.av_window_open(h)] == list(range(5, 21))
