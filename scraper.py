import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.message import EmailMessage

# URL der Pressemitteilungen
URL = "https://www.bundesfinanzministerium.de/Web/DE/Presse/Pressemitteilungen/pressemitteilungen.html"
BASE_URL = "https://www.bundesfinanzministerium.de"
STATUS_FILE = "last_news.txt"

def run():
    print("🔍 Suche nach der aktuellsten Pressemitteilung...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        res = requests.get(URL, headers=headers, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Fehler beim Laden der Seite: {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    
    # VALIDIERUNG & SUCHE:
    # Wir suchen jetzt gezielt nach h3-Überschriften, die einen Link enthalten.
    # Wir filtern zudem nach dem Haupt-Inhaltsbereich, um Navigation/Footer zu ignorieren.
    
    found_news = None
    # Wir suchen alle h3-Tags auf der Seite
    for h3 in soup.find_all('h3'):
        link_tag = h3.find('a')
        # Eine echte Pressemeldung hat immer einen Link im h3
        if link_tag and link_tag.get('href'):
            # Wir nehmen die allererste, die wir finden (das ist die oberste im Inhaltsbereich)
            found_news = {
                'title': h3.get_text(strip=True),
                'link': BASE_URL + link_tag.get('href') if link_tag.get('href').startswith('/') else link_tag.get('href')
            }
            break
            
    if not found_news:
        print("❌ Keine Pressemitteilung gefunden. Struktur prüfen!")
        return
    
    current_id = found_news['title']

    # 3. Letzten Stand lesen
    last_id = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            last_id = f.read().strip()

    # 4. Vergleich
    if current_id != last_id:
        print(f"🔔 NEU: {current_id}")
        
        # Falls die Datei leer war (erster Run), speichern wir nur ohne Mail
        if last_id != "":
            send_mail(found_news['title'], found_news['link'])
        else:
            print("Erster Durchlauf: Speichere Initialwert ohne Mail.")
        
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(current_id)
    else:
        print(f"☕ Keine Änderung. Aktuellste: {current_id}")

def send_mail(title, link):
    sender = os.environ.get('SENDER_MAIL')
    password = os.environ.get('EMAIL_PASSWORD')
    recipient = "philipp@langeweile.io"

    msg = EmailMessage()
    msg.set_content(f"Hallo Philipp,\n\ndas BMF hat eine neue Pressemitteilung veröffentlicht:\n\n📌 {title}\n\n🔗 Direkt-Link: {link}\n\nÜbersicht: {URL}")
    msg['Subject'] = f"🚨 BMF Update: {title[:40]}..."
    msg['From'] = sender
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("📧 E-Mail wurde versendet!")
    except Exception as e:
        print(f"❌ Mail-Fehler: {e}")

if __name__ == "__main__":
    run()
