import os
import time
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import requests

# ------------------------------------------------------------
# yfinance setup — MUST happen before any yf.* calls
# ------------------------------------------------------------
# 1) Point the tz-cache at /tmp. On Render (and most PaaS hosts) the default
#    cache path yfinance picks isn't guaranteed writable, and it can throw
#    at import/first-call time, which looks like "nothing works".
os.makedirs('/tmp/yf_cache', exist_ok=True)
import yfinance as yf
yf.set_tz_cache_location('/tmp/yf_cache')

# 2) Use a browser-impersonating session. Yahoo's undocumented endpoints
#    rate-limit / block plain-Python requests much more aggressively from
#    datacenter IPs (Render, Heroku, AWS) than from a residential IP, which
#    is why this often "works locally, fails when hosted". curl_cffi mimics
#    real browser TLS fingerprints and gets through far more reliably.
try:
    from curl_cffi import requests as cffi_requests
    YF_SESSION = cffi_requests.Session(impersonate="chrome")
except Exception:
    YF_SESSION = None  # falls back to yfinance's default session

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("value-desk")

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/')
def root():
    return send_from_directory('.', 'screener.html')

# ------------------------------------------------------------
# IN-MEMORY CACHE (Render's disk is ephemeral / can be read-only on
# some plans — a pickle file on disk is not reliable there. A plain
# dict with a TTL is simpler and good enough for a 6h refresh window.)
# ------------------------------------------------------------
CACHE = {}
CACHE_TTL = 6 * 3600  # 6 hours

def cache_get(key):
    hit = CACHE.get(key)
    if not hit:
        return None
    value, ts = hit
    if time.time() - ts > CACHE_TTL:
        return None
    return value

def cache_set(key, value):
    CACHE[key] = (value, time.time())

# ------------------------------------------------------------
# LISTS (sectors, currencies, commodities) — unchanged from your version
# ------------------------------------------------------------
SECTOR_ETFS = {
    "Energy (S&P)": "XLE", "Oil Exploration (E&P)": "XOP", "Oil Services": "OIH",
    "Oil Equipment": "IEZ", "Midstream Pipelines": "AMLP", "Natural Gas Producers": "FCG",
    "Refiners": "CRAK", "Uranium": "URA", "Metals & Mining": "XME", "Global Miners": "PICK",
    "Copper Miners": "COPX", "Silver Miners": "SIL", "Junior Silver Miners": "SILJ",
    "Gold Miners": "GDX", "Junior Gold Miners": "GDXJ", "Junior Gold Explorers": "GOEX",
    "Rare Earths": "REMX", "Lithium": "LIT", "Battery Materials": "BATT", "Steel": "SLX",
    "Agriculture/Fertilizer": "MOO", "Technology (S&P)": "XLK", "Semiconductors (SMH)": "SMH",
    "Semiconductors (SOXX)": "SOXX", "Software (IGV)": "IGV", "Cybersecurity (HACK)": "HACK",
    "Cybersecurity (BUG)": "BUG", "Cloud Computing (CLOU)": "CLOU", "Cloud (SKYY)": "SKYY",
    "Robotics (BOTZ)": "BOTZ", "Robotics (ROBO)": "ROBO", "Internet (FDN)": "FDN",
    "Software (XSW)": "XSW", "Cybersecurity (CIBR)": "CIBR", "Financials (S&P)": "XLF",
    "Regional Banks": "KRE", "Banks": "KBE", "Insurance": "KIE", "Brokers": "IAI",
    "Financial Services": "IYG", "Healthcare (S&P)": "XLV", "Biotech (equal weight)": "XBI",
    "Biotech (IBB)": "IBB", "Medical Devices": "IHI", "Pharmaceuticals": "PJP",
    "Industrials (S&P)": "XLI", "Infrastructure": "PAVE", "Aerospace & Defense": "ITA",
    "Aerospace (equal weight)": "XAR", "Defense (PPA)": "PPA", "Transportation": "IYT",
    "Airlines": "JETS", "Autos": "CARZ", "Consumer Discretionary (S&P)": "XLY",
    "Consumer Staples (S&P)": "XLP", "Retail": "XRT", "Online Retail": "IBUY",
    "Leisure & Entertainment": "PEJ", "Hotels": "BEDZ", "Travel": "AWAY",
    "Real Estate (S&P)": "XLRE", "REITs (VNQ)": "VNQ", "U.S. REITs": "IYR",
    "Residential REITs": "REZ", "Communication Services": "XLC", "Telecom & Media": "VOX",
    "Esports": "HERO", "Video Gaming": "ESPO", "Utilities (S&P)": "XLU",
    "Utilities (VPU)": "VPU", "Electric Grid": "GRID", "Materials (S&P)": "XLB",
    "Global Materials": "MXI", "Timber": "WOOD", "Timber & Forestry": "CUT"
}

