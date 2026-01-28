# Merch & Inventory Copilot (M5 Demo)
## Demo Video
▶️ [Watch the 2-min demo](https://drive.google.com/file/d/1jpmtLvkL9UbxpW9ET8Wv1ZHtc5HtMdSv/view?usp=sharing)


A **merchandising + inventory ML copilot** built on the **Kaggle M5 Forecasting** dataset.  
It combines **demand forecasting**, **inventory recommendations**, **pricing recommendations**, and a **ChatGPT-like copilot UI (with voice input)** into a recruiter-friendly demo that runs locally.

> **Note:** This is a demo using the M5 dataset (not Nordstrom internal data).

---

## What it does

### ✅ Copilot features (FastAPI + React)
- **Demand forecasting** metrics + future forecast preview
- **Inventory actions**: reorder policy outputs + **order_qty** + **days_of_supply**
- **Pricing actions**: base price vs optimized price + markdown + elasticity (demo)
- **Agentic chat endpoint**: returns a manager-ready decision memo + action tables
- **Downloads**: one-click CSV/JSON exports from the UI
- **Professional UI**: ChatGPT-style chat + optional **voice-to-text**

---

## Results (M5 demo)
- Validation: **WAPE ~0.756**, **RMSE ~2.012**
- Stockouts (simulated): **58,855 → 4,338**
- Cost proxy (simulated): **33,883 → 22,503**

---

## Tech stack
- **Backend:** Python, FastAPI, Uvicorn, Pandas, NumPy
- **Frontend:** React (Vite), TypeScript, Tailwind
- **Artifacts:** CSV/JSON reports served via `/downloads/*`

---

## Repo structure

```
.
├── backend/                # FastAPI app
├── frontend/               # React UI (ChatGPT-like + voice)
├── reports/                # demo artifacts (CSV/JSON) used by backend
└── pipeline/               # optional: code to regenerate reports
```

---

## Quickstart (local)

### 1) Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

Check:
- http://127.0.0.1:8001/docs
- http://127.0.0.1:8001/summary

### 2) Frontend
```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL (usually):
- http://localhost:5173

---

## Demo prompts
Try these in the UI:

**Inventory**
- `What should I order today for CA_1? Include item_id, order_qty, days_of_supply (top 5).`
- `Which items will stock out in CA_1 in the next 7 days?`

**Pricing**
- `Suggest pricing actions for CA_1. Show top 5 and include download links.`

**Store switch**
- Change store dropdown to `TX_1`, then ask the same prompt to see different results.

---

## API endpoints (backend)

- `GET /summary` → overall metrics JSON
- `GET /recs/inventory?store_id=CA_1` → inventory actions
- `GET /recs/pricing?store_id=CA_1` → pricing actions
- `POST /agent/chat` → structured manager-ready response
- `GET /downloads/...` → exports (CSV/JSON)

---

## Optional: regenerate reports (pipeline)
This repo includes `pipeline/` code used to generate the CSV/JSON artifacts under `reports/`.  
For a recruiter demo, the app runs using the precomputed artifacts.

(If you want, add exact commands here once you finalize your pipeline entrypoint.)

---

## License / Dataset
Uses the **Kaggle M5 Forecasting** dataset. Please follow Kaggle’s dataset terms.

---

## Contact
**Sai Deshith Sandakacharla**  
LinkedIn: https://www.linkedin.com/in/sai-deshith-6085a8237/  
Email: saideshith1905@gmail.com
