import os
import pickle
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
# CACHE – ABSOLUTE PATH
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, 'cache.pkl')

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'rb') as f:
            return pickle.load(f)
    except:
        return {}

def save_cache(cache):
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)

def get_cached_historical(ticker):
    cache = load_cache()
    key = f'hist_{ticker}'
    if key not in cache:
        return None
    raw_data = cache[key]['data']
    raw_index = cache[key]['index']
    if isinstance(raw_data, list) and len(raw_data) > 0:
        if isinstance(raw_data[0], list):
            flat_data = [float(x) for sublist in raw_data for x in sublist]
        else:
            flat_data = [float(x) for x in raw_data]
    else:
        flat_data = [float(x) for x in raw_data] if raw_data else []
    if not flat_data:
        return None
    index = pd.to_datetime(raw_index)
    return pd.Series(flat_data, index=index)

def get_gold_ratio(ticker):
    cache = load_cache()
    key = f'gold_ratio_{ticker}'
    if key in cache:
        return cache[key]
    gold_series = get_cached_historical('GC=F')
    if gold_series is None or gold_series.empty:
        return None
    asset_series = get_cached_historical(ticker)
    if asset_series is None or asset_series.empty:
        return None
    common_dates = asset_series.index.intersection(gold_series.index)
    if len(common_dates) < 5:
        return None
    asset_aligned = asset_series.loc[common_dates]
    gold_aligned = gold_series.loc[common_dates]
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
    result = {
        'current_ratio': float(current_ratio),
        'historical_mean': float(historical_mean),
        'deviation': float(deviation)
    }
    cache[key] = result
    save_cache(cache)
    return result

def get_etf_sentiment(ticker):
    cache = load_cache()
    key = f'sentiment_{ticker}'
    if key in cache:
        data = cache[key]
        return data.get('label'), data.get('score')
    return None, None

def rating_bonus(label):
    bonuses = {
        'Strong Buy': 15,
        'Buy': 10,
        'Hold': 0,
        'Sell': -10,
        'Strong Sell': -15
    }
    return bonuses.get(label, 0)