CURRENCY_NAMES = {
    "USD": "US Dollar", "EUR": "Euro", "JPY": "Japanese Yen", "GBP": "British Pound",
    "CHF": "Swiss Franc", "CAD": "Canadian Dollar", "AUD": "Australian Dollar",
    "NZD": "New Zealand Dollar", "SEK": "Swedish Krona", "NOK": "Norwegian Krone",
    "DKK": "Danish Krone", "CNH": "Chinese Yuan (Offshore)", "CNY": "Chinese Yuan (Onshore)",
    "HKD": "Hong Kong Dollar", "SGD": "Singapore Dollar", "KRW": "South Korean Won",
    "TWD": "Taiwan Dollar", "INR": "Indian Rupee", "IDR": "Indonesian Rupiah",
    "THB": "Thai Baht", "MYR": "Malaysian Ringgit", "PHP": "Philippine Peso",
    "VND": "Vietnamese Dong", "PLN": "Polish Zloty", "CZK": "Czech Koruna",
    "HUF": "Hungarian Forint", "RON": "Romanian Leu", "BGN": "Bulgarian Lev",
    "ISK": "Icelandic Krona", "HRK": "Croatian Kuna", "MXN": "Mexican Peso",
    "BRL": "Brazilian Real", "ARS": "Argentine Peso", "CLP": "Chilean Peso",
    "COP": "Colombian Peso", "PEN": "Peruvian Sol", "UYU": "Uruguayan Peso",
    "ILS": "Israeli Shekel", "TRY": "Turkish Lira", "SAR": "Saudi Riyal",
    "AED": "UAE Dirham", "QAR": "Qatari Riyal", "KWD": "Kuwaiti Dinar",
    "BHD": "Bahraini Dinar", "OMR": "Omani Rial", "ZAR": "South African Rand",
    "EGP": "Egyptian Pound", "NGN": "Nigerian Naira", "MAD": "Moroccan Dirham",
    "KES": "Kenyan Shilling", "RUB": "Russian Ruble", "KZT": "Kazakh Tenge",
    "UAH": "Ukrainian Hryvnia", "PKR": "Pakistani Rupee", "BDT": "Bangladeshi Taka",
    "LKR": "Sri Lankan Rupee"
}
CURRENCY_TICKERS = {code: (code + "USD=X" if code != "USD" else "USDUSD=X") for code in CURRENCY_NAMES}

COMMODITY_TICKERS = {
    "Gold": "GC=F", "Silver": "SI=F", "Platinum": "PL=F", "Palladium": "PA=F",
    "Copper": "HG=F", "WTI Crude Oil": "CL=F", "Brent Crude": "BZ=F", "Natural Gas": "NG=F",
    "Heating Oil": "HO=F", "RBOB Gasoline": "RB=F", "Propane": "B0=F", "Corn": "ZC=F",
    "Wheat": "ZW=F", "Kansas Wheat": "KE=F", "Soybeans": "ZS=F", "Soybean Meal": "ZM=F",
    "Soybean Oil": "ZL=F", "Oats": "ZO=F", "Rice": "ZR=F", "Coffee": "KC=F",
    "Sugar #11": "SB=F", "Cocoa": "CC=F", "Cotton": "CT=F", "Orange Juice": "OJ=F",
    "Lumber": "LBR=F", "Live Cattle": "LE=F", "Feeder Cattle": "GF=F", "Lean Hogs": "HE=F",
    "Class III Milk": "DC=F", "Butter": "CB=F", "Cheese": "CSC=F"
}

