"""Rolling-horizon CP-SAT dispatcher.

At every re-optimisation epoch, for each origin terminal, assign every pooled shipment to one candidate
departure slot within the horizon (AV slots for AVs at / arriving at the terminal, hourly human slots) or to
'defer' (beyond horizon). Minimise linehaul cost + late penalties + a small waiting cost, subject to trailer
capacity and at most one departure per AV in the horizon. Only slots starting now are executed; the rest is
re-planned next epoch (receding horizon)."""
from __future__ import annotations
import math
from ortools.sat.python import cp_model
from .config import HOUR
from .sim import Departure, other
from .policies import eta_delivery, build_load, pallets, GreedyAVFirst

class CPSATDispatcher:
    name = "cpsat"
    def __init__(self, horizon_h=8, reopt_min=60, slot_h=1, direct=True, wait_cost_per_h=1.0, time_limit_s=1.0, reposition=True, late_fixed=300.0, late_per_h=50.0, buffer_min=30.0):
        self.h, self.reopt, self.slot, self.direct = horizon_h, reopt_min, slot_h, direct
        self.wait_cost, self.tl, self.reposition = wait_cost_per_h, time_limit_s, reposition
        self.late_fixed, self.late_per_h, self.buffer = late_fixed, late_per_h, buffer_min
        self._last = -math.inf; self.stats = dict(solves=0, optimal=0, feasible=0, fallback=0)

    def late_cost(self, eta, due):
        """Service-failure cost: fixed charge once late, plus a per-hour charge (so late freight is never parked indefinitely)."""
        eta = eta + self.buffer   # same safety margin as the baselines' at-risk rule (dock queueing, loading variance)
        return 0.0 if eta <= due else self.late_fixed + self.late_per_h * (eta - due) / HOUR

    def defer_cost(self, tw, s, now):
        """Deferring past the horizon is not free: the shipment still needs a linehaul later (charged at its pallet
        share of the cheapest *full* trailer, i.e. a lower bound on future transport cost), plus the lateness it
        would incur leaving at the horizon end, plus waiting cost up to then."""
        cfg = tw.cfg; end = now + self.h * HOUR + self.slot * HOUR
        av_trip = cfg.lane_miles * cfg.av_cost_per_mile; hu_trip = cfg.lane_miles * cfg.human_cost_per_mile + cfg.human_dispatch_fixed
        per_pallet = (min(av_trip, hu_trip) if cfg.av_fleet > 0 else hu_trip) / cfg.trailer_pallets
        return s.pallets * per_pallet + self.late_cost(eta_delivery(tw, s, end, "human", False), s.due) + self.wait_cost * (end - now) / HOUR

    def _next_allowed(self, tw, t):
        step = tw.cfg.tick_min; n = 0
        while tw.av_blocked(t) and n < 200: t += step; n += 1
        return t

    def _slots(self, tw, now, term):
        cfg = tw.cfg; S = []; end = now + self.h * HOUR
        for av in tw.avs:     # AV candidate departures: every slot_h from the time it is at this terminal and allowed
            if av.busy and av.loc != term: t0 = av.eta
            elif not av.busy and av.loc == term: t0 = now
            else: continue
            t = self._next_allowed(tw, max(now, t0))
            while t <= end:
                S.append(("av", av.aid, t)); t = self._next_allowed(tw, t + self.slot * HOUR)
        t = now
        while t <= end: S.append(("human", None, t)); t += self.slot * HOUR
        return S

    def plan(self, tw, now, term, pool):
        cfg = tw.cfg; slots = self._slots(tw, now, term)
        if not pool or not slots: return []
        m = cp_model.CpModel(); P = cfg.trailer_pallets
        x = {(i, k): m.NewBoolVar("") for i in range(len(pool)) for k in range(len(slots))}
        defer = [m.NewBoolVar("") for _ in pool]; y = [m.NewBoolVar("") for _ in slots]
        cost = []
        for i, s in enumerate(pool):
            m.AddExactlyOne([x[i, k] for k in range(len(slots))] + [defer[i]])
            end = now + self.h * HOUR + self.slot * HOUR
            cost.append(defer[i] * int(round(self.defer_cost(tw, s, now))))
            for k, (v, _, t) in enumerate(slots):
                c = self.late_cost(eta_delivery(tw, s, t, v, False), s.due) + self.wait_cost * (t - now) / HOUR
                cost.append(x[i, k] * int(round(c)))
        for k, (v, aid, t) in enumerate(slots):
            m.Add(sum(x[i, k] * s.pallets for i, s in enumerate(pool)) <= P * y[k])
            miles = cfg.lane_miles
            c = miles * cfg.av_cost_per_mile if v == "av" else miles * cfg.human_cost_per_mile + cfg.human_dispatch_fixed
            cost.append(y[k] * int(round(c)))
        for av in tw.avs:
            ks = [k for k, (v, aid, _) in enumerate(slots) if v == "av" and aid == av.aid]
            if ks: m.Add(sum(y[k] for k in ks) <= 1)
        m.Minimize(sum(cost))
        sol = cp_model.CpSolver(); sol.parameters.max_time_in_seconds = self.tl; sol.parameters.num_workers = 1
        st = sol.Solve(m); self.stats["solves"] += 1
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            self.stats["fallback"] += 1; return None
        self.stats["optimal" if st == cp_model.OPTIMAL else "feasible"] += 1
        out = []
        for k, (v, aid, t) in enumerate(slots):
            if t > now + 1e-6 or not sol.Value(y[k]): continue
            load = [s for i, s in enumerate(pool) if sol.Value(x[i, k])]
            if not load: continue
            # stop choice: direct to a 3P endpoint only if the whole load is for that endpoint
            eps = {s.consignee for s in load}; stop = load[0].dest
            if self.direct and len(eps) == 1 and load[0].to_endpoint and (v == "human" or cfg.av_direct_to_endpoint): stop = load[0].consignee
            out.append(Departure(term, stop, v, load))
        return out

    def __call__(self, tw, now):
        if now - self._last < self.reopt - 1e-6: return []
        self._last = now; out = []
        for term in tw.cfg.terminals:
            pool = list(tw.pool[term])
            ds = self.plan(tw, now, term, pool)
            if ds is None:   # solver failure: fall back to the greedy baseline for this terminal
                ds = [d for d in GreedyAVFirst()(tw, now) if d.origin == term]
            idle = len(tw.idle_avs(term)); used = 0; keep = []
            for d in ds:
                if d.vehicle == "av":
                    if used >= idle or tw.av_blocked(now): d = Departure(d.origin, d.stop if d.stop in tw.cfg.terminals else d.shipments[0].dest, "human", d.shipments)
                    else: used += 1
                keep.append(d)
            out += keep
            if self.reposition and used < idle and not tw.av_blocked(now):
                far = other(term, tw.cfg); left = [s for s in pool if not any(s in d.shipments for d in keep)]
                if pallets(tw.pool[far]) >= tw.cfg.trailer_pallets and not tw.idle_avs(far) and pallets(left) < 8:
                    out.append(Departure(term, far, "av", []))
        return out
