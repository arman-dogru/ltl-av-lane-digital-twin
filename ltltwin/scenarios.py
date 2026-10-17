"""Named demand scenarios. Total daily shipments are equal (200/day) so scenarios differ only in directional balance."""
from .config import Config

def scenario(name: str, **kw) -> Config:
    if name == "balanced":
        return Config(shipments_per_day={"DAL": 100, "HOU": 100}, **kw)
    if name == "imbalanced":   # head-haul DAL->HOU, back-haul HOU->DAL at 3:7 ratio (assumption)
        return Config(shipments_per_day={"DAL": 140, "HOU": 60}, **kw)
    if name == "default":
        return Config(**kw)
    raise ValueError(name)

SCENARIOS = ("balanced", "imbalanced")
