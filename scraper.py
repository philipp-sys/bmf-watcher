import requests
from bs4 import BeautifulSoup
import smtplib
import os
import sys
from email.message import EmailMessage

# Konfiguration
URL = "https://www.bundesfinanzministerium.de/Web/DE/Presse/Pressemitteilungen/pressemitteilungen.html"
BASE_URL = "https://www.bundesfinanzministerium.de"
STATUS_FILE = "last_news.txt"
RECIPIENTS_FILE = "recipients.txt"

def run():
    print("--- 🚀 START BMF MONITOR ---")
    
    # 1. Daten aus GitHub Secrets laden
    sender = os.environ.get('SENDER_MAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    
    # Strenger Check: Wenn SENDER_MAIL fehlt, bricht das Skript hier mit Fehlermeldung ab
    if not sender:
        print("❌ FEHLER: SENDER_MAIL wurde nicht gefunden! Prüfe die GitHub Secrets.")
        sys.exit(1)
    if not password:
        print("❌ FEHLER: EMAIL_PASSWORD wurde nicht gefunden!")
        sys.exit(1)

    print(f"✅ Login-Check: Absender ist {sender}")

    # 2. Empfängerliste einlesen
    if not os.path.exists(RECIPIENTS_FILE):
        print(f"❌ FEHLER: {RECIPIENTS_FILE} fehlt.")
        sys.exit(1)
        
    with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
        recipients = [line.strip() for line in f if line.strip() and "@" in line]
    
    if not recipients:
        print("❌ FEHLER: Keine Empfänger gefunden.")
        sys.exit(1)

    # 3. Webseite scrapen
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Safari/537.36'}
    res = requests.get(URL, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Wir suchen die Ergebnisliste
    result_list = soup.find('ol', id='searchResult')
    if not result_list:
        print("❌ FEHLER: Listen-Struktur auf Website nicht gefunden.")
        return

    entries = result_list.find_all('li', class_='bmf-list-entry')
    parsed_data = []
    
    for entry in entries:
        title_tag = entry.find('h3', class_='bmf-entry-title').find('a')
        if title_tag:
            title = title_tag.get_text(strip=True)
            link = title_tag.get('href', '')
            if link.startswith('/'): link = BASE_URL + link
            date = entry.find('time').get_text(strip=True) if entry.find('time') else "Neu"
            parsed_data.append({'date': date, 'title': title, 'link': link})

    # 4. Snapshot-Vergleich
    current_snapshot = "\n".join([f"{e['date']}: {e['title']}" for e in parsed_data])
    
    last_snapshot = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            last_snapshot = f.read().strip()

    # Nur senden, wenn sich etwas geändert hat ODER die Datei RESET heißt
    if current_snapshot != last_snapshot:
        print("🔔 Änderung erkannt! Sende E-Mails...")
        
        # Sende Mail (außer beim allerersten Mal, wenn die Datei komplett neu angelegt wird)
        if last_snapshot != "":
            send_html_mail(parsed_data, recipients, sender, password)
        
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(current_snapshot)
    else:
        print("☕ Keine Änderungen zum letzten Check.")

def send_html_mail(entries, recipients, sender, password):
    msg = EmailMessage()
    msg['Subject'] = "🚨 BMF Update: Neue Pressemitteilung"
    msg['From'] = f"Finanz-Monitor <{sender}>"
    msg['To'] = ", ".join(recipients)

    # HTML-Liste bauen
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
            {news_html}
            <p style="font-size: 12px; color: #999; margin-top: 20px;">Automatisierter Service. <a href="{URL}">Zur BMF-Webseite</a></p>
        </body>
    </html>
    """
    msg.add_alternative(html_layout, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)
    print(f"✅ Mail erfolgreich an {len(recipients)} Empfänger verschickt.")

if __name__ == "__main__":
    run()