# ------------------------------------------------------------
# LISTS (sectors, currencies, commodities) – cleaned & expanded
# ------------------------------------------------------------
SECTOR_ETFS = {
    # ---- Energy ----
    "Energy (S&P)": "XLE",
    "Oil Exploration (E&P)": "XOP",
    "Oil Services": "OIH",
    "Oil Equipment": "IEZ",
    "Midstream Pipelines": "AMLP",
    "Natural Gas Producers": "FCG",
    "Refiners": "CRAK",
    "Uranium": "URA",

    # ---- Metals & Mining ----
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

    # ---- Technology ----
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

    # ---- Financials ----
    "Financials (S&P)": "XLF",
    "Regional Banks": "KRE",
    "Banks": "KBE",
    "Insurance": "KIE",
    "Brokers": "IAI",
    "Financial Services": "IYG",

    # ---- Healthcare ----
    "Healthcare (S&P)": "XLV",
    "Biotech (equal weight)": "XBI",
    "Biotech (IBB)": "IBB",
    "Medical Devices": "IHI",
    "Pharmaceuticals": "PJP",

    # ---- Industrials ----
    "Industrials (S&P)": "XLI",
    "Infrastructure": "PAVE",
    "Aerospace & Defense": "ITA",
    "Aerospace (equal weight)": "XAR",
    "Defense (PPA)": "PPA",
    "Transportation": "IYT",
    "Airlines": "JETS",
    "Autos": "CARZ",

    # ---- Consumer ----
    "Consumer Discretionary (S&P)": "XLY",
    "Consumer Staples (S&P)": "XLP",
    "Retail": "XRT",
    "Online Retail": "IBUY",
    "Leisure & Entertainment": "PEJ",
    "Hotels": "BEDZ",
    "Travel": "AWAY",

    # ---- Real Estate (consolidated) ----
    "Real Estate (S&P)": "XLRE",
    "US REITs": "VNQ",
    "Residential REITs": "REZ",
    "Global Real Estate": "REET",
    "Homebuilders": "ITB",
    "Homebuilders 2": "XHB",
    "Mortgage REITs": "REM",

    # ---- Materials ----
    "Materials (S&P)": "XLB",
    "Global Materials": "MXI",
    "Timber & Forestry": "WOOD",
    "Timber 2": "CUT",

    # ---- Communications ----
    "Communication Services": "XLC",
    "Telecom & Media": "VOX",
    "Esports": "HERO",
    "Video Gaming": "ESPO",

    # ---- Utilities ----
    "Utilities (S&P)": "XLU",
    "Utilities (VPU)": "VPU",
    "Electric Grid": "GRID",

    # ---- Foreign Country ETFs ----
    "Japan (EWJ)": "EWJ",
    "China (FXI)": "FXI",
    "Brazil (EWZ)": "EWZ",
    "India (INDA)": "INDA",
    "Emerging Markets (EEM)": "EEM",
    "Developed ex-US (EFA)": "EFA",
    "Europe (VGK)": "VGK",
    "Asia-Pacific (VPL)": "VPL",

    # ---- Additional Country ETFs ----
    "UK (EWU)": "EWU",
    "Switzerland (EWL)": "EWL",
    "Canada (EWC)": "EWC",
    "Australia (EWA)": "EWA",
    "New Zealand (ENZL)": "ENZL",
    "Sweden (EWD)": "EWD",
    "Norway (ENOR)": "ENOR",
    "Denmark (EDEN)": "EDEN",
    "Hong Kong (EWH)": "EWH",
    "Singapore (EWS)": "EWS",
    "South Korea (EWY)": "EWY",
    "Taiwan (EWT)": "EWT",
    "Indonesia (EIDO)": "EIDO",
    "Thailand (THD)": "THD",
    "Malaysia (EWM)": "EWM",
    "Philippines (EPHE)": "EPHE",
    "Vietnam (VNM)": "VNM",
    "Poland (EPOL)": "EPOL",
    "Mexico (EWW)": "EWW",
    "Argentina (ARGT)": "ARGT",
    "Chile (ECH)": "ECH",
    "Peru (EPU)": "EPU",
    "Turkey (TUR)": "TUR",
    "Saudi Arabia (KSA)": "KSA",
    "South Africa (EZA)": "EZA",
    "UAE (UAE)": "UAE",
    "Qatar (QAT)": "QAT",
    "Kuwait (KWT)": "KWT",
    "Israel (EIS)": "EIS",
    "Eurozone (EZU)": "EZU",
    "China A (KBA)": "KBA",
    "China (CNYA)": "CNYA",

    # ---- NEW: Commodity ETFs ----
    "Broad Commodities": "DBC",
    "Commodities (DJP)": "DJP",
    "Oil (USO)": "USO",
    "Natural Gas (UNG)": "UNG",
    "Gold (GLD)": "GLD",
    "Silver (SLV)": "SLV",
    "Copper (CPER)": "CPER",
    "Platinum (PPLT)": "PPLT",
    "Palladium (PALL)": "PALL",
}

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

CURRENCY_TICKERS = {code: code + "USD=X" if code != "USD" else "USDUSD=X" for code in CURRENCY_NAMES}

COMMODITY_TICKERS = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Platinum": "PL=F",
    "Palladium": "PA=F",
    "Copper (COMEX)": "HG=F",
    "Aluminum": "ALI=F",
    "Hot Rolled Coil Steel": "HRC=F",
    "Iron Ore 62%": "TIO=F",
    "WTI Crude Oil": "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Heating Oil": "HO=F",
    "RBOB Gasoline": "RB=F",
    "Corn": "ZC=F",
    "Wheat (Chicago)": "ZW=F",
    "Kansas Wheat": "KE=F",
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
    "Live Cattle": "LE=F",
    "Feeder Cattle": "GF=F",
    "Lean Hogs": "HE=F",
    "Class III Milk": "DC=F",
    "Butter": "CB=F",
    "Cheese": "CSC=F",
    "Lumber": "LBR=F",
}

