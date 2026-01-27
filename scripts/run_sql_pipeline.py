import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import os
import duckdb

from src.m5_io import read_m5_from_zip
from src.features import to_long_sales, join_calendar_prices, add_time_series_features

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip_path", required=True)
    ap.add_argument("--db_path", default="reports/m5.duckdb")
    ap.add_argument("--max_series", type=int, default=2000)
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.db_path), exist_ok=True)
    con = duckdb.connect(args.db_path)

    m5 = read_m5_from_zip(args.zip_path)
    sales_long = to_long_sales(m5["sales_train_validation"], max_series=args.max_series)
    joined = join_calendar_prices(sales_long, m5["calendar"], m5["sell_prices"])
    feat = add_time_series_features(joined).dropna(subset=["date"])

    fact = feat[["date","store_id","item_id","dept_id","cat_id","state_id","units","sell_price_filled"]]
    con.execute("CREATE OR REPLACE TABLE fact_sales AS SELECT * FROM fact")

    sql_path = os.path.join("scripts","sql","examples.sql")
    q = open(sql_path, "r", encoding="utf-8").read()
    df = con.execute(q).fetchdf()

    out_csv = os.path.join("reports", "sql_top_items.csv")
    os.makedirs("reports", exist_ok=True)
    df.to_csv(out_csv, index=False)

    print("DONE ✅", out_csv)

if __name__ == "__main__":
    main()
