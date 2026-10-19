import os, sys, requests
from playwright.sync_api import sync_playwright

URL = "https://shop.mango.com/be/nl/p/37097133/99/00"
SIZE = "M"
SIZES = ["XXS", "XS", "S", "M", "L", "XL", "XXL"]

def send(text):
    requests.post(
        f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
        data={"chat_id": os.environ["CHAT_ID"], "text": text}, timeout=20)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(locale="nl-BE")
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    try:
        page.get_by_role("button", name="Alleen noodzakelijke cookies").click(timeout=5000)
    except Exception:
        pass
    page.wait_for_timeout(4000)
    stock = {}
    for li in page.locator("li").all():
        try:
            t = li.inner_text(timeout=1000).strip()
        except Exception:
            continue
        s = t.split("\n")[0].strip()
        if s in SIZES and s not in stock:
            stock[s] = "ik wil hem" not in t.lower()
    browser.close()

print(stock)
if not stock:
    sys.exit("Size list not found")
if os.environ.get("TEST") == "yes":
    send(f"Test OK. Stock: {stock}")
if stock.get(SIZE):
    send(f"Size {SIZE} is BACK in stock!\n{URL}")