CONVERGENCE_MAP = {
    # ---- Energy ----
    "Energy (S&P)": ("WTI Crude Oil", "CAD"),
    "Oil Exploration (E&P)": ("WTI Crude Oil", "CAD"),
    "Oil Services": ("WTI Crude Oil", "CAD"),
    "Oil Equipment": ("WTI Crude Oil", "CAD"),
    "Midstream Pipelines": ("Natural Gas", "CAD"),
    "Natural Gas Producers": ("Natural Gas", "CAD"),
    "Refiners": ("WTI Crude Oil", "CAD"),
    "Uranium": (None, None),

    # ---- Metals & Mining ----
    "Metals & Mining": ("Copper (COMEX)", "AUD"),
    "Global Miners": ("Copper (COMEX)", "AUD"),
    "Copper Miners": ("Copper (COMEX)", "AUD"),
    "Silver Miners": ("Silver", "AUD"),
    "Junior Silver Miners": ("Silver", "AUD"),
    "Gold Miners": ("Gold", "AUD"),
    "Junior Gold Miners": ("Gold", "AUD"),
    "Junior Gold Explorers": ("Gold", "AUD"),
    "Rare Earths": (None, None),
    "Lithium": (None, None),
    "Battery Materials": ("Copper (COMEX)", "AUD"),
    "Steel": ("Hot Rolled Coil Steel", "USD"),

    # ---- Agriculture ----
    "Agriculture/Fertilizer": ("Corn", "USD"),

    # ---- Technology ----
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

    # ---- Financials ----
    "Financials (S&P)": (None, "USD"),
    "Regional Banks": (None, "USD"),
    "Banks": (None, "USD"),
    "Insurance": (None, "USD"),
    "Brokers": (None, "USD"),
    "Financial Services": (None, "USD"),

    # ---- Healthcare ----
    "Healthcare (S&P)": (None, "USD"),
    "Biotech (equal weight)": (None, "USD"),
    "Biotech (IBB)": (None, "USD"),
    "Medical Devices": (None, "USD"),
    "Pharmaceuticals": (None, "USD"),

    # ---- Industrials ----
    "Industrials (S&P)": (None, "USD"),
    "Infrastructure": ("Copper (COMEX)", "USD"),
    "Aerospace & Defense": (None, "USD"),
    "Aerospace (equal weight)": (None, "USD"),
    "Defense (PPA)": (None, "USD"),
    "Transportation": ("WTI Crude Oil", "USD"),
    "Airlines": ("WTI Crude Oil", "USD"),
    "Autos": (None, "USD"),

    # ---- Consumer ----
    "Consumer Discretionary (S&P)": (None, "USD"),
    "Consumer Staples (S&P)": (None, "USD"),
    "Retail": (None, "USD"),
    "Online Retail": (None, "USD"),
    "Leisure & Entertainment": (None, "USD"),
    "Hotels": (None, "USD"),
    "Travel": (None, "USD"),

    # ---- Real Estate (consolidated) ----
    "Real Estate (S&P)": (None, "USD"),
    "US REITs": ("Lumber", "USD"),
    "Residential REITs": ("Lumber", "USD"),
    "Global Real Estate": (None, "USD"),
    "Homebuilders": ("Lumber", "USD"),
    "Homebuilders 2": ("Lumber", "USD"),
    "Mortgage REITs": (None, "USD"),

    # ---- Materials ----
    "Materials (S&P)": ("Copper (COMEX)", "AUD"),
    "Global Materials": ("Copper (COMEX)", "AUD"),
    "Timber & Forestry": ("Lumber", "CAD"),
    "Timber 2": ("Lumber", "CAD"),

    # ---- Communications ----
    "Communication Services": (None, "USD"),
    "Telecom & Media": (None, "USD"),
    "Esports": (None, "USD"),
    "Video Gaming": (None, "USD"),

    # ---- Utilities ----
    "Utilities (S&P)": ("Natural Gas", "USD"),
    "Utilities (VPU)": ("Natural Gas", "USD"),
    "Electric Grid": ("Copper (COMEX)", "USD"),

    # ---- Country ETFs ----
    "Japan (EWJ)": ("WTI Crude Oil", "JPY"),
    "China (FXI)": ("Copper (COMEX)", "CNY"),
    "Brazil (EWZ)": ("Soybeans", "BRL"),
    "India (INDA)": ("WTI Crude Oil", "INR"),
    "Emerging Markets (EEM)": ("Copper (COMEX)", "USD"),
    "Developed ex-US (EFA)": ("WTI Crude Oil", "USD"),
    "Europe (VGK)": ("Natural Gas", "EUR"),
    "Asia-Pacific (VPL)": ("Copper (COMEX)", "USD"),
    "UK (EWU)": ("Brent Crude", "GBP"),
    "Switzerland (EWL)": ("Gold", "CHF"),
    "Canada (EWC)": ("WTI Crude Oil", "CAD"),
    "Australia (EWA)": ("Iron Ore 62%", "AUD"),
    "New Zealand (ENZL)": ("Class III Milk", "NZD"),
    "Sweden (EWD)": (None, "SEK"),
    "Norway (ENOR)": ("Brent Crude", "NOK"),
    "Denmark (EDEN)": (None, "DKK"),
    "Hong Kong (EWH)": (None, "HKD"),
    "Singapore (EWS)": (None, "SGD"),
    "South Korea (EWY)": ("Copper (COMEX)", "KRW"),
    "Taiwan (EWT)": ("Copper (COMEX)", "TWD"),
    "Indonesia (EIDO)": (None, "IDR"),
    "Thailand (THD)": ("Rice", "THB"),
    "Malaysia (EWM)": (None, "MYR"),
    "Philippines (EPHE)": (None, "PHP"),
    "Vietnam (VNM)": (None, "VND"),
    "Poland (EPOL)": (None, "PLN"),
    "Mexico (EWW)": ("WTI Crude Oil", "MXN"),
    "Argentina (ARGT)": ("Soybeans", "ARS"),
    "Chile (ECH)": ("Copper (COMEX)", "CLP"),
    "Peru (EPU)": ("Copper (COMEX)", "PEN"),
    "Turkey (TUR)": (None, "TRY"),
    "Saudi Arabia (KSA)": ("WTI Crude Oil", "SAR"),
    "South Africa (EZA)": ("Gold", "ZAR"),
    "UAE (UAE)": ("WTI Crude Oil", "AED"),
    "Qatar (QAT)": ("Natural Gas", "QAR"),
    "Kuwait (KWT)": ("WTI Crude Oil", "KWD"),
    "Israel (EIS)": (None, "ILS"),
    "Eurozone (EZU)": ("Natural Gas", "EUR"),
    "China A (KBA)": ("Copper (COMEX)", "CNY"),
    "China (CNYA)": ("Copper (COMEX)", "CNY"),

    # ---- NEW: Commodity ETFs ----
    "Broad Commodities": ("WTI Crude Oil", "USD"),
    "Commodities (DJP)": ("WTI Crude Oil", "USD"),
    "Oil (USO)": ("WTI Crude Oil", "USD"),
    "Natural Gas (UNG)": ("Natural Gas", "USD"),
    "Gold (GLD)": ("Gold", "USD"),
    "Silver (SLV)": ("Silver", "USD"),
    "Copper (CPER)": ("Copper (COMEX)", "USD"),
    "Platinum (PPLT)": ("Platinum", "USD"),
    "Palladium (PALL)": ("Palladium", "USD"),

    # ---- FRED series mappings ----
    "Lumber (PPI)": ("Lumber", "USD"),
    "Structural Steel (PPI)": ("Hot Rolled Coil Steel", "USD"),
    "Copper Wire (PPI)": ("Copper (COMEX)", "USD"),
    "Cass Freight Index": ("WTI Crude Oil", "USD"),
    "Farm Real Estate Value": ("Corn", "USD"),
    "Green Street Commercial Property Price Index": ("Lumber", "USD"),
}

