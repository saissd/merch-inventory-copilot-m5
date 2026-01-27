import pandas as pd

def recommend_assortment(pricing_rec: pd.DataFrame, forecast_df: pd.DataFrame, max_items_per_store: int = 200, min_items_per_cat: int = 10) -> pd.DataFrame:
    if pricing_rec.empty:
        return pd.DataFrame()

    meta = forecast_df[["item_id","store_id","cat_id"]].drop_duplicates()
    df = pricing_rec.merge(meta, on=["item_id","store_id"], how="left")
    df["profit"] = df["profit"].fillna(0.0)

    picks = []
    for store, g in df.groupby("store_id", sort=False):
        g = g.sort_values("profit", ascending=False).copy()
        picked = set()

        # Ensure diversity
        for cat, cg in g.groupby("cat_id", sort=False):
            top = cg.head(min_items_per_cat)
            for _, r in top.iterrows():
                key = (r["item_id"], r["store_id"])
                if key not in picked:
                    picked.add(key)
                    picks.append(r)

        # Fill remaining capacity
        if len(picked) < max_items_per_store:
            remaining = g[~g.apply(lambda r: (r["item_id"], r["store_id"]) in picked, axis=1)]
            need = max_items_per_store - len(picked)
            picks.extend([r for _, r in remaining.head(need).iterrows()])

    out = pd.DataFrame(picks)
    keep = [c for c in ["store_id","cat_id","item_id","base_price","markdown","opt_price","profit","elasticity"] if c in out.columns]
    return out[keep].drop_duplicates(subset=["store_id","item_id"]).sort_values(["store_id","profit"], ascending=[True, False])
