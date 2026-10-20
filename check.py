import os, requests, unicodedata
from playwright.sync_api import sync_playwright

# ===== YOUR ITEMS =====
ITEMS = [
    {"name": "Mango zebra coat", "sizes": ["M"],
     "url": "https://shop.mango.com/be/nl/p/37097133/99/00"},
    {"name": "Mango leather bag", "sizes": ["Één maat"],
     "url": "https://shop.mango.com/be/nl/p/37036007/99/00"},
    {"name": "COS leopard coat", "sizes": ["XS", "S"],
     "url": "https://www.cos.com/en-eu/women/womenswear/coatsjackets/coats/product/leopard-print-wool-blend-funnel-neck-coat-brown-leopard-1366944001"},
    {"name": "COS leather bomber", "sizes": ["XS", "S"],
     "url": "https://www.cos.com/en-eu/women/womenswear/coatsjackets/jackets/funnelneck/product/leather-funnel-neck-bomber-jacket-dark-brown-1354919001"},
]
# ======================

def norm(x):
    return unicodedata.normalize("NFC", x).replace("\xa0", " ").strip().lower()

MANGO_SIZES = [norm(s) for s in ["XXS", "XS", "S", "M", "L", "XL", "XXL"]
               + [str(n) for n in range(30, 50)]]
MANGO_SOLD_WORDS = ["disabled", "unavailable", "nostock", "no-stock", "outofstock", "soldout"]
COS_SIZES = ["XXS", "XXL", "XL", "XS", "S", "M", "L"] + [str(n) for n in range(30, 50)]
COS_SOLD_WORDS = ["coming soon", "notify me", "sold out", "out of stock"]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")

def send(text, url=None):
    topic = os.environ["CHAT_ID"].strip()
    headers = {"Title": "Stock alert"}
    if url:
        headers["Click"] = url
    r = requests.post(f"https://ntfy.sh/{topic}", data=text.encode("utf-8"),
                      headers=headers, timeout=20)
    print("NTFY SAYS:", r.status_code)

def mango_stock(page):
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
        s = norm(text.split("\n")[0])
        if (s in MANGO_SIZES or "maat" in s) and s not in stock:
            stock[s] = not any(w in html.lower() for w in MANGO_SOLD_WORDS)
    return stock

def cos_stock(page):
    page.wait_for_timeout(6000)
    lines = [l.strip() for l in page.inner_text("body").split("\n") if l.strip()]
    start = next((i for i, l in enumerate(lines) if l.lower() == "select size"), None)
    if start is None:
        print("COS: 'Select Size' not found. First lines:", lines[:30])
        return {}
    stock = {}
    for i in range(start + 1, min(start + 40, len(lines))):
        low = lines[i].lower()
        if low in ("add to bag", "find in store"):
            break
        for s in COS_SIZES:
            if lines[i].upper().startswith(s):
                rest = low[len(s):].strip()
                if rest:
                    sold = any(rest.startswith(w) for w in COS_SOLD_WORDS)
                else:
                    nxt = lines[i + 1].lower() if i + 1 < len(lines) else ""
                    sold = any(nxt.startswith(w) for w in COS_SOLD_WORDS)
                stock[s] = not sold
                break
    return stock

report = []
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
    page = browser.new_page(user_agent=UA, viewport={"width": 1280, "height": 900})
    for item in ITEMS:
        try:
            page.goto(item["url"], wait_until="domcontentloaded", timeout=60000)
            stock = cos_stock(page) if "cos.com" in item["url"] else mango_stock(page)
        except Exception as e:
            print(item["name"], "failed:", e)
            report.append(f"{item['name']}: ERROR")
            continue
        print(item["name"], "STOCK:", stock)
        report.append(f"{item['name']}: {stock}")
        found = [s for s in item["sizes"]
                 if any(norm(k) == norm(s) and v for k, v in stock.items())]
        if found:
            send(f"{item['name']} is AVAILABLE in {', '.join(found)}! Tap to open.", item["url"])
    browser.close()

if os.environ.get("TEST") == "yes":
    send("Test OK.\n" + "\n".join(report))
