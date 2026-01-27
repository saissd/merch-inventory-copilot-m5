import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import argparse
import os
import json
import pandas as pd
from joblib import dump

from src.m5_io import read_m5_from_zip
from src.features import to_long_sales, join_calendar_prices, add_time_series_features, make_train_valid_split
from src.forecast import train_forecast_model
from src.config import PipelineConfig

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip_path", required=True)
    ap.add_argument("--max_series", type=int, default=5000)
    ap.add_argument("--out_dir", default="reports")
    args = ap.parse_args()

    cfg = PipelineConfig()
    os.makedirs(args.out_dir, exist_ok=True)

    m5 = read_m5_from_zip(args.zip_path)
    sales_long = to_long_sales(m5["sales_train_validation"], max_series=args.max_series)
    joined = join_calendar_prices(sales_long, m5["calendar"], m5["sell_prices"])
    feat = add_time_series_features(joined).dropna(subset=["date"])

    train_df, valid_df = make_train_valid_split(feat, horizon=cfg.horizon)
    model, metrics, _ = train_forecast_model(train_df, valid_df)

    dump(model, os.path.join(args.out_dir, "lgbm_model.joblib"))
    with open(os.path.join(args.out_dir, "retrain_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("DONE ✅ retrained model saved.")

if __name__ == "__main__":
    main()
