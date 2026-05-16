# scraper.py — سحب البيانات من موقع البورصة العراقية مع الحماية من الحظر

import requests
from bs4 import BeautifulSoup
import random
import time
import re
import urllib3

# تجاهل تحذيرات SSL القديم للموقع
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "http://isx-iq.net/isxportal/portal"


# ── قائمة User-Agents حقيقية ──
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Referer": "http://www.isx-iq.net/isxportal/portal/homePage.html",
    }

def smart_sleep(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def safe_get(url, retries=3):
    for attempt in range(retries):
        try:
            smart_sleep(1, 3)
            r = requests.get(url, headers=get_headers(), timeout=15, verify=False, allow_redirects=True)
            if r.status_code == 200:
                return r
            elif r.status_code == 403:
                print(f"[Scraper] ⚠️ محظور (403) - المحاولة {attempt+1}/{retries}")
                time.sleep(random.uniform(10, 20))
            else:
                time.sleep(random.uniform(3, 6))
        except requests.exceptions.ConnectionError:
            print(f"[Scraper] ❌ خطأ في الاتصال - المحاولة {attempt+1}/{retries}")
            time.sleep(random.uniform(5, 10))
        except requests.exceptions.Timeout:
            print(f"[Scraper] ❌ انتهت المهلة - المحاولة {attempt+1}/{retries}")
            time.sleep(random.uniform(3, 6))
        except Exception as e:
            print(f"[Scraper] ❌ خطأ: {e}")
            time.sleep(random.uniform(2, 4))
    return None

def get_market_summary():
    r = safe_get(f"{BASE_URL}/homePage.html")
    if not r:
        return None
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]
        data = {}
        for i, line in enumerate(lines):
            def nxt(n=1): return lines[i+n] if i+n < len(lines) else ""
            if "Main Index"    in line: data["index"]      = nxt()
            if "Change %"      in line: data["change_pct"] = nxt()
            if "Change"        in line and "%" not in line and "change" not in data:
                data["change"] = nxt()
            if "Value Traded"  in line: data["value"]      = nxt()
            if "Trades"        in line and "Value" not in line: data["trades"] = nxt()
            if "Symbols Up"    in line: data["up"]         = nxt()
            if "Symbols Down"  in line: data["down"]       = nxt()
            if "Flat"          in line: data["flat"]       = nxt()
            if "Latest Update" in line: data["date"]       = nxt()
        return data if len(data) >= 4 else None
    except Exception as e:
        print(f"[Scraper] market_summary error: {e}")
        return None

def get_top_stocks():
    r = safe_get(f"{BASE_URL}/homePage.html")
    if not r:
        return {"up": [], "down": []}
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        up_stocks, down_stocks = [], []
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cols = [td.get_text(strip=True) for td in row.find_all("td")]
                if len(cols) >= 3 and re.match(r"^[A-Z]{2,6}$", cols[0]):
                    try:
                        change = float(cols[-1].replace("%", "").replace(",", ""))
                        if change > 0:
                            up_stocks.append({"symbol": cols[0], "change": round(change, 2)})
                        elif change < 0:
                            down_stocks.append({"symbol": cols[0], "change": round(change, 2)})
                    except:
                        pass
        return {
            "up":   sorted(up_stocks,   key=lambda x: x["change"], reverse=True)[:5],
            "down": sorted(down_stocks, key=lambda x: x["change"])[:5],
        }
    except Exception as e:
        print(f"[Scraper] top_stocks error: {e}")
        return {"up": [], "down": []}

def get_latest_news():
    r = safe_get(f"{BASE_URL}/storyList.html?activeTab=0")
    if not r:
        return []
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        news, seen = [], set()
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "storyDetails" not in href:
                continue
            story_id = re.search(r"storyId=(\d+)", href)
            title = link.get_text(strip=True)
            if story_id and title and len(title) > 5 and story_id.group(1) not in seen:
                seen.add(story_id.group(1))
                news.append({
                    "id":    story_id.group(1),
                    "title": title,
                    "url":   f"http://www.isx-iq.net{href}" if href.startswith("/") else href,
                })
        return news[:10]
    except Exception as e:
        print(f"[Scraper] news error: {e}")
        return []

def get_stock_info(symbol):
    symbol = symbol.upper().strip()
    r = safe_get(f"{BASE_URL}/companyProfileByInvestor.html?companyCode={symbol}")
    if not r or len(r.text) < 500:
        return None
    try:
        soup = BeautifulSoup(r.text, "html.parser")
        lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]
        data = {"symbol": symbol}
        for i, line in enumerate(lines):
            def nxt(): return lines[i+1] if i+1 < len(lines) else ""
            if "Company Name" in line: data["name"]       = nxt()
            if "Last Price"   in line: data["price"]      = nxt()
            if "Change %"     in line: data["change_pct"] = nxt()
            if line == "High":         data["high"]       = nxt()
            if line == "Low":          data["low"]        = nxt()
            if "Volume"       in line: data["volume"]     = nxt()
        return data if len(data) > 2 else None
    except Exception as e:
        print(f"[Scraper] stock_info error: {e}")
        return None

def get_stock_price_for_alert(symbol):
    """يجلب السعر الحالي فقط لفحص التنبيهات"""
    data = get_stock_info(symbol)
    if data and data.get("price"):
        try:
            return float(data["price"].replace(",", ""))
        except:
            return None
    return None
