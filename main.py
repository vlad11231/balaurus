import os
import requests
import time

# ==========================================
# 1. EXTRAGERE CREDENȚIALE DIN RAILWAY
# ==========================================
PROXY_URL = os.getenv("PROXY_URL")

if not PROXY_URL or "@" not in PROXY_URL:
    print("❌ EROARE: Nu ai setat PROXY_URL corect în Railway.")
    exit(1)

# Extragem bucata cu "http://USERNAME:PAROLA" ca să o refolosim
creds_part = PROXY_URL.split('@')[0]

# O listă de servere proaspete din Spania de la NordVPN
SPANISH_SERVERS = [
    "es250", "es251", "es260", "es261", "es270", 
    "es280", "es281", "es285", "es290", "es295",
    "es234", "es235", "es240", "es245", "es220"
]

FAKE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8"
}

# ==========================================
# 2. VÂNĂTOAREA DE SERVERE
# ==========================================
def hunt_for_working_proxy():
    print("🕵️‍♂️ Încep vânătoarea de servere active din Spania...\n")
    
    for server in SPANISH_SERVERS:
        test_url = f"{creds_part}@{server}.nordvpn.com:80"
        proxy_dict = {"http": test_url, "https": test_url}
        
        print(f"🔄 Testez {server}.nordvpn.com ... ", end="")
        
        try:
            # Testăm rapid dacă serverul NordVPN răspunde și ne dă IP de Spania
            r = requests.get("https://ipinfo.io/json", proxies=proxy_dict, timeout=5)
            
            if r.status_code == 200:
                data = r.json()
                if data.get('country') == "ES":
                    print(f"✅ ACTIV! (IP Spania: {data.get('ip')})")
                    
                    # Dacă VPN-ul merge, batem la ușa Polymarket!
                    print(f"⏳ Încerc să sparg Cloudflare-ul Polymarket prin {server}...")
                    
                    session = requests.Session()
                    session.headers.update(FAKE_HEADERS)
                    session.proxies.update(proxy_dict)
                    
                    poly_req = session.get("https://clob.polymarket.com/markets", timeout=10)
                    
                    if poly_req.status_code == 200:
                        print(f"\n🚀 JACKPOT! Serverul {server}.nordvpn.com funcționează perfect!")
                        print("Notifică-mă cu numele acestui server ca să-l punem în botul final.")
                        return True
                    elif poly_req.status_code == 403:
                        print("❌ Blocat de Polymarket (Geoblock). Trec la următorul...")
                    else:
                        print(f"⚠️ Răspuns dubios ({poly_req.status_code}). Trec la următorul...")
                else:
                    print(f"⚠️ E activ, dar locația e greșită ({data.get('country')}).")
            
        except requests.exceptions.Timeout:
            print("❌ Timeout (Server picat).")
        except requests.exceptions.ConnectionError:
            print("❌ Conexiune respinsă de NordVPN.")
        except Exception as e:
            print("❌ Eroare tehnică.")
            
        time.sleep(1) # Pauză mică să nu dăm spam
        
    print("\n💀 Vânătoarea a eșuat. Toate serverele din listă au fost respinse.")
    return False

if __name__ == "__main__":
    hunt_for_working_proxy()
    time.sleep(86400)
