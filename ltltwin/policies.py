"""Dispatch policies. Each is a callable policy(twin, now) -> list[Departure].

Baselines (from the brief): human-only, AV on a fixed schedule, greedy AV-first.
All share the same human 'safety net' rules so differences come from how the AV is used."""
from __future__ import annotations
from .config import HOUR, DAY
from .sim import Departure, local_hour, other

BUFFER = 30.0  # minutes of safety margin in at-risk tests

def eta_delivery(tw, s, now, vehicle, direct):
    cfg = tw.cfg; t = now + s.pallets * cfg.load_min_per_pallet + cfg.transit_min(vehicle == "av", direct) + s.pallets * cfg.unload_min_per_pallet
    return tw._final_mile(t) if (s.to_endpoint and not direct) else t

def at_risk(tw, s, now, vehicle="human", wait=0.0):
    """True if the shipment would be late unless it leaves within `wait` minutes on `vehicle` via the terminal/direct default."""
    # conservative: assume routing via the destination terminal (no direct-to-endpoint shortcut)
    return eta_delivery(tw, s, now + wait + tw.cfg.tick_min, vehicle, False) + BUFFER > s.due

def build_load(tw, ships, vehicle, direct_min=20, cap=None):
    """Pick a stop and a set of shipments (earliest due first, first-fit to capacity).
    Direct-to-endpoint if one endpoint alone has >= direct_min pallets (AV only if allowed)."""
    cfg = tw.cfg; cap = cap or cfg.trailer_pallets
    ships = sorted(ships, key=lambda s: s.due)
    if not ships: return None, []
    dest = ships[0].dest; allow_direct = vehicle == "human" or cfg.av_direct_to_endpoint
    stop, cand = dest, ships
    if allow_direct:
        by_ep = {}
        for s in ships:
            if s.to_endpoint: by_ep.setdefault(s.consignee, []).append(s)
        best = max(by_ep.items(), key=lambda kv: sum(x.pallets for x in kv[1]), default=None)
        if best and sum(x.pallets for x in best[1]) >= direct_min:
            # only go direct if no terminal-bound shipment is about to be stranded by it
            stop, cand = best
    load, pal = [], 0
    for s in cand:
        if pal + s.pallets <= cap: load.append(s); pal += s.pallets
    return stop, load

def pallets(ships): return sum(s.pallets for s in ships)

class HumanOnly:
    """Full trailers go immediately; scheduled sweeps carry everything; at-risk freight triggers an extra run."""
    name = "human_only"
    def __init__(self, sweep_hours=None): self.sweep_hours = sweep_hours; self._last_sweep = {}   # None -> cfg.human_sweep_hours
    def is_sweep(self, tw, now, term):
        h = int(local_hour(now)); key = (term, int(now // HOUR)); hours = self.sweep_hours if self.sweep_hours is not None else tw.cfg.human_sweep_hours
        if h in hours and local_hour(now) % 1 < tw.cfg.tick_min / 60 and key not in self._last_sweep:
            self._last_sweep[key] = True; return True
        return False
    def human_rules(self, tw, now, term, pool, keep_for_av=0):
        out = []; pool = list(pool)
        while pallets(pool) - keep_for_av >= tw.cfg.trailer_pallets:            # full-trailer rule
            stop, load = build_load(tw, pool, "human")
            if not load: break
            out.append(Departure(term, stop, "human", load)); pool = [s for s in pool if s not in load]
        sweep = self.is_sweep(tw, now, term)
        while pool and (sweep or any(at_risk(tw, s, now) for s in pool)):     # sweep / at-risk rule
            urgent = pool if sweep else [s for s in pool if at_risk(tw, s, now)] + [s for s in pool if not at_risk(tw, s, now)]
            stop, load = build_load(tw, urgent, "human")
            if not load: break
            out.append(Departure(term, stop, "human", load)); pool = [s for s in pool if s not in load]
            if not sweep and not any(at_risk(tw, s, now) for s in pool): break
        return out, pool
    def __call__(self, tw, now):
        out = []
        for term in tw.cfg.terminals:
            d, _ = self.human_rules(tw, now, term, tw.pool[term]); out += d
        return out

class AVFixed(HumanOnly):
    """AV departs on a fixed headway inside its operating window with whatever is waiting (urgent first);
    humans cover at-risk freight and the night sweep."""
    name = "av_fixed"
    def __init__(self, headway_h=4, **kw): super().__init__(**kw); self.headway = headway_h
    def __call__(self, tw, now):
        out = []; a, b = tw.cfg.av_hours
        for term in tw.cfg.terminals:
            pool = list(tw.pool[term]); h = local_hour(now)
            slot = tw.cfg.av_window_open(h) and (((h - a) % 24) % self.headway) < tw.cfg.tick_min / 60
            if slot and not tw.av_blocked(now):
                for av in tw.idle_avs(term):
                    stop, load = build_load(tw, pool, "av")
                    out.append(Departure(term, stop if load else other(term, tw.cfg), "av", load)); pool = [s for s in pool if s not in load]
            d, _ = self.human_rules(tw, now, term, pool, keep_for_av=tw.cfg.trailer_pallets * self.av_capacity_soon(tw, now, term)); out += d
        return out
    @staticmethod
    def av_capacity_soon(tw, now, term, horizon=6 * HOUR):
        return sum(1 for av in tw.avs if (not av.busy and av.loc == term) or (av.busy and av.loc != term and av.eta <= now + horizon))

class GreedyAVFirst(AVFixed):
    """AV leaves as soon as it has >= min_fill pallets (or at-risk freight) and is allowed to run;
    idle AVs deadhead to the other terminal when freight is waiting there and no AV is."""
    name = "greedy_av_first"
    def __init__(self, min_fill=20, **kw): super().__init__(**kw); self.min_fill = min_fill
    def __call__(self, tw, now):
        out = []; cfg = tw.cfg
        for term in cfg.terminals:
            pool = list(tw.pool[term])
            if not tw.av_blocked(now):
                for av in tw.idle_avs(term):
                    urgent = any(at_risk(tw, s, now, "av") for s in pool)
                    if pallets(pool) >= self.min_fill or (urgent and pool):
                        stop, load = build_load(tw, pool, "av")
                        out.append(Departure(term, stop, "av", load)); pool = [s for s in pool if s not in load]
                    else:
                        far = other(term, cfg)
                        if pallets(tw.pool[far]) >= cfg.trailer_pallets and not tw.idle_avs(far) and pallets(pool) < 8:
                            out.append(Departure(term, far, "av", []))   # empty reposition
            d, _ = self.human_rules(tw, now, term, pool, keep_for_av=cfg.trailer_pallets * self.av_capacity_soon(tw, now, term)); out += d
        return out
