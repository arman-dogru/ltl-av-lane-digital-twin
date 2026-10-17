"""SimPy discrete-event model: shipments -> origin dock -> pool -> linehaul (AV or human) -> destination dock / 3P endpoint."""
from __future__ import annotations
import math
from dataclasses import dataclass, field
import numpy as np, simpy
from .config import Config, HOUR, DAY

@dataclass
class Shipment:
    sid: int; origin: str; dest: str; consignee: str; pallets: int; ready: float; due: float
    in_pool: float = math.nan; departed: float = math.nan; delivered: float = math.nan
    mode: str = ""; direct: bool = False
    @property
    def to_endpoint(self) -> bool: return self.consignee != self.dest

@dataclass
class Trip:
    origin: str; stop: str; vehicle: str; pallets: int; depart: float; arrive: float = math.nan; empty: bool = False

@dataclass
class AV:
    aid: int; loc: str; free_at: float = 0.0; busy: bool = False; eta: float = 0.0; loaded_min: float = 0.0; empty_min: float = 0.0

@dataclass
class Departure:
    """A policy decision: send `shipments` from `origin` to `stop` on `vehicle` ('av'|'human'). Empty shipments + av = reposition."""
    origin: str; stop: str; vehicle: str; shipments: list = field(default_factory=list)

def est_cycle(cfg: Config, d: "Departure") -> float:
    pal = sum(s.pallets for s in d.shipments); ep = d.stop not in cfg.terminals
    return pal * (cfg.load_min_per_pallet + cfg.unload_min_per_pallet) + cfg.transit_min(d.vehicle == "av", ep) + (60.0 * cfg.endpoint_extra_miles / cfg.av_mph if ep else 0)

def other(t: str, cfg: Config) -> str: return cfg.terminals[1] if t == cfg.terminals[0] else cfg.terminals[0]
def local_hour(t: float) -> float: return (t % DAY) / HOUR

