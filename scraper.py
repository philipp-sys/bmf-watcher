import requests
from bs4 import BeautifulSoup
import smtplib
import os
from email.message import EmailMessage

URL = "https://www.bundesfinanzministerium.de/Web/DE/Presse/Pressemitteilungen/pressemitteilungen.html"
STATUS_FILE = "last_news.txt"

def run():
    # 1. Seite laden
    res = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(res.text, 'html.parser')
    current_news = soup.find('h3').get_text(strip=True)

    # 2. Letzten Stand lesen
    last_news = ""
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            last_news = f.read().strip()

    # 3. Vergleichen & Mailen
    if current_news != last_news:
        print(f"Neu: {current_news}")
        send_mail(current_news)
        with open(STATUS_FILE, "w") as f:
            f.write(current_news)
    else:
        print("Nichts Neues.")

def send_mail(content):
    msg = EmailMessage()
    msg.set_content(f"Neue BMF Meldung:\n\n{content}\n\nLink: {URL}")
    msg['Subject'] = "🚨 BMF Update"
    msg['From'] = os.environ['SENDER_EMAIL']
    msg['To'] = "philipp@langeweile.io"

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(os.environ['SENDER_EMAIL'], os.environ['EMAIL_PASSWORD'])
        smtp.send_message(msg)

if __name__ == "__main__":
    run()
