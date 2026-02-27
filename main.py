import time
import requests

# ==========================================
# 1. PROXY-UL TĂU WEBSHARE
# ==========================================
proxy_dict = {
    "http": "http://lnigvxes:11agoe0f1dqv@64.137.96.74:6641/",
    "https": "http://lnigvxes:11agoe0f1dqv@64.137.96.74:6641/"
}

# Mască de browser pentru a păcăli Cloudflare
FAKE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9"
}

# ==========================================
# 2. TEST POLYMARKET (Mascat)
# ==========================================
def test_polymarket():
    print("⏳ Testez conexiunea cu Polymarket (prin Webshare)...")
    try:
        session = requests.Session()
        session.headers.update(FAKE_HEADERS)
        session.proxies.update(proxy_dict)
        
        # Încercăm să luăm lista de piețe de pe Polymarket
        r = session.get("https://clob.polymarket.com/markets", timeout=10)
        
        if r.status_code == 200:
            print("✅ SUCCES: Polymarket a acceptat conexiunea! Geoblock-ul a fost distrus.")
            return True
        elif r.status_code == 403:
            print("❌ EROARE 403: Încă primim block. IP-ul proxy-ului ar putea fi banat.")
            return False
        else:
            print(f"⚠️ Răspuns neașteptat: {r.status_code}")
            return False
    except Exception as e:
        print(f"❌ Eroare fatală rețea Polymarket: {e}")
        return False

# ==========================================
# 3. TEST PYTH ORACLE (Viteza Luminii)
# ==========================================
# ID-ul oficial Pyth pentru prețul Bitcoin
PYTH_BTC_ID = "0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43"

def test_pyth():
    print("\n⏳ Citesc oracolul Pyth Network...")
    try:
        # Pyth se citește DIRECT (fără proxy) pentru a nu pierde nicio milisecundă
        url = f"https://hermes.pyth.network/api/latest_price_feeds?ids[]={PYTH_BTC_ID}"
        r = requests.get(url, timeout=5)
        
        if r.status_code == 200:
            data = r.json()[0]['price']
            price = int(data['price']) * (10 ** data['expo'])
            print(f"🎯 PYTH LIVE: Prețul Bitcoin la milisecundă este: ${price:.2f}")
        else:
            print(f"❌ Eroare API Pyth: {r.status_code}")
    except Exception as e:
        print(f"❌ Eroare Pyth: {e}")

# ==========================================
# EXECUȚIE
# ==========================================
if __name__ == "__main__":
    poly_ok = test_polymarket()
    
    if poly_ok:
        test_pyth()
        print("\n🚀 INFRASTRUCTURA ESTE GATA DE ATAC! Putem trece la scrierea logicii botului.")
    
    # Adormim scriptul 24h ca să nu dea Railway eroare de "Crash"
    time.sleep(86400)
