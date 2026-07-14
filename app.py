from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yfinance as yf
import requests
import pandas as pd

app = Flask(__name__, static_folder='.')
CORS(app)

# ------------------------------------------------------------
# ROOT – serves the HTML file
# ------------------------------------------------------------
@app.route('/')
def root():
    return send_from_directory('.', 'screener.html')

# ------------------------------------------------------------
# SECTOR ETFS (74)
# ------------------------------------------------------------
SECTOR_ETFS = {
    "Energy (S&P)": "XLE",
    "Oil Exploration (E&P)": "XOP",
    "Oil Services": "OIH",
    "Oil Equipment": "IEZ",
    "Midstream Pipelines": "AMLP",
    "Natural Gas Producers": "FCG",
    "Refiners": "CRAK",
    "Uranium": "URA",
    "Coal": "KOL",
    "Metals & Mining": "XME",
    "Global Miners": "PICK",
    "Copper Miners": "COPX",
    "Silver Miners": "SIL",
    "Junior Silver Miners": "SILJ",
    "Gold Miners": "GDX",
    "Junior Gold Miners": "GDXJ",
    "Junior Gold Explorers": "GOEX",
    "Rare Earths": "REMX",
    "Lithium": "LIT",
    "Battery Materials": "BATT",
    "Steel": "SLX",
    "Agriculture/Fertilizer": "MOO",
    "Technology (S&P)": "XLK",
    "Semiconductors (SMH)": "SMH",
    "Semiconductors (SOXX)": "SOXX",
    "Software (IGV)": "IGV",
    "Cybersecurity (HACK)": "HACK",
    "Cybersecurity (BUG)": "BUG",
    "Cloud Computing (CLOU)": "CLOU",
    "Cloud (SKYY)": "SKYY",
    "Robotics (BOTZ)": "BOTZ",
    "Robotics (ROBO)": "ROBO",
    "Internet (FDN)": "FDN",
    "Software (XSW)": "XSW",
    "Cybersecurity (CIBR)": "CIBR",
    "Financials (S&P)": "XLF",
    "Regional Banks": "KRE",
    "Banks": "KBE",
    "Insurance": "KIE",
    "Brokers": "IAI",
    "Financial Services": "IYG",
    "Healthcare (S&P)": "XLV",
    "Biotech (equal weight)": "XBI",
    "Biotech (IBB)": "IBB",
    "Medical Devices": "IHI",
    "Pharmaceuticals": "PJP",
    "Industrials (S&P)": "XLI",
    "Infrastructure": "PAVE",
    "Aerospace & Defense": "ITA",
    "Aerospace (equal weight)": "XAR",
    "Defense (PPA)": "PPA",
    "Transportation": "IYT",
    "Airlines": "JETS",
    "Autos": "CARZ",
    "Consumer Discretionary (S&P)": "XLY",
    "Consumer Staples (S&P)": "XLP",
    "Retail": "XRT",
    "Online Retail": "IBUY",
    "Leisure & Entertainment": "PEJ",
    "Hotels": "BEDZ",
    "Travel": "AWAY",
    "Real Estate (S&P)": "XLRE",
    "REITs (VNQ)": "VNQ",
    "U.S. REITs": "IYR",
    "Residential REITs": "REZ",
    "Communication Services": "XLC",
    "Telecom & Media": "VOX",
    "Esports": "HERO",
    "Video Gaming": "ESPO",
    "Utilities (S&P)": "XLU",
    "Utilities (VPU)": "VPU",
    "Electric Grid": "GRID",
    "Materials (S&P)": "XLB",
    "Global Materials": "MXI",
    "Timber": "WOOD",
    "Timber & Forestry": "CUT"
}

