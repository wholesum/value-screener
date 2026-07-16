import os
import pickle
import yfinance as yf
import pandas as pd
import requests  # <-- THIS WAS MISSING

CACHE_FILE = 'cache.pkl'

# ------------------------------------------------------------
# FRED API CONFIGURATION
# ------------------------------------------------------------
FRED_API_KEY = 'a5eb5a40ad542ffb9d13f6fb6269ca08'
FRED_BASE_URL = 'https://api.stlouisfed.org/fred/series/observations'

# ------------------------------------------------------------
# FULL DICTIONARIES – copy exactly as in app.py
# ------------------------------------------------------------
import os
import pickle
import yfinance as yf
import pandas as pd
import requests

CACHE_FILE = 'cache.pkl'

# ------------------------------------------------------------
# FRED API CONFIGURATION
# ------------------------------------------------------------
FRED_API_KEY = 'a5eb5a40ad542ffb9d13f6fb6269ca08'
FRED_BASE_URL = 'https://api.stlouisfed.org/fred/series/observations'

# ------------------------------------------------------------
# FULL DICTIONARIES – now cleaned and expanded
# ------------------------------------------------------------
SECTOR_ETFS = {
    # ---- Energy (existing) ----
    "Energy (S&P)": "XLE",
    "Oil Exploration (E&P)": "XOP",
    "Oil Services": "OIH",
    "Oil Equipment": "IEZ",
    "Midstream Pipelines": "AMLP",
    "Natural Gas Producers": "FCG",
    "Refiners": "CRAK",
    "Uranium": "URA",

    # ---- Metals & Mining (existing) ----
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

    # ---- Technology (unchanged) ----
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

    # ---- Financials (unchanged) ----
    "Financials (S&P)": "XLF",
    "Regional Banks": "KRE",
    "Banks": "KBE",
    "Insurance": "KIE",
    "Brokers": "IAI",
    "Financial Services": "IYG",

    # ---- Healthcare (unchanged) ----
    "Healthcare (S&P)": "XLV",
    "Biotech (equal weight)": "XBI",
    "Biotech (IBB)": "IBB",
    "Medical Devices": "IHI",
    "Pharmaceuticals": "PJP",

    # ---- Industrials (unchanged) ----
    "Industrials (S&P)": "XLI",
    "Infrastructure": "PAVE",
    "Aerospace & Defense": "ITA",
    "Aerospace (equal weight)": "XAR",
    "Defense (PPA)": "PPA",
    "Transportation": "IYT",
    "Airlines": "JETS",
    "Autos": "CARZ",

    # ---- Consumer (unchanged) ----
    "Consumer Discretionary (S&P)": "XLY",
    "Consumer Staples (S&P)": "XLP",
    "Retail": "XRT",
    "Online Retail": "IBUY",
    "Leisure & Entertainment": "PEJ",
    "Hotels": "BEDZ",
    "Travel": "AWAY",

    # ---- Real Estate (consolidated) ----
    "Real Estate (S&P)": "XLRE",
    "US REITs": "VNQ",           # merged VNQ and IYR? Keep VNQ as main
    "Residential REITs": "REZ",
    "Global Real Estate": "REET",
    "Homebuilders": "ITB",
    "Homebuilders 2": "XHB",
    "Mortgage REITs": "REM",

    # ---- Materials (added) ----
    "Materials (S&P)": "XLB",
    "Global Materials": "MXI",
    "Timber & Forestry": "WOOD",  # merged WOOD and CUT
    "Timber 2": "CUT",           # keep CUT separately if desired

    # ---- Communication (unchanged) ----
    "Communication Services": "XLC",
    "Telecom & Media": "VOX",
    "Esports": "HERO",
    "Video Gaming": "ESPO",

    # ---- Utilities (unchanged) ----
    "Utilities (S&P)": "XLU",
    "Utilities (VPU)": "VPU",
    "Electric Grid": "GRID",

    # ---- Foreign Country ETFs (unchanged) ----
    "Japan (EWJ)": "EWJ",
    "China (FXI)": "FXI",
    "Brazil (EWZ)": "EWZ",
    "India (INDA)": "INDA",
    "Emerging Markets (EEM)": "EEM",
    "Developed ex-US (EFA)": "EFA",
    "Europe (VGK)": "VGK",
    "Asia-Pacific (VPL)": "VPL",

    # ---- Additional Country ETFs (unchanged) ----
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

    # ---- NEW Commodity ETFs (added) ----
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

COMMODITY_TICKERS = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Platinum": "PL=F",
    "Palladium": "PA=F",
    "Copper (COMEX)": "HG=F",
    "Aluminum": "ALI=F",
    # Removed: Nickel, Zinc, Lead, Tin (delisted)
    "Hot Rolled Coil Steel": "HRC=F",
    "Iron Ore 62%": "TIO=F",
    "WTI Crude Oil": "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Heating Oil": "HO=F",
    "RBOB Gasoline": "RB=F",
    # Removed: Low Sulfur Gasoil (QS=F) – delisted
    "Corn": "ZC=F",
    "Wheat (Chicago)": "ZW=F",
    "Kansas Wheat": "KE=F",
    # Removed: Minneapolis Wheat (MWE=F) – delisted
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

# ------------------------------------------------------------
# FRED SERIES DICTIONARY
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
# DOWNLOAD & CACHE (unchanged)
# ------------------------------------------------------------
def get_historical(ticker, periods=['max', '10y', '5y']):
    for period in periods:
        try:
            data = yf.download(ticker, period=period, interval='1wk', progress=False, timeout=30)
            if not data.empty:
                series = data['Close'] if 'Close' in data.columns else data.iloc[:, 0]
                if isinstance(series, pd.DataFrame):
                    series = series.squeeze()
                series = series.dropna()
                if not series.empty:
                    return series
        except Exception as e:
            print(f"  {ticker} with {period} failed: {e}")
            continue
    return None


# ------------------------------------------------------------
# FRED DATA FETCHER
# ------------------------------------------------------------
def get_fred_series(series_id, frequency=None):
    """Fetch a FRED series and return a pandas Series."""
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'sort_order': 'asc',
        'units': 'lin',
    }
    if frequency:
        params['frequency'] = frequency
    try:
        response = requests.get(FRED_BASE_URL, params=params, timeout=30)
        if response.status_code != 200:
            print(f"FRED error for {series_id}: {response.status_code}")
            return None
        data = response.json()
        observations = data.get('observations', [])
        if not observations:
            print(f"No data for {series_id}")
            return None
        dates = [pd.to_datetime(obs['date']) for obs in observations]
        values = []
        for obs in observations:
            val = obs.get('value')
            if val == '.':
                values.append(None)
            else:
                try:
                    values.append(float(val))
                except:
                    values.append(None)
        series = pd.Series(values, index=dates).dropna()
        if series.empty:
            return None
        weekly = series.resample('W').last().dropna()
        return weekly
    except Exception as e:
        print(f"Error fetching FRED {series_id}: {e}")
        return None

