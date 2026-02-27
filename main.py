import os
import requests
import time
from collections import Counter

# ==========================================
# 1. CONFIGURARE
# ==========================================
TARGET_ADDRESS = "0x1d0034134e339a309700ff2d34e99fa2d48b0313".lower()
TELEGRAM_TOKEN = os.getenv("8261089656:AAF_JM39II4DpfiFzVTd0zsXZKtKcDE5G9A")
TELEGRAM_CHAT_ID = os.getenv("6854863928")
API_ACTIVITY = "https://data-api.polymarket.com/activity"

def send_telegram_alert(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ EROARE: Nu ai setat datele de Telegram în Railway!")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload)
        print("✅ Raport trimis cu succes pe Telegram!")
    except Exception as e:
        print(f"❌ Eroare la trimiterea pe Telegram: {e}")

# ==========================================
# 2. LOGICA DE EXTRAGERE ȘI ANALIZĂ
# ==========================================
def analyze_wallet():
    print(f"🔍 Extrag ultimele tranzacții pentru: {TARGET_ADDRESS}")
    
    try:
        # Cerem ultimele 200 de evenimente
        r = requests.get(API_ACTIVITY, params={"user": TARGET_ADDRESS, "limit": 200}, timeout=15)
        if r.status_code != 200:
            send_telegram_alert(f"⚠️ Eroare API Polymarket: {r.status_code}")
            return
            
        data = r.json()
    except Exception as e:
        send_telegram_alert(f"❌ Eroare de rețea: {e}")
        return

    if not data:
        send_telegram_alert("📉 Nu am găsit tranzacții pentru această adresă.")
        return

    total_tx = len(data)
    
    # Analiză de bază
    buys = [d for d in data if d.get("side") == "BUY"]
    sells = [d for d in data if d.get("side") == "SELL"]
    
    # Piețele preferate
    titles = [d.get("title", "Unknown") for d in data if "title" in d]
    top_markets = Counter(titles).most_common(3)
    
    # Analiza prețurilor medii de cumpărare (ca să vedem dacă vânează reduceri)
    buy_prices = [float(b.get("price", 0)) for b in buys if b.get("price")]
    avg_buy_price = (sum(buy_prices) / len(buy_prices)) if buy_prices else 0
    
    # Formatăm un raport frumos pentru Telegram
    raport = f"🕵️‍♂️ <b>RAPORT ANALIZĂ BALENĂ</b> 🕵️‍♂️\n"
    raport += f"Adresă: <code>{TARGET_ADDRESS[:10]}...</code>\n\n"
    
    raport += f"📊 <b>Ultimele {total_tx} tranzacții extrase:</b>\n"
    raport += f"🛒 Cumpărări (BUY): <b>{len(buys)}</b>\n"
    raport += f"💰 Vânzări (SELL): <b>{len(sells)}</b>\n"
    raport += f"💵 Preț mediu de BUY: <b>{avg_buy_price * 100:.1f}¢</b>\n\n"
    
    raport += f"🎯 <b>Top 3 Piețe Tranzacționate:</b>\n"
    for idx, (market, count) in enumerate(top_markets, 1):
        raport += f"{idx}. {market} ({count} txs)\n"
        
    raport += "\n💡 <i>Concluzie script: Dacă prețul mediu este în jur de 30-40 cenți și tranzacționează aceeași piață obsesiv, confirmă teoria de Arbitraj Matematic.</i>"

    # Trimitem alerta o singură dată
    send_telegram_alert(raport)

if __name__ == "__main__":
    analyze_wallet()
    # Adormim scriptul 24 de ore ca să nu se restarteze pe Railway și să îți facă spam pe telefon
    print("💤 Analiză terminată. Botul intră în stand-by pentru 24h.")
    time.sleep(86400)
