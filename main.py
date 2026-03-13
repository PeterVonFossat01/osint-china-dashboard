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

# FONTI STRATEGICHE MIRATE PER NICCHIA
SOURCES = {
    "SCMP_Macro": "https://www.scmp.com/rss/2/feed", # Economia generale
    "USNI_Military": "https://news.usni.org/category/china/feed", # US Naval Institute - Movimenti Flotta PLAN (Militare)
    "DigiTimes_Tech": "https://www.digitimes.com/rss/daily.xml", # Supply chain asiatica e Semiconduttori (Tech War)
    "Nikkei_Asia": "https://asia.nikkei.com/rss/feed/category/53" # Dinamiche immobiliari e debito (Economia)
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
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # PROMPT A MATRICE PONDERATA (Ingegneria Avanzata)
    prompt = f"""
    Sei il Direttore dell'OSINT per un'agenzia di intelligence strategica. Il tuo compito è filtrare il rumore e individuare segnali deboli in questo feed di dati grezzi sulla Cina.

    I TUOI UNICI 3 VETTORI DI RICERCA (Ignora categoricamente tutto il resto):
    1. 💻 GUERRA DEI CHIP E TECH: Cerca restrizioni all'export, progressi SMIC/Huawei, dazi su EV, AI computing, colli di bottiglia su terre rare.
    2. ⚓ POSTURA MILITARE E PLAN: Cerca manovre della Marina (PLAN) nel Mar Cinese Meridionale, incursioni ADIZ a Taiwan, cambi ai vertici dell'Esercito (PLA).
    3. 🏢 CRISI MACRO E DEBITO: Cerca default immobiliari (Vanke, Evergrande), iniezioni di liquidità della PBOC, dati su deflazione e disoccupazione giovanile.

    PROTOCOLLO DI ANALISI:
    - Se una notizia non rientra in questi 3 vettori, ELIMINALA.
    - Per ogni notizia rilevante, estrai il fatto oggettivo e calcola l'IMPATTO STRATEGICO (Basso, Medio, Alto).

    FORMATO DI OUTPUT OBBLIGATORIO (Max 3500 caratteri, usa Markdown, sii telegrafico):
    # 🔴 EXECUTIVE BRIEFING: RPC
    
    ### 💻 Semiconduttori & Tech War
    [Nessun dato rilevante] (Oppure elenca i fatti con -> *Impatto: [Valutazione]*)
    
    ### ⚓ Postura Militare (PLA/PLAN)
    [Nessun dato rilevante] (Oppure elenca i fatti con -> *Impatto: [Valutazione]*)
    
    ### 🏢 Crisi Debito & Macroeconomia
    [Nessun dato rilevante] (Oppure elenca i fatti con -> *Impatto: [Valutazione]*)

    DATI GREZZI DA ANALIZZARE:
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