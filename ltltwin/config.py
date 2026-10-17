"""All modelling assumptions live here, explicitly. None of these are Waabi/Volvo/Warp figures;
they are public-domain-plausible defaults chosen for a synthetic study and are swept in experiments."""
from dataclasses import dataclass, field

MIN = 1; HOUR = 60; DAY = 24 * HOUR

@dataclass
class Config:
    # --- network -------------------------------------------------------------
    terminals: tuple = ("DAL", "HOU")
    # third-party endpoints reachable directly by linehaul (customer DCs / partner docks), by metro
    endpoints: dict = field(default_factory=lambda: {"DAL": ("DAL-3P-A", "DAL-3P-B"), "HOU": ("HOU-3P-A", "HOU-3P-B")})
    lane_miles: float = 240.0               # I-45 terminal-to-terminal, approx.
    endpoint_extra_miles: float = 20.0      # terminal metro -> 3P endpoint
    human_mph: float = 58.0                 # door-to-door average incl. traffic
    av_mph: float = 55.0                    # assume conservative AV speed policy
    # --- operations ----------------------------------------------------------
    doors: int = 6                          # doors per terminal usable for linehaul
    unload_min_per_pallet: float = 2.0
    load_min_per_pallet: float = 2.5
    trailer_pallets: int = 26               # 53' dry van, single-stacked
    av_fleet: int = 2                       # AV tractors dedicated to the lane, split across terminals
    av_hours: tuple = (5, 21)               # AVs may be *dispatched* (start loading) only within [start, end) local hours (assumption); start > end wraps midnight, e.g. (21, 5)
    av_direct_to_endpoint: bool = True      # AV may deliver straight to a 3P endpoint (as in the Oct 2026 release)
    human_driver_hours: float = 11.0        # US HOS drive limit; one-way lane fits easily
    # --- costs (USD, assumptions) ---------------------------------------------
    human_cost_per_mile: float = 2.30
    av_cost_per_mile: float = 1.60          # incl. observer-phase overhead amortised; swept in sensitivity
    human_dispatch_fixed: float = 150.0     # driver call-out / minimum pay per trip
    late_penalty_per_shipment: float = 75.0 # service failure cost used by optimising policies & reported cost
    # --- demand --------------------------------------------------------------
    days: int = 14
    warmup_days: int = 2                    # KPIs exclude shipments created during warm-up
    shipments_per_day: dict = field(default_factory=lambda: {"DAL": 110, "HOU": 90})  # each direction, pre-noise
    pallets_per_shipment: tuple = (1, 6)    # uniform integer
    endpoint_share: float = 0.35            # share of shipments consigned to a 3P endpoint (else to the terminal)
    # ready-time profile: most freight arrives at the origin terminal after afternoon P&D sweeps
    hourly_profile: tuple = (1,1,1,1,1,1,2,2,3,3,4,4,4,5,6,8,10,10,9,7,5,3,2,1)
    sla_hours: tuple = (12, 28)             # due = ready + U[lo, hi] h; calibrated so human-only ~92.5% on-time (experiments/calibrate.py)
    # --- disruptions (off by default) -------------------------------------------
    weather_hold: tuple = ()                # ((start_min, end_min), ...): AV departures blocked
    dock_outage: tuple = ()                 # ((terminal, start_min, end_min, doors_lost), ...)
    late_pickup_prob: float = 0.0           # share of shipments whose ready time slips
    late_pickup_hours: tuple = (1, 4)
    late_pickup_window: tuple = ()          # (start_min, end_min): restrict late pickups to a surge window; () = whole run
    # --- dispatcher -------------------------------------------------------------
    tick_min: int = 15                      # decision epoch
    human_sweep_hours: tuple = (22, 2)      # fixed human linehaul departures (local hour) used by baselines

    def __post_init__(self): self.validate()

    def validate(self):
        """Reject configs that would otherwise run silently and produce meaningless KPIs. Raises ValueError."""
        def need(ok, msg):
            if not ok: raise ValueError(f"invalid Config: {msg}")
        a, b = self.av_hours
        need(0 <= a <= 24 and 0 <= b <= 24 and a != b, f"av_hours={self.av_hours}: need 0 <= start, end <= 24 and start != end (start > end wraps midnight)")
        lo, hi = self.pallets_per_shipment
        need(self.trailer_pallets >= 1, f"trailer_pallets={self.trailer_pallets} must be >= 1")
        need(1 <= lo <= hi <= self.trailer_pallets, f"pallets_per_shipment={self.pallets_per_shipment}: need 1 <= lo <= hi <= trailer_pallets={self.trailer_pallets} (shipments are not split)")
        need(self.av_fleet >= 0, f"av_fleet={self.av_fleet} must be >= 0")
        need(self.tick_min > 0, f"tick_min={self.tick_min} must be > 0")
        need(self.human_mph > 0 and self.av_mph > 0, "speeds must be > 0")
        need(self.doors >= 1, f"doors={self.doors} must be >= 1")
        need(0 <= self.sla_hours[0] <= self.sla_hours[1], f"sla_hours={self.sla_hours}: need 0 <= lo <= hi")
        need(all(n >= 0 for n in self.shipments_per_day.values()), "shipments_per_day must be >= 0")
        need(self.days > self.warmup_days >= 0, "need days > warmup_days >= 0")

    def av_window_open(self, hour: float) -> bool:
        a, b = self.av_hours
        return a <= hour < b if a < b else (hour >= a or hour < b)

    def transit_min(self, av: bool, to_endpoint: bool) -> float:
        miles = self.lane_miles + (self.endpoint_extra_miles if to_endpoint else 0.0)
        return 60.0 * miles / (self.av_mph if av else self.human_mph)
