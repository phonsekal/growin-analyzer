# app/services.py
import yfinance as yf
import pandas as pd
import numpy as np
from app.config import TARGET_DIVIDEND_YIELD, PE_WAJAR_BANK, PE_WAJAR_UMUM

def hitung_indikator_lengkap(df, period=14):
    """Menghitung RSI, Stochastic, MACD, ADX, dan DI+/DI- secara native"""
    # 1. Hitung RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-10)
    df['RSI14'] = 100 - (100 / (1 + rs))
    
    # 2. Hitung Stochastic (%K dan %D)
    df['L14'] = df['Low'].rolling(window=period).min()
    df['H14'] = df['High'].rolling(window=period).max()
    df['Stoch_K'] = 100 * ((df['Close'] - df['L14']) / (df['H14'] - df['L14'] + 1e-10))
    df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()

    # 3. Hitung MACD
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']

    # 4. Hitung ADX dan DI+ / DI-
    df['UpMove'] = df['High'].diff()
    df['DownMove'] = df['Low'].diff()
    
    df['+DM'] = np.where((df['UpMove'] > df['DownMove']) & (df['UpMove'] > 0), df['UpMove'], 0)
    df['-DM'] = np.where((df['DownMove'] > df['UpMove']) & (df['DownMove'] > 0), df['DownMove'], 0)
    
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    
    atr = df['TR'].rolling(window=period).mean()
    plus_di = 100 * (df['+DM'].rolling(window=period).mean() / (atr + 1e-10))
    minus_di = 100 * (df['-DM'].rolling(window=period).mean() / (atr + 1e-10))
    
    df['+DI14'] = plus_di
    df['-DI14'] = minus_di
    
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10))
    df['ADX14'] = dx.rolling(window=period).mean()
    
    return df

def cek_kekuatan_support_dan_resisten(df, harga_sekarang, toleransi_persen=0.015):
    df['is_low'] = df['Low'] == df['Low'].rolling(window=10, center=True).min()
    titik_terendah_historis = df[df['is_low']]['Low'].tolist()
    jumlah_sentuhan_support = 0
    area_support_kuat = 0
    
    for low_val in titik_terendah_historis:
        if abs(harga_sekarang - low_val) / low_val <= toleransi_persen:
            jumlah_sentuhan_support += 1
            area_support_kuat = int(low_val)
            
    if jumlah_sentuhan_support >= 3:
        klasifikasi_support = f"SANGAT KUAT 🔥 (Telah diuji {jumlah_sentuhan_support}x di area Rp{area_support_kuat})"
    elif jumlah_sentuhan_support == 2:
        klasifikasi_support = f"SEDANG 🛡️ (Telah diuji 2x di area Rp{area_support_kuat})"
    else:
        klasifikasi_support = "LEMAH / DINAMIS 💤 (Hanya mengandalkan garis EMA berjalan)"
        
    resisten_terdekat = int(df['High'].tail(120).max())
    return klasifikasi_support, resisten_terdekat

