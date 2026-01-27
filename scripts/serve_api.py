from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

from src.m5_io import read_m5_from_zip
from src.features import to_long_sales, join_calendar_prices, add_time_series_features
from src.forecast import train_forecast_model
from src.inventory import compute_inventory_policy
from src.pricing import estimate_elasticity_loglog, optimize_markdown
from src.assortment import recommend_assortment
from src.config import PipelineConfig

app = FastAPI(title="Merch & Inventory ML API")

class RunRequest(BaseModel):
    zip_path: str
    max_series: int = 1000

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/run")
def run(req: RunRequest):
    cfg = PipelineConfig()
    m5 = read_m5_from_zip(req.zip_path)
    sales_long = to_long_sales(m5["sales_train_validation"], max_series=req.max_series)
    joined = join_calendar_prices(sales_long, m5["calendar"], m5["sell_prices"])
    feat = add_time_series_features(joined).dropna(subset=["date"])

    train_df = feat[feat["date"] <= feat["date"].max() - pd.Timedelta(days=cfg.horizon)].copy()
    valid_df = feat[feat["date"] >  feat["date"].max() - pd.Timedelta(days=cfg.horizon)].copy()
    model, metrics, valid_pred = train_forecast_model(train_df, valid_df)

    inv = compute_inventory_policy(valid_pred, service_level=cfg.service_level, lead_time_days=cfg.lead_time_days)
    elast = estimate_elasticity_loglog(valid_pred)
    pricing = optimize_markdown(valid_pred, elast, cost_fraction=cfg.cost_fraction_of_base_price, inventory_days_of_supply=90)
    assort = recommend_assortment(pricing, valid_pred, max_items_per_store=200, min_items_per_cat=10)

    return {
        "forecast_metrics": metrics,
        "inventory_rows": int(len(inv)),
        "pricing_rows": int(len(pricing)),
        "assortment_rows": int(len(assort)),
    }
