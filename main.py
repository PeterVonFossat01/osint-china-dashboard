import feedparser
import requests
import google.generativeai as genai
import os
import sys
import time
import calendar

# 1. CREDENZIALI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("ERRORE: Credenziali mancanti.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# 2. SET DI FONTI UNIFICATO
SOURCES = {
    "SCMP_General": "https://www.scmp.com/rss/2/feed",
    "SCMP_Tech": "https://www.scmp.com/rss/318198/feed",
    "USNI_Military": "https://news.usni.org/category/china/feed",
    "DigiTimes_Asia": "https://www.digitimes.com/rss/daily.xml",
    "Nikkei_China": "https://asia.nikkei.com/rss/feed/category/53"
}

# 3. ESTRAZIONE DATI CON FILTRO TEMPORALE E CACHE-BUSTER
def fetch_latest_intel():
    intel_data = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache'
    }
    
    # Calcola il limite di tempo esatto: 48 ore fa (in secondi)
    time_limit = time.time() - (48 * 3600)
    
    for category, url in SOURCES.items():
        try:
            print(f"Scansione {category}...")
            # CACHE-BUSTER: Aggiunge l'ora esatta all'URL per forzare dati freschi
            cache_buster_url = f"{url}?_={int(time.time())}"
            response = requests.get(cache_buster_url, headers=headers, timeout=12)
            feed = feedparser.parse(response.content)
            
            valid_entries = 0
            for entry in feed.entries:
                if valid_entries >= 3:
                    break # Si ferma dopo aver trovato 3 notizie VALIDE E RECENTI
                
                # CONTROLLO DATA: Se la notizia è più vecchia di 48 ore, la ignora
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    entry_time = calendar.timegm(entry.published_parsed)
                    if entry_time < time_limit:
                        continue 
                
                intel_data.append(f"[{category}] {entry.title}: {entry.description}")
                valid_entries += 1
                
        except Exception as e:
            print(f"Skip {category} causa timeout/errore: {e}")
            
    return "\n".join(intel_data)

# 4. ANALISI INTEGRATA
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
    - Usa Markdown in modo corretto (chiudi sempre gli asterischi).

    DATI:
    {raw_data}
    """
    response = model.generate_content(prompt)
    return response.text

# 5. CONSEGNA MULTI-MESSAGGIO INTELLIGENTE
def send_telegram_briefing(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    paragraphs = message.split('\n')
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        if len(current_chunk) + len(p) + 1 < 3800: 
            current_chunk += p + "\n"
        else:
            chunks.append(current_chunk)
            current_chunk = p + "\n"
    if current_chunk:
        chunks.append(current_chunk)
        
    print(f"Messaggio diviso in {len(chunks)} blocchi. Inizio trasmissione...")
    
    for index, chunk in enumerate(chunks):
        prefix = f"📄 *REPORT OSINT - Parte {index+1}/{len(chunks)}*\n\n" if len(chunks) > 1 else ""
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": prefix + chunk, "parse_mode": "Markdown"}
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code != 200:
                print(f"Errore Markdown al blocco {index+1}. Rinvio come testo semplice...")
                payload["parse_mode"] = "" 
                requests.post(url, json=payload, timeout=15)
            else:
                print(f"Blocco {index+1} consegnato con successo.")
        except Exception as e:
            print(f"Errore invio blocco {index+1}: {e}")
            
        time.sleep(2) 

# ESECUZIONE
if __name__ == "__main__":
    print("--- START V4.0 TOTAL INTEL (TIME-GATED) ---")
    data = fetch_latest_intel()
    if data:
        briefing = analyze_with_gemini(data)
        send_telegram_briefing(briefing)
        print("--- MISSION COMPLETE ---")
    else:
        print("Nessun dato recente raccolto nelle ultime 48h.")