# ------------------------------------------------------------
# CURRENCIES (58) with full names
# ------------------------------------------------------------
CURRENCY_NAMES = {
    "USD": "US Dollar",
    "EUR": "Euro",
    "JPY": "Japanese Yen",
    "GBP": "British Pound",
    "CHF": "Swiss Franc",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "NZD": "New Zealand Dollar",
    "SEK": "Swedish Krona",
    "NOK": "Norwegian Krone",
    "DKK": "Danish Krone",
    "CNH": "Chinese Yuan (Offshore)",
    "CNY": "Chinese Yuan (Onshore)",
    "HKD": "Hong Kong Dollar",
    "SGD": "Singapore Dollar",
    "KRW": "South Korean Won",
    "TWD": "Taiwan Dollar",
    "INR": "Indian Rupee",
    "IDR": "Indonesian Rupiah",
    "THB": "Thai Baht",
    "MYR": "Malaysian Ringgit",
    "PHP": "Philippine Peso",
    "VND": "Vietnamese Dong",
    "PLN": "Polish Zloty",
    "CZK": "Czech Koruna",
    "HUF": "Hungarian Forint",
    "RON": "Romanian Leu",
    "BGN": "Bulgarian Lev",
    "ISK": "Icelandic Krona",
    "HRK": "Croatian Kuna",
    "MXN": "Mexican Peso",
    "BRL": "Brazilian Real",
    "ARS": "Argentine Peso",
    "CLP": "Chilean Peso",
    "COP": "Colombian Peso",
    "PEN": "Peruvian Sol",
    "UYU": "Uruguayan Peso",
    "ILS": "Israeli Shekel",
    "TRY": "Turkish Lira",
    "SAR": "Saudi Riyal",
    "AED": "UAE Dirham",
    "QAR": "Qatari Riyal",
    "KWD": "Kuwaiti Dinar",
    "BHD": "Bahraini Dinar",
    "OMR": "Omani Rial",
    "ZAR": "South African Rand",
    "EGP": "Egyptian Pound",
    "NGN": "Nigerian Naira",
    "MAD": "Moroccan Dirham",
    "KES": "Kenyan Shilling",
    "RUB": "Russian Ruble",
    "KZT": "Kazakh Tenge",
    "UAH": "Ukrainian Hryvnia",
    "PKR": "Pakistani Rupee",
    "BDT": "Bangladeshi Taka",
    "LKR": "Sri Lankan Rupee"
}

CURRENCY_TICKERS = {code: code + "USD=X" if code != "USD" else "USDUSD=X" for code in CURRENCY_NAMES}

# ------------------------------------------------------------
# COMMODITIES (54 – removed Micro Gold & Micro Silver)
# ------------------------------------------------------------
COMMODITY_TICKERS = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Platinum": "PL=F",
    "Palladium": "PA=F",
    "Copper": "HG=F",
    "Aluminum": "ALI=F",
    "Nickel": "NICKEL=F",
    "Zinc": "ZINC=F",
    "Lead": "LEAD=F",
    "Tin": "TIN=F",
    "WTI Crude Oil": "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Heating Oil": "HO=F",
    "RBOB Gasoline": "RB=F",
    "Propane": "B0=F",
    "Corn": "ZC=F",
    "Wheat": "ZW=F",
    "Kansas Wheat": "KE=F",
    "Minneapolis Wheat": "MWE=F",
    "Soybeans": "ZS=F",
    "Soybean Meal": "ZM=F",
    "Soybean Oil": "ZL=F",
    "Oats": "ZO=F",
    "Rice": "ZR=F",
    "Coffee": "KC=F",
    "Sugar #11": "SB=F",
    "Cocoa": "CC=F",
    "Cotton": "CT=F",
    "Orange Juice": "OJ=F",
    "Lumber": "LBR=F",
    "Live Cattle": "LE=F",
    "Feeder Cattle": "GF=F",
    "Lean Hogs": "HE=F",
    "Class III Milk": "DC=F",
    "Butter": "CB=F",
    "Cheese": "CSC=F",
    "Rubber": "JRU=F"
}

