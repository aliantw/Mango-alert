import os, sys, requests
from playwright.sync_api import sync_playwright

URL = "https://shop.mango.com/be/nl/p/37097133/99/00"
SIZE = "M"
SIZES = ["XXS", "XS", "S", "M", "L", "XL", "XXL"]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")

def send(text):
    token = os.environ["TELEGRAM_TOKEN"].strip()
    chat = os.environ["CHAT_ID"].strip()
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      data={"chat_id": chat, "text": text}, timeout=20)
    print("TELEGRAM SAYS:", r.text)

responses = []
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
    page = browser.new_page(locale="nl-BE", user_agent=UA,
                            viewport={"width": 1280, "height": 900})
    page.on("response", lambda r: responses.append(r) if "stock" in r.url.lower() else None)
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    try:
        page.get_by_role("button", name="Alleen noodzakelijke cookies").click(timeout=8000)
    except Exception:
        pass
    try:
        page.get_by_text("XXS", exact=True).first.wait_for(timeout=20000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    title = page.title()
    lines = [l.strip() for l in page.inner_text("body").split("\n") if l.strip()]
    browser.close()

print("TITLE:", title)
stock = {}
for i, l in enumerate(lines):
    if l in SIZES and l not in stock:
        nxt = lines[i + 1].lower() if i + 1 < len(lines) else ""
        stock[l] = "ik wil hem" not in nxt
        print("SIZE:", lines[i:i + 3])
print("STOCK:", stock)

if not stock:
    print("PAGE TEXT:", lines[:40])
    sys.exit("Size list not found")
send(f"Test OK. Stock: {stock}") if os.environ.get("TEST") == "yes" else None
if stock.get(SIZE):
    send(f"Size {SIZE} is BACK in stock!\n{URL}")
