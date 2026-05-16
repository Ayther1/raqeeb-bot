# scraper.py — سحب البيانات من Investing.com بتجاوز الحجب

import cloudscraper
from bs4 import BeautifulSoup
import re
import time
import random

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

ISX_BASE = "http://isx-iq.net/isxportal/portal"
INVESTING_BASE = "https://www.investing.com"

def smart_sleep():
    time.sleep(random.uniform(1.5, 3.5))

def safe_get(url, retries=3):
    for attempt in range(retries):
        try:
            smart_sleep()
            r = scraper.get(url, timeout=20)
            if r.status_code == 200:
                return r
            print(f"[Scraper] ⚠️ {r.status_code} - المحاولة {attempt+1}/{retries}")
            time.sleep(random.uniform(5, 10))
        except Exception as e:
            print(f"[Scraper] ❌ خطأ: {e} - المحاولة {attempt+1}/{retries}")
            time.sleep(random.uniform(3, 6))
    return None

# ── قائمة الأسهم العراقية الرئيسية ──
IRAQI_STOCKS = {
    "BBOB": {"name": "مصرف بغداد", "investing_id": "iq/baghdad-bank"},
    "TASC": {"name": "شركة الاتصالات العراقية", "investing_id": "iq/iraqi-telecommunications"},
    "BCOI": {"name": "مصرف الخليج التجاري", "investing_id": "iq/commercial-bank-of-iraq"},
    "BUND": {"name": "مصرف الاتحاد", "investing_id": "iq/union-bank-of-iraq"},
    "BNOI": {"name": "مصرف الشمال", "investing_id": "iq/north-bank"},
    "IBSD": {"name": "مصرف الاستثمار العراقي", "investing_id": "iq/investment-bank-of-iraq"},
    "HLIS": {"name": "شركة الهلال للصناعة", "investing_id": "iq/hilal-industries"},
    "TELE": {"name": "شركة آسيا سيل للاتصالات", "investing_id": "iq/asiacell"},
    "AAHP": {"name": "شركة آسيا للفنادق", "investing_id": "iq/asia-hotel"},
    "IICL": {"name": "شركة التأمين العراقية", "investing_id": "iq/iraqi-insurance"},
}

def get_market_summary():
    """يجلب ملخص السوق من ISX أو يرجع بيانات افتراضية"""
    r = safe_get(f"{ISX_BASE}/homePage.html")
    if r:
        try:
            soup = BeautifulSoup(r.text, "html.parser")
            lines = [l.strip() for l in soup.get_text().split("\n") if l.strip()]
            data = {}
            for i, line in enumerate(lines):
                def nxt(n=1): return lines[i+n] if i+n < len(lines) else ""
                if "Main Index"   in line: data["index"]      = nxt()
                if "Change %"     in line: data["change_pct"] = nxt()
                if "Value Traded" in line: data["value"]      = nxt()
                if "Trades"       in line and "Value" not in line: data["trades"] = nxt()
                if "Symbols Up"   in line: data["up"]         = nxt()
                if "Symbols Down" in line: data["down"]       = nxt()
                if "Flat"         in line: data["flat"]       = nxt()
            if len(data) >= 4:
                return data
        except Exception as e:
            print(f"[Scraper] market_summary error: {e}")

    # بيانات احتياطية لو الموقع محجوب
    return {
        "index": "—",
        "change_pct": "—",
        "value": "—",
        "trades": "—",
        "up": "—",
        "down": "—",
        "flat": "—",
    }

def get_stock_info(symbol):
    """يبحث عن سهم - يجرب ISX أولاً ثم Investing"""
    symbol = symbol.upper().strip()

    # جرب ISX أولاً
    r = safe_get(f"{ISX_BASE}/companyProfileByInvestor.html?companyCode={symbol}")
    if r and len(r.text) > 500:
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
            if len(data) > 2:
                return data
        except Exception as e:
            print(f"[Scraper] ISX stock error: {e}")

    # جرب Investing.com
    stock_info = IRAQI_STOCKS.get(symbol)
    if stock_info:
        url = f"{INVESTING_BASE}/equities/{stock_info['investing_id']}"
        r2 = safe_get(url)
        if r2:
            try:
                soup = BeautifulSoup(r2.text, "html.parser")

                # السعر
                price_el = soup.find("span", {"data-test": "instrument-price-last"})
                if not price_el:
                    price_el = soup.select_one('[class*="last-price"]') or soup.select_one('[class*="price"]')

                # التغيير
                change_el = soup.find("span", {"data-test": "instrument-price-change-percent"})

                price = price_el.get_text(strip=True) if price_el else "—"
                change = change_el.get_text(strip=True) if change_el else "—"

                return {
                    "symbol": symbol,
                    "name": stock_info["name"],
                    "price": price,
                    "change_pct": change,
                    "high": "—",
                    "low": "—",
                    "volume": "—",
                }
            except Exception as e:
                print(f"[Scraper] Investing stock error: {e}")

        # لو Investing ما اشتغل، ارجع بيانات أساسية
        return {
            "symbol": symbol,
            "name": stock_info["name"],
            "price": "⏳ البيانات غير متاحة حالياً",
            "change_pct": "—",
            "high": "—",
            "low": "—",
            "volume": "—",
        }

    return None  # سهم غير موجود بالقاموس

def get_top_stocks():
    """يجلب أبرز الأسهم"""
    r = safe_get(f"{ISX_BASE}/homePage.html")
    if r:
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
            if up_stocks or down_stocks:
                return {
                    "up":   sorted(up_stocks,   key=lambda x: x["change"], reverse=True)[:5],
                    "down": sorted(down_stocks, key=lambda x: x["change"])[:5],
                }
        except Exception as e:
            print(f"[Scraper] top_stocks error: {e}")

    # بيانات احتياطية
    return {"up": [], "down": []}

def get_latest_news():
    """يجلب آخر الأخبار"""
    r = safe_get(f"{ISX_BASE}/storyList.html?activeTab=0")
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
                    "url":   f"http://isx-iq.net{href}" if href.startswith("/") else href,
                })
        return news[:10]
    except Exception as e:
        print(f"[Scraper] news error: {e}")
        return []

def get_stock_price_for_alert(symbol):
    """يجلب السعر الحالي فقط لفحص التنبيهات"""
    data = get_stock_info(symbol)
    if data and data.get("price") and data["price"] not in ["—", "⏳ البيانات غير متاحة حالياً"]:
        try:
            return float(data["price"].replace(",", "").replace(" ", ""))
        except:
            return None
    return None
