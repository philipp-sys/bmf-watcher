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
    print(f"🔍 Starte Scan der BMF-Liste...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        res = requests.get(URL, headers=headers, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Fehler beim Laden der Seite: {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    result_list = soup.find('ol', id='searchResult')
    
    if not result_list:
        print("❌ Liste 'searchResult' nicht gefunden.")
        return

    entries = result_list.find_all('li', class_='bmf-list-entry')
    parsed_entries = []
    
    for entry in entries:
        title_link = entry.find('h3', class_='bmf-entry-title').find('a')
        if title_link:
            title = title_link.get_text(strip=True)
            link = title_link.get('href', '')
            if link.startswith('/'): link = BASE_URL + link
            
            date_tag = entry.find('time')
            date_text = date_tag.get_text(strip=True) if date_tag else "K.A."
            
            parsed_entries.append({'date': date_text, 'title': title, 'link': link})

    if not parsed_entries:
        print("❌ Keine Einträge gefunden.")
        return

    current_snapshot = "\n".join([f"{e['date']}: {e['title']}" for e in parsed_entries])

    last_snapshot = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            last_snapshot = f.read().strip()

    if current_snapshot != last_snapshot:
        print("🔔 Änderung erkannt!")
        
        if last_snapshot != "":
            send_html_mail(parsed_entries)
        else:
            print("Initial-Lauf: Snapshot gespeichert.")
        
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(current_snapshot)
    else:
        print("☕ Keine Änderungen.")

def send_html_mail(entries):
    sender = os.environ.get('SENDER_MAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    
    # --- EMPFÄNGER AUS DATEI EINLESEN ---
    recipients = []
    if os.path.exists(RECIPIENTS_FILE):
        with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
            # Liest Zeile für Zeile, entfernt Leerzeichen und ignoriert leere Zeilen
            recipients = [line.strip() for line in f if line.strip()]
    
    if not recipients:
        print("⚠️ Keine Empfänger in recipients.txt gefunden!")
        return
    
    msg = EmailMessage()
    msg['Subject'] = "🔔 Update: Neue BMF Pressemitteilungen"
    msg['From'] = f"Finanz-Monitor <{sender}>"
    msg['To'] = ", ".join(recipients)

    rows_html = ""
    for e in entries[:5]:
        rows_html += f"""
        <div style="margin-bottom: 20px; padding: 15px; border-left: 4px solid #00528e; background-color: #fcfcfc; border-bottom: 1px solid #eee;">
            <span style="color: #888; font-size: 12px; font-weight: bold; text-transform: uppercase;">{e['date']}</span><br>
            <h3 style="margin: 8px 0; color: #333; font-family: Arial, sans-serif; font-size: 18px;">{e['title']}</h3>
            <a href="{e['link']}" style="display: inline-block; margin-top: 10px; padding: 10px 18px; background-color: #00528e; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 14px;">Meldung lesen →</a>
        </div>
        """

    html_layout = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 30px; border-bottom: 3px solid #00528e; padding-bottom: 20px;">
                    <h1 style="color: #00528e; margin: 0; font-size: 24px;">BMF Monitor</h1>
                    <p style="color: #666; margin: 5px 0;">Aktuelle Veröffentlichungen im Überblick</p>
                </div>
                <p>Guten Tag,</p>
                <p>das Bundesfinanzministerium hat neue Informationen veröffentlicht oder bestehende Einträge aktualisiert:</p>
                {rows_html}
                <div style="margin-top: 30px; text-align: center; font-size: 12px; color: #999;">
                    <p>Dieser Service wird automatisch betrieben.<br>
                    <a href="{URL}" style="color: #00528e;">Direkt zur BMF-Website</a></p>
                </div>
            </div>
        </body>
    </html>
    """

    msg.set_content("Updates vom BMF verfügbar. Nutzen Sie HTML-Mail.")
    msg.add_alternative(html_layout, subtype='html')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print(f"📧 Mail an {len(recipients)} Empfänger gesendet.")
    except Exception as e:
        print(f"❌ Mail-Fehler: {e}")

if __name__ == "__main__":
    run()