def hitung_analisis_saham(ticker_symbol: str):
    if not ticker_symbol.endswith(".JK"):
        ticker = f"{ticker_symbol.upper()}.JK"
    else:
        ticker = ticker_symbol.upper()
        
    saham = yf.Ticker(ticker)
    info = saham.info
    
    if not info or 'trailingEps' not in info:
        return None

    # --- A. PROSES DATA FUNDAMENTAL ---
    eps = info.get('trailingEps', 0)
    pbv_ratio = info.get('priceToBook', 0)
    return_on_equity = info.get('returnOnEquity', 0)
    beta = info.get('beta', 1.0)
    
    total_dividen = info.get('dividendRate', 0)
    if total_dividen == 0 or total_dividen is None:
        divs = saham.dividends
        total_dividen = int(divs.resample('YE').sum().iloc[-1]) if not divs.empty else 0

    pe_acuan = PE_WAJAR_BANK if "Bank" in info.get('industry', '') else PE_WAJAR_UMUM
    harga_wajar = int(eps * pe_acuan) if eps > 0 else int(info.get('previousClose', 0))
    
    if total_dividen > 0:
        harga_maks_layak_beli = int(total_dividen / TARGET_DIVIDEND_YIELD)
        status_dividen = f"LAYAK ({round((total_dividen/info.get('previousClose',1))*100, 2)}% Yield)"
        is_dividend_stock = True
    else:
        harga_maks_layak_beli = int(harga_wajar * 0.85)
        status_dividen = "TIDAK ADA DIVIDEN ❌"
        is_dividend_stock = False

    # --- B. PROSES DATA TEKNIKAL ---
    df = saham.history(period="1y", auto_adjust=False)
    if df.empty or len(df) < 200:
        return None
        
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    df = hitung_indikator_lengkap(df)
    
    terakhir = df.iloc[-1]
    harga_sekarang = int(terakhir['Close'])
    ema20, ema50, ema200 = int(terakhir['EMA20']), int(terakhir['EMA50']), int(terakhir['EMA200'])
    macd, stoch_d, rsi = terakhir['MACD'], terakhir['Stoch_D'], terakhir['RSI14']
    adx, plus_di, minus_di = terakhir['ADX14'], terakhir['+DI14'], terakhir['-DI14']
    
    volume_terakhir = int(terakhir['Volume'])
    volume_rata_rata = int(df['Volume'].tail(20).mean())
    is_volume_strong = volume_terakhir > (volume_rata_rata * 1.5)

    klasifikasi_support, resisten_terdekat = cek_kekuatan_support_dan_resisten(df, harga_sekarang)
    jarak_ke_resisten = round(((resisten_terdekat - harga_sekarang) / harga_sekarang) * 100, 2)

    # --- C. DETEKSI TEKANAN JUAL INSTITUSI & FORUM MATCH ---
    is_panic_selling = (harga_sekarang < ema50) and is_volume_strong
    status_arus_modal = "PANIC SELLING / INSTITUSI KELUAR ⚠️" if is_panic_selling else "ARUS KAS STABIL / NORMAL 👍"

    f1_kondisi = harga_sekarang < ema20 and harga_sekarang > ema200 and stoch_d <= 20 and macd < 0
    status_forum_swing = "AKTIF 🔥" if f1_kondisi else "TIDAK AKTIF 💤"

    f2_kondisi = (ema20 > ema50) and (rsi >= 50) and (adx > 20) and (plus_di > minus_di) and (harga_sekarang > ema200) and is_volume_strong
    status_forum_day = "TREN SANGAT KUAT 🚀" if f2_kondisi else "TREN LEMAH / SIDEWAYS 💤"

    # --- D. LOGIKA GUARDRAIL & STRATEGI ---
    wajib_stop_loss = beta > 1.3 or not is_dividend_stock

    if wajib_stop_loss:
        kategori_risiko = f"TINGGI (Beta: {round(beta, 2)}) 🔥"
        status_proteksi = "MURNI TRADING CEPAT (Wajib Stop Loss)"
        status_tren = "UPTREND SPEKULATIF 📈" if harga_sekarang > ema20 else "DOWNTREND SPEKULATIF 📉"
        rekomendasi = "WAIT/TRADING CEPAT - SET STOP LOSS DI GROWIN KETAT 3-5%!"
    else:
        kategori_risiko = f"RENDAH/AMAN (Beta: {round(beta, 2)}) 🛡️"
        status_proteksi = "AMAN UNTUK STRATEGI GABUNGAN (Bisa Tanpa Cut Loss)"
        
        if is_panic_selling:
            status_tren = "DOWNTREND DISKONTINU 📉"
            rekomendasi = "ANTRE BELI SUPER PASIF (Institusi sedang jualan, tunggu reda)"
        elif harga_sekarang > ema20 and ema20 > ema50:
            status_tren = "UPTREND 📈"
            rekomendasi = "BUY ON WEAKNESS (Antre Beli di GROWIN dekat EMA20)" if harga_sekarang <= (ema20 * 1.015) else "HOLD (Tunggu Koreksi Sehat)"
        elif harga_sekarang < ema20 and harga_sekarang > ema50:
            status_tren = "KOREKSI DALAM 📉"
            rekomendasi = "WAIT AND SEE (Tunggu Sentuh EMA50)"
        elif harga_sekarang < ema50:
            status_tren = "ZONA DISKON / BEARISH SEMANTARA 📉"
            rekomendasi = "ZONA SEROK / AKUMULASI (Harga Murah di Bawah EMA50)"
        else:
            status_tren = "KONSOLIDASI 📊"
            rekomendasi = "WAIT AND SEE"

    if f1_kondisi and not wajib_stop_loss and not is_panic_selling:
        rekomendasi = "BUY ON WEAKNESS ★★★ (Konfirmasi Oversold Forum Aktif!)"
    elif f2_kondisi and not wajib_stop_loss:
        rekomendasi = "STRONG BUY / MOMENTUM RIDE 🚀 (Konfirmasi Tren ADX Meledak!)"

    return {
        "saham": ticker_symbol.upper(),
        "harga_saat_ini": harga_sekarang,
        "fundamental": {
            "harga_wajar": harga_wajar,
            "harga_maks_layak_beli": harga_maks_layak_beli,
            "pbv_ratio": round(pbv_ratio, 2) if pbv_ratio else "N/A",
            "return_on_equity": f"{round(return_on_equity * 100, 2)}%" if return_on_equity else "N/A",
            "status_dividen": status_dividen
        },
        "teknikal": {
            "status_tren": status_tren,
            "klasifikasi_lantai": klasifikasi_support,
            "target_atap_resisten": f"Rp{resisten_terdekat} (Potensi ruang kenaikan: +{jarak_ke_resisten}%)",
            "ema20": ema20, "ema50": ema50, "ema200": ema200,
            "rsi_14": round(rsi, 2), "stochastic_d": round(stoch_d, 2), "adx_strength": round(adx, 2),
            "status_arus_modal": status_arus_modal,
            "konfirmasi_oversold_swing": status_forum_swing,
            "konfirmasi_daytrading_adx": status_forum_day
        },
        "guardrail_proteksi": {
            "kategori_risiko": kategori_risiko,
            "aturan_akun": status_proteksi,
            "wajib_stop_loss": wajib_stop_loss
        },
        "rekomendasi_akhir": rekomendasi
    }

