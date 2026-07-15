import os
import pickle
import yfinance as yf
import pandas as pd

CACHE_FILE = 'cache.pkl'

# ------------------------------------------------------------

# FULL DICTIONARIES – copy exactly as in app.py

# ------------------------------------------------------------

SECTOR_ETFS = {
    # ---- Existing sectors (unchanged) ----
    "Energy (S&P)": "XLE",
    "Oil Exploration (E&P)": "XOP",
    "Oil Services": "OIH",
    "Oil Equipment": "IEZ",
    "Midstream Pipelines": "AMLP",
    "Natural Gas Producers": "FCG",
    "Refiners": "CRAK",
    "Uranium": "URA",
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
    "Timber & Forestry": "CUT",

    # ---- Foreign Country ETFs (from previous expansion) ----
    "Japan (EWJ)": "EWJ",
    "China (FXI)": "FXI",
    "Brazil (EWZ)": "EWZ",
    "India (INDA)": "INDA",
    "Emerging Markets (EEM)": "EEM",
    "Developed ex-US (EFA)": "EFA",
    "Europe (VGK)": "VGK",
    "Asia-Pacific (VPL)": "VPL",

    # ---- NEW Real Estate ETFs (as requested) ----
    "US Real Estate (VNQ)": "VNQ",          # (already exists as REITs (VNQ), but duplicate ok)
    "Global Real Estate (REET)": "REET",
    "Dow Jones REIT (IYR)": "IYR",          # already exists as U.S. REITs
    "Schwab REIT (SCHH)": "SCHH",
    "Homebuilders ETF": "ITB",              # already exists
    "Homebuilders ETF 2 (XHB)": "XHB",
    "Mortgage REIT ETF (REM)": "REM",
    "Timber ETF (WOOD)": "WOOD",            # already exists
    "Global Timber (CUT)": "CUT",           # already exists

    # ---- Additional Country ETFs (from your list) ----
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
"Eurozone (EZU)": "EZU",      # broad Eurozone, complement to VGK
"China A (KBA)": "KBA",       # alternative China exposure
"China (CNYA)": "CNYA",       # iShares China A
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
    # =========================
    # Precious Metals
    # =========================
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Platinum": "PL=F",
    "Palladium": "PA=F",

    # =========================
    # Base / Industrial Metals
    # =========================
    "Copper (COMEX)": "HG=F",

    # LME contracts (availability varies by Yahoo region/account)
    "Aluminum": "ALI=F",
    "Nickel": "NICKEL=F",
    "Zinc": "ZINC=F",
    "Lead": "LEAD=F",
    "Tin": "TIN=F",

    # Steel
    "Hot Rolled Coil Steel": "HRC=F",

    # Iron ore
    "Iron Ore 62%": "TIO=F",

    # =========================
    # Energy
    # =========================
    "WTI Crude Oil": "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Heating Oil": "HO=F",
    "RBOB Gasoline": "RB=F",

    # ICE Gas Oil
    "Low Sulfur Gasoil": "QS=F",

    # =========================
    # Agriculture - Grains
    # =========================
    "Corn": "ZC=F",
    "Wheat (Chicago)": "ZW=F",
    "Kansas Wheat": "KE=F",
    "Minneapolis Wheat": "MWE=F",

    "Soybeans": "ZS=F",
    "Soybean Meal": "ZM=F",
    "Soybean Oil": "ZL=F",

    "Oats": "ZO=F",
    "Rice": "ZR=F",

    # =========================
    # Soft Commodities
    # =========================
    "Coffee": "KC=F",
    "Sugar #11": "SB=F",
    "Cocoa": "CC=F",
    "Cotton": "CT=F",
    "Orange Juice": "OJ=F",

    # =========================
    # Livestock
    # =========================
    "Live Cattle": "LE=F",
    "Feeder Cattle": "GF=F",
    "Lean Hogs": "HE=F",

    # Dairy
    "Class III Milk": "DC=F",
    "Butter": "CB=F",
    "Cheese": "CSC=F",

    # Lumber
    "Lumber": "LBR=F",
}

# ------------------------------------------------------------
# DOWNLOAD FUNCTION (unchanged)
# ------------------------------------------------------------
def get_historical(ticker):
    try:
        data = yf.download(ticker, period='max', interval='1wk', progress=False, timeout=30)
        if data.empty:
            return None
        series = data['Close'] if 'Close' in data.columns else data.iloc[:, 0]
        if isinstance(series, pd.DataFrame):
            series = series.squeeze()
        series = series.dropna()
        return series if not series.empty else None
    except Exception as e:
        print(f"Error downloading {ticker}: {e}")
        return None

# ------------------------------------------------------------
# RATING FETCHER
# ------------------------------------------------------------
def get_etf_rating(ticker):
    """Return (rating_label, count) for an ETF."""
    try:
        etf = yf.Ticker(ticker)
        info = etf.info
        direct = info.get('recommendationKey')
        if direct in ['strong_buy', 'buy', 'hold', 'sell', 'strong_sell']:
            label = direct.replace('_', ' ').title()
            count = info.get('numberOfAnalystOpinions', 0)
            return label, count
    except:
        pass
    return None, None

# ------------------------------------------------------------
# BUILD CACHE (price + ratings)
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

# ---- Prices for all tickers ----
all_tickers = set(SECTOR_ETFS.values()) | set(CURRENCY_TICKERS.values()) | set(COMMODITY_TICKERS.values())
all_tickers.discard('USDUSD=X')

for ticker in all_tickers:
    print(f"Downloading price for {ticker}...")
    series = get_historical(ticker)
    if series is not None:
        cache[f'hist_{ticker}'] = {
            'data': series.values.tolist(),
            'index': series.index.strftime('%Y-%m-%d').tolist()
        }

# ---- Ratings for all ETFs (SECTOR_ETFS) ----
print("Fetching analyst ratings for ETFs...")
for sector_name, etf_ticker in SECTOR_ETFS.items():
    label, count = get_etf_rating(etf_ticker)
    if label:
        cache[f'rating_{etf_ticker}'] = {'label': label, 'count': count}
        print(f"  {etf_ticker}: {label} ({count} analysts)")
    else:
        print(f"  {etf_ticker}: N/A")

# Save cache
with open(CACHE_FILE, 'wb') as f:
    pickle.dump(cache, f)

print(f"Cache saved to {CACHE_FILE} with {len(cache)} entries.")
