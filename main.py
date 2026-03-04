import requests
import csv
import time

# ==========================================
# 1. CONFIGURARE
# ==========================================
TARGET_ADDRESS = "0xddea36f12a3babf31d5c2a5018e4210c3f07db30".lower()

# Datele tale de Telegram:
TELEGRAM_TOKEN = "8261089656:AAF_JM39II4DpfiFzVTd0zsXZKtKcDE5G9A"
TELEGRAM_CHAT_ID = "6854863928"

API_ACTIVITY = "https://data-api.polymarket.com/activity"

# ==========================================
# 2. LOGICA DE EXTRAGERE (PÂNĂ LA 1000 TX)
# ==========================================
def fetch_and_send_csv():
    print(f"🔍 Extrag ultimele 1000 tranzacții brute pentru: {TARGET_ADDRESS}")
    
    all_data = []
    
    # Polymarket permite teoretic limit=1000, dar uneori blochează cererile prea mari.
    # Cerem direct 1000.
    try:
        r = requests.get(API_ACTIVITY, params={"user": TARGET_ADDRESS, "limit": 1000}, timeout=20)
        if r.status_code != 200:
            print(f"⚠️ Eroare API Polymarket: {r.status_code}")
            return
        all_data = r.json()
    except Exception as e:
        print(f"❌ Eroare de rețea: {e}")
        return

    if not all_data:
        print("📉 Nu am găsit date pentru această adresă.")
        return

    print(f"✅ Am extras cu succes {len(all_data)} tranzacții din API!")

    filename = "balena_1000_tranzactii.csv"
    print("📝 Formatez datele în Excel (CSV)...")
    
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Data/Ora (UTC)", "Piața (Market)", "Acțiune (BUY/SELL)", "Tip", "Preț (USD)", "Acțiuni (Size)", "Total (USD)", "Hash Tranzacție"])
        
        for d in all_data:
            timestamp = d.get("timestamp", "")
            title = d.get("title", "Unknown")
            side = d.get("side", "")
            tx_type = d.get("type", "")
            
            try:
                price = float(d.get("price", 0))
                size = float(d.get("size", 0))
            except:
                price = 0
                size = 0
                
            total_usd = price * size
            tx_hash = d.get("transactionHash", "")
            
            writer.writerow([timestamp, title, side, tx_type, f"${price:.4f}", round(size, 2), f"${total_usd:.2f}", tx_hash])
            
    print("🚀 Îl trimit pe Telegram...")
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    with open(filename, "rb") as file:
        files = {"document": file}
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": f"📁 Aici ai fișierul brut cu ultimele {len(all_data)} tranzacții!\nE gata pentru o analiză avansată."
        }
        
        try:
            req = requests.post(url, data=payload, files=files)
            if req.status_code == 200:
                print("✅ Fișier trimis cu succes pe Telegram!")
            else:
                print(f"❌ Eroare la trimiterea fișierului: {req.text}")
        except Exception as e:
            print(f"❌ Eroare la conexiunea cu Telegram: {e}")

if __name__ == "__main__":
    fetch_and_send_csv()
    print("💤 Analiză terminată. Botul intră în stand-by.")
    time.sleep(86400)
