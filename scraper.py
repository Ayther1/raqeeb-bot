# scraper.py — سحب بيانات بورصة العراق وتجنب الحظر والـ 404
import cloudscraper
from bs4 import BeautifulSoup
import re
import time
import random

# إنشاء السكرابر متخفي بصيغة متصفح كروم حقيقي
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

ISX_BASE = "http://isx-iq.net/isxportal/portal"
INVESTING_BASE = "https://www.investing.com"

def smart_sleep():
    """تأخير زمني عشوائي لتجنب كشف البوت من جدران الحماية"""
    time.sleep(random.uniform(1.5, 3.5))

def safe_get(url, headers=None, retries=3):
    """إرسال الطلب بأمان مع محاولات إعادة الاتصال عند الفشل"""
    if headers is None:
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        }
    
    for attempt in range(retries):
        try:
            smart_sleep()
            r = scraper.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                return r
            print(f"[Scraper] ⚠️ كود الاستجابة {r.status_code} - المحاولة {attempt+1}/{retries}")
            time.sleep(random.uniform(4, 8))
        except Exception as e:
            print(f"[Scraper] ❌ خطأ اتصال: {e} - المحاولة {attempt+1}/{retries}")
            time.sleep(random.uniform(3, 5))
    return None

# ── قائمة الأسهم العراقية الرئيسية (محدثة ومطابقة لروابط Investing العالمية) ──
IRAQI_STOCKS = {
    "BBOB": {"name": "مصرف بغداد", "investing_id": "bank-of-baghdad"},
    "TELE": {"name": "آسيا سيل للاتصالات", "investing_id": "asiacell"},
    "TASC": {"name": "آسيا سيل للاتصالات", "investing_id": "asiacell"},  # لدعم الرمزين
    "BNOI": {"name": "المصرف الأهلي العراقي", "investing_id": "national-bank-of-iraq"},
    "BCOI": {"name": "مصرف الخليج التجاري", "investing_id": "commercial-bank-of-iraq"},
    "BUND": {"name": "مصرف الاتحاد العراقي", "investing_id": "union-bank-of-iraq"},
    "HBAY": {"name": "مصرف المنصور للاستثمار", "investing_id": "al-mansour-bank"},
    "BIME": {"name": "مصرف الشرق الأوسط العراقي", "investing_id": "iraq-middle-east-investment-bank"},
    "HLIS": {"name": "شركة الهلال للصناعة", "investing_id": "hilal-industries"},
    "AAHP": {"name": "شركة آسيا للفنادق", "investing_id": "asia-hotel"},
    "IICL": {"name": "شركة التأمين العراقية", "investing_id": "iraqi-insurance"},
}

def get_market_summary():
    """يجلب ملخص البورصة العام من ISX أو يرجع بيانات احتياطية"""
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

    return {
        "index": "—", "change_pct": "—", "value": "—", "trades": "—", "up": "—", "down": "—", "flat": "—",
    }

def get_stock_info(symbol):
    """يبحث عن السهم المطلوب: يجرب الموقع الرسمي أولاً، وإن فشل ينتقل لـ Investing"""
    symbol = symbol.upper().strip()

    # 1. المحاولة الأولى من موقع سوق العراق للأوراق المالية المباشر
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
            print(f"[Scraper] ISX stock error for {symbol}: {e}")

    # 2. المحاولة الثانية (الخطة البديلة المستقرة) عبر موقع Investing.com
    stock_info = IRAQI_STOCKS.get(symbol)
    if stock_info:
        url = f"{INVESTING_BASE}/equities/{stock_info['investing_id']}"
        
        # فرض لغة متصفح عالمية لمنع تحويل الموقع للنسخة العربية المعطلة (تجنب 404)
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        r2 = safe_get(url, headers=headers)
        if r2:
            try:
                soup = BeautifulSoup(r2.text, "html.parser")

                # جلب السعر الفوري بناءً على المعرفات المستقرة للموقع
                price_el = soup.find("span", {"data-test": "instrument-price-last"})
                if not price_el:
                    price_el = soup.select_one('[data-test="instrument-price-last"]') or soup.select_one('[class*="last-price"]')

                # جلب نسبة التغير اليومي
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
                print(f"[Scraper] Investing parse error for {symbol}: {e}")

        # إذا تعطل كلا الموقعين، يرجع البوت اسم الشركة من القاموس مع رسالة تنبيه ذكية بدلاً من الانهيار
        return {
            "symbol": symbol,
            "name": stock_info["name"],
            "price": "⏳ البيانات غير متاحة حالياً",
            "change_pct": "—",
            "high": "—",
            "low": "—",
            "volume": "—",
        }

    return None  # السهم غير معرف كلياً في قاموس البوت

def get_top_stocks():
    """يجلب أبرز الأسهم الرابحة والخاسرة في الجلسة"""
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

    return {"up": [], "down": []}

def get_latest_news():
    """يجلب شريط آخر الأخبار والتعاميم من البورصة"""
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
    """جلب السعر كرقم فلوت (Float) مخصص لنظام التنبيهات والأسعار المحددة"""
    data = get_stock_info(symbol)
    if data and data.get("price") and data["price"] not in ["—", "⏳ البيانات غير متاحة حالياً"]:
        try:
            return float(data["price"].replace(",", "").replace(" ", ""))
        except:
            return None
    return None
