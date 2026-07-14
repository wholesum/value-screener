from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yfinance as yf
import requests
import pandas as pd
import traceback

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/')
def root():
    return send_from_directory('.', 'screener.html')

# ------------------------------------------------------------
# SECTOR ETFS (KOL removed)
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
    # "Coal": "KOL",  # removed – delisted
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
# CURRENCIES (unchanged – 58, all working)
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
# COMMODITIES – cleaned, only reliable symbols
# ------------------------------------------------------------
COMMODITY_TICKERS = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Platinum": "PL=F",
    "Palladium": "PA=F",
    "Copper": "HG=F",
    "Aluminum": "ALI=F",        # may work, keep
    # Removed: Nickel, Zinc, Lead, Tin (no data)
    "WTI Crude Oil": "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Heating Oil": "HO=F",
    "RBOB Gasoline": "RB=F",
    "Propane": "B0=F",
    "Corn": "ZC=F",
    "Wheat": "ZW=F",
    "Kansas Wheat": "KE=F",
    # Removed: Minneapolis Wheat (MWE=F) – no data
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
    "Cheese": "CSC=F"
    # Removed: Rubber (JRU=F) – no data
}

# ------------------------------------------------------------
# CONVERGENCE MAP (still valid – all referenced commodities exist)
# ------------------------------------------------------------
CONVERGENCE_MAP = {
    "Energy (S&P)": ("WTI Crude Oil", "CAD"),
    "Oil Exploration (E&P)": ("WTI Crude Oil", "CAD"),
    "Oil Services": ("WTI Crude Oil", "CAD"),
    "Oil Equipment": ("WTI Crude Oil", "CAD"),
    "Midstream Pipelines": ("Natural Gas", "CAD"),
    "Natural Gas Producers": ("Natural Gas", "CAD"),
    "Refiners": ("WTI Crude Oil", "CAD"),
    "Metals & Mining": ("Copper", "AUD"),
    "Global Miners": ("Copper", "AUD"),
    "Copper Miners": ("Copper", "AUD"),
    "Silver Miners": ("Silver", "AUD"),
    "Junior Silver Miners": ("Silver", "AUD"),
    "Gold Miners": ("Gold", "AUD"),
    "Junior Gold Miners": ("Gold", "AUD"),
    "Junior Gold Explorers": ("Gold", "AUD"),
    "Battery Materials": ("Copper", "AUD"),
    "Agriculture/Fertilizer": ("Corn", "USD"),
    "Infrastructure": ("Copper", "USD"),
    "Transportation": ("WTI Crude Oil", "USD"),
    "Airlines": ("WTI Crude Oil", "USD"),
    "Utilities (S&P)": ("Natural Gas", "USD"),
    "Utilities (VPU)": ("Natural Gas", "USD"),
    "Electric Grid": ("Copper", "USD"),
    "Materials (S&P)": ("Copper", "AUD"),
    "Global Materials": ("Copper", "AUD"),
    "Timber": ("Lumber", "CAD"),
    "Timber & Forestry": ("Lumber", "CAD")
}

# ------------------------------------------------------------
# Helpers (unchanged – same as before)
# ------------------------------------------------------------
historical_cache = {}

def get_historical(ticker, period='max', interval='1wk'):
    key = f"{ticker}_{period}_{interval}"
    if key in historical_cache:
        return historical_cache[key]
    try:
        data = yf.download(ticker, period='max', interval='1d', progress=False, timeout=15)
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
        weekly = series.resample('W').last().dropna()
        if weekly.empty:
            return None
        historical_cache[key] = weekly
        return weekly
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

https://value-screener-2.onrender.com