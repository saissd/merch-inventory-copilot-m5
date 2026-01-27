import os

from pydantic import BaseModel


def _repo_root() -> str:
    # backend/app/core/config.py -> backend/app/core -> backend/app -> backend -> repo_root
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", ".."))


class Settings(BaseModel):
    """Runtime configuration.

    - PIPELINE_REPO: path to the separate forecasting/optimization repo (optional)
    - REPORTS_DIR: where CSV/JSON artifacts live (defaults to repo_root/reports)
    """

    PIPELINE_REPO: str = os.getenv("PIPELINE_REPO", "")
    REPORTS_DIR: str = os.getenv("REPORTS_DIR", os.path.join(_repo_root(), "reports"))


settings = Settings()