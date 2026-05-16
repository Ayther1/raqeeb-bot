cat > /mnt/user-data/outputs/scraper.py << 'ENDOFFILE'
# scraper.py — سحب البيانات من البورصة العراقية

import cloudscraper
from bs4 import BeautifulSoup
import re
import time
import random

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

ISX_BASE = "http://isx-iq.net/isxportal/portal"

def smart_sleep():
    time.sleep(random.uniform(1.0, 2.0))

def safe_get(url, retries=3):
    for attempt in range(retries):
        try:
            smart_sleep()
            r = scraper.get(url, timeout=15)
            if r.status_code == 200:
                return r
            print(f"[Scraper] {r.status_code} - المحاولة {attempt+1}/{retries}")
            time.sleep(random.uniform(3, 6))
        except Exception as e:
            print(f"[Scraper] خطأ: {e} - المحاولة {attempt+1}/{retries}")
            time.sleep(random.uniform(2, 4))
    return None

IRAQI_STOCKS = {
    "BBOB": {"name": "مصرف بغداد", "sector": "مصارف"},
    "BCOI": {"name": "مصرف الخليج التجاري", "sector": "مصارف"},
    "BDSI": {"name": "مصرف بغداد للاستثمار", "sector": "مصارف"},
    "BGUC": {"name": "مصرف الخليج العراقي", "sector": "مصارف"},
    "BIAP": {"name": "مصرف بيروت عمان", "sector": "مصارف"},
    "BIKE": {"name": "مصرف كردستان الإسلامي", "sector": "مصارف"},
    "BIME": {"name": "مصرف الاستثمار والتنمية", "sector": "مصارف"},
    "BISR": {"name": "المصرف العراقي الإسلامي", "sector": "مصارف"},
    "BKUI": {"name": "مصرف كوردستان المتحد", "sector": "مصارف"},
    "BLAD": {"name": "مصرف بلاد الرافدين", "sector": "مصارف"},
    "BNOI": {"name": "مصرف الشمال", "sector": "مصارف"},
    "BSUC": {"name": "مصرف الجنوب التجاري", "sector": "مصارف"},
    "BUND": {"name": "مصرف الاتحاد", "sector": "مصارف"},
    "BWOI": {"name": "مصرف الوركاء للاستثمار", "sector": "مصارف"},
    "BZII": {"name": "مصرف الزوراء", "sector": "مصارف"},
    "CIFI": {"name": "مصرف كيمان الإسلامي", "sector": "مصارف"},
    "CSIB": {"name": "المصرف الصناعي", "sector": "مصارف"},
    "DIJL": {"name": "مصرف دجلة والفرات", "sector": "مصارف"},
    "EBDI": {"name": "بنك الشرق الأوسط", "sector": "مصارف"},
    "FABI": {"name": "مصرف الأول للاستثمار", "sector": "مصارف"},
    "FIBK": {"name": "المصرف العراقي الأول", "sector": "مصارف"},
    "IBSD": {"name": "مصرف الاستثمار العراقي", "sector": "مصارف"},
    "IICB": {"name": "مصرف الائتمان العراقي", "sector": "مصارف"},
    "IMAM": {"name": "مصرف الإمام علي", "sector": "مصارف"},
    "INBU": {"name": "مصرف الاستثمار الوطني", "sector": "مصارف"},
    "JIBI": {"name": "مصرف الجمهورية", "sector": "مصارف"},
    "KFHO": {"name": "مصرف الكوفة الإسلامي", "sector": "مصارف"},
    "LBIS": {"name": "مصرف لبنان والمهجر", "sector": "مصارف"},
    "MBIS": {"name": "مصرف بابل", "sector": "مصارف"},
    "MDIG": {"name": "مصرف الشرق الأوسط العراقي", "sector": "مصارف"},
    "MEBI": {"name": "مصرف الشرق الأوسط للاستثمار", "sector": "مصارف"},
    "MIBZ": {"name": "مصرف الميزان الإسلامي", "sector": "مصارف"},
    "MSBI": {"name": "مصرف المصرف", "sector": "مصارف"},
    "NABI": {"name": "المصرف الوطني للاستثمار", "sector": "مصارف"},
    "NIBD": {"name": "مصرف نينوى", "sector": "مصارف"},
    "NIBF": {"name": "مصرف نور الإسلامي", "sector": "مصارف"},
    "NOOR": {"name": "مصرف نور", "sector": "مصارف"},
    "NSIB": {"name": "المصرف الوطني الإسلامي", "sector": "مصارف"},
    "OFBI": {"name": "مصرف الوفاء الإسلامي", "sector": "مصارف"},
    "RIIN": {"name": "مصرف الرشيد الإسلامي", "sector": "مصارف"},
    "SBIS": {"name": "مصرف الصفا الإسلامي", "sector": "مصارف"},
    "SHBI": {"name": "مصرف الشهداء للاستثمار", "sector": "مصارف"},
    "SIIB": {"name": "مصرف سومر الإسلامي", "sector": "مصارف"},
    "SLBI": {"name": "مصرف السلام", "sector": "مصارف"},
    "TAAN": {"name": "مصرف التعاون الإسلامي", "sector": "مصارف"},
    "TAIB": {"name": "مصرف طيبة للاستثمار", "sector": "مصارف"},
    "TTBI": {"name": "مصرف التجارة والتمويل", "sector": "مصارف"},
    "UBAI": {"name": "مصرف الاتحاد للاستثمار", "sector": "مصارف"},
    "UIBI": {"name": "مصرف الوحدة الإسلامي", "sector": "مصارف"},
    "UNBI": {"name": "مصرف الائتمان الوطني", "sector": "مصارف"},
    "WABI": {"name": "مصرف واسط", "sector": "مصارف"},
    "WARK": {"name": "مصرف الوركاء", "sector": "مصارف"},
    "WIIB": {"name": "مصرف الوسيط الإسلامي", "sector": "مصارف"},
    "TASC": {"name": "شركة الاتصالات العراقية", "sector": "اتصالات"},
    "TELE": {"name": "شركة آسيا سيل للاتصالات", "sector": "اتصالات"},
    "AMDI": {"name": "شركة أمنية للاتصالات", "sector": "اتصالات"},
    "ITLI": {"name": "شركة المعلومات للتكنولوجيا", "sector": "اتصالات"},
    "HLIS": {"name": "شركة الهلال للصناعة", "sector": "صناعة"},
    "AIPT": {"name": "شركة الاتحاد العراقية للبلاستيك", "sector": "صناعة"},
    "BSTC": {"name": "شركة بصرة للصلب", "sector": "صناعة"},
    "CALL": {"name": "شركة الكيبل العراقية", "sector": "صناعة"},
    "CCBI": {"name": "شركة بغداد للكوكاكولا", "sector": "صناعة"},
    "CFIQ": {"name": "شركة الإسمنت العراقية", "sector": "صناعة"},
    "GIIC": {"name": "الشركة العامة للصناعات الغذائية", "sector": "صناعة"},
    "HLSI": {"name": "شركة الهلال للصناعات الغذائية", "sector": "صناعة"},
    "IACI": {"name": "شركة الصناعات العراقية الأمريكية", "sector": "صناعة"},
    "ICFI": {"name": "شركة الإسمنت الحجاري", "sector": "صناعة"},
    "IICM": {"name": "شركة الصناعات العراقية المختلطة", "sector": "صناعة"},
    "IPCO": {"name": "شركة النفط العراقية للإنتاج", "sector": "صناعة"},
    "IRFI": {"name": "شركة الرافدين للصناعة", "sector": "صناعة"},
    "ISDC": {"name": "شركة الإسمنت الجنوبية", "sector": "صناعة"},
    "KAIN": {"name": "شركة الكابلات العراقية", "sector": "صناعة"},
    "MEFK": {"name": "شركة مصفى الكوت", "sector": "صناعة"},
    "NAIN": {"name": "شركة نينوى للصناعة", "sector": "صناعة"},
    "NCPI": {"name": "شركة الإسمنت الشمالية", "sector": "صناعة"},
    "SAIH": {"name": "شركة صناعة الادوية العراقية", "sector": "صناعة"},
    "SCBI": {"name": "شركة الإسمنت المركزية", "sector": "صناعة"},
    "SDBI": {"name": "شركة صناعة البطاريات", "sector": "صناعة"},
    "SPPI": {"name": "شركة الصحة للصناعة الدوائية", "sector": "صناعة"},
    "UCFI": {"name": "شركة الإسمنت الموحدة", "sector": "صناعة"},
    "AAHP": {"name": "شركة آسيا للفنادق", "sector": "فنادق"},
    "AIHI": {"name": "شركة عشتار للفنادق", "sector": "فنادق"},
    "BAHI": {"name": "شركة بابل للفنادق", "sector": "فنادق"},
    "BGHI": {"name": "شركة بغداد للفنادق", "sector": "فنادق"},
    "ESHT": {"name": "شركة عشتار ريجنسي", "sector": "فنادق"},
    "IAHI": {"name": "شركة العراق للفنادق والسياحة", "sector": "فنادق"},
    "IRSH": {"name": "شركة الرشيد للفنادق", "sector": "فنادق"},
    "MHSI": {"name": "شركة المنصور ميليا للفنادق", "sector": "فنادق"},
    "NAHI": {"name": "شركة النجف للفنادق", "sector": "فنادق"},
    "SAHI": {"name": "شركة السفراء للفنادق", "sector": "فنادق"},
    "IICL": {"name": "شركة التأمين العراقية", "sector": "تأمين"},
    "ALIQ": {"name": "شركة التأمين الأهلية", "sector": "تأمين"},
    "AMII": {"name": "شركة التأمين الأمانة", "sector": "تأمين"},
    "BAIN": {"name": "شركة بغداد للتأمين", "sector": "تأمين"},
    "DAIN": {"name": "شركة دار السلام للتأمين", "sector": "تأمين"},
    "IAIN": {"name": "شركة التأمين الإسلامية", "sector": "تأمين"},
    "IIIN": {"name": "شركة التأمين الدولية", "sector": "تأمين"},
    "MEIN": {"name": "شركة شرق أوسط للتأمين", "sector": "تأمين"},
    "RAIN": {"name": "شركة الرشيد للتأمين", "sector": "تأمين"},
    "SAIN": {"name": "شركة سومر للتأمين", "sector": "تأمين"},
    "UAIN": {"name": "شركة الاتحاد للتأمين", "sector": "تأمين"},
    "WAIN": {"name": "شركة وقاية للتأمين", "sector": "تأمين"},
    "DAGR": {"name": "شركة دجلة للزراعة", "sector": "زراعة"},
    "IAGR": {"name": "شركة العراقية للزراعة", "sector": "زراعة"},
    "MAGR": {"name": "شركة الموصل للزراعة", "sector": "زراعة"},
    "NAGR": {"name": "شركة النهرين للزراعة", "sector": "زراعة"},
    "RAGR": {"name": "شركة الرافدين للزراعة", "sector": "زراعة"},
    "SAGR": {"name": "شركة سومر للزراعة", "sector": "زراعة"},
}

