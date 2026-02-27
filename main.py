import os
import requests

# ==========================================
# 1. PRELUARE DATE
# ==========================================
PROXY_URL = os.getenv("PROXY_URL")

# Mască de browser (ca să nu ne detecteze ca fiind un script Python)
FAKE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8"
}

proxy_dict = None
if PROXY_URL:
    clean_proxy = PROXY_URL.rstrip('/')
    proxy_dict = {
        "http": clean_proxy,
        "https": clean_proxy
    }
    print("🌍 Proxy HTTP setat!")
else:
    print("⚠️ ATENȚIE: Nu ai setat PROXY_URL.")

# ==========================================
# 2. TEST 1: VERIFICARE LOCAȚIE (Suntem în Spania?)
# ==========================================
def check_ip():
    print("🔍 Verific adresa IP și locația...")
    try:
        r = requests.get("https://ipinfo.io/json", proxies=proxy_dict, timeout=10)
        data = r.json()
        print(f"✅ Locație detectată: {data.get('country')} (IP: {data.get('ip')})")
        
        if data.get('country') == "ES":
            print("🇪🇸 BINGO! Suntem în Spania. Trecem la pasul 2...")
            return True
        else:
            print("⚠️ Avertisment: Nu pare a fi IP de Spania.")
            return True # Continuam oricum
    except Exception as e:
        print(f"❌ Eroare la verificarea IP-ului (Proxy Invalid sau Timeout): {e}")
        return False

# ==========================================
# 3. TEST 2: TEST POLYMARKET
# ==========================================
def test_polymarket():
    print("\n⏳ Batem la ușa Polymarket...")
    try:
        # Folosim session pentru a pastra header-ele
        session = requests.Session()
        session.headers.update(FAKE_HEADERS)
        if proxy_dict:
            session.proxies.update(proxy_dict)
            
        # Cerem date de la Polymarket
        r = session.get("https://clob.polymarket.com/markets", timeout=10)
        
        if r.status_code == 200:
            print("🚀 SUCCES ABSOLUT! Polymarket ne-a acceptat conexiunea din prima!")
            print("Sistemul e gata de trading.")
        elif r.status_code == 403:
            print("❌ EROARE 403: Cloudflare ne-a dat Block. (Geoblock detectat).")
        else:
            print(f"⚠️ Răspuns neașteptat: {r.status_code}")
            
    except Exception as e:
        print(f"❌ Eroare fatală de rețea cu Polymarket: {e}")

# ==========================================
# EXECUȚIE
# ==========================================
if __name__ == "__main__":
    if check_ip():
        test_polymarket()
    else:
        print("Misiune anulată. Verifică setările proxy-ului.")
