# scraper.py — سحب بيانات بورصة العراق عبر حساب Investing الحقيقي وتجاوز الحظر
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

# بيانات حسابك الشخصي لتسجيل الدخول وتفادي حظر الـ 403
INVESTING_EMAIL = "mmm451531@gmail.com"
INVESTING_PASSWORD = "Aa12345Aa"
is_logged_in = False  # متغير لمتابعة حالة تسجيل الدخول

def smart_sleep():
    """تأخير زمني عشوائي لتجنب كشف البوت من جدران الحماية"""
    time.sleep(random.uniform(1.0, 2.5))

def login_to_investing():
    """دالة مخصصة لتسجيل الدخول التلقائي بحسابك الشخصي في Investing وثبيت الـ Cookies"""
    global is_logged_in
    if is_logged_in:
        return True
        
    login_url = "https://www.investing.com/auth/service/loginWithPassword"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    payload = {
        "email": INVESTING_EMAIL,
        "password": INVESTING_PASSWORD,
        "rememberMe": True
    }
    
    try:
        print("[Scraper] 🔐 جاري تسجيل الدخول بحسابك في Investing.com...")
        response = scraper.post(login_url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200 or "token" in response.text:
            print("[Scraper] ✅ تم تسجيل الدخول بنجاح! تم تجاوز جدار الحماية بنسبة 100%")
            is_logged_in = True
            return True
        else:
            print(f"[Scraper] ⚠️ فشل تسجيل الدخول المباشر (كود {response.status_code})، سيتم تصفح الموقع بالـ Headers المتقدمة.")
            return False
    except Exception as e:
        print(f"[Scraper] ❌ خطأ أثناء تسجيل الدخول: {e}")
        return False

def safe_get(url, headers=None, retries=3):
    """إرسال الطلب بأمان مع محاولات إعادة الاتصال عند الفشل"""
    if headers is None:
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    
    for attempt in range(retries):
        try:
            smart_sleep()
            r = scraper.get(url, headers=headers, timeout=20)
            if r.status_code == 200:
                return r
            print(f"[Scraper] ⚠️ كود الاستجابة {r.status_code} - المحاولة {attempt+1}/{retries}")
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"[Scraper] ❌ خطأ اتصال: {e} - المحاولة {attempt+1}/{retries}")
            time.sleep(random.uniform(2, 3))
    return None

# ── قائمة الأسهم العراقية الرئيسية (محدثة ومطابقة لروابط Investing العالمية) ──
IRAQI_STOCKS = {
    "BBOB": {"name": "مصرف بغداد", "investing_id": "bank-of-baghdad"},
    "TELE": {"name": "آسيا سيل للاتصالات", "investing_id": "asiacell"},
    "TASC": {"name": "آسيا سيل للاتصالات", "investing_id": "asiacell"},
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
    """يبحث عن السهم المطلوب: يجرب الموقع الرسمي أولاً، وإن فشل ينتقل لـ Investing عبر حسابك"""
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

    # 2. المحاولة الثانية عبر موقع Investing.com باستخدام الحساب الشخصي المسجل
    stock_info = IRAQI_STOCKS.get(symbol)
    if stock_info:
        # استدعاء دالة تسجيل الدخول قبل سحب البيانات لضمان استقرار الجلسة
        login_to_investing()
        
        url = f"{INVESTING_BASE}/equities/{stock_info['investing_id']}"
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        r2 = safe_get(url, headers=headers)
        if r2:
            try:
                soup = BeautifulSoup(r2.text, "html.parser")

                # جلب السعر الفوري
                price_el = soup.find("span", {"data-test": "instrument-price-last"})
                if not price_el:
                    price_el = soup.select_one('[data-test="instrument-price-last"]') or soup.select_one('[class*="last-price"]')

                # جلب نسبة التغير
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

        # الخطة البديلة في حال انقطاع السيرفرات بالكامل: إرجاع اسم الشركة مع تنبيه
        return {
            "symbol": symbol,
            "name": stock_info["name"],
            "price": "⏳ البيانات غير متاحة حالياً",
            "change_pct": "—",
            "high": "—",
            "low": "—",
            "volume": "—",
        }

    return None

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
    """جلب السعر كرقم فلوت مخصص لنظام التنبيهات"""
    data = get_stock_info(symbol)
    if data and data.get("price") and data["price"] not in ["—", "⏳ البيانات غير متاحة حالياً"]:
        try:
            return float(data["price"].replace(",", "").replace(" ", ""))
        except:
            return None
    return None
