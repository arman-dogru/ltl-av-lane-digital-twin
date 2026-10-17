"""Named demand scenarios. Total daily shipments are equal (200/day) so scenarios differ only in directional balance."""
from .config import Config

def parse(name: str):
    """'balanced@av_fleet=3,demand=1.3,av_hours=(0,24)' -> ('balanced', {...}). `demand` scales shipments_per_day."""
    import ast
    base, _, rest = name.partition("@"); kw = {}
    for part in filter(None, rest.split(";")):
        k, v = part.split("="); kw[k] = ast.literal_eval(v)
    return base, kw

def scenario(name: str, **kw) -> Config:
    if "@" in name:
        base, over = parse(name); scale = over.pop("demand", 1.0); cfg = scenario(base, **{**over, **kw})
        cfg.shipments_per_day = {t: int(round(n * scale)) for t, n in cfg.shipments_per_day.items()}; return cfg
    if name == "balanced":
        return Config(shipments_per_day={"DAL": 100, "HOU": 100}, **kw)
    if name == "imbalanced":   # head-haul DAL->HOU, back-haul HOU->DAL at 3:7 ratio (assumption)
        return Config(shipments_per_day={"DAL": 140, "HOU": 60}, **kw)
    if name == "default":
        return Config(**kw)
    raise ValueError(name)

SCENARIOS = ("balanced", "imbalanced")
