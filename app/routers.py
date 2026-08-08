# app/routers.py - Versi AMAN 500 Error
from fastapi import APIRouter, HTTPException
from app.services import hitung_analisis_saham, hitung_momentum_gorengan
from app.config import INDEX_BLUECHIP_UTAMA, WATCHLIST_GORENGAN

router = APIRouter(prefix="/v1")

# ... (Kode endpoints /analisis/swing dan /analisis/gorengan di sini)

@router.get("/screener/swing-dividen")
async def run_screener_swing_dividen():
    saham_lolos = []
    for ticker in INDEX_BLUECHIP_UTAMA:
        try:
            # ... (Logika penapisan dengan .get() agar aman)
            pass
        except Exception:
            continue
    return {"status": "success", "data": saham_lolos}

@router.get("/screener/gorengan-momentum")
async def run_screener_gorengan_momentum():
    saham_lolos = []
    for ticker in WATCHLIST_GORENGAN:
        try:
            symbol = ticker.replace(".JK", "")
            data = hitung_momentum_gorengan(symbol)
            # PENTING: Gunakan data.get() untuk menghindari KeyError
            if data and "LOLOS" in data.get("status_filter", ""):
                saham_lolos.append({
                    "saham": data.get("saham"),
                    "status": data.get("status_filter"),
                    "rsi_momentum": data.get("indikator", {}).get("rsi_momentum"),
                    "adx_power": data.get("indikator", {}).get("adx_power"),
                    "rekomendasi": data.get("rekomendasi_aksi")
                })
        except Exception:
            continue
            
    return {"status": "success", "radar_saham_gorengan_aktif": saham_lolos}
