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
    av_hours: tuple = (5, 21)               # AV may *depart* only within [start, end) local hours (assumption)
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

    def transit_min(self, av: bool, to_endpoint: bool) -> float:
        miles = self.lane_miles + (self.endpoint_extra_miles if to_endpoint else 0.0)
        return 60.0 * miles / (self.av_mph if av else self.human_mph)
