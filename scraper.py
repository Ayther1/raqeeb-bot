import cloudscraper
from bs4 import BeautifulSoup
import random, time, re, json

ISX_URL  = "http://www.isx-iq.net/isxportal/portal"
NEWS_URL = "https://www.alsumaria.tv"

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

def _sleep():
    time.sleep(random.uniform(1.5, 3.5))

def _get(url, retries=3):
    for i in range(retries):
        try:
            _sleep()
            r = scraper.get(url, timeout=15)
            if r.status_code == 200:
                return r
            time.sleep(random.uniform(5, 10))
        except Exception as e:
            print(f"[Scraper] error {i+1}: {e}")
            time.sleep(random.uniform(3, 6))
    return None

# ── ملخص السوق من ISX ──
def get_market_summary():
    r = _get(f"{ISX_URL}/homePage.html")
    if not r:
        return None
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]
        d = {}
        for i, line in enumerate(lines):
            n = lambda k=1: lines[i+k] if i+k < len(lines) else "—"
            if "Main Index"    in line: d["index"]      = n()
            if "Change %"      in line: d["change_pct"] = n()
            if "Change"        in line and "%" not in line and "index" in d and "change" not in d:
                d["change"] = n()
            if "Value Traded"  in line: d["value"]   = n()
            if "Trades"        in line and "Value" not in line: d["trades"] = n()
            if "Symbols Up"    in line: d["up"]      = n()
            if "Symbols Down"  in line: d["down"]    = n()
            if "Flat"          in line: d["flat"]    = n()
            if "Latest Update" in line: d["date"]    = n()
        return d if len(d) >= 4 else None
    except Exception as e:
        print(f"[Scraper] market error: {e}")
        return None

# ── أبرز الأسهم من ISX ──
def get_top_stocks():
    r = _get(f"{ISX_URL}/homePage.html")
    if not r:
        return {"up": [], "down": []}
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        up, dn = [], []
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cols = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cols) >= 3 and re.match(r"^[A-Z]{2,6}$", cols[0]):
                    try:
                        chg = float(cols[-1].replace("%","").replace(",",""))
                        if chg > 0: up.append({"symbol": cols[0], "change": round(chg,2)})
                        elif chg < 0: dn.append({"symbol": cols[0], "change": round(chg,2)})
                    except: pass
        return {
            "up":   sorted(up, key=lambda x: x["change"], reverse=True)[:5],
            "down": sorted(dn, key=lambda x: x["change"])[:5],
        }
    except: return {"up": [], "down": []}

# ── معلومات سهم من Investing.com ──
def get_stock_info(symbol):
    symbol = symbol.upper().strip()
    # أولاً جرب ISX
    isx_data = _get_from_isx(symbol)
    if isx_data:
        return isx_data
    # ثانياً Investing.com
    return _get_from_investing(symbol)

def _get_from_isx(symbol):
    r = _get(f"{ISX_URL}/companyProfileByInvestor.html?companyCode={symbol}")
    if not r or len(r.text) < 500:
        return None
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]
        d = {"symbol": symbol, "source": "ISX"}
        for i, line in enumerate(lines):
            n = lambda: lines[i+1] if i+1 < len(lines) else "—"
            if "Company Name" in line: d["name"]       = n()
            if "Last Price"   in line: d["price"]      = n()
            if "Change %"     in line: d["change_pct"] = n()
            if line == "High":         d["high"]       = n()
            if line == "Low":          d["low"]        = n()
            if "Volume"       in line: d["volume"]     = n()
        return d if len(d) > 3 else None
    except: return None

def _get_from_investing(symbol):
    try:
        url = f"https://www.investing.com/search/?q={symbol}"
        r = _get(url)
        if not r:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        # ابحث عن أول نتيجة
        results = soup.select(".js-inner-all-results-quote-item")
        if not results:
            return None
        first = results[0]
        name = first.select_one(".second")
        href = first.get("href","")
        if not href:
            return None
        # جلب صفحة السهم
        r2 = _get(f"https://www.investing.com{href}")
        if not r2:
            return None
        soup2 = BeautifulSoup(r2.text, "html.parser")
        price_el = soup2.select_one('[data-test="instrument-price-last"]')
        change_el = soup2.select_one('[data-test="instrument-price-change-percent"]')
        high_el   = soup2.select_one('[data-test="high"]')
        low_el    = soup2.select_one('[data-test="low"]')
        vol_el    = soup2.select_one('[data-test="volume"]')
        return {
            "symbol":     symbol,
            "name":       name.get_text(strip=True) if name else symbol,
            "price":      price_el.get_text(strip=True)  if price_el  else "—",
            "change_pct": change_el.get_text(strip=True) if change_el else "—",
            "high":       high_el.get_text(strip=True)   if high_el   else "—",
            "low":        low_el.get_text(strip=True)    if low_el    else "—",
            "volume":     vol_el.get_text(strip=True)    if vol_el    else "—",
            "source":     "Investing.com",
        }
    except Exception as e:
        print(f"[Scraper] investing error: {e}")
        return None

# ── أخبار البورصة العراقية ──
def get_isx_news():
    news = []
    # من ISX
    r = _get(f"{ISX_URL}/storyList.html?activeTab=0")
    if r:
        try:
            soup = BeautifulSoup(r.text, "html.parser")
            seen = set()
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "storyDetails" not in href: continue
                sid = re.search(r"storyId=(\d+)", href)
                title = link.get_text(strip=True)
                if sid and title and len(title) > 5 and sid.group(1) not in seen:
                    seen.add(sid.group(1))
                    news.append({
                        "id":    f"isx_{sid.group(1)}",
                        "title": title,
                        "source": "ISX",
                    })
        except: pass
    # من السومرية
    r2 = _get("https://www.alsumaria.tv/economy/stock-exchange")
    if r2:
        try:
            soup2 = BeautifulSoup(r2.text, "html.parser")
            for item in soup2.select("article h2 a, .post-title a")[:5]:
                title = item.get_text(strip=True)
                href  = item.get("href","")
                if title and len(title) > 10:
                    news.append({
                        "id":    f"sum_{abs(hash(title))}",
                        "title": title,
                        "source": "السومرية",
                    })
        except: pass
    return news[:10]

# ── أخبار شركة معينة ──
def get_company_news(company):
    results = []
    # من ISX
    r = _get(f"{ISX_URL}/storyList.html?activeTab=0")
    if r:
        try:
            soup = BeautifulSoup(r.text, "html.parser")
            for link in soup.find_all("a", href=True):
                if "storyDetails" not in link["href"]: continue
                title = link.get_text(strip=True)
                if company.upper() in title.upper() or company in title:
                    sid = re.search(r"storyId=(\d+)", link["href"])
                    if sid:
                        results.append({
                            "id":    f"isx_{sid.group(1)}",
                            "title": title,
                            "source": "ISX",
                        })
        except: pass
    # من السومرية
    r2 = _get(f"https://www.alsumaria.tv/search?q={company}")
    if r2:
        try:
            soup2 = BeautifulSoup(r2.text, "html.parser")
            for item in soup2.select("article h2 a, .post-title a")[:3]:
                title = item.get_text(strip=True)
                if title and len(title) > 10:
                    results.append({
                        "id":    f"sum_{abs(hash(title))}",
                        "title": title,
                        "source": "السومرية",
                    })
        except: pass
    return results[:5]

# ── سعر سهم للتنبيهات ──
def get_price(symbol):
    d = _get_from_isx(symbol.upper())
    if d and d.get("price"):
        try: return float(d["price"].replace(",",""))
        except: pass
    return None