# ------------------------------------------------------------
# CONVERGENCE MAP (sector -> commodity, currency)
# ------------------------------------------------------------
CONVERGENCE_MAP = {
    "Energy (S&P)": ("WTI Crude Oil", "CAD"),
    "Oil Exploration (E&P)": ("WTI Crude Oil", "CAD"),
    "Oil Services": ("WTI Crude Oil", "CAD"),
    "Oil Equipment": ("WTI Crude Oil", "CAD"),
    "Midstream Pipelines": ("Natural Gas", "CAD"),
    "Natural Gas Producers": ("Natural Gas", "CAD"),
    "Refiners": ("WTI Crude Oil", "CAD"),
    "Uranium": (None, None),
    "Coal": (None, None),
    "Metals & Mining": ("Copper", "AUD"),
    "Global Miners": ("Copper", "AUD"),
    "Copper Miners": ("Copper", "AUD"),
    "Silver Miners": ("Silver", "AUD"),
    "Junior Silver Miners": ("Silver", "AUD"),
    "Gold Miners": ("Gold", "AUD"),
    "Junior Gold Miners": ("Gold", "AUD"),
    "Junior Gold Explorers": ("Gold", "AUD"),
    "Rare Earths": (None, None),
    "Lithium": (None, None),
    "Battery Materials": ("Copper", "AUD"),
    "Steel": (None, None),
    "Agriculture/Fertilizer": ("Corn", "USD"),
    "Technology (S&P)": (None, "USD"),
    "Semiconductors (SMH)": (None, "USD"),
    "Semiconductors (SOXX)": (None, "USD"),
    "Software (IGV)": (None, "USD"),
    "Cybersecurity (HACK)": (None, "USD"),
    "Cybersecurity (BUG)": (None, "USD"),
    "Cloud Computing (CLOU)": (None, "USD"),
    "Cloud (SKYY)": (None, "USD"),
    "Robotics (BOTZ)": (None, "USD"),
    "Robotics (ROBO)": (None, "USD"),
    "Internet (FDN)": (None, "USD"),
    "Software (XSW)": (None, "USD"),
    "Cybersecurity (CIBR)": (None, "USD"),
    "Financials (S&P)": (None, "USD"),
    "Regional Banks": (None, "USD"),
    "Banks": (None, "USD"),
    "Insurance": (None, "USD"),
    "Brokers": (None, "USD"),
    "Financial Services": (None, "USD"),
    "Healthcare (S&P)": (None, "USD"),
    "Biotech (equal weight)": (None, "USD"),
    "Biotech (IBB)": (None, "USD"),
    "Medical Devices": (None, "USD"),
    "Pharmaceuticals": (None, "USD"),
    "Industrials (S&P)": (None, "USD"),
    "Infrastructure": ("Copper", "USD"),
    "Aerospace & Defense": (None, "USD"),
    "Aerospace (equal weight)": (None, "USD"),
    "Defense (PPA)": (None, "USD"),
    "Transportation": ("WTI Crude Oil", "USD"),
    "Airlines": ("WTI Crude Oil", "USD"),
    "Autos": (None, "USD"),
    "Consumer Discretionary (S&P)": (None, "USD"),
    "Consumer Staples (S&P)": (None, "USD"),
    "Retail": (None, "USD"),
    "Online Retail": (None, "USD"),
    "Leisure & Entertainment": (None, "USD"),
    "Hotels": (None, "USD"),
    "Travel": (None, "USD"),
    "Real Estate (S&P)": (None, "USD"),
    "REITs (VNQ)": (None, "USD"),
    "U.S. REITs": (None, "USD"),
    "Residential REITs": (None, "USD"),
    "Communication Services": (None, "USD"),
    "Telecom & Media": (None, "USD"),
    "Esports": (None, "USD"),
    "Video Gaming": (None, "USD"),
    "Utilities (S&P)": ("Natural Gas", "USD"),
    "Utilities (VPU)": ("Natural Gas", "USD"),
    "Electric Grid": ("Copper", "USD"),
    "Materials (S&P)": ("Copper", "AUD"),
    "Global Materials": ("Copper", "AUD"),
    "Timber": ("Lumber", "CAD"),
    "Timber & Forestry": ("Lumber", "CAD")
}