def hitung_momentum_gorengan(ticker_symbol: str):
    if not ticker_symbol.endswith(".JK"):
        ticker = f"{ticker_symbol.upper()}.JK"
    else:
        ticker = ticker_symbol.upper()
        
    saham = yf.Ticker(ticker)
    df = saham.history(period="60d", interval="1h", auto_adjust=False)
    
    if df.empty or len(df) < 20:
        return None
        
    df['EMA5'] = df['Close'].ewm(span=5, adjust=False).mean()
    df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df = hitung_indikator_lengkap(df)
    
    terakhir = df.iloc[-1]
    harga_sekarang = int(terakhir['Close'])
    ema5, ema10 = terakhir['EMA5'], terakhir['EMA10']
    rsi, adx, plus_di, minus_di = terakhir['RSI14'], terakhir['ADX14'], terakhir['+DI14'], terakhir['-DI14']
    
    volume_terakhir = terakhir['Volume']
    volume_rata_rata = df['Volume'].tail(35).mean()
    # Perbaikan: Tambahkan baris baru
    is_volume_spike = volume_terakhir > (volume_rata_rata * 2.5) 
    is_bullish_momentum = harga_sekarang > ema5 and ema5 > ema10
    is_trend_explosive = adx > 20.0 and plus_di > minus_di
    
    cl_level = int(harga_sekarang * 0.965) 
    tp_level = int(harga_sekarang * 1.07) 
    
    info = saham.info
    beta = info.get('beta', 1.8) 
    
    # === PERBAIKAN STRUKTUR AKHIR FUNGSI GORENGAN ===
    status_filter = "GAGAL 💤"
    if is_volume_spike and is_bullish_momentum and is_trend_explosive:
        status_filter = "LOLOS SCREENING 🔥"

    # Baris Wajib: Mengembalikan payload data JSON utuh agar tidak memicu Error 500
    return {
        "saham": ticker_symbol.upper(),
        "status_filter": status_filter,
        "indikator": {
            "rsi_momentum": round(rsi, 2),
            "adx_power": round(adx, 2),
        },
        "rekomendasi_aksi": "DAY TRADING CEPAT"
    }

   
