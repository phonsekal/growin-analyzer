import sys
import os

# Jembatan pengenal agar Vercel bisa membaca folder app di luar folder api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from app.routers import router

app = FastAPI(
    title="GROWIN Multi-Strategy Trading Engine",
    version="4.0"
)

app.include_router(router)

@app.get("/")
def check_status():
    return {"status": "active", "message": "Server v4.0 Online di Vercel!"}

# WAJIB UNTUK VERCEL RUNTIME
handler = app
