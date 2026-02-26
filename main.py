import os
import time
import requests
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs

# ==========================================
# 0. BYPASS GEO-BLOCK (VPN PENTRU BOT)
# ==========================================
PROXY_URL = os.getenv("PROXY_URL")
if PROXY_URL:
    os.environ["http_proxy"] = PROXY_URL
    os.environ["https_proxy"] = PROXY_URL
    print("🌐 Sistem anti-block activat! Traficul este rutat prin serverul din Europa.")
else:
    print("⚠️ ATENȚIE: Nu ai setat PROXY_URL. Dacă serverul e în SUA, Polymarket te va bloca.")

# ==========================================
# 1. CONFIGURARE COPY TRADING TEST
# ==========================================

TARGET_ADDRESS = "0x1d0034134e339a309700ff2d34e99fa2d48b0313".lower()
TRADE_AMOUNT_USD = 1.0  # Cumpără exact de $1
MAX_TRADES = 5          # Se oprește definitiv după 5 tranzacții reușite
MIN_PRICE = 0.30        # Ignoră tranzacțiile sub 30 de cenți

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    print("❌ EROARE: Nu ai setat PRIVATE_KEY în variabilele de mediu din Railway!")
    exit(1)

# Asigură-te că cheia privată începe cu 0x
if not PRIVATE_KEY.startswith("0x"):
    PRIVATE_KEY = "0x" + PRIVATE_KEY

HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  # Rețeaua Polygon Mainnet
API_ACTIVITY = "https://data-api.polymarket.com/activity"

# ==========================================
# 2. INIȚIALIZARE CLIENT POLYMARKET
# ==========================================

print("⏳ Se inițializează conexiunea securizată cu Polymarket...")
try:
    client = ClobClient(host=HOST, key=PRIVATE_KEY, chain_id=CHAIN_ID)
    creds = client.create_or_derive_api_creds()
    client.set_api_creds(creds)
    print("✅ Autentificare reușită! Botul este conectat la portofelul tău.")
except Exception as e:
    print(f"❌ Eroare critică la conectarea portofelului: {e}")
    exit(1)

# ==========================================
# 3. LOGICA DE COPY TRADING
# ==========================================

processed_ids = set()

def fetch_activity(addr):
    try:
        r = requests.get(API_ACTIVITY, params={"user": addr, "limit": 10}, timeout=10)
        return r.json() if r.status_code == 200 else []
    except:
        return []

print("🔍 Scanez istoricul vechi pentru a nu-l copia...")
initial_events = fetch_activity(TARGET_ADDRESS)
for e in initial_events:
    uid = e.get("id") or f"{e.get('transactionHash')}_{e.get('logIndex')}"
    processed_ids.add(uid)

trades_executed = 0

print(f"🚀 BOT PORNIT! Urmăresc adresa: {TARGET_ADDRESS}")
print(f"🎯 Obiectiv: Execută {MAX_TRADES} tranzacții de ${TRADE_AMOUNT_USD} (Doar poziții >= {MIN_PRICE*100}¢)")

while trades_executed < MAX_TRADES:
    try:
        events = fetch_activity(TARGET_ADDRESS)
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
                    print(f"⏭️ TARGETUL A CUMPĂRAT: {title} la {price*100}¢. (IGNORAT - Preț sub {MIN_PRICE*100}¢)")
                    continue

                print(f"\n🚨 DETECTAT VALID: Targetul a cumpărat: {title} @ {price*100}¢")
                
                exec_price = min(price + 0.01, 0.99)
                size = round(TRADE_AMOUNT_USD / exec_price, 2)
                
                print(f"🛒 Pun ordin: Cumpăr {size} acțiuni la prețul de {exec_price*100:.1f}¢ (Total: ~${TRADE_AMOUNT_USD})")
                
                try:
                    order_args = OrderArgs(
                        price=exec_price,
                        size=size,
                        side="BUY",
                        token_id=token_id
                    )
                    
                    signed_order = client.create_order(order_args)
                    resp = client.post_order(signed_order)
                    
                    if resp and resp.get("success"):
                        trades_executed += 1
                        print(f"✅ SUCCES! Trade {trades_executed}/{MAX_TRADES} executat. OrderID: {resp.get('orderID')}")
                    else:
                        print(f"⚠️ Ordin refuzat: {resp}")

                except Exception as ex:
                    print(f"❌ Eroare la execuția comenzii: {ex}")

                if trades_executed >= MAX_TRADES:
                    print("\n🎉 OBIECTIV ATINS! Am executat 5 trade-uri. Botul se oprește conform instrucțiunilor.")
                    exit(0)

    except Exception as e:
        print(f"Eroare în bucla de monitorizare: {e}")
    
    time.sleep(10)
