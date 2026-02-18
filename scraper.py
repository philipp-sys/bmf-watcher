import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.message import EmailMessage

URL = "https://www.bundesfinanzministerium.de/Web/DE/Presse/Pressemitteilungen/pressemitteilungen.html"
BASE_URL = "https://www.bundesfinanzministerium.de"
STATUS_FILE = "last_news.txt"

def run():
    print(f"🔍 Scanne BMF-Ergebnisliste auf: {URL}")
    
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
    
    # Wir suchen gezielt die Liste mit der ID 'searchResult'
    result_list = soup.find('ol', id='searchResult')
    
    if not result_list:
        print("❌ Die Liste 'searchResult' wurde nicht gefunden. Struktur hat sich eventuell geändert.")
        return

    # Wir extrahieren alle Einträge (li) innerhalb dieser Liste
    entries = result_list.find_all('li', class_='bmf-list-entry')
    
    parsed_entries = []
    for entry in entries:
        # Den Link und Titel aus dem h3-Tag extrahieren
        title_link = entry.find('h3', class_='bmf-entry-title').find('a')
        if title_link:
            title = title_link.get_text(strip=True)
            link = title_link.get('href', '')
            # Link vervollständigen falls nötig
            if link.startswith('/'): link = BASE_URL + link
            
            # Datum finden (aus dem <time> Tag)
            date_tag = entry.find('time')
            date_text = date_tag.get_text(strip=True) if date_tag else "Unbekanntes Datum"
            
            parsed_entries.append(f"{date_text}: {title} ({link})")

    if not parsed_entries:
        print("❌ Keine Pressemitteilungen in der Liste gefunden.")
        return

    # Snapshot erstellen: Alle Zeilen zu einem Block zusammenfügen
    current_snapshot = "\n".join(parsed_entries)

    # Alten Stand lesen
    last_snapshot = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            last_snapshot = f.read().strip()

    # Vergleich
    if current_snapshot != last_snapshot:
        print("🔔 ÄNDERUNG DETEKTIERT!")
        
        # Mail nur senden, wenn wir einen Vergleichswert haben (verhindert Mail beim ersten Setup)
        if last_snapshot != "":
            # Vorschau der obersten 3 Meldungen für die Mail
            preview = "\n\n".join(parsed_entries[:3])
            send_mail(preview)
        else:
            print("Initialer Lauf: Snapshot gespeichert. Ab jetzt wird bei jeder Änderung alarmiert.")
        
        # Neuen Stand speichern
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(current_snapshot)
    else:
        print("☕ Liste ist unverändert.")

def send_mail(content):
    sender = os.environ.get('SENDER_MAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    recipient = "philipp@langeweile.io"

    msg = EmailMessage()
    msg.set_content(f"Hallo Philipp,\n\nes gibt eine Änderung in der Liste der BMF-Pressemitteilungen!\n\nAktuelle Top-Meldungen:\n\n{content}\n\nAlle Meldungen findest du hier: {URL}")
    msg['Subject'] = "🚨 BMF-Monitor: Änderung in der Ergebnisliste"
    msg['From'] = sender
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("📧 Benachrichtigungs-Mail erfolgreich versendet.")
    except Exception as e:
        print(f"❌ Mail-Fehler: {e}")

if __name__ == "__main__":
    run()
