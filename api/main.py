# api/index.py
import sys
import os

# Baris sakti: Memaksa Vercel memasukkan folder root ke dalam path sistem Python
# Ini adalah solusi mutlak agar error "not import" atau ModuleNotFoundError hilang total
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from app.routers import router

app = FastAPI(
    title="GROWIN Multi-Strategy Trading Engine",
    description="Sistem API Otomatis Penggabungan Strategi Swing Dividen & Day Trading ADX Forum v4.0",
    version="4.0"
)

app.include_router(router)

@app.get("/")
def check_status():
    return {"status": "active", "message": "Server v4.0 Online di Vercel! Siap kirim data ke n8n."}
