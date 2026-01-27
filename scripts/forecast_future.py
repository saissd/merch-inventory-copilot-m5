
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import future as fut
import argparse
import os
import pandas as pd

from src.m5_io import read_m5_from_zip
from src.features import to_long_sales, join_calendar_prices, add_time_series_features
from src.forecast import train_forecast_model
from src.future import build_future_frame, recursive_forecast
from src.config import PipelineConfig

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip_path", required=True)
    ap.add_argument("--max_series", type=int, default=2000)
    ap.add_argument("--out_dir", default="reports")
    args = ap.parse_args()

    cfg = PipelineConfig()
    os.makedirs(args.out_dir, exist_ok=True)

    m5 = read_m5_from_zip(args.zip_path)
    sales_long = to_long_sales(m5["sales_train_validation"], max_series=args.max_series)
    joined = join_calendar_prices(sales_long, m5["calendar"], m5["sell_prices"])
    feat = add_time_series_features(joined).dropna(subset=["date"])

    train_df = feat[feat["date"] <= feat["date"].max() - pd.Timedelta(days=cfg.horizon)].copy()
    valid_df = feat[feat["date"] >  feat["date"].max() - pd.Timedelta(days=cfg.horizon)].copy()
    model, metrics, _ = train_forecast_model(train_df, valid_df)

    future_base = fut.build_future_frame(feat, m5["calendar"], m5["sell_prices"], horizon=cfg.horizon)
    future_pred = fut.recursive_forecast(model, feat, future_base)

    out_path = os.path.join(args.out_dir, "future_forecast_next_28d.csv")
    cols = ["id","item_id","store_id","date","pred_units","sell_price_filled","snap","is_event"]
    future_pred[cols].to_csv(out_path, index=False)

    print("DONE ✅ future forecast saved:", out_path)
    print("Forecast metrics (validation):", metrics)

if __name__ == "__main__":
    main()
