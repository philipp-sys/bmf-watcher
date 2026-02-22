import requests
from bs4 import BeautifulSoup
import json
import os
import smtplib
import time
from email.message import EmailMessage

# --- KONFIGURATION ---
BMF_URL = "https://www.bundesfinanzministerium.de/Web/DE/Themen/Briefmarken-Sammlermuenzen/Sammlermuenzen/Letzte_Meldungen/letzte_meldungen.html"
BASE_URL = "https://www.bundesfinanzministerium.de/"
HISTORY_FILE = "bmf_history.json"

def check_bmf():
    print("🏛️ BMF-Monitor: Suche nach neuen Meldungen...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safari/537.36'}
    
    try:
        response = requests.get(BMF_URL, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"❌ Fehler: BMF Seite nicht erreichbar (Status {response.status_code})")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Wir suchen alle Meldungs-Container
        teasers = soup.find_all('div', class_='listenteaser-wrapper')
        
        # Lade Historie bereits bekannter Links
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)

        new_entries = []

        for teaser in teasers:
            link_tag = teaser.find('h3').find('a') if teaser.find('h3') else None
            if not link_tag: continue
            
            title = link_tag.get_text(strip=True)
            relative_link = link_tag.get('href')
            full_link = BASE_URL + relative_link if not relative_link.startswith('http') else relative_link
            date_tag = teaser.find('p', class_='date')
            date_text = date_tag.get_text(strip=True) if date_tag else "Unbekanntes Datum"
            
            # Wenn der Link noch nicht in der Historie ist -> Neue Meldung!
            if full_link not in history:
                new_entries.append({
                    'title': title,
                    'link': full_link,
                    'date': date_text
                })
                history.append(full_link)

        if new_entries:
            print(f"✨ {len(new_entries)} neue BMF-Meldungen gefunden!")
            send_bmf_mail(new_entries)
            
            # Historie aktualisieren (wir behalten nur die letzten 50 Links)
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history[-50:], f, indent=4)
        else:
            print("☕ Keine neuen Meldungen beim BMF.")

    except Exception as e:
        print(f"❌ Fehler beim BMF-Check: {e}")

def send_bmf_mail(entries):
    sender = os.environ.get('SENDER_MAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    
    # Empfängerliste laden (wir nutzen dieselbe wie beim MDM-Skript)
    recipients = []
    if os.path.exists("recipients.txt"):
        with open("recipients.txt", "r") as f:
            recipients = [l.strip() for l in f if "@" in l]
    
    if not recipients:
        recipients = [sender]

    msg = EmailMessage()
    msg['Subject'] = f"🏛️ BMF ALARM: {len(entries)} neue Münz-Meldung(en)"
    msg['From'] = f"BMF-Wächter <{sender}>"
    msg['To'] = ", ".join(recipients)

    body = "Das Bundesfinanzministerium hat neue Informationen veröffentlicht:\n\n"
    for e in entries:
        body += f"📅 Datum: {e['date']}\n📌 Titel: {e['title']}\n🔗 Link: {e['link']}\n\n"
        body += "-"*30 + "\n\n"
    
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("📧 BMF-E-Mail erfolgreich versendet.")
    except Exception as e:
        print(f"❌ E-Mail-Fehler BMF: {e}")

if __name__ == "__main__":
    check_bmf()
