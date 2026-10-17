"""KPIs over shipments created in [warmup, days) — each must finish within the run's extra days or counts as late."""
import math, numpy as np
from .config import DAY, HOUR

def kpis(tw) -> dict:
    cfg = tw.cfg; S = [s for s in tw.shipments if cfg.warmup_days * DAY <= s.ready < cfg.days * DAY]
    done = [s for s in S if not math.isnan(s.delivered)]
    on_time = sum(s.delivered <= s.due for s in done) / len(S)
    late_h = [max(0.0, (s.delivered - s.due) / HOUR) for s in done]
    dwell = np.array([(s.departed - s.in_pool) / HOUR for s in done])
    T = [t for t in tw.trips if cfg.warmup_days * DAY <= t.depart < cfg.days * DAY]
    fill = lambda v: np.mean([t.pallets / cfg.trailer_pallets for t in T if t.vehicle == v and not t.empty]) if any(t.vehicle == v and not t.empty for t in T) else math.nan
    horizon = (cfg.days + 3) * DAY
    av_util = sum(a.loaded_min for a in tw.avs) / (len(tw.avs) * horizon) if tw.avs else 0.0
    cost = tw.cost["human_miles"] * cfg.human_cost_per_mile + tw.cost["av_miles"] * cfg.av_cost_per_mile + tw.cost["human_dispatches"] * cfg.human_dispatch_fixed
    n_late = len(S) - sum(s.delivered <= s.due for s in done)
    pal = sum(s.pallets for s in tw.shipments)
    return dict(shipments=len(S), on_time=on_time, undelivered=len(S) - len(done), mean_late_h=float(np.mean(late_h)) if late_h else 0.0,
                dwell_mean_h=float(dwell.mean()), dwell_p90_h=float(np.percentile(dwell, 90)),
                fill_av=fill("av"), fill_human=fill("human"), av_trips=sum(t.vehicle == "av" and not t.empty for t in T),
                av_empty_trips=sum(t.vehicle == "av" and t.empty for t in T), human_trips=sum(t.vehicle == "human" for t in T),
                av_share_pallets=sum(s.pallets for s in done if s.mode == "av") / max(1, sum(s.pallets for s in done)),
                direct_share=sum(s.direct for s in done if s.to_endpoint) / max(1, sum(s.to_endpoint for s in done)),
                av_util=av_util, cost_per_pallet=cost / pal, cost_incl_late_per_pallet=(cost + n_late * cfg.late_penalty_per_shipment) / pal)

def window_kpis(tw, t0: float, t1: float) -> dict:
    """On-time / lateness for shipments whose original pickup time (`created`, before any slip) is in [t0, t1)."""
    S = [s for s in tw.shipments if t0 <= s.created < t1]
    late = [s for s in S if math.isnan(s.delivered) or s.delivered > s.due]
    lh = [max(0.0, (s.delivered - s.due) / HOUR) for s in S if not math.isnan(s.delivered)]
    return dict(n=len(S), on_time=1 - len(late) / max(1, len(S)), late_hours_total=float(np.sum(lh)))