CONVERGENCE_MAP = {
    "Energy (S&P)": ("WTI Crude Oil", "CAD"), "Oil Exploration (E&P)": ("WTI Crude Oil", "CAD"),
    "Oil Services": ("WTI Crude Oil", "CAD"), "Oil Equipment": ("WTI Crude Oil", "CAD"),
    "Midstream Pipelines": ("Natural Gas", "CAD"), "Natural Gas Producers": ("Natural Gas", "CAD"),
    "Refiners": ("WTI Crude Oil", "CAD"), "Metals & Mining": ("Copper", "AUD"),
    "Global Miners": ("Copper", "AUD"), "Copper Miners": ("Copper", "AUD"),
    "Silver Miners": ("Silver", "AUD"), "Junior Silver Miners": ("Silver", "AUD"),
    "Gold Miners": ("Gold", "AUD"), "Junior Gold Miners": ("Gold", "AUD"),
    "Junior Gold Explorers": ("Gold", "AUD"), "Battery Materials": ("Copper", "AUD"),
    "Agriculture/Fertilizer": ("Corn", "USD"), "Infrastructure": ("Copper", "USD"),
    "Transportation": ("WTI Crude Oil", "USD"), "Airlines": ("WTI Crude Oil", "USD"),
    "Utilities (S&P)": ("Natural Gas", "USD"), "Utilities (VPU)": ("Natural Gas", "USD"),
    "Electric Grid": ("Copper", "USD"), "Materials (S&P)": ("Copper", "AUD"),
    "Global Materials": ("Copper", "AUD"), "Timber": ("Lumber", "CAD"),
    "Timber & Forestry": ("Lumber", "CAD")
}

ALL_SECTOR_TICKERS = list(SECTOR_ETFS.values())
ALL_CURRENCY_TICKERS = list(CURRENCY_TICKERS.values())
ALL_COMMODITY_TICKERS = list(COMMODITY_TICKERS.values())

# ------------------------------------------------------------
# BATCHED HISTORICAL DOWNLOAD (this is the big fix — one network
# round trip covering ~160 tickers instead of ~160 separate ones)
# ------------------------------------------------------------
def batch_weekly_closes(tickers, period='5y'):
    """
    Download weekly closes for a list of tickers in as few requests as
    possible. Returns a DataFrame (columns = tickers) or an empty
    DataFrame on failure. Always includes 'GC=F' (gold) so gold-ratio
    math has something to divide by.
    """
    cache_key = f"batch_{period}_{','.join(sorted(tickers))}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    tickers = list(dict.fromkeys(tickers + ['GC=F']))  # dedupe, ensure gold present
    try:
        data = yf.download(
            tickers, period=period, interval='1d', progress=False,
            timeout=30, group_by='column', threads=True,
            session=YF_SESSION
        )
        if data.empty:
            log.warning("batch_weekly_closes: empty response for %d tickers", len(tickers))
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):
            close = data['Close'] if 'Close' in data.columns.get_level_values(0) else data.iloc[:, 0]
        else:
            # Single-ticker request collapses to flat columns
            col = 'Close' if 'Close' in data.columns else data.columns[0]
            close = data[[col]]
            close.columns = tickers[:1]

        weekly = close.resample('W').last()
        cache_set(cache_key, weekly)
        return weekly
    except Exception:
        log.error("batch_weekly_closes failed:\n%s", traceback.format_exc())
        return pd.DataFrame()

def gold_ratio_deviation(weekly_df, ticker):
    """Given the batched weekly-close DataFrame, compute this ticker's
    current price/gold ratio vs its own 5y average ratio."""
    if weekly_df is None or weekly_df.empty:
        return None
    if ticker not in weekly_df.columns or 'GC=F' not in weekly_df.columns:
        return None
    pair = weekly_df[[ticker, 'GC=F']].dropna()
    if len(pair) < 5:
        return None
    ratio = pair[ticker] / pair['GC=F']
    mean = ratio.mean()
    if mean == 0 or pd.isna(mean):
        return None
    current = ratio.iloc[-1]
    return float((current - mean) / mean * 100)

# ------------------------------------------------------------
# LIGHTWEIGHT INFO LOOKUPS (for P/E, P/B, rating, insider %)
# Parallelized with a thread pool since each is still one HTTP call —
# this cuts wall-clock time a lot even though the call count is the same.
# ------------------------------------------------------------
def get_stock_metrics(ticker):
    cached = cache_get(f"info_{ticker}")
    if cached is not None:
        return cached
    try:
        t = yf.Ticker(ticker, session=YF_SESSION)
        info = t.info
        if not info or info.get('regularMarketPrice') is None:
            return None
        pe = info.get('trailingPE') or info.get('forwardPE')
        pb = info.get('priceToBook')
        insider = info.get('heldPercentInsiders')
        result = {
            'pe': round(pe, 2) if pe else None,
            'pb': round(pb, 2) if pb else None,
            'rating': info.get('recommendationKey', 'none'),
            'insider': round(insider * 100, 2) if insider else None,
            'price': info.get('regularMarketPrice'),
            'name': info.get('shortName', ticker)
        }
        cache_set(f"info_{ticker}", result)
        return result
    except Exception as e:
        log.warning("get_stock_metrics(%s) failed: %s", ticker, e)
        return None

