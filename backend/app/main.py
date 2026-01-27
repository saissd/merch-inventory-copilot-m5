from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from fastapi.responses import PlainTextResponse
import traceback

load_dotenv()

app = FastAPI(title="Merch & Inventory ML API")


@app.get("/")
def root():
    return {
        "service": "Merch & Inventory ML API",
        "health": "/health",
        "docs": "/docs",
        "summary": "/summary",
        "agent_chat": "/agent/chat",
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    return PlainTextResponse(traceback.format_exc(), status_code=500)

