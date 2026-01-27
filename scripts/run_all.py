import argparse
import os
import sys

# allow `python scripts/run_all.py` from repo root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.config import PipelineConfig
from src.m5_io import read_m5_from_zip
from src.features import to_long_sales, join_calendar_prices, add_time_series_features, make_train_valid_split
from src.forecast import train_forecast_model, save_model
from src.inventory import compute_inventory_policy, simulate_replenishment
from src.pricing import estimate_elasticity_loglog, optimize_markdown
from src.plots import plot_forecast_example, plot_wape_by_store, plot_before_after_bars
from src.utils import ensure_dir, save_json
from src.assortment import recommend_assortment
from src.assortment import recommend_assortment


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip_path", required=True)
    ap.add_argument("--max_series", type=int, default=3000)
    ap.add_argument("--out_dir", default="reports")
    args = ap.parse_args()

    cfg = PipelineConfig()
    out_dir = args.out_dir
    fig_dir = os.path.join(out_dir, "figures")
    ensure_dir(out_dir)
    ensure_dir(fig_dir)

    print("1) Loading M5 from zip...")
    m5 = read_m5_from_zip(args.zip_path)

    print("2) Build long dataset + joins...")
    sales_long = to_long_sales(m5["sales_train_validation"], max_series=args.max_series)
    joined = join_calendar_prices(sales_long, m5["calendar"], m5["sell_prices"])
    feat = add_time_series_features(joined)
    feat = feat.dropna(subset=["date"]).copy()

    print("3) Train + validate forecast model...")
    train_df, valid_df = make_train_valid_split(feat, horizon=cfg.horizon)
    model, metrics, valid_pred = train_forecast_model(train_df, valid_df)
    save_model(model, os.path.join(out_dir, "lgbm_model.joblib"))

    print("4) Forecast charts...")
    plot_forecast_example(valid_pred, os.path.join(fig_dir, "forecast_actual_vs_pred.png"))
    plot_wape_by_store(valid_pred, os.path.join(fig_dir, "backtest_wape_by_store.png"))

    print("5) Inventory positioning + simulation...")
    inv_df = compute_inventory_policy(valid_pred, service_level=cfg.service_level, lead_time_days=cfg.lead_time_days)

    inv_before = inv_df.copy()
    inv_before["reorder_point"] = -1e9  # effectively disables ordering

    before_metrics = simulate_replenishment(
        inv_before,
        lead_time_days=cfg.lead_time_days,
        holding_cost_per_unit_day=cfg.holding_cost_per_unit_day,
        stockout_penalty_per_unit=cfg.stockout_penalty_per_unit,
    )
    after_metrics = simulate_replenishment(
        inv_df,
        lead_time_days=cfg.lead_time_days,
        holding_cost_per_unit_day=cfg.holding_cost_per_unit_day,
        stockout_penalty_per_unit=cfg.stockout_penalty_per_unit,
    )

    plot_before_after_bars(
        before_metrics["stockout_units"], after_metrics["stockout_units"],
        title="Inventory policy impact: stockout units (lower is better)",
        ylabel="Stockout units",
        out_path=os.path.join(fig_dir, "inventory_stockouts_before_after.png"),
    )

    inv_rec = (
        inv_df.groupby(["item_id","store_id"], as_index=False)
              .agg(avg_pred=("pred_units","mean"),
                   reorder_point=("reorder_point","mean"),
                   safety_stock=("safety_stock","mean"))
              .sort_values("avg_pred", ascending=False)
              .head(200)
    )
    inv_rec.to_csv(os.path.join(out_dir, "recommendations_inventory.csv"), index=False)

    print("6) Pricing / markdown optimization (subset)...")
    top_ids = valid_pred.groupby("id")["units"].sum().sort_values(ascending=False).head(500).index
    price_df = valid_pred[valid_pred["id"].isin(top_ids)].copy()

    elast = estimate_elasticity_loglog(price_df)
    pricing_rec = optimize_markdown(
        price_df,
        elast,
        cost_fraction=cfg.cost_fraction_of_base_price,
        horizon_days=cfg.horizon,
        inventory_days_of_supply=90,   # was 21 inside pricing.py default; make it “overstock”
        markdown_grid=(0.0, 0.10, 0.20, 0.30, 0.40, 0.50),
    )

    pricing_rec.head(500).to_csv(os.path.join(out_dir, "recommendations_pricing.csv"), index=False)
    assort = recommend_assortment(pricing_rec, valid_pred, max_items_per_store=200, min_items_per_cat=10)
    assort.to_csv(os.path.join(out_dir, "recommendations_assortment.csv"), index=False)

    if len(pricing_rec) > 0:
        base_profit = (
            pricing_rec["base_price"] * (1 - cfg.cost_fraction_of_base_price) *
            (pricing_rec["base_demand_per_day"] * cfg.horizon).clip(upper=pricing_rec["inventory_on_hand"])
        ).head(200).sum()
        opt_profit = pricing_rec["profit"].head(200).sum()

        plot_before_after_bars(
            float(base_profit), float(opt_profit),
            title="Pricing/markdown optimization: profit (top 200 recs)",
            ylabel="Profit (proxy units*$)",
            out_path=os.path.join(fig_dir, "pricing_before_after_profit.png"),
        )

    summary = {
        "forecast_valid_rmse": metrics["valid_rmse"],
        "forecast_valid_wape": metrics["valid_wape"],
        "inventory_before": before_metrics,
        "inventory_after": after_metrics,
        "pricing_recommendations_rows": int(len(pricing_rec)),
    }
    save_json(os.path.join(out_dir, "summary_metrics.json"), summary)

    print("\nDONE ✅")
    print(f"Outputs in: {out_dir}/")

if __name__ == "__main__":
    main()
