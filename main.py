import feedparser
import requests
import google.generativeai as genai
import os
import sys

# 1. CREDENZIALI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("ERRORE: Credenziali mancanti.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# 2. SET DI FONTI UNIFICATO (Generali + Tattiche)
SOURCES = {
    "SCMP_General": "https://www.scmp.com/rss/2/feed",
    "SCMP_Tech": "https://www.scmp.com/rss/318198/feed",
    "USNI_Military": "https://news.usni.org/category/china/feed",
    "DigiTimes_Asia": "https://www.digitimes.com/rss/daily.xml",
    "Nikkei_China": "https://asia.nikkei.com/rss/feed/category/53"
}

# 3. ESTRAZIONE DATI
def fetch_latest_intel():
    intel_data = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    
    for category, url in SOURCES.items():
        try:
            print(f"Scansione {category}...")
            response = requests.get(url, headers=headers, timeout=12)
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:3]:
                intel_data.append(f"[{category}] {entry.title}: {entry.description}")
        except Exception as e:
            print(f"Skip {category} causa timeout/errore.")
            
    return "\n".join(intel_data)

# 4. ANALISI INTEGRATA (GENERALISTA + SPECIFICA)
def analyze_with_gemini(raw_data):
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Agisci come Direttore dell'Intelligence Strategica. Analizza questi dati sulla Cina e produci un Executive Briefing integrato.
    
    IL TUO REPORT DEVE COPRIRE:
    
    PARTE A - QUADRO GENERALE:
    1. 📊 SINTESI ECONOMICA E GEOPOLITICA: I fatti principali della giornata.
    2. 🎯 INDICATORI CHIAVE: Cosa monitorare nelle prossime 24 ore.

    PARTE B - FOCUS TATTICO (Solo se i dati lo permettono):
    - 💻 TECH WAR: Semiconduttori, AI, Restrizioni.
    - ⚓ MILITARE: Movimenti PLAN, Mar Cinese Meridionale, Taiwan.
    - 🏢 CRISI DEBITO: Immobiliare e PBOC.

    REGOLE:
    - Sii analitico e denso. Calcola l'impatto strategico per ogni notizia.
    - Usa Markdown per la leggibilità.
    - Non avere limiti di lunghezza, il sistema gestirà l'invio multiplo.

    DATI:
    {raw_data}
    """
    response = model.generate_content(prompt)
    return response.text

# 5. CONSEGNA MULTI-MESSAGGIO (CHUNKING)
def send_telegram_briefing(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    chunk_size = 4000
    chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
    
    for index, chunk in enumerate(chunks):
        # Aggiunge intestazione se il messaggio è diviso
        prefix = f"📄 *REPORT OSINT - Parte {index+1}/{len(chunks)}*\n\n" if len(chunks) > 1 else ""
        payload = {
            "chat_id": TELEGRAM_CHAT_ID, 
            "text": prefix + chunk, 
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload, timeout=15)
        except Exception as e:
            print(f"Errore invio: {e}")

# ESECUZIONE
if __name__ == "__main__":
    print("--- START V3.0 TOTAL INTEL ---")
    data = fetch_latest_intel()
    if data:
        briefing = analyze_with_gemini(data)
        send_telegram_briefing(briefing)
        print("--- MISSION COMPLETE ---")
    else:
        print("Nessun dato raccolto.")