# ------------------------------------------------------------
# COMPUTE SENTIMENT FROM PRICE SERIES (RSI + MA)
# ------------------------------------------------------------
def compute_sentiment(series):
    if series is None or len(series) < 52:
        return None, None

    ma52 = series.rolling(52).mean()
    if ma52.isna().iloc[-1]:
        return None, None

    last_price = series.iloc[-1]
    ma52_last = ma52.iloc[-1]
    pct_from_ma = (last_price - ma52_last) / ma52_last * 100

    delta = series.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_val = rsi.iloc[-1] if not rsi.isna().iloc[-1] else 50

    pct_scaled = max(-30, min(30, pct_from_ma)) / 30 * 70
    rsi_scaled = (rsi_val - 50) / 50 * 30
    score = pct_scaled + rsi_scaled
    score = max(-100, min(100, score))

    if score > 40:
        label = 'Strong Buy'
    elif score > 20:
        label = 'Buy'
    elif score > -20:
        label = 'Hold'
    elif score > -40:
        label = 'Sell'
    else:
        label = 'Strong Sell'

    return round(score, 1), label

# ------------------------------------------------------------
# BUILD CACHE (price history + sentiment + FRED)
# ------------------------------------------------------------
print("Downloading gold...")
gold_series = get_historical('GC=F')
if gold_series is None:
    print("ERROR: Could not get gold data. Aborting.")
    exit(1)

cache = {}
cache['hist_GC=F'] = {
    'data': gold_series.values.tolist(),
    'index': gold_series.index.strftime('%Y-%m-%d').tolist()
}

# Get all unique tickers
all_tickers = set(SECTOR_ETFS.values()) | set(CURRENCY_TICKERS.values()) | set(COMMODITY_TICKERS.values())
all_tickers.discard('USDUSD=X')

# Store price series for sentiment computation later
price_series = {}

for ticker in all_tickers:
    print(f"Downloading price for {ticker}...")
    series = get_historical(ticker)
    if series is not None:
        price_series[ticker] = series
        cache[f'hist_{ticker}'] = {
            'data': series.values.tolist(),
            'index': series.index.strftime('%Y-%m-%d').tolist()
        }

# ---- Fetch FRED data ----
print("Fetching FRED economic data...")
for name, series_id in FRED_SERIES.items():
    print(f"  {name} ({series_id})...")
    s = get_fred_series(series_id)  # no frequency specified
    if s is not None:
        cache[f'hist_fred_{series_id}'] = {
            'data': s.values.tolist(),
            'index': s.index.strftime('%Y-%m-%d').tolist()
        }

# ---- Compute sentiment for all tickers ----
print("Computing sentiment scores...")
for ticker, series in price_series.items():
    score, label = compute_sentiment(series)
    if label:
        cache[f'sentiment_{ticker}'] = {'score': score, 'label': label}
        print(f"  {ticker}: {label} (score: {score})")
    else:
        print(f"  {ticker}: N/A (insufficient data)")

# Save cache
with open(CACHE_FILE, 'wb') as f:
    pickle.dump(cache, f)

print(f"Cache saved to {CACHE_FILE} with {len(cache)} entries.")
