import feedparser
import requests
import google.generativeai as genai
import os
import sys

# 1. RECUPERO CREDENZIALI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("ERRORE CRITICO: Credenziali mancanti nei GitHub Secrets.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

SOURCES = {
    "SCMP_China": "https://www.scmp.com/rss/2/feed",
    "SCMP_Tech": "https://www.scmp.com/rss/318198/feed"
}

def fetch_latest_intel():
    intel_data = []
    # CONTROMISURA 1: Travestimento (Spoofing). Facciamo credere al firewall di essere un browser Windows.
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    for category, url in SOURCES.items():
        try:
            print(f"Estrazione da {category}...")
            # CONTROMISURA 2: Fail-Fast. Se non risponde in 10 secondi, abbandona e passa oltre.
            response = requests.get(url, headers=headers, timeout=10)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:3]:
                intel_data.append(f"[{category}] Titolo: {entry.title}\nSommario: {entry.description}\n")
        except Exception as e:
            print(f"Avviso: Timeout o blocco su {category}. Errore: {str(e)}")
            intel_data.append(f"Errore recupero {category}: Dati non disponibili al momento.")
            
    return "\n".join(intel_data)

def analyze_with_gemini(raw_data):
    # Uso del modello ultra-rapido
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Agisci come Analista Geopolitico. Analizza questo raw data feed sulle dinamiche della Cina.
    Genera un Executive Briefing in italiano strutturato in markdown con:
    1. 📊 Movimenti Economici / Tech
    2. ⚔️ Postura Geopolitica
    3. 🎯 Indicatori Chiave (Prossime 24h)
    
    REGOLE IMPERATIVE:
    - Densità informativa massima. Zero fluff.
    - LUNGHEZZA MASSIMA ASSOLUTA: 3500 caratteri. Sii estremamente sintetico.
    
    Dati grezzi:
    {raw_data}
    """
    response = model.generate_content(prompt)
    return response.text

def send_telegram_briefing(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # CONTROMISURA 3: La Ghigliottina. Tronca per evitare l'errore "message too long"
    safe_message = message[:4000]
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": safe_message, "parse_mode": "Markdown"}
    
    try:
        # CONTROMISURA 4: Timeout anche verso Telegram
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Errore Telegram: {response.text}")
        else:
            print("Briefing consegnato con successo su Telegram!")
    except Exception as e:
        print(f"Errore critico di connessione a Telegram: {str(e)}")

if __name__ == "__main__":
    print("--- AVVIO PIPELINE OSINT ---")
    raw_intel = fetch_latest_intel()
    
    if raw_intel and "Titolo:" in raw_intel:
        print("Dati estratti. Inizio analisi IA...")
        final_briefing = analyze_with_gemini(raw_intel)
        
        print("Analisi completata. Trasmissione in corso...")
        send_telegram_briefing(final_briefing)
    else:
        print("Estrazione fallita o nessun dato rilevante. Analisi annullata per evitare messaggi vuoti.")
    
    print("--- CHIUSURA SISTEMA ---")