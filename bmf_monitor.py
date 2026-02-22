import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
from email.message import EmailMessage

# --- KONFIGURATION ---
URL = "https://www.bundesfinanzministerium.de/Web/DE/Themen/Briefmarken-Sammlermuenzen/Sammlermuenzen/Letzte_Meldungen/letzte_meldungen.html"
BASE_URL = "https://www.bundesfinanzministerium.de/"
HISTORY_FILE = "bmf_history.json"
RECIPIENTS_FILE = "recipients.txt"

def check_bmf():
    print("🏛️ BMF-Wächter startet...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safari/537.36'}
    
    try:
        res = requests.get(URL, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Den Container greifen, den du identifiziert hast
        teasers = soup.find_all('div', class_='listenteaser-wrapper')
        
        # Historie laden
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)

        new_entries = []
        for teaser in teasers:
            link_tag = teaser.find('h3').find('a') if teaser.find('h3') else None
            if not link_tag: continue
            
            title = link_tag.get_text(strip=True)
            path = link_tag.get('href')
            # Link vervollständigen, falls er relativ ist
            full_link = BASE_URL + path if not path.startswith('http') else path
            
            date_tag = teaser.find('p', class_='date')
            date = date_tag.get_text(strip=True) if date_tag else "Unbekannt"

            if full_link not in history:
                new_entries.append({'title': title, 'link': full_link, 'date': date})
                history.append(full_link)

        if new_entries:
            print(f"✨ {len(new_entries)} neue Meldungen gefunden!")
            send_mail(new_entries)
            # Historie speichern (nur die letzten 100, um die Datei klein zu halten)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history[-100:], f, indent=4)
        else:
            print("☕ Keine neuen Meldungen.")

    except Exception as e:
        print(f"❌ Fehler: {e}")

def send_mail(entries):
    sender = os.environ.get('SENDER_MAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    
    # Empfänger aus Datei lesen oder Standard an Sender
    recs = [sender]
    if os.path.exists(RECIPIENTS_FILE):
        with open(RECIPIENTS_FILE, "r") as f:
            recs = [l.strip() for l in f if "@" in l]

    msg = EmailMessage()
    msg['Subject'] = f"🏛️ BMF UPDATE: {len(entries)} neue Meldung(en)"
    msg['From'] = f"BMF Monitor <{sender}>"
    msg['To'] = ", ".join(recs)

    body = "Es gibt neue offizielle Meldungen vom Bundesfinanzministerium:\n\n"
    for e in entries:
        body += f"📅 {e['date']}\n📌 {e['title']}\n🔗 {e['link']}\n\n"
    
    msg.set_content(body)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)
    print("📧 E-Mail versendet.")

if __name__ == "__main__":
    check_bmf()
