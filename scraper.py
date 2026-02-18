import requests
from bs4 import BeautifulSoup
import smtplib
import os
import sys
from email.message import EmailMessage
from urllib.parse import urljoin # Neu: Für sichere URLs

# --- EINSTELLUNGEN ---
URL = "https://www.bundesfinanzministerium.de/Web/DE/Presse/Pressemitteilungen/pressemitteilungen.html"
BASE_URL = "https://www.bundesfinanzministerium.de"
STATUS_FILE = "last_news.txt"
RECIPIENTS_FILE = "recipients.txt"

def run():
    print("--- 🚀 START BMF MONITOR (BCC-VERSION) ---")
    
    sender = os.environ.get('SENDER_MAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    
    if not sender or not password:
        print("❌ FEHLER: Secrets fehlen.")
        sys.exit(1)

    # 1. Empfängerliste einlesen
    if not os.path.exists(RECIPIENTS_FILE):
        print(f"❌ FEHLER: {RECIPIENTS_FILE} fehlt.")
        sys.exit(1)
        
    with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
        recipients = [line.strip() for line in f if line.strip() and "@" in line]
    
    if not recipients:
        print("❌ FEHLER: Keine Empfänger gefunden.")
        sys.exit(1)

    # 2. Webseite scrapen
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safari/537.36'}
    res = requests.get(URL, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    result_list = soup.find('ol', id='searchResult')
    if not result_list:
        print("❌ FEHLER: Listen-Struktur nicht gefunden.")
        return

    entries = result_list.find_all('li', class_='bmf-list-entry')
    parsed_data = []
    
    for entry in entries:
        title_tag = entry.find('h3', class_='bmf-entry-title').find('a')
        if title_tag:
            title = title_tag.get_text(strip=True)
            raw_link = title_tag.get('href', '')
            
            # KORREKTUR: URL sicher zusammenbauen (egal ob /Content oder Content)
            link = urljoin(BASE_URL, raw_link)
            
            date = entry.find('time').get_text(strip=True) if entry.find('time') else "Neu"
            parsed_data.append({'date': date, 'title': title, 'link': link})

    # 3. Snapshot-Vergleich
    current_snapshot = "\n".join([f"{e['date']}: {e['title']}" for e in parsed_data])
    
    last_snapshot = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            last_snapshot = f.read().strip()

    if current_snapshot != last_snapshot:
        print("🔔 Änderung erkannt!")
        
        # Sende Mail (außer beim allerersten Mal)
        if last_snapshot != "" and "FORCETEST" not in last_snapshot:
            send_html_mail(parsed_data, recipients, sender, password)
        elif "FORCETEST" in last_snapshot:
            print("🧪 Test-Modus aktiv...")
            send_html_mail(parsed_data, recipients, sender, password)
        
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(current_snapshot)
    else:
        print("☕ Keine Änderungen.")

def send_html_mail(entries, recipients, sender, password):
    msg = EmailMessage()
    msg['Subject'] = "🚨 BMF Update: Neue Pressemitteilung"
    msg['From'] = f"Finanz-Monitor <{sender}>"
    
    # BCC LOGIK: 
    # Im sichtbaren "An" Feld steht nur der Absender selbst.
    msg['To'] = sender 

    news_html = ""
    for e in entries[:5]:
        news_html += f"""
        <div style="margin-bottom: 15px; padding: 10px; border-left: 5px solid #00528e; background: #f9f9f9;">
            <small style="color: #666;">{e['date']}</small><br>
            <strong style="font-size: 16px;">{e['title']}</strong><br>
            <a href="{e['link']}" style="color: #00528e; text-decoration: none; font-weight: bold;">Meldung lesen →</a>
        </div>
        """

    html_layout = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #00528e; border-bottom: 2px solid #00528e;">Aktuelles vom BMF</h2>
            <p>Es gibt neue Veröffentlichungen:</p>
            {news_html}
            <p style="font-size: 12px; color: #999; margin-top: 20px;">Automatisierter Service. <a href="{URL}">Zur BMF-Webseite</a></p>
        </body>
    </html>
    """
    msg.add_alternative(html_layout, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            # Hier schicken wir die Mail an die gesamte Empfängerliste (BCC-Effekt)
            smtp.send_message(msg, to_addrs=recipients)
        print(f"📧 Mail erfolgreich via BCC an {len(recipients)} Empfänger verschickt.")
    except Exception as e:
        print(f"❌ Fehler beim Versenden: {e}")

if __name__ == "__main__":
    run()
