import numpy as np
import pandas as pd
from typing import Dict
from scipy.stats import norm

def compute_inventory_policy(forecast_df: pd.DataFrame, service_level: float = 0.95, lead_time_days: int = 7) -> pd.DataFrame:
    z = float(norm.ppf(service_level))
    df = forecast_df.sort_values(["id","date"]).copy()

    sigma_day = df["roll_std_28"].fillna(0.0).astype(np.float32)
    mu_day = df["pred_units"].astype(np.float32)

    mu_lt = mu_day * lead_time_days
    sigma_lt = sigma_day * np.sqrt(lead_time_days)

    df["safety_stock"] = (z * sigma_lt).astype(np.float32)
    df["reorder_point"] = (mu_lt + df["safety_stock"]).astype(np.float32)
    return df

def simulate_replenishment(
    df: pd.DataFrame,
    lead_time_days: int = 7,
    initial_on_hand_days: int = 14,
    holding_cost_per_unit_day: float = 0.01,
    stockout_penalty_per_unit: float = 0.50
) -> Dict[str, float]:
    sim = df.sort_values(["id","date"]).copy()

    total_stockout_units = 0.0
    total_holding_units = 0.0

    for _id, g in sim.groupby("id", sort=False):
        g = g.reset_index(drop=True)
        if g.empty:
            continue

        mean_pred = float(g["pred_units"].mean())
        on_hand = initial_on_hand_days * mean_pred
        orders = []

        for t in range(len(g)):
            if orders:
                arrived = [o for o in orders if o[0] == t]
                if arrived:
                    on_hand += sum(q for _, q in arrived)
                orders = [o for o in orders if o[0] != t]

            demand = float(g.loc[t, "units"])
            fulfilled = min(on_hand, demand)
            on_hand -= fulfilled

            if demand > fulfilled:
                total_stockout_units += (demand - fulfilled)

            total_holding_units += max(on_hand, 0.0)

            rop = float(g.loc[t, "reorder_point"])
            target = float(g.loc[t, "pred_units"] * lead_time_days + g.loc[t, "safety_stock"])

            if on_hand <= rop:
                order_qty = max(target - on_hand, 0.0)
                arrive_t = min(t + lead_time_days, len(g)-1)
                orders.append((arrive_t, order_qty))

    holding_cost = total_holding_units * holding_cost_per_unit_day
    stockout_cost = total_stockout_units * stockout_penalty_per_unit

    return {
        "stockout_units": float(total_stockout_units),
        "avg_holding_units": float(total_holding_units / max(1, len(sim))),
        "holding_cost": float(holding_cost),
        "stockout_cost": float(stockout_cost),
        "total_cost": float(holding_cost + stockout_cost),
    }
