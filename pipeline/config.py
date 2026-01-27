from dataclasses import dataclass

@dataclass(frozen=True)
class PipelineConfig:
    horizon: int = 28
    service_level: float = 0.95
    lead_time_days: int = 7
    holding_cost_per_unit_day: float = 0.01
    stockout_penalty_per_unit: float = 0.50
    cost_fraction_of_base_price: float = 0.60
