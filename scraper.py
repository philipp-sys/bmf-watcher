import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.message import EmailMessage

# --- EINSTELLUNGEN ---
URL = "https://www.bundesfinanzministerium.de/Web/DE/Presse/Pressemitteilungen/pressemitteilungen.html"
BASE_URL = "https://www.bundesfinanzministerium.de"
STATUS_FILE = "last_news.txt"
RECIPIENTS_FILE = "recipients.txt"

def run():
    print("--- 🚀 DEBUG START ---")
    
    # 1. Secrets prüfen (nur ob sie da sind)
    sender = os.environ.get('SENDER_MAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    print(f"DEBUG: SENDER_MAIL vorhanden: {'Ja' if sender else 'NEIN ❌'}")
    print(f"DEBUG: EMAIL_PASSWORD vorhanden: {'Ja' if password else 'NEIN ❌'}")

    # 2. Empfänger prüfen
    recipients = []
    if os.path.exists(RECIPIENTS_FILE):
        with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
            recipients = [line.strip() for line in f if line.strip()]
    print(f"DEBUG: Empfänger gefunden: {recipients}")

    # 3. Seite laden
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(URL, headers=headers, timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        result_list = soup.find('ol', id='searchResult')
        entries = result_list.find_all('li', class_='bmf-list-entry') if result_list else []
        print(f"DEBUG: Einträge auf Webseite gefunden: {len(entries)}")
    except Exception as e:
        print(f"DEBUG: Fehler beim Scrapen: {e}")
        return

    # Strukturieren
    parsed_entries = []
    for entry in entries:
        title_link = entry.find('h3', class_='bmf-entry-title').find('a')
        if title_link:
            parsed_entries.append({
                'date': entry.find('time').get_text(strip=True) if entry.find('time') else "K.A.",
                'title': title_link.get_text(strip=True),
                'link': (BASE_URL + title_link.get('href')) if title_link.get('href').startswith('/') else title_link.get('href')
            })

    # 4. Vergleichs-Snapshot
    current_snapshot = "\n".join([f"{e['date']}: {e['title']}" for e in parsed_entries])
    
    last_snapshot = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            last_snapshot = f.read().strip()
    
    print(f"DEBUG: Länge alter Snapshot: {len(last_snapshot)} Zeichen")
    print(f"DEBUG: Länge neuer Snapshot: {len(current_snapshot)} Zeichen")

    # 5. Die Logik-Entscheidung
    if current_snapshot != last_snapshot:
        print("DEBUG: 🔔 UNTERSCHIED ERKANNT!")
        if last_snapshot != "":
            print("DEBUG: Starte E-Mail Versand...")
            send_html_mail(parsed_entries, recipients, sender, password)
        else:
            print("DEBUG: Erster Lauf (last_snapshot war leer). Speichere nur.")
        
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(current_snapshot)
    else:
        print("DEBUG: ☕ Keine Änderungen zum letzten Snapshot.")
    
    print("--- 🏁 DEBUG ENDE ---")

def send_html_mail(entries, recipients, sender, password):
    msg = EmailMessage()
    msg['Subject'] = "🔔 BMF Update - Neue Pressemitteilung"
    msg['From'] = f"Finanz-Monitor <{sender}>"
    msg['To'] = ", ".join(recipients)

    rows_html = "".join([f"<p><b>{e['date']}</b>: {e['title']}<br><a href='{e['link']}'>Link</a></p><hr>" for e in entries[:5]])
    html_layout = f"<html><body><h2>BMF Updates</h2>{rows_html}</body></html>"
    msg.add_alternative(html_layout, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("DEBUG: ✅ E-Mail wurde erfolgreich abgeschickt!")
    except Exception as e:
        print(f"DEBUG: ❌ SMTP FEHLER: {e}")

if __name__ == "__main__":
    run()
