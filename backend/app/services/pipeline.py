import os, subprocess, time
from typing import Dict, Any
from app.core.config import settings

def _run(cmd: list[str], cwd: str) -> Dict[str, Any]:
    start = time.time()
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return {
        "cmd": " ".join(cmd),
        "returncode": p.returncode,
        "stdout_tail": (p.stdout or "")[-4000:],
        "stderr_tail": (p.stderr or "")[-4000:],
        "duration_s": round(time.time() - start, 2),
    }

def run_all(zip_path: str, max_series: int = 3000):
    repo = os.path.abspath(settings.PIPELINE_REPO)
    return _run(["python","scripts/run_all.py","--zip_path",zip_path,"--max_series",str(max_series)], repo)

def forecast_future(zip_path: str, max_series: int = 3000):
    repo = os.path.abspath(settings.PIPELINE_REPO)
    return _run(["python","scripts/forecast_future.py","--zip_path",zip_path,"--max_series",str(max_series)], repo)

def run_sql(zip_path: str, max_series: int = 3000):
    repo = os.path.abspath(settings.PIPELINE_REPO)
    return _run(["python","scripts/run_sql_pipeline.py","--zip_path",zip_path,"--max_series",str(max_series)], repo)

def retrain(zip_path: str, max_series: int = 5000):
    repo = os.path.abspath(settings.PIPELINE_REPO)
    return _run(["python","scripts/retrain.py","--zip_path",zip_path,"--max_series",str(max_series)], repo)