class Twin:
    def __init__(self, cfg: Config, policy, seed: int = 0):
        self.cfg, self.policy, self.rng = cfg, policy, np.random.default_rng(seed)
        self.env = simpy.Environment()
        self.doors = {t: simpy.PriorityResource(self.env, capacity=cfg.doors) for t in cfg.terminals}
        self.pool = {t: [] for t in cfg.terminals}
        self.shipments: list[Shipment] = []; self.trips: list[Trip] = []
        n = cfg.av_fleet; self.avs = [AV(i, cfg.terminals[i % 2]) for i in range(n)]
        self.cost = {"human_miles": 0.0, "av_miles": 0.0, "human_dispatches": 0}
        self._sid = 0

    # ---------------- demand ----------------
    def _demand(self, origin: str):
        cfg = self.cfg; prof = np.array(cfg.hourly_profile, float); prof /= prof.sum()
        dest = other(origin, cfg); horizon = cfg.days * DAY
        for day in range(cfg.days):
            n = self.rng.poisson(cfg.shipments_per_day[origin])
            hours = self.rng.choice(24, size=n, p=prof); mins = self.rng.uniform(0, HOUR, size=n)
            for t in sorted(day * DAY + hours * HOUR + mins):
                pal = int(self.rng.integers(cfg.pallets_per_shipment[0], cfg.pallets_per_shipment[1] + 1))
                cons = str(self.rng.choice(cfg.endpoints[dest])) if self.rng.random() < cfg.endpoint_share else dest
                due = t + HOUR * self.rng.uniform(*cfg.sla_hours)
                ready = t + (HOUR * self.rng.uniform(*cfg.late_pickup_hours) if self.rng.random() < cfg.late_pickup_prob else 0.0)
                s = Shipment(self._sid, origin, dest, cons, pal, ready, due); self._sid += 1; self.shipments.append(s)
                if ready < horizon: self.env.process(self._arrive(s))
        yield self.env.timeout(0)

    def _arrive(self, s: Shipment):
        yield self.env.timeout(max(0.0, s.ready - self.env.now))
        with self.doors[s.origin].request(priority=1) as req:      # inbound P&D has lower priority than linehaul
            yield req; yield self.env.timeout(s.pallets * self.cfg.unload_min_per_pallet)
        s.in_pool = self.env.now; self.pool[s.origin].append(s)

    # ---------------- disruptions ----------------
    def av_blocked(self, t: float) -> bool:
        h = local_hour(t); a, b = self.cfg.av_hours
        return not (a <= h < b) or any(s <= t < e for s, e in self.cfg.weather_hold)

    def _dock_outages(self):
        for term, s, e, lost in self.cfg.dock_outage:
            self.env.process(self._block_doors(term, s, e, lost))
        yield self.env.timeout(0)

    def _block_doors(self, term, s, e, lost):
        yield self.env.timeout(s); reqs = [self.doors[term].request(priority=-1) for _ in range(lost)]
        for r in reqs: yield r
        yield self.env.timeout(max(0.0, e - self.env.now))
        for r in reqs: self.doors[term].release(r)

    # ---------------- linehaul ----------------
    def _run(self, d: Departure, av: AV | None):
        cfg, env = self.cfg, self.env
        to_ep = d.stop not in cfg.terminals; pal = sum(s.pallets for s in d.shipments)
        dest = other(d.origin, cfg)
        if d.shipments:
            with self.doors[d.origin].request(priority=0) as req:
                yield req; yield env.timeout(pal * cfg.load_min_per_pallet)
        t0 = env.now
        for s in d.shipments: s.departed, s.mode, s.direct = t0, d.vehicle, to_ep
        tr = Trip(d.origin, d.stop, d.vehicle, pal, t0, empty=not d.shipments); self.trips.append(tr)
        miles = cfg.lane_miles + (cfg.endpoint_extra_miles if to_ep else 0)
        if d.vehicle == "av": self.cost["av_miles"] += miles
        else: self.cost["human_miles"] += miles; self.cost["human_dispatches"] += 1
        yield env.timeout(cfg.transit_min(d.vehicle == "av", to_ep)); tr.arrive = env.now
        if to_ep:   # 3P dock: assume a door is waiting (appointment), no terminal contention
            yield env.timeout(pal * cfg.unload_min_per_pallet)
        elif d.shipments:
            with self.doors[dest].request(priority=0) as req:
                yield req; yield env.timeout(pal * cfg.unload_min_per_pallet)
        for s in d.shipments:
            s.delivered = env.now if (to_ep or not s.to_endpoint) else self._final_mile(env.now)
        if av is not None:
            if to_ep:  # reposition from endpoint back to the destination terminal
                yield env.timeout(60.0 * cfg.endpoint_extra_miles / cfg.av_mph); self.cost["av_miles"] += cfg.endpoint_extra_miles
            av.loc, av.busy, av.free_at = dest, False, env.now
            span = env.now - t0; (av.__setattr__("empty_min", av.empty_min + span) if not d.shipments else av.__setattr__("loaded_min", av.loaded_min + span))

    def _final_mile(self, t: float) -> float:
        """Endpoint freight that went via the terminal: 60 min cross-dock, then local delivery runs 07:00-17:00 (+60 min drive)."""
        t += 60.0; h = local_hour(t)
        if h < 7: t += (7 - h) * HOUR
        elif h >= 17: t += (24 - h + 7) * HOUR
        return t + 60.0

    # ---------------- control loop ----------------
    def _control(self):
        cfg = self.cfg
        while True:
            for d in self.policy(self, self.env.now):
                for s in d.shipments: self.pool[d.origin].remove(s)
                av = None
                if d.vehicle == "av":
                    av = next(a for a in self.avs if not a.busy and a.loc == d.origin); av.busy = True
                    av.eta = self.env.now + est_cycle(cfg, d)
                self.env.process(self._run(d, av))
            yield self.env.timeout(cfg.tick_min)

    def idle_avs(self, term: str) -> list[AV]: return [a for a in self.avs if not a.busy and a.loc == term]

    def run(self, extra_days: int = 3):
        for t in self.cfg.terminals: self.env.process(self._demand(t))
        self.env.process(self._dock_outages()); self.env.process(self._control())
        self.env.run(until=(self.cfg.days + extra_days) * DAY)
        return self
