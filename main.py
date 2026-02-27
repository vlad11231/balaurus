import os
import time
import requests
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs

# ==========================================
# 1. CONFIGURARE SETĂRI TEST
# ==========================================
TARGET_ADDRESS = "0x1d0034134e339a309700ff2d34e99fa2d48b0313".lower()
TRADE_AMOUNT_USD = 1.0  # Fix 1 Dolar per trade
MAX_TRADES = 5          # Se oprește după 5 trade-uri
MIN_PRICE = 0.30        # Doar tranzacții de peste 30 de cenți

# Preluăm cheia MetaMask din Railway
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if PRIVATE_KEY and not PRIVATE_KEY.startswith("0x"):
    PRIVATE_KEY = "0x" + PRIVATE_KEY

# Dacă nu ai setat cheia, oprim botul să nu dea crash urât
if not PRIVATE_KEY:
    print("❌ EROARE: Nu ai setat variabila PRIVATE_KEY în Railway!")
    exit(1)

HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  
API_ACTIVITY = "https://data-api.polymarket.com/activity"

# ==========================================
# 2. PROXY-UL WEBSHARE ȘI MASCA
# ==========================================
proxy_dict = {
    "http": "http://lnigvxes:11agoe0f1dqv@64.137.96.74:6641/",
    "https": "http://lnigvxes:11agoe0f1dqv@64.137.96.74:6641/"
}

FAKE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# ==========================================
# 3. AUTENTIFICARE PE POLYMARKET
# ==========================================
print("⏳ Se inițializează armamentul greu (Conexiune Polymarket prin Webshare)...")
try:
    client = ClobClient(host=HOST, key=PRIVATE_KEY, chain_id=CHAIN_ID)
    
    # Injectăm proxy-ul și masca direct în clientul oficial
    client.session.headers.update(FAKE_HEADERS)
    client.session.proxies.update(proxy_dict)
    
    creds = client.create_or_derive_api_creds()
    client.set_api_creds(creds)
    print("✅ Autentificare reușită! Botul are acces la portofelul tău.")
except Exception as e:
    print(f"❌ Eroare la conectarea portofelului: {e}")
    exit(1)

# ==========================================
# 4. LOGICA DE VÂNĂTOARE (COPY TRADING)
# ==========================================
processed_ids = set()

def fetch_activity(addr):
    try:
        # Folosim requests normal cu proxy pentru a citi istoricul balenei
        r = requests.get(API_ACTIVITY, params={"user": addr, "limit": 10}, headers=FAKE_HEADERS, proxies=proxy_dict, timeout=10)
        return r.json() if r.status_code == 200 else []
    except: 
        return []

print("🔍 Memorez tranzacțiile vechi ca să nu le dublez...")
for e in fetch_activity(TARGET_ADDRESS):
    uid = e.get("id") or f"{e.get('transactionHash')}_{e.get('logIndex')}"
    processed_ids.add(uid)

trades_executed = 0
print(f"\n🚀 BOT PORNIT ȘI ÎNARMAT! Urmăresc balena: {TARGET_ADDRESS}")
print(f"Setări: Maxim {MAX_TRADES} trade-uri | {TRADE_AMOUNT_USD}$ bucata | Minim {MIN_PRICE*100}¢")

while trades_executed < MAX_TRADES:
    try:
        events = fetch_activity(TARGET_ADDRESS)
        # Sortăm cronologic ca să prindem prima mișcare
        events.sort(key=lambda x: x.get("timestamp", 0))

        for e in events:
            uid = e.get("id") or f"{e.get('transactionHash')}_{e.get('logIndex')}"
            if uid in processed_ids: 
                continue
            processed_ids.add(uid)

            side = e.get("side", "").upper()
            event_type = e.get("type", "TRADE").upper()
            title = e.get("title", "Unknown Market")
            token_id = e.get("asset") 
            price = float(e.get("price", 0))

            if side == "BUY" and event_type == "TRADE" and token_id:
                if price < MIN_PRICE:
                    continue

                print(f"\n🚨 ALERTĂ: Balena a cumpărat {title} la prețul de {price*100}¢")
                
                # Calculăm câte acțiuni luăm de 1 Dolar
                size = round(TRADE_AMOUNT_USD / price, 2)
                # Market Order (punem preț mai mare cu 5 cenți ca să execute sigur)
                exec_price = min(price + 0.05, 0.99)
                
                print(f"🛒 Execut ordin: Cumpăr {size} acțiuni...")
                
                try:
                    order_args = OrderArgs(price=exec_price, size=size, side="BUY", token_id=token_id)
                    signed_order = client.create_order(order_args)
                    resp = client.post_order(signed_order)
                    
                    if resp and resp.get("success"):
                        trades_executed += 1
                        print(f"✅ BINGO! Trade executat pe blockchain ({trades_executed}/{MAX_TRADES}). ID: {resp.get('orderID')}")
                    else:
                        print(f"⚠️ Ordin refuzat de Polymarket: {resp}")
                except Exception as ex:
                    print(f"❌ Eroare la trimiterea ordinului: {ex}")

                # Dacă am atins limita de 5, oprim totul
                if trades_executed >= MAX_TRADES:
                    print("\n🎉 OBIECTIV ATINS (5/5)! Botul se închide în siguranță.")
                    exit(0)

    except Exception as e:
        pass # Trecem peste erorile mici de rețea
    
    # Verificăm la fiecare 3 secunde (pentru că proxy-ul ne permite o viteză bună)
    time.sleep(3)