# ------------------------------------------------------------
# CACHE & HELPERS
# ------------------------------------------------------------
historical_cache = {}

def get_historical(ticker, period='5y'):
    key = f"{ticker}_{period}"
    if key in historical_cache:
        return historical_cache[key]
    try:
        data = yf.download(ticker, period=period, progress=False)
        if data.empty:
            return None
        if 'Close' in data.columns:
            series = data['Close']
        elif 'Adj Close' in data.columns:
            series = data['Adj Close']
        else:
            series = data.iloc[:, 0]
        if isinstance(series, pd.DataFrame):
            series = series.squeeze()
        series = series.dropna().sort_index()
        if series.empty:
            return None
        historical_cache[key] = series
        return series
    except Exception:
        return None

def get_historical_gold_ratio(ticker):
    try:
        gold_hist = get_historical('GC=F')
        if gold_hist is None or gold_hist.empty:
            return None
        asset_hist = get_historical(ticker)
        if asset_hist is None or asset_hist.empty:
            return None
        common_dates = asset_hist.index.intersection(gold_hist.index)
        if len(common_dates) < 5:
            return None
        asset_aligned = asset_hist.loc[common_dates]
        gold_aligned = gold_hist.loc[common_dates]
        ratio_series = asset_aligned / gold_aligned
        if ratio_series.empty:
            return None
        current_ratio = ratio_series.iloc[-1]
        historical_mean = ratio_series.mean()
        if isinstance(historical_mean, pd.Series):
            historical_mean = historical_mean.iloc[0]
        if historical_mean == 0:
            return None
        deviation = (current_ratio - historical_mean) / historical_mean * 100
        return {
            'current_ratio': float(current_ratio),
            'historical_mean': float(historical_mean),
            'deviation': float(deviation)
        }
    except Exception:
        return None

