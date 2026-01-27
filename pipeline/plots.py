import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from .utils import ensure_dir

def plot_forecast_example(pred_df: pd.DataFrame, out_path: str, n_series: int = 1):
    ensure_dir(os.path.dirname(out_path))
    by = pred_df.groupby("id")["units"].sum().sort_values(ascending=False).head(n_series).index.tolist()
    sub = pred_df[pred_df["id"].isin(by)].copy()

    fig = plt.figure()
    for _id, g in sub.groupby("id"):
        g = g.sort_values("date")
        plt.plot(g["date"], g["units"], label=f"{_id} actual")
        plt.plot(g["date"], g["pred_units"], label=f"{_id} pred")
    plt.xticks(rotation=30)
    plt.ylabel("Units")
    plt.title("Actual vs Predicted (validation window)")
    plt.legend()
    plt.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)

def plot_wape_by_store(pred_df: pd.DataFrame, out_path: str):
    ensure_dir(os.path.dirname(out_path))
    store = pred_df.groupby("store_id").apply(
        lambda g: np.sum(np.abs(g["units"] - g["pred_units"])) / max(1e-6, np.sum(np.abs(g["units"])))
    ).reset_index()
    store.columns = ["store_id","wape"]
    store = store.sort_values("wape")

    fig = plt.figure()
    plt.bar(store["store_id"].astype(str), store["wape"].values)
    plt.ylabel("WAPE")
    plt.title("Validation WAPE by store")
    plt.xticks(rotation=30)
    plt.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)

def plot_before_after_bars(before: float, after: float, title: str, ylabel: str, out_path: str):
    ensure_dir(os.path.dirname(out_path))
    fig = plt.figure()
    plt.bar(["Before","After"], [before, after])
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