def get_market_summary():
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
    return {"index":"—","change_pct":"—","value":"—","trades":"—","up":"—","down":"—","flat":"—"}

def get_stock_info(symbol):
    symbol = symbol.upper().strip()
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
            print(f"[Scraper] stock error: {e}")
    stock_info = IRAQI_STOCKS.get(symbol)
    if stock_info:
        return {
            "symbol": symbol,
            "name": stock_info["name"],
            "sector": stock_info.get("sector","—"),
            "price": "⏳ البيانات غير متاحة حالياً",
            "change_pct": "—",
            "high": "—",
            "low": "—",
            "volume": "—",
        }
    return None

def get_top_stocks():
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
                            change = float(cols[-1].replace("%","").replace(",",""))
                            if change > 0:
                                up_stocks.append({"symbol":cols[0],"change":round(change,2)})
                            elif change < 0:
                                down_stocks.append({"symbol":cols[0],"change":round(change,2)})
                        except:
                            pass
            if up_stocks or down_stocks:
                return {
                    "up":   sorted(up_stocks,   key=lambda x: x["change"], reverse=True)[:5],
                    "down": sorted(down_stocks, key=lambda x: x["change"])[:5],
                }
        except Exception as e:
            print(f"[Scraper] top_stocks error: {e}")
    return {"up":[],"down":[]}

def get_latest_news():
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
    data = get_stock_info(symbol)
    if data and data.get("price") and data["price"] not in ["—","⏳ البيانات غير متاحة حالياً"]:
        try:
            return float(data["price"].replace(",","").replace(" ",""))
        except:
            return None
    return None
ENDOFFILE
echo "done"
{
  "returncode" : 0,
  "stdout" : "done\n",
  "stderr" : ""
}