# ------------------------------------------------------------
# FRED SERIES DICTIONARY (must match populate_cache.py)
# ------------------------------------------------------------
FRED_SERIES = {
    # ---- National House Prices ----
    "FHFA Purchase Only HPI (US)": "PONHPIM226S",
    "All-Transactions HPI (US)": "USSTHPI",
    "S&P Case-Shiller National": "CSUSHPISA",
    "S&P Case-Shiller 10-City": "SPCS10RSA",
    "S&P Case-Shiller 20-City": "SPCS20RSA",
    "Median Sales Price New Homes": "MSPUS",

    # ---- Commercial Real Estate ----
    "Green Street Commercial Property Price Index": "COMREPUSQ159N",
    "Commercial Real Estate Price Index": "QUSR628BIS",

    # ---- Farmland ----
    "Farm Real Estate Value": "FRBV",
    "Cropland Value": "CRLV",
    "Pastureland Value": "PTLV",

    # ---- Construction Materials (PPIs) ----
    "Lumber (PPI)": "WPU081",
    "Plywood (PPI)": "WPU082",
    "Millwork (PPI)": "WPU083",
    "Concrete Products (PPI)": "WPU133",
    "Ready-Mix Concrete (PPI)": "WPU132101",
    "Cement (PPI)": "WPU132201",
    "Gypsum Products (PPI)": "WPU136",
    "Flat Glass (PPI)": "WPU124",
    "Structural Steel (PPI)": "WPU10740514",
    "Copper Wire (PPI)": "WPU102501",
    "Plastic Pipe (PPI)": "WPU072",

    # ---- Metals PPIs ----
    "Iron & Steel (PPI)": "WPS101",
    "Steel Mill Products (PPI)": "WPU1017",
    "Copper (PPI)": "WPU102",
    "Aluminum (PPI)": "WPU103",
    "Nickel (PPI)": "WPU104",
    "Zinc (PPI)": "WPU105",
    "Lead (PPI)": "WPU106",

    # ---- Chemicals ----
    "Industrial Chemicals (PPI)": "WPU061",
    "Petrochemicals (PPI)": "WPU0613",
    "Nitrogen Fertilizer (PPI)": "WPU065201",
    "Phosphate Fertilizer (PPI)": "WPU065202",
    "Potash Fertilizer (PPI)": "WPU065203",

    # ---- Shipping / Freight ----
    "Cass Freight Index": "FRGSHPUSM649NCIS",
    "Rail Freight Carloads": "RAILFRTCARLOADS",
    "Truck Transportation PPI": "PCU484484",
    "Deep Sea Freight Transportation PPI": "PCU483111483111",

    # ---- IMF Commodity Spot Prices ----
    "Gold (IMF)": "PGOLDUSDM",
    "Silver (IMF)": "PSILVERUSDM",
    "Copper (IMF)": "PCOPPUSDM",
    "Aluminum (IMF)": "PALUMUSDM",
    "Nickel (IMF)": "PNICKUSDM",
    "Zinc (IMF)": "PZINCUSDM",
    "Lead (IMF)": "PLEADUSDM",
    "Tin (IMF)": "PTINUSDM",
    "Iron Ore (IMF)": "PIORECRUSDM",
    "WTI Crude (IMF)": "POILWTIUSDM",
    "Brent Crude (IMF)": "POILBREUSDM",
    "Henry Hub Gas (IMF)": "PNGASUSUSDM",
    "Coal (IMF)": "PCOALAUUSDM",
    "Corn (IMF)": "PMAIZMTUSDM",
    "Wheat (IMF)": "PWHEAMTUSDM",
    "Soybeans (IMF)": "PSOYBUSDM",
    "Cotton (IMF)": "PCOTTINDUSDM",
    "Coffee (IMF)": "PCOFFOTMUSDM",
    "Cocoa (IMF)": "PCOCOUSDM",
    "Sugar (IMF)": "PSUGAUSAUSDM",
}

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
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
# ENDPOINTS
# ------------------------------------------------------------
@app.route('/api/dashboard')
def dashboard():
    try:
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

            gold_info = get_gold_ratio(etf_ticker)
            cheapness = gold_info['deviation'] if gold_info else None
            sentiment_label, sentiment_score = get_etf_sentiment(etf_ticker)
            sectors.append({
                'sector': sector_name,
                'etf': etf_ticker,
                'avg_pe': pe,
                'cheapness': cheapness,
                'analyst_rating': sentiment_label if sentiment_label else 'N/A',
                'analysts': sentiment_score if sentiment_score is not None else 0
            })
        sectors.sort(key=lambda x: x['cheapness'] if x['cheapness'] is not None else 999)

        rates = get_currency_rates()
        currencies = []
        for code, ticker in CURRENCY_TICKERS.items():
            if code == "USD":
                currencies.append({'code': code, 'name': CURRENCY_NAMES[code], 'rate_usd': 1.0, 'cheapness': 0})
                continue
            rate = rates.get(code)
            gold_info = get_gold_ratio(ticker)
            cheapness = gold_info['deviation'] if gold_info else None
            currencies.append({'code': code, 'name': CURRENCY_NAMES.get(code, code), 'rate_usd': rate, 'cheapness': cheapness})
        currencies.sort(key=lambda x: x['cheapness'] if x['cheapness'] is not None else 999)

        # Commodities: use cached gold price
        commodities = []
        gold_series = get_cached_historical('GC=F')
        if gold_series is not None and not gold_series.empty:
            gold_price = gold_series.iloc[-1]
            for name, ticker in COMMODITY_TICKERS.items():
                try:
                    series = get_cached_historical(ticker)
                    if series is not None and not series.empty:
                        price = series.iloc[-1]
                        ratio = price / gold_price if gold_price else None
                        gold_info = get_gold_ratio(ticker)
                        cheapness = gold_info['deviation'] if gold_info else None
                        commodities.append({
                            'name': name,
                            'price': price,
                            'gold_ratio': ratio,
                            'cheapness': cheapness
                        })
                except:
                    pass
        commodities.sort(key=lambda x: x['cheapness'] if x['cheapness'] is not None else 999)

        return jsonify({'sectors': sectors, 'currencies': currencies, 'commodities': commodities})
    except Exception as e:
        print("Dashboard error:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search():
    try:
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

        # ETFs (with holdings)
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

        # Recommendations (simple scoring)
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
    except Exception as e:
        print("Search error:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommendations')
def recommendations():
    try:
        sector_cheapness = {}
        sector_sentiment = {}
        for sector_name, etf_ticker in SECTOR_ETFS.items():
            gold_info = get_gold_ratio(etf_ticker)
            sector_cheapness[sector_name] = gold_info['deviation'] if gold_info else None
            label, score = get_etf_sentiment(etf_ticker)
            sector_sentiment[sector_name] = (label, score)

        commodity_cheapness = {}
        for com_name, ticker in COMMODITY_TICKERS.items():
            gold_info = get_gold_ratio(ticker)
            commodity_cheapness[com_name] = gold_info['deviation'] if gold_info else None

        currency_cheapness = {}
        for code, ticker in CURRENCY_TICKERS.items():
            if code == "USD":
                currency_cheapness[code] = 0.0
                continue
            gold_info = get_gold_ratio(ticker)
            currency_cheapness[code] = gold_info['deviation'] if gold_info else None

        results = []
        for sector_name, (com_key, curr_code) in CONVERGENCE_MAP.items():
            sec = sector_cheapness.get(sector_name)
            if sec is None:
                continue
            com = commodity_cheapness.get(com_key) if com_key else None
            cur = currency_cheapness.get(curr_code) if curr_code else None
            vals = [sec]
            if com is not None:
                vals.append(com)
            if cur is not None:
                vals.append(cur)
            if len(vals) < 2:
                continue
            avg_cheapness = sum(vals) / len(vals)

            label, score = sector_sentiment.get(sector_name, (None, None))
            bonus = rating_bonus(label) if label else 0
            combined = avg_cheapness + bonus

            results.append({
                'sector': sector_name,
                'etf': SECTOR_ETFS[sector_name],
                'convergence_score': avg_cheapness,
                'combined_score': combined,
                'sector_cheapness': sec,
                'commodity': com_key,
                'commodity_cheapness': com,
                'currency': curr_code,
                'currency_cheapness': cur,
                'rating_bonus': bonus,
                'analyst_rating': label if label else 'N/A',
                'num_factors': len(vals)
            })
        results.sort(key=lambda x: x['combined_score'])
        return jsonify(results)
    except Exception as e:
        print("Recommendations error:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# ------------------------------------------------------------
# FIXED FRED ENDPOINT (direct cache reading)
# ------------------------------------------------------------
@app.route('/api/fred')
def get_fred():
    try:
        cache = load_cache()
        gold_key = 'hist_GC=F'
        if gold_key not in cache:
            return jsonify({'error': 'Gold data not in cache'}), 500
        gold_data = cache[gold_key]
        gold_series = pd.Series(gold_data['data'], index=pd.to_datetime(gold_data['index']))
        if gold_series.empty:
            return jsonify({'error': 'Gold series empty'}), 500

        # Resample gold to month start
        gold_monthly = gold_series.resample('MS').last().dropna()

        result = {}
        for name, series_id in FRED_SERIES.items():
            cache_key = f'hist_fred_{series_id}'
            if cache_key not in cache:
                continue

            fred_data = cache[cache_key]
            fred_series = pd.Series(fred_data['data'], index=pd.to_datetime(fred_data['index']))
            if fred_series.empty:
                continue

            # Resample FRED to month start
            fred_monthly = fred_series.resample('MS').last().dropna()
            if fred_monthly.empty:
                continue

            # Intersect indices
            common = fred_monthly.index.intersection(gold_monthly.index)
            if len(common) < 5:
                continue

            asset = fred_monthly.loc[common]
            gold = gold_monthly.loc[common]
            ratio = asset / gold
            current_ratio = ratio.iloc[-1]
            mean_ratio = ratio.mean()
            if mean_ratio == 0:
                continue

            deviation = (current_ratio - mean_ratio) / mean_ratio * 100
            result[name] = {
                'current_ratio': float(current_ratio),
                'mean_ratio': float(mean_ratio),
                'deviation': float(deviation),
                'last_value': float(asset.iloc[-1]),
            }

        return jsonify(result)
    except Exception as e:
        print("FRED error:", traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# ------------------------------------------------------------
# DEBUG ROUTE (optional) – to check cache keys
# ------------------------------------------------------------
@app.route('/api/debug')
def debug():
    cache = load_cache()
    keys = [k for k in cache.keys() if 'fred' in k or k == 'hist_GC=F']
    return jsonify({'cache_keys': keys[:20], 'total_keys': len(cache)})

@app.route('/api/debug_fred')
def debug_fred():
    cache = load_cache()
    gold_series = get_cached_historical('GC=F')
    gold_len = len(gold_series) if gold_series is not None else 0
    
    result = {}
    for name, series_id in FRED_SERIES.items():
        cache_key = f'hist_fred_{series_id}'
        has_key = cache_key in cache
        if has_key:
            # Try to reconstruct the series
            series = get_cached_historical(cache_key.replace('hist_', ''))
            series_len = len(series) if series is not None else 0
            if series is not None and gold_series is not None:
                common = series.index.intersection(gold_series.index)
                common_len = len(common)
            else:
                common_len = 0
            result[name] = {
                'cache_key': cache_key,
                'in_cache': has_key,
                'series_len': series_len,
                'gold_len': gold_len,
                'common_len': common_len
            }
        else:
            result[name] = {
                'cache_key': cache_key,
                'in_cache': False
            }
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
