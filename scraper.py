import cloudscraper
from bs4 import BeautifulSoup
import random, time, re
from datetime import datetime

ISX = "http://www.isx-iq.net/isxportal/portal"

_scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

def _get(url, retries=3):
    for i in range(retries):
        try:
            time.sleep(random.uniform(1.5, 3.0))
            r = _scraper.get(url, timeout=15)
            if r.status_code == 200:
                return r
            time.sleep(random.uniform(5, 10))
        except Exception as e:
            print(f"[Scraper] {i+1}/{retries} error: {e}")
            time.sleep(random.uniform(3, 6))
    return None

def get_market_summary():
    r = _get(f"{ISX}/homePage.html")
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
            if "Value Traded"  in line: d["value"]      = n()
            if "Trades"        in line and "Value" not in line: d["trades"] = n()
            if "Symbols Up"    in line: d["up"]         = n()
            if "Symbols Down"  in line: d["down"]       = n()
            if "Flat"          in line: d["flat"]        = n()
            if "Latest Update" in line: d["date"]       = n()
        return d if len(d) >= 4 else None
    except Exception as e:
        print(f"[Scraper] market error: {e}")
        return None

def get_top_stocks():
    r = _get(f"{ISX}/homePage.html")
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
                        if chg > 0:   up.append({"symbol": cols[0], "change": round(chg,2)})
                        elif chg < 0: dn.append({"symbol": cols[0], "change": round(chg,2)})
                    except: pass
        return {
            "up":   sorted(up, key=lambda x: x["change"], reverse=True)[:5],
            "down": sorted(dn, key=lambda x: x["change"])[:5],
        }
    except:
        return {"up": [], "down": []}

def get_stock_info(symbol):
    """يجلب معلومات سهم — يرجع أحدث بيانات متاحة من ISX"""
    symbol = symbol.upper().strip()
    r = _get(f"{ISX}/companyProfileByInvestor.html?companyCode={symbol}")
    if not r or len(r.text) < 500:
        return None
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]
        d = {"symbol": symbol}
        for i, line in enumerate(lines):
            n = lambda: lines[i+1] if i+1 < len(lines) else "—"
            if "Company Name"  in line: d["name"]       = n()
            if "Last Price"    in line: d["price"]      = n()
            if "Change %"      in line: d["change_pct"] = n()
            if "Change"        in line and "%" not in line: d["change"] = n()
            if line == "High":          d["high"]       = n()
            if line == "Low":           d["low"]        = n()
            if "Volume"        in line: d["volume"]     = n()
            if "Latest Update" in line: d["date"]       = n()
        return d if len(d) > 3 else None
    except Exception as e:
        print(f"[Scraper] stock error: {e}")
        return None

def get_isx_news():
    news = []
    r = _get(f"{ISX}/storyList.html?activeTab=0")
    if not r:
        return []
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        seen = set()
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "storyDetails" not in href:
                continue
            sid = re.search(r"storyId=(\d+)", href)
            title = link.get_text(strip=True)
            if sid and title and len(title) > 5 and sid.group(1) not in seen:
                seen.add(sid.group(1))
                news.append({"id": f"isx_{sid.group(1)}", "title": title})
    except Exception as e:
        print(f"[Scraper] news error: {e}")
    return news[:10]

def get_company_news(company):
    all_news = get_isx_news()
    return [n for n in all_news if company.upper() in n["title"].upper()][:5]

def get_price(symbol):
    d = get_stock_info(symbol.upper())
    if d and d.get("price"):
        try:
            return float(d["price"].replace(",",""))
        except: pass
    return None