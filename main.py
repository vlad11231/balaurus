import os
import time
import requests
from py_clob_client.client import ClobClient

# ==========================================
# 1. SETĂRI ȘI MASCĂ STEALTH
# ==========================================
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "0x0000000000000000000000000000000000000000000000000000000000000000") # Key falsa doar pt test de conexiune
PROXY_URL = os.getenv("PROXY_URL")

HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  

# Mască de browser normal ca să păcălim Cloudflare
FAKE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8"
}

proxy_dict = None
if PROXY_URL:
    clean_proxy = PROXY_URL.rstrip('/')
    proxy_dict = {
        "http": clean_proxy,
        "https": clean_proxy
    }
    print("🥷 Modul STEALTH (SOCKS5) Activat!")
else:
    print("⚠️ Lipsă PROXY_URL. Botul e vizibil.")

# ==========================================
# 2. TEST CONEXIUNE POLYMARKET (SOCKS5)
# ==========================================
def test_polymarket():
    print("⏳ Testez infiltrarea în Polymarket...")
    try:
        # Creăm o sesiune simplă mascată pentru a cere date de la ei
        session = requests.Session()
        session.headers.update(FAKE_HEADERS)
        if proxy_dict:
            session.proxies.update(proxy_dict)
            
        # Cerem statusul piețelor (dacă trece de Cloudflare, ne dă 200 OK)
        r = session.get("https://clob.polymarket.com/markets", timeout=10)
        
        if r.status_code == 200:
            print("✅ SUCCES: Polymarket a acceptat conexiunea! Geoblock-ul a fost evitat.")
            return True
        else:
            print(f"❌ EROARE Polymarket (Status {r.status_code}): Cloudflare ne-a blocat.")
            return False
    except Exception as e:
        print(f"❌ Eroare fatală de rețea (Proxy invalid): {e}")
        return False

# ==========================================
# 3. TEST ORACOL PYTH (Viteza Luminii)
# ==========================================
# ID-ul oficial Pyth pentru prețul Bitcoin
PYTH_BTC_ID = "0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43"

def test_pyth_oracle():
    print("\n⏳ Conectare la Oracolul Pyth...")
    try:
        url = f"https://hermes.pyth.network/api/latest_price_feeds?ids[]={PYTH_BTC_ID}"
        r = requests.get(url, timeout=5)
        
        if r.status_code == 200:
            data = r.json()[0]['price']
            price = int(data['price']) * (10 ** data['expo'])
            print(f"✅ SUCCES Pyth: Prețul exact BTC acum este: ${price:.2f}")
        else:
            print("❌ EROARE: Nu pot citi oracolul Pyth.")
    except Exception as e:
        print(f"❌ Eroare Pyth: {e}")

# ==========================================
# 4. EXECUȚIA
# ==========================================
if __name__ == "__main__":
    poly_ok = test_polymarket()
    if poly_ok:
        test_pyth_oracle()
        print("\n🎉 Toate sistemele sunt VERZI! Railway e gata de vânătoare.")
    
    print("💤 Test finalizat.")
    time.sleep(86400)
