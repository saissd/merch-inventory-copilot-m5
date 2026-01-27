"""Agent orchestrator.

Goal: generate decision-grade recommendations backed by *only* local report files.

This keeps the demo trustworthy (no hallucinated numbers):
  - We compute KPIs and tables from CSV/JSON in REPORTS_DIR.
  - Gemini (optional) is used only for concise explanation text.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.agent.gemini_client import gemini_generate
from app.services.reports import summary, future_forecast, recs


def _pct_change(before: Optional[float], after: Optional[float]) -> Optional[float]:
    if before is None or after is None:
        return None
    if before == 0:
        return None
    return (after - before) / before


def _round(v: Optional[float], nd: int = 3) -> Optional[float]:
    if v is None:
        return None
    try:
        return round(float(v), nd)
    except Exception:
        return None


def _top_inventory_actions(inv_rows: List[Dict[str, Any]], n: int = 10) -> List[Dict[str, Any]]:
    # Prefer highest reorder_point (more urgent / high volume); fallback to avg_pred.
    def key(r):
        return (
            float(r.get("reorder_point", 0.0) or 0.0),
            float(r.get("avg_pred", 0.0) or 0.0),
        )

    out = sorted(inv_rows, key=key, reverse=True)[:n]
    for i, r in enumerate(out, 1):
        r = r  # noqa
        r["rank"] = i
        # Light formatting
        for k in ("avg_pred", "reorder_point", "safety_stock"):
            if k in r:
                try:
                    r[k] = _round(float(r[k]), 3)
                except Exception:
                    pass
    return out


def _top_pricing_actions(prc_rows: List[Dict[str, Any]], n: int = 10) -> List[Dict[str, Any]]:
    # Prefer rows where markdown > 0, then highest profit.
    def key(r):
        return (
            float(r.get("markdown", 0.0) or 0.0),
            float(r.get("profit", 0.0) or 0.0),
        )

    out = sorted(prc_rows, key=key, reverse=True)[:n]
    for i, r in enumerate(out, 1):
        r["rank"] = i
        for k in ("base_price", "opt_price", "markdown", "elasticity", "profit"):
            if k in r:
                try:
                    r[k] = _round(float(r[k]), 3)
                except Exception:
                    pass
    return out


def _compose_markdown_answer(
    key_metrics: Dict[str, Any],
    decisions: List[str],
    inv_top: List[Dict[str, Any]],
    prc_top: List[Dict[str, Any]],
    tradeoffs: List[str],
    assumptions: List[str],
    confidence: float,
) -> str:
    # Keep this deterministic and presentable.
    lines: List[str] = []
    lines.append("KEY METRICS")
    for k in (
        "forecast_valid_wape",
        "forecast_valid_rmse",
        "stockout_units_before",
        "stockout_units_after",
        "stockout_units_pct_change",
        "total_cost_before",
        "total_cost_after",
        "total_cost_pct_change",
    ):
        if k in key_metrics and key_metrics[k] is not None:
            lines.append(f"- {k}: {key_metrics[k]}")

    lines.append("")
    lines.append("DECISION (what to do now)")
    for d in decisions:
        lines.append(f"- {d}")

    def md_table(rows: List[Dict[str, Any]], cols: List[str]) -> List[str]:
        if not rows:
            return ["(no rows)"]
        out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
        for r in rows:
            out.append("| " + " | ".join(str(r.get(c, "")) for c in cols) + " |")
        return out

    lines.append("")
    lines.append("TOP 10 INVENTORY ACTIONS")
    lines += md_table(inv_top, ["rank", "item_id", "avg_pred", "reorder_point", "safety_stock"])

    lines.append("")
    lines.append("TOP 10 PRICING ACTIONS")
    lines += md_table(prc_top, ["rank", "item_id", "base_price", "opt_price", "markdown", "elasticity", "profit"])

    lines.append("")
    lines.append("TRADEOFFS")
    for t in tradeoffs:
        lines.append(f"- {t}")

    lines.append("")
    lines.append("ASSUMPTIONS")
    for a in assumptions:
        lines.append(f"- {a}")

    lines.append("")
    lines.append(f"CONFIDENCE: {round(confidence, 2)}")
    return "\n".join(lines)


def agent_answer(user_message: str, store_id: Optional[str] = None, item_id: Optional[str] = None):
    # 1) Tool calls (deterministic)
    s = summary()
    inv_rows = recs("inventory", store_id=store_id, limit=200)
    prc_rows = recs("pricing", store_id=store_id, limit=200)
    ast_rows = recs("assortment", store_id=store_id, limit=50)
    fut_rows = future_forecast(store_id=store_id, item_id=item_id, limit=50)

    # 2) Key metrics
    inv_before = (s.get("inventory_before") or {})
    inv_after = (s.get("inventory_after") or {})
    stock_before = inv_before.get("stockout_units")
    stock_after = inv_after.get("stockout_units")
    cost_before = inv_before.get("total_cost")
    cost_after = inv_after.get("total_cost")

    key_metrics: Dict[str, Any] = {
        "forecast_valid_wape": _round(s.get("forecast_valid_wape"), 3),
        "forecast_valid_rmse": _round(s.get("forecast_valid_rmse"), 3),
        "stockout_units_before": _round(stock_before, 3),
        "stockout_units_after": _round(stock_after, 3),
        "stockout_units_pct_change": _round(_pct_change(stock_before, stock_after), 3),
        "total_cost_before": _round(cost_before, 3),
        "total_cost_after": _round(cost_after, 3),
        "total_cost_pct_change": _round(_pct_change(cost_before, cost_after), 3),
    }

    inv_top = _top_inventory_actions(inv_rows, 10)
    prc_top = _top_pricing_actions(prc_rows, 10)

    # 3) Decisions (make it “decision grade”)
    decisions: List[str] = []
    if store_id:
        decisions.append(f"Prioritize replenishment for {store_id}: execute reorder_point + safety_stock for the top 10 SKUs below.")
    else:
        decisions.append("Select a store_id (e.g., CA_1) and execute reorder_point + safety_stock for the top 10 SKUs below.")
    if stock_before is not None and stock_after is not None:
        decisions.append(
            f"This policy reduces projected stockout units from {int(stock_before):,} to {int(stock_after):,} (simulated)."
        )
    if cost_before is not None and cost_after is not None:
        decisions.append(
            f"Total cost proxy changes from {int(cost_before):,} to {int(cost_after):,}; validate holding vs. stockout tradeoff for your service-level target."
        )

    # 4) Tradeoffs + assumptions (mostly deterministic)
    tradeoffs = [
        "Lower stockouts usually increases average inventory on hand (holding cost rises while stockout cost falls).",
        "Pricing recommendations depend on elasticity assumptions; validate with A/B or historical promo outcomes.",
        "Forecast error (WAPE/RMSE) compounds into inventory decisions; monitor drift and retrain regularly.",
    ]
    assumptions = [
        "This is a demo using the M5 dataset; item/store IDs are from the dataset, not Nordstrom production catalogs.",
        "Lead time and service level are simplified; reorder_point is based on forecast mean + safety_stock.",
        "Profit and cost are proxies; real systems need unit cost, margin, and markdown constraints.",
    ]
    confidence = 0.7

    # 5) Optional: short LLM explanation (kept small to avoid truncation)
    explain_prompt = f"""