def get_stock_metrics(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info or 'regularMarketPrice' not in info:
            return None
        pe = info.get('trailingPE') or info.get('forwardPE')
        pb = info.get('priceToBook')
        rec = info.get('recommendationKey', 'hold')
        insider = info.get('heldPercentInsiders', 0) * 100
        return {
            'pe': round(pe, 2) if pe else None,
            'pb': round(pb, 2) if pb else None,
            'rating': rec,
            'insider': round(insider, 2) if insider else None,
            'price': info.get('regularMarketPrice'),
            'name': info.get('shortName', ticker)
        }
    except:
        return None

def get_currency_rates():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json().get('rates', {})
    except:
        pass
    return {}

# ------------------------------------------------------------
# ENDPOINT: /api/dashboard
# ------------------------------------------------------------
@app.route('/api/dashboard')
def dashboard():
    sectors = []
    for sector_name, etf_ticker in SECTOR_ETFS.items():
        pe = None
        try:
            etf = yf.Ticker(etf_ticker)
            holdings = etf.funds_data.get('topHoldings', [])[:10]
            total_pe = 0
            count = 0
            for h in holdings:
                sym = h.get('symbol')
                if sym:
                    m = get_stock_metrics(sym)
                    if m and m.get('pe'):
                        total_pe += m['pe']
                        count += 1
            if count:
                pe = round(total_pe / count, 2)
        except:
            pass
        gold_info = get_historical_gold_ratio(etf_ticker)
        cheapness = gold_info['deviation'] if gold_info else None
        sectors.append({
            'sector': sector_name,
            'etf': etf_ticker,
            'avg_pe': pe,
            'cheapness': cheapness
        })
    sectors.sort(key=lambda x: x['cheapness'] if x['cheapness'] is not None else 999)

    rates = get_currency_rates()
    currencies = []
    for code, ticker in CURRENCY_TICKERS.items():
        if code == "USD":
            currencies.append({'code': code, 'name': CURRENCY_NAMES[code], 'rate_usd': 1.0, 'cheapness': 0})
            continue
        rate = rates.get(code)
        gold_info = get_historical_gold_ratio(ticker)
        cheapness = gold_info['deviation'] if gold_info else None
        currencies.append({'code': code, 'name': CURRENCY_NAMES.get(code, code), 'rate_usd': rate, 'cheapness': cheapness})
    currencies.sort(key=lambda x: x['cheapness'] if x['cheapness'] is not None else 999)

    commodities = []
    try:
        gold = yf.Ticker("GC=F")
        gold_price = gold.info.get('regularMarketPrice')
        if gold_price:
            for name, ticker in COMMODITY_TICKERS.items():
                try:
                    com = yf.Ticker(ticker)
                    price = com.info.get('regularMarketPrice')
                    if price:
                        ratio = price / gold_price if gold_price else None
                        gold_info = get_historical_gold_ratio(ticker)
                        cheapness = gold_info['deviation'] if gold_info else None
                        commodities.append({
                            'name': name,
                            'price': price,
                            'gold_ratio': ratio,
                            'cheapness': cheapness
                        })
                except:
                    pass
    except:
        pass
    commodities.sort(key=lambda x: x['cheapness'] if x['cheapness'] is not None else 999)

    return jsonify({'sectors': sectors, 'currencies': currencies, 'commodities': commodities})

# ------------------------------------------------------------
# ENDPOINT: /api/search
# ------------------------------------------------------------
@app.route('/api/search')
def search():
    query = request.args.get('q', '').strip().upper()
    if not query:
        return jsonify({'error': 'Query required'}), 400

    response = {
        'sectors': [], 'etfs': [], 'stocks': [],
        'currencies': [], 'commodities': [], 'recommendations': []
    }

    # Sectors
    for sector_name, etf_ticker in SECTOR_ETFS.items():
        if query in sector_name.upper() or query in etf_ticker:
            pe = None
            try:
                etf = yf.Ticker(etf_ticker)
                holdings = etf.funds_data.get('topHoldings', [])[:10]
                total_pe = 0
                count = 0
                for h in holdings:
                    sym = h.get('symbol')
                    if sym:
                        m = get_stock_metrics(sym)
                        if m and m.get('pe'):
                            total_pe += m['pe']
                            count += 1
                if count:
                    pe = round(total_pe / count, 2)
            except:
                pass
            response['sectors'].append({'name': sector_name, 'etf': etf_ticker, 'avg_pe': pe})

    # ETFs with holdings
    for sector_name, etf_ticker in SECTOR_ETFS.items():
        if query in etf_ticker or query in sector_name.upper():
            try:
                etf = yf.Ticker(etf_ticker)
                holdings = etf.funds_data.get('topHoldings', [])[:10]
                holdings_data = []
                for h in holdings:
                    sym = h.get('symbol')
                    if sym:
                        m = get_stock_metrics(sym)
                        if m:
                            m['ticker'] = sym
                            holdings_data.append(m)
                response['etfs'].append({
                    'ticker': etf_ticker,
                    'sector': sector_name,
                    'holdings': holdings_data
                })
            except:
                pass

    # Stocks (direct + watchlist)
    popular = ["AAPL","MSFT","GOOGL","AMZN","META","TSLA","NVDA","JPM","V","WMT",
               "JNJ","PG","UNH","HD","DIS","MA","BAC","XOM","CVX","PFE"]
    try:
        stock = yf.Ticker(query)
        info = stock.info
        if info and info.get('regularMarketPrice'):
            m = get_stock_metrics(query)
            if m:
                m['ticker'] = query
                response['stocks'].append(m)
    except:
        pass
    for t in popular:
        if query in t:
            m = get_stock_metrics(t)
            if m:
                m['ticker'] = t
                response['stocks'].append(m)

    # Currencies
    rates = get_currency_rates()
    for code, ticker in CURRENCY_TICKERS.items():
        if code == "USD":
            continue
        if query in code:
            rate = rates.get(code)
            response['currencies'].append({'code': code, 'name': CURRENCY_NAMES.get(code, code), 'rate_usd': rate})

    # Commodities
    try:
        gold = yf.Ticker("GC=F")
        gold_price = gold.info.get('regularMarketPrice')
        if gold_price:
            for name, ticker in COMMODITY_TICKERS.items():
                if query in name.upper() or query in ticker:
                    try:
                        com = yf.Ticker(ticker)
                        price = com.info.get('regularMarketPrice')
                        if price:
                            ratio = price / gold_price if gold_price else None
                            response['commodities'].append({
                                'name': name,
                                'price': price,
                                'gold_ratio': ratio
                            })
                    except:
                        pass
    except:
        pass

    # Recommendations (simple score)
    for stock in response['stocks']:
        score = 50
        m = stock
        if m.get('pe') and m['pe'] > 0:
            if m['pe'] < 10: score += 15
            elif m['pe'] < 15: score += 10
            elif m['pe'] < 20: score += 5
            else: score -= 10
        if m.get('pb') and m['pb'] > 0:
            if m['pb'] < 1: score += 15
            elif m['pb'] < 1.5: score += 10
            elif m['pb'] < 2: score += 5
            else: score -= 10
        insider = m.get('insider')
        if insider and insider > 5:
            score += 10
        elif insider and insider > 2:
            score += 5
        rating = m.get('rating', '').lower()
        if 'buy' in rating:
            score += 10
        elif 'sell' in rating:
            score -= 10
        score = max(0, min(100, score))
        response['recommendations'].append({
            'ticker': m['ticker'],
            'name': m.get('name', m['ticker']),
            'score': score,
            'metrics': m
        })
    response['recommendations'] = sorted(response['recommendations'], key=lambda x: x['score'], reverse=True)

    return jsonify(response)

# ------------------------------------------------------------
# ENDPOINT: /api/recommendations
# ------------------------------------------------------------
@app.route('/api/recommendations')
def recommendations():
    sector_cheapness = {}
    for sector_name, etf_ticker in SECTOR_ETFS.items():
        gold_info = get_historical_gold_ratio(etf_ticker)
        sector_cheapness[sector_name] = gold_info['deviation'] if gold_info else None
    commodity_cheapness = {}
    for com_name, ticker in COMMODITY_TICKERS.items():
        gold_info = get_historical_gold_ratio(ticker)
        commodity_cheapness[com_name] = gold_info['deviation'] if gold_info else None
    currency_cheapness = {}
    for code, ticker in CURRENCY_TICKERS.items():
        if code == "USD":
            currency_cheapness[code] = 0.0
            continue
        gold_info = get_historical_gold_ratio(ticker)
        currency_cheapness[code] = gold_info['deviation'] if gold_info else None

    results = []
    for sector_name, (com_key, curr_code) in CONVERGENCE_MAP.items():
        sec = sector_cheapness.get(sector_name)
        com = commodity_cheapness.get(com_key) if com_key else None
        cur = currency_cheapness.get(curr_code) if curr_code else None
        if sec is None:
            continue
        vals = [sec]
        if com is not None:
            vals.append(com)
        if cur is not None:
            vals.append(cur)
        if len(vals) < 2:
            continue
        avg = sum(vals) / len(vals)
        results.append({
            'sector': sector_name,
            'etf': SECTOR_ETFS[sector_name],
            'convergence_score': avg,
            'sector_cheapness': sec,
            'commodity': com_key,
            'commodity_cheapness': com,
            'currency': curr_code,
            'currency_cheapness': cur,
            'num_factors': len(vals)
        })
    results.sort(key=lambda x: x['convergence_score'])
    return jsonify(results)

# ------------------------------------------------------------
# RUN
# ------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)