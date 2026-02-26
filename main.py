import os
import time
import requests
import threading
from flask import Flask
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs

# ==========================================
# 1. CONFIGURARE COPY TRADING TEST
# ==========================================

TARGET_ADDRESS = "0x1d0034134e339a309700ff2d34e99fa2d48b0313".lower()
TRADE_AMOUNT_USD = 1.0  
MAX_TRADES = 5          
MIN_PRICE = 0.30        

PRIVATE_KEY = os.getenv("PRIVATE_KEY")

HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  
API_ACTIVITY = "https://data-api.polymarket.com/activity"

# ==========================================
# 2. SERVER WEB (CA SĂ ȚINĂ BOTUL ONLINE)
# ==========================================
app = Flask(__name__)
PORT = int(os.getenv("PORT", 5000))

@app.route("/")
def index():
    return "🤖 Botul de Copy Trading rulează direct din Europa!"

def run_server():
    app.run(host="0.0.0.0", port=PORT)

# ==========================================
# 3. LOGICA DE COPY TRADING
# ==========================================
def bot_loop():
    if not PRIVATE_KEY:
        print("❌ EROARE: Nu ai setat PRIVATE_KEY în variabilele de mediu!")
        return

    pk = PRIVATE_KEY if PRIVATE_KEY.startswith("0x") else "0x" + PRIVATE_KEY

    print("⏳ Se inițializează conexiunea securizată cu Polymarket...")
    try:
        client = ClobClient(host=HOST, key=pk, chain_id=CHAIN_ID)
        creds = client.create_or_derive_api_creds()
        client.set_api_creds(creds)
        print("✅ Autentificare reușită! Botul este conectat.")
    except Exception as e:
        print(f"❌ Eroare critică la conectare: {e}")
        return

    processed_ids = set()

    def fetch_activity(addr):
        try:
            r = requests.get(API_ACTIVITY, params={"user": addr, "limit": 10}, timeout=10)
            return r.json() if r.status_code == 200 else []
        except: return []

    print("🔍 Scanez istoricul vechi...")
    for e in fetch_activity(TARGET_ADDRESS):
        uid = e.get("id") or f"{e.get('transactionHash')}_{e.get('logIndex')}"
        processed_ids.add(uid)

    trades_executed = 0
    print(f"🚀 BOT PORNIT! Urmăresc: {TARGET_ADDRESS}")

    while trades_executed < MAX_TRADES:
        try:
            events = fetch_activity(TARGET_ADDRESS)
            events.sort(key=lambda x: x.get("timestamp", 0))

            for e in events:
                uid = e.get("id") or f"{e.get('transactionHash')}_{e.get('logIndex')}"
                if uid in processed_ids: continue
                processed_ids.add(uid)

                side = e.get("side", "").upper()
                event_type = e.get("type", "TRADE").upper()
                title = e.get("title", "Unknown Market")
                token_id = e.get("asset") 
                price = float(e.get("price", 0))

                if side == "BUY" and event_type == "TRADE" and token_id:
                    if price < MIN_PRICE: continue

                    print(f"\n🚨 DETECTAT: Targetul a cumpărat {title} @ {price*100}¢")
                    
                    size = round(TRADE_AMOUNT_USD / price, 2)
                    exec_price = min(price + 0.05, 0.99)
                    
                    print(f"🛒 Execut Market Order: Cumpăr {size} acțiuni")
                    
                    try:
                        order_args = OrderArgs(price=exec_price, size=size, side="BUY", token_id=token_id)
                        signed_order = client.create_order(order_args)
                        resp = client.post_order(signed_order)
                        
                        if resp and resp.get("success"):
                            trades_executed += 1
                            print(f"✅ SUCCES! Trade {trades_executed}/{MAX_TRADES}. ID: {resp.get('orderID')}")
                        else:
                            print(f"⚠️ Ordin refuzat: {resp}")

                    except Exception as ex:
                        print(f"❌ Eroare execuție: {ex}")

                    if trades_executed >= MAX_TRADES:
                        print("\n🎉 OBIECTIV ATINS! Opresc tranzacționarea.")
                        return

        except Exception as e:
            print(f"Eroare loop: {e}")
        
        time.sleep(10)

if __name__ == "__main__":
    t = threading.Thread(target=bot_loop)
    t.daemon = True
    t.start()
    run_server()