def get_metrics_parallel(tickers, max_workers=12):
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(get_stock_metrics, t): t for t in tickers}
        for fut in as_completed(futures):
            t = futures[fut]
            try:
                results[t] = fut.result()
            except Exception:
                results[t] = None
    return results

def get_currency_rates():
    cached = cache_get('fx_rates')
    if cached is not None:
        return cached
    try:
        resp = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=8)
        if resp.status_code == 200:
            rates = resp.json().get('rates', {})
            cache_set('fx_rates', rates)
            return rates
    except Exception as e:
        log.warning("get_currency_rates failed: %s", e)
    return {}

# ------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------
@app.route('/api/dashboard')
def dashboard():
    try:
        # One batched download covers gold-ratio math for everything.
        all_tickers = ALL_SECTOR_TICKERS + ALL_CURRENCY_TICKERS + ALL_COMMODITY_TICKERS
        weekly = batch_weekly_closes(all_tickers)

        # Sector P/E: each ETF's own trailingPE, fetched in parallel & cached —
        # NOT the old per-holding average (that's what needed funds_data).
        sector_pe = get_metrics_parallel(ALL_SECTOR_TICKERS)

        sectors = []
        for sector_name, etf_ticker in SECTOR_ETFS.items():
            m = sector_pe.get(etf_ticker)
            sectors.append({
                'sector': sector_name,
                'etf': etf_ticker,
                'avg_pe': m['pe'] if m else None,
                'cheapness': gold_ratio_deviation(weekly, etf_ticker)
            })
        sectors.sort(key=lambda x: x['cheapness'] if x['cheapness'] is not None else 999)

        rates = get_currency_rates()
        currencies = []
        for code, ticker in CURRENCY_TICKERS.items():
            if code == "USD":
                currencies.append({'code': code, 'name': CURRENCY_NAMES[code], 'rate_usd': 1.0, 'cheapness': 0})
                continue
            currencies.append({
                'code': code,
                'name': CURRENCY_NAMES.get(code, code),
                'rate_usd': rates.get(code),
                'cheapness': gold_ratio_deviation(weekly, ticker)
            })
        currencies.sort(key=lambda x: x['cheapness'] if x['cheapness'] is not None else 999)

        commodities = []
        for name, ticker in COMMODITY_TICKERS.items():
            price = None
            if weekly is not None and not weekly.empty and ticker in weekly.columns:
                series = weekly[ticker].dropna()
                if not series.empty:
                    price = float(series.iloc[-1])
            gold_price = None
            if weekly is not None and not weekly.empty and 'GC=F' in weekly.columns:
                gseries = weekly['GC=F'].dropna()
                if not gseries.empty:
                    gold_price = float(gseries.iloc[-1])
            ratio = (price / gold_price) if (price and gold_price) else None
            commodities.append({
                'name': name,
                'price': price,
                'gold_ratio': ratio,
                'cheapness': gold_ratio_deviation(weekly, ticker)
            })
        commodities.sort(key=lambda x: x['cheapness'] if x['cheapness'] is not None else 999)

        return jsonify({'sectors': sectors, 'currencies': currencies, 'commodities': commodities})
    except Exception as e:
        log.error("Dashboard error:\n%s", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations')
def recommendations():
    try:
        all_tickers = ALL_SECTOR_TICKERS + ALL_CURRENCY_TICKERS + ALL_COMMODITY_TICKERS
        weekly = batch_weekly_closes(all_tickers)

        sector_cheapness = {name: gold_ratio_deviation(weekly, t) for name, t in SECTOR_ETFS.items()}
        commodity_cheapness = {name: gold_ratio_deviation(weekly, t) for name, t in COMMODITY_TICKERS.items()}
        currency_cheapness = {}
        for code, ticker in CURRENCY_TICKERS.items():
            currency_cheapness[code] = 0.0 if code == "USD" else gold_ratio_deviation(weekly, ticker)

        results = []
        for sector_name, (com_key, curr_code) in CONVERGENCE_MAP.items():
            sec = sector_cheapness.get(sector_name)
            if sec is None:
                continue
            com = commodity_cheapness.get(com_key) if com_key else None
            cur = currency_cheapness.get(curr_code) if curr_code else None
            vals = [v for v in [sec, com, cur] if v is not None]
            if len(vals) < 2:
                continue
            avg = sum(vals) / len(vals)
            results.append({
                'sector': sector_name, 'etf': SECTOR_ETFS[sector_name],
                'convergence_score': avg, 'sector_cheapness': sec,
                'commodity': com_key, 'commodity_cheapness': com,
                'currency': curr_code, 'currency_cheapness': cur,
                'num_factors': len(vals)
            })
        results.sort(key=lambda x: x['convergence_score'])
        return jsonify(results)
    except Exception as e:
        log.error("Recommendations error:\n%s", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search():
    try:
        query = request.args.get('q', '').strip().upper()
        if not query:
            return jsonify({'error': 'Query required'}), 400

        response = {'sectors': [], 'etfs': [], 'stocks': [], 'currencies': [], 'commodities': [], 'recommendations': []}

        matched_sectors = {n: t for n, t in SECTOR_ETFS.items() if query in n.upper() or query in t}
        if matched_sectors:
            pe_lookup = get_metrics_parallel(list(matched_sectors.values()))
            for sector_name, etf_ticker in matched_sectors.items():
                m = pe_lookup.get(etf_ticker)
                response['sectors'].append({'name': sector_name, 'etf': etf_ticker, 'avg_pe': m['pe'] if m else None})
                response['etfs'].append({'ticker': etf_ticker, 'sector': sector_name, 'info': m})

        candidates = [query] if query.isalpha() and 1 <= len(query) <= 5 else []
        popular = ["AAPL","MSFT","GOOGL","AMZN","META","TSLA","NVDA","JPM","V","WMT",
                   "JNJ","PG","UNH","HD","DIS","MA","BAC","XOM","CVX","PFE"]
        candidates += [t for t in popular if query in t]
        candidates = list(dict.fromkeys(candidates))
        if candidates:
            stock_lookup = get_metrics_parallel(candidates)
            for t in candidates:
                m = stock_lookup.get(t)
                if m:
                    m = dict(m); m['ticker'] = t
                    response['stocks'].append(m)

        rates = get_currency_rates()
        for code, ticker in CURRENCY_TICKERS.items():
            if code != "USD" and query in code:
                response['currencies'].append({'code': code, 'name': CURRENCY_NAMES.get(code, code), 'rate_usd': rates.get(code)})

        for name, ticker in COMMODITY_TICKERS.items():
            if query in name.upper() or query in ticker:
                m = get_stock_metrics(ticker)
                response['commodities'].append({'name': name, 'price': m['price'] if m else None})

        for stock in response['stocks']:
            score = 50
            if stock.get('pe') and stock['pe'] > 0:
                score += 15 if stock['pe'] < 10 else 10 if stock['pe'] < 15 else 5 if stock['pe'] < 20 else -10
            if stock.get('pb') and stock['pb'] > 0:
                score += 15 if stock['pb'] < 1 else 10 if stock['pb'] < 1.5 else 5 if stock['pb'] < 2 else -10
            insider = stock.get('insider')
            if insider and insider > 5: score += 10
            elif insider and insider > 2: score += 5
            rating = (stock.get('rating') or '').lower()
            if 'buy' in rating: score += 10
            elif 'sell' in rating: score -= 10
            score = max(0, min(100, score))
            response['recommendations'].append({'ticker': stock['ticker'], 'name': stock.get('name', stock['ticker']), 'score': score, 'metrics': stock})
        response['recommendations'].sort(key=lambda x: x['score'], reverse=True)

        return jsonify(response)
    except Exception as e:
        log.error("Search error:\n%s", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/<ticker>')
def debug_ticker(ticker):
    """Hit this directly in a browser (e.g. /api/debug/AAPL or /api/debug/XLE)
    to see exactly what yfinance returns or throws on the live server."""
    out = {'ticker': ticker, 'session_type': 'curl_cffi' if YF_SESSION else 'default'}
    try:
        t = yf.Ticker(ticker, session=YF_SESSION)
        info = t.info
        out['info_keys_found'] = len(info) if info else 0
        out['sample'] = {k: info.get(k) for k in ['regularMarketPrice', 'trailingPE', 'priceToBook', 'shortName']} if info else None
    except Exception:
        out['info_error'] = traceback.format_exc()
    try:
        hist = yf.download(ticker, period='5d', progress=False, session=YF_SESSION)
        out['history_rows'] = len(hist)
    except Exception:
        out['history_error'] = traceback.format_exc()
    return jsonify(out)

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'session_type': 'curl_cffi' if YF_SESSION else 'default', 'cached_keys': len(CACHE)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
