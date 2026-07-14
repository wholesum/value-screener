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

    # ---- New: Foreign Country ETFs ----
    "Japan (EWJ)": "EWJ",
    "China (FXI)": "FXI",
    "Brazil (EWZ)": "EWZ",
    "India (INDA)": "INDA",
    "Emerging Markets (EEM)": "EEM",
    "Developed ex-US (EFA)": "EFA",
    "Europe (VGK)": "VGK",
    "Asia-Pacific (VPL)": "VPL",

    # ---- New: Real Estate / Homebuilders ----
    "Homebuilders": "ITB"
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
    # Precious metals
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Platinum": "PL=F",
    "Palladium": "PA=F",

    # Base / industrial metals (re‑added)
    "Copper": "HG=F",
    "Aluminum": "ALI=F",
    "Nickel": "NICKEL=F",
    "Zinc": "ZINC=F",
    "Lead": "LEAD=F",
    "Tin": "TIN=F",

    # Energy
    "WTI Crude Oil": "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Heating Oil": "HO=F",
    "RBOB Gasoline": "RB=F",
    "Propane": "B0=F",

    # Grains
    "Corn": "ZC=F",
    "Wheat": "ZW=F",
    "Kansas Wheat": "KE=F",
    "Soybeans": "ZS=F",
    "Soybean Meal": "ZM=F",
    "Soybean Oil": "ZL=F",
    "Oats": "ZO=F",
    "Rice": "ZR=F",

    # Softs
    "Coffee": "KC=F",
    "Sugar #11": "SB=F",
    "Cocoa": "CC=F",
    "Cotton": "CT=F",
    "Orange Juice": "OJ=F",

    # Livestock & dairy
    "Lumber": "LBR=F",
    "Live Cattle": "LE=F",
    "Feeder Cattle": "GF=F",
    "Lean Hogs": "HE=F",
    "Class III Milk": "DC=F",
    "Butter": "CB=F",
    "Cheese": "CSC=F"
}

# ------------------------------------------------------------

# DOWNLOAD FUNCTION

# ------------------------------------------------------------

def get_historical(ticker):

    try:

        data = yf.download(ticker, period='5y', interval='1d', progress=False, timeout=30)

        if data.empty:

            return None

        series = data['Close'] if 'Close' in data.columns else data.iloc[:, 0]

        weekly = series.resample('W').last().dropna()

        return weekly if not weekly.empty else None

    except Exception as e:

        print(f"Error downloading {ticker}: {e}")

        return None

# ------------------------------------------------------------

# BUILD CACHE

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

all_tickers.discard('USDUSD=X')  # skip dummy

for ticker in all_tickers:

    print(f"Downloading {ticker}...")

    series = get_historical(ticker)

    if series is not None:

        cache[f'hist_{ticker}'] = {

            'data': series.values.tolist(),

            'index': series.index.strftime('%Y-%m-%d').tolist()

        }

with open(CACHE_FILE, 'wb') as f:

    pickle.dump(cache, f)

print(f"Cache saved to {CACHE_FILE} with {len(cache)} entries.")
 
