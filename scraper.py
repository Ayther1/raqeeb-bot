"""
خدمة جلب بيانات السوق من المصادر الرسمية
المصادر: ISX, RS.iq, ISC
"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime
from bs4 import BeautifulSoup

# رموز الشركات العراقية الكاملة
IRAQI_STOCKS = {
    # القطاع المصرفي
    "BBOB": "مصرف بغداد",
    "BNOI": "مصرف الاقتصاد الوطني",
    "BSUC": "مصرف سومر التجاري",
    "BTRI": "مصرف الخليج التجاري",
    "BGUC": "مصرف الخليج",
    "BMNS": "مصرف المنصور",
    "BNOK": "مصرف بابل",
    "BSRQ": "مصرف الشرق الأوسط العراقي للاستثمار",
    "BDSI": "مصرف دار السلام للاستثمار",
    "BKUI": "مصرف الكردي الاسلامي",
    "BIRQ": "مصرف بيروت والعراق",
    "BKNH": "مصرف الاتحاد العراقي",
    "BNSI": "مصرف بغداد الاسلامي",
    "BUND": "المصرف الدولي العراقي",
    "BWAK": "مصرف الوارث",
    "BKUR": "مصرف كردستان الدولي",
    "BMFI": "مصرف الموصل للتنمية والاستثمار",
    "BNBK": "المصرف الأهلي العراقي",
    "BQUI": "مصرف القبس",
    "BTKH": "مصرف التجارة الدولية",
    "BZAI": "مصرف الزوراء",
    "BNOO": "مصرف النور الاسلامي",
    "BIMI": "مصرف المتحد",
    "BRCB": "مصرف الرشيد",
    "BSFB": "مصرف الرافدين",
    "BCRI": "مصرف كريمي",
    "BDOI": "مصرف دجلة والفرات",
    "BKBK": "مصرف الكوفة الاسلامي",
    "BMUI": "مصرف التمويل المتناهي الصغر",
    "BSOB": "بنك الاقتراض",
    "BACI": "المصرف العراقي التجاري",
    "BALI": "مصرف الأهالي",
    "BEGI": "مصرف الايمان",
    "BKRI": "مصرف كردستان الاسلامي",
    "BDNI": "مصرف النخبة",
    # قطاع الاتصالات
    "TZNI": "آسياسيل",
    "AMAN": "المدى للاتصالات",
    "TCOI": "الشركة التجارية لتشغيل المنافذ",
    # قطاع الصناعة
    "IICL": "الشركة الصناعية العراقية",
    "IIDX": "الشركة العراقية للصناعات الدوائية",
    "IISH": "الشركة العراقية للاسمدة الجنوبية",
    "IOBK": "شركة الشرق الاوسط لانتاج الورق",
    "IOBI": "الشركة العراقية للبناء والاسكان",
    "IOKB": "شركة خلوص",
    "INCP": "الشركة الوطنية للاسمنت",
    "IBSD": "شركة الوحدة العامة",
    "IIMI": "الشركة العراقية لصناعة الادوية",
    "IKLC": "شركة الكرخ للصناعات",
    "IMPI": "شركة مصنع الاحذية",
    # قطاع الخدمات
    "SAIR": "شركة الطيران العراقية",
    "SAIB": "شركة التأمين الوطنية",
    "SAII": "شركة التأمين الاهلية",
    "SAIP": "شركة التأمين العراقية",
    "SAIS": "شركة التأمين الإسلامية",
    "SIIC": "شركة التأمين الاسلامية",
    "SIIB": "شركة التأمين الاسلامية للبنية",
    # قطاع الزراعة والغذاء
    "AFLI": "شركة الغذاء العراقي",
    "AIQI": "الشركة العراقية للزراعة والتسويق",
    "AIPI": "شركة المنتجات الغذائية",
    # قطاع الفنادق والسياحة
    "HBAY": "فندق بابل",
    "HISC": "فندق إيشتار",
    "HRSS": "فندق الرشيد",
    "HSAF": "فندق المنصور ميلية",
    # قطاع الاستثمار
    "NKLI": "شركة كليو للاستثمار",
    "NIIC": "شركة الاستثمار العراقية",
    "NAOI": "شركة الأوراق المالية الوطنية",
    # قطاع العقارات
    "RPKG": "شركة بغداد للمجمعات السكنية",
    "RRDI": "شركة التطوير العقاري",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

async def fetch_url(url: str, timeout: int = 15) -> str | None:
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout), ssl=False) as resp:
                if resp.status == 200:
                    return await resp.text(errors="ignore")
    except Exception as e:
        print(f"[fetch_url] Error {url}: {e}")
    return None

async def get_stock_from_isx(symbol: str) -> dict | None:
    """جلب بيانات السهم من ISX الرسمي"""
    url = f"https://www.isx-iq.net/isxportal/portal/companyprofilecontainer.html?companyCode={symbol}"
    html = await fetch_url(url)
    if not html:
        return None
    try:
        soup = BeautifulSoup(html, "html.parser")
        data = {"symbol": symbol, "source": "ISX", "timestamp": datetime.now().strftime("%H:%M %Y-%m-%d")}

        # استخراج السعر
        price_el = soup.find("span", {"id": re.compile(r".*price.*", re.I)})
        if not price_el:
            price_el = soup.find(class_=re.compile(r"price|lastPrice", re.I))
        if price_el:
            data["price"] = price_el.get_text(strip=True)

        # استخراج التغير
        change_el = soup.find(class_=re.compile(r"change|percent", re.I))
        if change_el:
            data["change"] = change_el.get_text(strip=True)

        # اسم الشركة
        name_el = soup.find("h1") or soup.find("h2")
        if name_el:
            data["company"] = name_el.get_text(strip=True)
        else:
            data["company"] = IRAQI_STOCKS.get(symbol, symbol)

        return data
    except Exception as e:
        print(f"[isx] Parse error: {e}")
        return None

async def get_stock_from_rs(symbol: str) -> dict | None:
    """جلب بيانات السهم من RS.iq"""
    url = f"https://www.rs.iq/securities/{symbol}"
    html = await fetch_url(url)
    if not html:
        # جرب البحث المباشر
        url2 = f"https://www.rs.iq/market/stocks?symbol={symbol}"
        html = await fetch_url(url2)
    if not html:
        return None
    try:
        soup = BeautifulSoup(html, "html.parser")
        data = {"symbol": symbol, "source": "RS.iq", "timestamp": datetime.now().strftime("%H:%M %Y-%m-%d")}
        data["company"] = IRAQI_STOCKS.get(symbol, symbol)

        # البحث عن الأرقام في الجداول
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                if len(cells) >= 2:
                    if any(k in cells[0] for k in ["السعر", "Price", "آخر", "Last"]):
                        data["price"] = cells[1]
                    elif any(k in cells[0] for k in ["التغيير", "Change", "نسبة"]):
                        data["change"] = cells[1]
                    elif any(k in cells[0] for k in ["الكمية", "Volume", "حجم"]):
                        data["volume"] = cells[1]
                    elif any(k in cells[0] for k in ["أعلى", "High"]):
                        data["high"] = cells[1]
                    elif any(k in cells[0] for k in ["أدنى", "Low"]):
                        data["low"] = cells[1]
        return data if data.get("price") else None
    except Exception as e:
        print(f"[rs] Parse error: {e}")
        return None

async def get_stock_data(symbol: str) -> dict:
    """جلب بيانات السهم من عدة مصادر"""
    symbol = symbol.upper().strip()
    company_name = IRAQI_STOCKS.get(symbol, symbol)

    # جرب المصادر بالتوازي
    tasks = [
        get_stock_from_isx(symbol),
        get_stock_from_rs(symbol),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged = {
        "symbol": symbol,
        "company": company_name,
        "timestamp": datetime.now().strftime("%I:%M %p — %Y/%m/%d"),
        "price": None,
        "change": None,
        "volume": None,
        "high": None,
        "low": None,
        "sources": []
    }

    for r in results:
        if isinstance(r, dict) and r:
            merged["sources"].append(r.get("source", "?"))
            for field in ["price", "change", "volume", "high", "low", "company"]:
                if not merged[field] and r.get(field):
                    merged[field] = r[field]

    return merged

async def get_top_stocks() -> list[dict]:
    """جلب أبرز أسهم اليوم من ISX"""
    url = "https://www.isx-iq.net/isxportal/portal/mainPage.html"
    html = await fetch_url(url)
    if not html:
        return []
    try:
        soup = BeautifulSoup(html, "html.parser")
        stocks = []
        tables = soup.find_all("table")
        for table in tables[:3]:
            rows = table.find_all("tr")[1:]  # تخطي الرأس
            for row in rows[:10]:
                cells = [c.get_text(strip=True) for c in row.find_all("td")]
                if len(cells) >= 4:
                    sym = cells[0].upper() if cells[0] else ""
                    stocks.append({
                        "symbol": sym,
                        "company": IRAQI_STOCKS.get(sym, cells[1] if len(cells) > 1 else sym),
                        "price": cells[2] if len(cells) > 2 else "—",
                        "change": cells[3] if len(cells) > 3 else "—",
                        "volume": cells[4] if len(cells) > 4 else "—",
                    })
        return stocks[:15]
    except Exception as e:
        print(f"[top_stocks] Error: {e}")
        return []

async def get_market_summary() -> dict:
    """ملخص السوق الكلي"""
    html = await fetch_url("https://www.isx-iq.net/isxportal/portal/mainPage.html")
    summary = {
        "date": datetime.now().strftime("%A — %d %B %Y"),
        "status": "مفتوح" if is_market_open() else "مغلق",
        "index": None,
        "change": None,
        "volume": None,
        "value": None,
    }
    if html:
        try:
            soup = BeautifulSoup(html, "html.parser")
            # استخراج مؤشر ISX15
            idx = soup.find(id=re.compile(r".*index.*|.*ISX.*", re.I))
            if idx:
                summary["index"] = idx.get_text(strip=True)
        except:
            pass
    return summary

def is_market_open() -> bool:
    """هل السوق مفتوح الآن؟"""
    from config import MARKET_OPEN_HOUR, MARKET_CLOSE_HOUR
    now = datetime.utcnow()
    # تحويل لتوقيت بغداد UTC+3
    baghdad_hour = (now.hour + 3) % 24
    baghdad_weekday = now.weekday()  # 0=Monday
    # السوق يعمل الأحد-الخميس
    # في Python: Sunday=6, Monday=0, Tuesday=1, Wednesday=2, Thursday=3
    open_days = [6, 0, 1, 2, 3]  # Sunday to Thursday
    if baghdad_weekday not in open_days:
        return False
    return MARKET_OPEN_HOUR <= baghdad_hour < MARKET_CLOSE_HOUR

def get_next_open_time() -> str:
    """موعد فتح السوق القادم"""
    now = datetime.utcnow()
    baghdad_hour = (now.hour + 3) % 24
    baghdad_day = now.weekday()
    days_ar = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
    open_days = [6, 0, 1, 2, 3]

    # إيجاد اليوم التالي
    for i in range(1, 8):
        next_day = (baghdad_day + i) % 7
        if next_day in open_days:
            day_name = days_ar[next_day]
            return f"{day_name} الساعة 10:00 صباحاً"
    return "الأحد القادم الساعة 10:00 صباحاً"
