import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.message import EmailMessage

# Einstellungen
URL = "https://www.bundesfinanzministerium.de/Web/DE/Presse/Pressemitteilungen/pressemitteilungen.html"
STATUS_FILE = "last_news.txt"

def run():
    print("🔍 Suche nach neuen Pressemitteilungen...")
    
    # 1. Seite laden mit einem "User-Agent" (damit das BMF uns nicht für einen bösen Bot hält)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        res = requests.get(URL, headers=headers, timeout=10)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Fehler beim Laden der Seite: {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 2. Die erste Überschrift (h3) finden
    first_h3 = soup.find('h3')
    if not first_h3:
        print("❌ Struktur der Seite konnte nicht gelesen werden.")
        return
    
    current_news = first_h3.get_text(strip=True)

    # 3. Den letzten Stand aus der Datei lesen
    last_news = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            last_news = f.read().strip()

    # 4. Vergleich und Aktion
    if current_news != last_news:
        print(f"🔔 NEU ENTDECKT: {current_news}")
        
        # Nur Mail schicken, wenn wir schon mal einen alten Stand hatten 
        # (verhindert eine Mail beim allerersten Durchlauf)
        if last_news != "":
            send_mail(current_news)
        
        # Den neuen Stand speichern
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(current_news)
    else:
        print("☕ Nichts Neues. Alles beim Alten.")

def send_mail(content):
    # Daten aus den GitHub Secrets holen
    sender = os.environ.get('SENDER_MAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    recipient = "philipp@langeweile.io"

    msg = EmailMessage()
    msg.set_content(f"Hallo Philipp,\n\ndas BMF hat eine neue Pressemitteilung veröffentlicht:\n\n{content}\n\nLink zur Übersicht: {URL}")
    msg['Subject'] = "🚨 BMF Update: Neue Meldung"
    msg['From'] = sender
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("📧 E-Mail wurde erfolgreich versendet!")
    except Exception as e:
        print(f"❌ Fehler beim E-Mail-Versand: {e}")

if __name__ == "__main__":
    run()
