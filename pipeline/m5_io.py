import zipfile
import pandas as pd
from typing import Dict

def read_m5_from_zip(zip_path: str) -> Dict[str, pd.DataFrame]:
    '''
    Reads the core M5 CSVs from the Kaggle zip.
    Returns dict with keys: calendar, sell_prices, sales_train_validation, sales_train_evaluation, sample_submission
    '''
    out = {}
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.endswith(".csv"):
                continue
            with zf.open(name) as f:
                out[name.replace(".csv","")] = pd.read_csv(f)

    return {
        "calendar": out["calendar"],
        "sell_prices": out["sell_prices"],
        "sales_train_validation": out["sales_train_validation"],
        "sales_train_evaluation": out["sales_train_evaluation"],
        "sample_submission": out["sample_submission"],
    }
