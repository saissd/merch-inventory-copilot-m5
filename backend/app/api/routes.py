import os
from fastapi.responses import JSONResponse

import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.agent.orchestrator import agent_answer
from app.core.config import settings
from app.services.pipeline import forecast_future, retrain, run_all, run_sql
from app.services.reports import future_forecast, recs, summary


router = APIRouter()


class RunReq(BaseModel):
    zip_path: str
    max_series: int = 3000


class AgentReq(BaseModel):
    message: str
    store_id: str | None = None
    item_id: str | None = None


@router.get("/health")
def health():
    return {
        "status": "ok",
        "marker": "DEBUG_123",   # <-- add this
        "reports_dir": settings.REPORTS_DIR,
        "pipeline_repo": settings.PIPELINE_REPO,
    }


@router.get("/summary")
def get_summary():
    return summary()


@router.post("/pipeline/run_all")
def p_run_all(req: RunReq):
    return run_all(req.zip_path, req.max_series)


@router.post("/pipeline/forecast_future")
def p_future(req: RunReq):
    return forecast_future(req.zip_path, req.max_series)


@router.post("/pipeline/run_sql")
def p_sql(req: RunReq):
    return run_sql(req.zip_path, req.max_series)


@router.post("/pipeline/retrain")
def p_retrain(req: RunReq):
    return retrain(req.zip_path, max(1000, req.max_series))


@router.get("/forecast/future")
def get_future(store_id: str | None = None, item_id: str | None = None, limit: int = 1000):
    return future_forecast(store_id, item_id, limit)


@router.get("/recs/{kind}")
def get_recs(kind: str, store_id: str | None = None, limit: int = 200):
    if kind not in {"inventory", "pricing", "assortment", "sql_top_items"}:
        raise HTTPException(400, "Invalid kind")
    return recs(kind, store_id, limit)



@router.post("/agent/chat")
def chat(req: AgentReq):
    try:
        out = agent_answer(req.message, req.store_id, req.item_id)
        return {"answer": out}
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "agent_chat_failed", "trace": traceback.format_exc()},
        )



@router.get("/downloads/{filename}")
def download(filename: str):
    """Download a report artifact (CSV/JSON) from REPORTS_DIR."""

    allowed = {
        "summary_metrics.json",
        "retrain_metrics.json",
        "recommendations_inventory.csv",
        "recommendations_pricing.csv",
        "recommendations_assortment.csv",
        "future_forecast_next_28d.csv",
        "sql_top_items.csv",
        "m5.duckdb",
    }
    if filename not in allowed:
        raise HTTPException(404, "Not found")

    path = os.path.join(settings.REPORTS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(404, f"Missing file in REPORTS_DIR: {filename}")

    media = "text/csv" if filename.endswith(".csv") else "application/json"
    if filename.endswith(".duckdb"):
        media = "application/octet-stream"
    return FileResponse(path, media_type=media, filename=filename)
