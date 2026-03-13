import feedparser
import requests
import google.generativeai as genai
import os
import sys

# 1. RECUPERO CREDENZIALI BLINDATE
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("ERRORE CRITICO: Credenziali mancanti nei GitHub Secrets.")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# 2. FONTI STRATEGICHE MIRATE PER NICCHIA
SOURCES = {
    "SCMP_Macro": "https://www.scmp.com/rss/2/feed", 
    "USNI_Military": "https://news.usni.org/category/china/feed", 
    "DigiTimes_Tech": "https://www.digitimes.com/rss/daily.xml", 
    "Nikkei_Asia": "https://asia.nikkei.com/rss/feed/category/53" 
}

# 3. MOTORE DI ESTRAZIONE (CON ANTI-FIREWALL)
def fetch_latest_intel():
    intel_data = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    for category, url in SOURCES.items():
        try:
            print(f"Estrazione da {category}...")
            response = requests.get(url, headers=headers, timeout=10)
            feed = feedparser.parse(response.content)
            
            for entry in feed.entries[:3]:
                intel_data.append(f"[{category}] Titolo: {entry.title}\nSommario: {entry.description}\n")
        except Exception as e:
            print(f"Avviso: Timeout o blocco su {category}. Errore: {str(e)}")
            intel_data.append(f"Errore recupero {category}: Dati non disponibili al momento.")
            
    return "\n".join(intel_data)

# 4. MOTORE COGNITIVO (PROMPT A MATRICE)
def analyze_with_gemini(raw_data):
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Sei il Direttore dell'OSINT per un'agenzia di intelligence strategica. Il tuo compito è filtrare il rumore e individuare segnali deboli in questo feed di dati grezzi sulla Cina.

    I TUOI UNICI 3 VETTORI DI RICERCA (Ignora categoricamente tutto il resto):
    1. 💻 GUERRA DEI CHIP E TECH: Cerca restrizioni all'export, progressi SMIC/Huawei, dazi su EV, AI computing, colli di bottiglia su terre rare.
    2. ⚓ POSTURA MILITARE E PLAN: Cerca manovre della Marina (PLAN) nel Mar Cinese Meridionale, incursioni ADIZ a Taiwan, cambi ai vertici dell'Esercito (PLA).
    3. 🏢 CRISI MACRO E DEBITO: Cerca default immobiliari (Vanke, Evergrande), iniezioni di liquidità della PBOC, dati su deflazione e disoccupazione giovanile.

    PROTOCOLLO DI ANALISI:
    - Se una notizia non rientra in questi 3 vettori, ELIMINALA.
    - Per ogni notizia rilevante, estrai il fatto oggettivo e calcola l'IMPATTO STRATEGICO (Basso, Medio, Alto).

    FORMATO DI OUTPUT OBBLIGATORIO (Usa Markdown, sii denso e analitico):
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

# 5. MOTORE DI CONSEGNA (ALGORITMO DI CHUNKING)
def send_telegram_briefing(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    chunk_size = 4000 
    chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
    
    print(f"Messaggio diviso in {len(chunks)} blocchi. Inizio trasmissione...")
    
    for index, chunk in enumerate(chunks):
        if len(chunks) > 1:
            testo_formattato = f"📄 *Parte {index + 1} di {len(chunks)}*\n\n{chunk}"
        else:
            testo_formattato = chunk

        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": testo_formattato, "parse_mode": "Markdown"}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"Errore Telegram sul blocco {index + 1}: {response.text}")
            else:
                print(f"Blocco {index + 1} consegnato con successo.")
        except Exception as e:
            print(f"Errore critico di connessione sul blocco {index + 1}: {str(e)}")

# --- ESECUZIONE PRINCIPALE ---
if __name__ == "__main__":
    print("--- AVVIO PIPELINE OSINT (V2.0 MULTI-CHUNK) ---")
    raw_intel = fetch_latest_intel()
    
    if raw_intel and "Titolo:" in raw_intel:
        print("Dati estratti. Inizio analisi IA...")
        final_briefing = analyze_with_gemini(raw_intel)
        
        print("Analisi completata. Trasmissione in corso...")
        send_telegram_briefing(final_briefing)
    else:
        print("Estrazione fallita o nessun dato rilevante. Analisi annullata per evitare messaggi vuoti.")
    
    print("--- CHIUSURA SISTEMA ---")