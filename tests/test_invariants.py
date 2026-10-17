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
    row = next(r for r in csv.DictReader(open("results/grid_baselines.csv")) if r["scenario"] == "balanced" and r["policy"] == "human_only" and r["seed"] == "0")
    k = kpis(Twin(scenario("balanced"), HumanOnly(), seed=0).run())
    assert abs(k["on_time"] - float(row["on_time"])) < 1e-9 and abs(k["cost_per_pallet"] - float(row["cost_per_pallet"])) < 1e-9

def test_late_pickup_window_only_affects_window():
    from ltltwin.config import DAY
    tw = Twin(small(late_pickup_prob=1.0, late_pickup_window=(2 * DAY, 3 * DAY)), HumanOnly(), seed=0).run()
    for s in tw.shipments:
        assert (s.ready > s.created) == (2 * DAY <= s.created < 3 * DAY)
