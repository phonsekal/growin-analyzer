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
    return {"status": "active", "message": "Server v4.0 Online! Siap kirim data ke n8n."}
