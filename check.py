import os, sys, requests
from playwright.sync_api import sync_playwright

# ===== YOUR ITEMS: add one line per item =====
ITEMS = [
    {"name": "Zebra coat", "size": "M", "url": "https://shop.mango.com/be/nl/p/37097133/99/00"},
    {"name": "Leather shopper bag", "size": "Één maat", "url": "https://shop.mango.com/be/nl/p/37036007/99/00"},
]
# =============================================

SIZES = ["XXS", "XS", "S", "M", "L", "XL", "XXL", "Één maat"] + [str(n) for n in range(30, 50)]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
SOLD_OUT_WORDS = ["disabled", "unavailable", "nostock", "no-stock", "outofstock", "soldout"]

def send(text, url=None):
    topic = os.environ["CHAT_ID"].strip()
    headers = {"Title": "Mango alert"}
    if url:
        headers["Click"] = url
    r = requests.post(f"https://ntfy.sh/{topic}", data=text.encode("utf-8"),
                      headers=headers, timeout=20)
    print("NTFY SAYS:", r.status_code)

def get_stock(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.get_by_role("button", name="Alleen noodzakelijke cookies").click(timeout=5000)
    except Exception:
        pass
    page.wait_for_timeout(6000)
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
    return stock

report = []
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
    page = browser.new_page(locale="nl-BE", user_agent=UA,
                            viewport={"width": 1280, "height": 900})
    for item in ITEMS:
        if not item["url"].startswith("http"):
            continue
        try:
            stock = get_stock(page, item["url"])
        except Exception as e:
            print(item["name"], "failed:", e)
            continue
        print(item["name"], "STOCK:", stock)
        report.append(f"{item['name']}: {stock}")
        if stock.get(item["size"]):
            send(f"{item['name']} is BACK in stock ({item['size']})! Tap to open.", item["url"])
    browser.close()

if os.environ.get("TEST") == "yes":
    send("Test OK.\n" + "\n".join(report))
