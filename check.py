import os, sys, requests
from playwright.sync_api import sync_playwright

URL = "https://shop.mango.com/be/nl/p/37097133/99/00"
SIZE = "M"
SIZES = ["XXS", "XS", "S", "M", "L", "XL", "XXL"]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
SOLD_OUT_WORDS = ["disabled", "unavailable", "nostock", "no-stock", "outofstock", "soldout"]

def send(text):
    topic = os.environ["CHAT_ID"].strip()
    r = requests.post(f"https://ntfy.sh/{topic}", data=text.encode("utf-8"),
                      headers={"Title": "Mango alert", "Click": URL}, timeout=20)
    print("NTFY SAYS:", r.status_code, r.text[:200])

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
    page = browser.new_page(locale="nl-BE", user_agent=UA,
                            viewport={"width": 1280, "height": 900})
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
    stock = {}
    for li in page.locator("li").all():
        try:
            text = li.inner_text(timeout=1000).strip()
            html = li.inner_html(timeout=1000)
        except Exception:
            continue
        s = text.split("\n")[0].strip()
        if s in SIZES and s not in stock:
            stock[s] = not any(w in html.lower() for w in SOLD_OUT_WORDS)
            print("SIZE", s, "HTML:", html[:300])
    browser.close()

print("STOCK:", stock)
if not stock:
    sys.exit("Size list not found")
if os.environ.get("TEST") == "yes":
    send(f"Test OK. Stock: {stock}")
if stock.get(SIZE):
    send(f"Size {SIZE} is BACK in stock! Tap to open.")
