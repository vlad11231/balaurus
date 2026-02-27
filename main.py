import requests
import csv
import time

# ==========================================
# 1. CONFIGURARE
# ==========================================
TARGET_ADDRESS = "0x1d0034134e339a309700ff2d34e99fa2d48b0313".lower()

# Datele tale de Telegram:
TELEGRAM_TOKEN = "8261089656:AAF_JM39II4DpfiFzVTd0zsXZKtKcDE5G9A"
TELEGRAM_CHAT_ID = "6854863928"

API_ACTIVITY = "https://data-api.polymarket.com/activity"

# ==========================================
# 2. LOGICA DE EXTRAGERE ȘI TRIMITERE FISIER
# ==========================================
def fetch_and_send_csv():
    print(f"🔍 Extrag ultimele 200 tranzacții brute pentru: {TARGET_ADDRESS}")
    
    try:
        r = requests.get(API_ACTIVITY, params={"user": TARGET_ADDRESS, "limit": 200}, timeout=15)
        if r.status_code != 200:
            print(f"⚠️ Eroare API Polymarket: {r.status_code}")
            return
        data = r.json()
    except Exception as e:
        print(f"❌ Eroare de rețea: {e}")
        return

    if not data:
        print("📉 Nu am găsit date pentru această adresă.")
        return

    # Numele fișierului pe care îl va genera
    filename = "tranzactii_balena.csv"
    
    print("📝 Formatez datele în Excel (CSV)...")
    
    # Deschidem fișierul pentru scriere
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Capul de tabel
        writer.writerow(["Data/Ora (UTC)", "Piața (Market)", "Acțiune (BUY/SELL)", "Tip", "Preț (USD)", "Acțiuni (Size)", "Total (USD)", "Hash Tranzacție"])
        
        for d in data:
            timestamp = d.get("timestamp", "")
            title = d.get("title", "Unknown")
            side = d.get("side", "")
            tx_type = d.get("type", "")
            
            # Polymarket returnează uneori stringuri, le facem float pentru calcule
            try:
                price = float(d.get("price", 0))
                size = float(d.get("size", 0))
            except:
                price = 0
                size = 0
                
            total_usd = price * size
            tx_hash = d.get("transactionHash", "")
            
            writer.writerow([timestamp, title, side, tx_type, f"${price:.4f}", round(size, 2), f"${total_usd:.2f}", tx_hash])
            
    print(f"✅ Fișierul {filename} a fost creat cu succes!")
    print("🚀 Îl trimit pe Telegram...")
    
    # Trimiterea fișierului pe Telegram ca Document
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    
    with open(filename, "rb") as file:
        files = {"document": file}
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": "📁 Aici ai fișierul brut cu ultimele 200 de tranzacții! Poți să-l deschizi în Excel sau Google Sheets pentru analiză."
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
    # Îl punem pe pauză o zi ca să nu facă spam pe server
    print("💤 Analiză terminată. Botul intră în stand-by.")
    time.sleep(86400)
