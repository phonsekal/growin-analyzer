# app/routers.py
from fastapi import APIRouter, HTTPException
from app.services import hitung_analisis_saham, hitung_momentum_gorengan
from app.config import INDEX_BLUECHIP_UTAMA, WATCHLIST_GORENGAN

router = APIRouter(prefix="/v1")

@router.get("/analisis/swing/{ticker}")
async def get_analisis_swing(ticker: str):
    hasil = hitung_analisis_saham(ticker)
    if not hasil:
        raise HTTPException(status_code=404, detail=f"Saham {ticker} gagal diproses.")
    return hasil

@router.get("/analisis/gorengan/{ticker}")
async def get_analisis_gorengan(ticker: str):
    hasil = hitung_momentum_gorengan(ticker)
    if not hasil:
        raise HTTPException(status_code=404, detail=f"Saham {ticker} gagal diproses.")
    return hasil

@router.get("/screener/swing-dividen")
async def run_screener_swing_dividen():
    saham_lolos = []
    for ticker in INDEX_BLUECHIP_UTAMA:
        symbol = ticker.replace(".JK", "")
        data = hitung_analisis_saham(symbol)
        if data and not data["guardrail_proteksi"]["wajib_stop_loss"]:
            if "BUY" in data["rekomendasi_akhir"] or "SEROK" in data["rekomendasi_akhir"] or "PASIF" in data["rekomendasi_akhir"]:
                saham_lolos.append({
                    "saham": data["saham"],
                    "harga_saat_ini": data["harga_saat_ini"],
                    "yield_dividen": data["fundamental"]["status_dividen"],
                    "arus_modal": data["teknikal"]["status_arus_modal"],
                    "rekomendasi": data["rekomendasi_akhir"]
                })
    return {"status": "success", "jumlah_saham_lolos": len(saham_lolos), "data_watchlist_siap_beli": saham_lolos}

@router.get("/screener/gorengan-momentum")
async def run_screener_gorengan_momentum():
    saham_lolos = []
    for ticker in WATCHLIST_GORENGAN:
        symbol = ticker.replace(".JK", "")
        data = hitung_momentum_gorengan(symbol)
        if data and "LOLOS" in data["status_filter"]:
            saham_lolos.append({
                "saham": data["saham"],
                "harga_saat_ini": data["harga_saat_ini"],
                "lonjakan_volume": data["indikator"]["lonjakan_volume"],
                "adx_power": data["indikator"]["adx_power"],
                "auto_tp_growin": data["bracket_order_growin"]["target_take_profit"],
                "auto_cl_growin": data["bracket_order_growin"]["batas_cut_loss"]
            })
    return {"status": "success", "jumlah_saham_meledak": len(s导), "radar_saham_gorengan_aktif": saham_lolos}