You are an ML engineer explaining a retail merchandising/inventory recommendation to a recruiter.
Write 6-8 bullet points max. Use the exact KPI numbers below; do not invent anything.

User goal: {user_message}
Store: {store_id or 'N/A'}

KPIs:
- forecast_valid_wape: {key_metrics.get('forecast_valid_wape')}
- forecast_valid_rmse: {key_metrics.get('forecast_valid_rmse')}
- stockout_units_before: {key_metrics.get('stockout_units_before')}
- stockout_units_after: {key_metrics.get('stockout_units_after')}
- total_cost_before: {key_metrics.get('total_cost_before')}
- total_cost_after: {key_metrics.get('total_cost_after')}

Focus on: demand forecasting → inventory optimization → pricing/markdown → assortment, and mention monitoring/retraining.
"""
    explanation = gemini_generate(explain_prompt).strip()

    answer_md = _compose_markdown_answer(
        key_metrics=key_metrics,
        decisions=decisions,
        inv_top=inv_top,
        prc_top=prc_top,
        tradeoffs=tradeoffs,
        assumptions=assumptions,
        confidence=confidence,
    )

    tool_calls = [
        {"tool": "summary", "ok": bool(s)},
        {"tool": "recs.inventory", "rows": len(inv_rows)},
        {"tool": "recs.pricing", "rows": len(prc_rows)},
        {"tool": "recs.assortment", "rows": len(ast_rows)},
        {"tool": "forecast.future", "rows": len(fut_rows)},
    ]

    downloads = {
        "summary_metrics.json": "/downloads/summary_metrics.json",
        "recommendations_inventory.csv": "/downloads/recommendations_inventory.csv",
        "recommendations_pricing.csv": "/downloads/recommendations_pricing.csv",
        "recommendations_assortment.csv": "/downloads/recommendations_assortment.csv",
        "future_forecast_next_28d.csv": "/downloads/future_forecast_next_28d.csv",
    }

    return {
        "answer": answer_md,
        "explanation": explanation,
        "key_metrics": key_metrics,
        "decisions": decisions,
        "inventory_actions": inv_top,
        "pricing_actions": prc_top,
        "assortment_preview": ast_rows[:10],
        "future_forecast_preview": fut_rows[:10],
        "tool_calls": tool_calls,
        "downloads": downloads,
    }
