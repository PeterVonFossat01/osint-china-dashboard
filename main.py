import feedparser
import requests
import google.generativeai as genai
import os
import sys

# Recupero variabili d'ambiente nascoste
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("ERRORE: Credenziali mancanti. Controlla i GitHub Secrets.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# Fonti RSS più stabili (Focus su SCMP ed Economia asiatica)
SOURCES = {
    "SCMP_China": "https://www.scmp.com/rss/2/feed",
    "SCMP_Tech": "https://www.scmp.com/rss/318198/feed"
}

def fetch_latest_intel():
    intel_data = []
    for category, url in SOURCES.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: # Estrae le top 3 notizie per fonte
                intel_data.append(f"[{category}] Titolo: {entry.title}\nSommario: {entry.description}\nLink: {entry.link}\n")
        except Exception as e:
            intel_data.append(f"Errore {category}: {str(e)}")
    return "\n".join(intel_data)

def analyze_with_gemini(raw_data):
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Agisci come Analista Geopolitico e Architetto di Sistemi. Analizza questo raw data feed sulle dinamiche della RPC (Cina).
    Genera un Executive Briefing in italiano strutturato in markdown con:
    1. 📊 Movimenti Economici / Tech (Sintesi e impatto)
    2. ⚔️ Postura Geopolitica (Rischi e sviluppi)
    3. 🎯 Indicatori Chiave (Cosa monitorare nelle prossime 24h)
    
    Densità informativa massima. Zero fluff.
    
    Dati grezzi:
    {raw_data}
    """
    response = model.generate_content(prompt)
    return response.text

def send_telegram_briefing(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Errore Telegram: {response.text}")

if __name__ == "__main__":
    raw_intel = fetch_latest_intel()
    if raw_intel:
        final_briefing = analyze_with_gemini(raw_intel)
        send_telegram_briefing(final_briefing)
        print("Esecuzione completata.")
