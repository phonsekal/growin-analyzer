# app/routers.py - Versi Perbaikan (2024-05-24)
from fastapi import APIRouter, HTTPException
from app.services import hitung_analisis_saham, hitung_momentum_gorengan
from app.config import INDEX_BLUECHIP_UTAMA, WATCHLIST_GORENGAN

router = APIRouter(prefix="/v1")

# ... (Fungsi /analisis/swing dan /analisis/gorengan tetap sama)

@router.get("/screener/swing-dividen")
async def run_screener_swing_dividen():
    # ... (Logika sama)
    return {"status": "success", "jumlah_saham_lolos": len(saham_lolos), "data_watchlist_siap_beli": saham_lolos}

@router.get("/screener/gorengan-momentum")
async def run_screener_gorengan_momentum():
    saham_lolos = []
    for ticker in WATCHLIST_GORENGAN:
        symbol = ticker.replace(".JK", "")
        data = hitung_momentum_gorengan(symbol)
        # Perbaikan: Menggunakan kunci yang ada di services.py yang diperbarui
        if data and "LOLOS" in data["status_filter"]:
            saham_lolos.append({
                "saham": data["saham"],
                "status": data["status_filter"],
                "rsi_momentum": data["indikator"]["rsi_momentum"],
                "adx_power": data["indikator"]["adx_power"],
                "rekomendasi": data["rekomendasi_aksi"]
            })
    # Perbaikan: Perbaikan typo len(s导) -> len(saham_lolos)
    return {"status": "success", "jumlah_saham_meledak": len(saham_lolos), "radar_saham_gorengan_aktif": saham_lolos}
