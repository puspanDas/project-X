from dotenv import load_dotenv
load_dotenv()

import json
import os
import re
from datetime import datetime, timezone

import httpx
import phonenumbers
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Phone Number Tracer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

# NumVerify API — free tier 100/month (sign up at numverify.com for free key)
# Set env var: NUMVERIFY_API_KEY=your_key_here
NUMVERIFY_URL = "http://apilayer.net/api/validate"
NUMVERIFY_KEY = os.environ.get("NUMVERIFY_API_KEY", "")

# ---------------------------------------------------------------------------
# Country code -> name mapping (covers most used codes)
# ---------------------------------------------------------------------------
COUNTRY_MAP = {
    "AF": "Afghanistan", "AL": "Albania", "DZ": "Algeria", "AD": "Andorra",
    "AO": "Angola", "AR": "Argentina", "AM": "Armenia", "AU": "Australia",
    "AT": "Austria", "AZ": "Azerbaijan", "BH": "Bahrain", "BD": "Bangladesh",
    "BY": "Belarus", "BE": "Belgium", "BZ": "Belize", "BJ": "Benin",
    "BT": "Bhutan", "BO": "Bolivia", "BA": "Bosnia and Herzegovina",
    "BW": "Botswana", "BR": "Brazil", "BN": "Brunei", "BG": "Bulgaria",
    "BF": "Burkina Faso", "BI": "Burundi", "KH": "Cambodia", "CM": "Cameroon",
    "CA": "Canada", "CF": "Central African Republic", "TD": "Chad",
    "CL": "Chile", "CN": "China", "CO": "Colombia", "KM": "Comoros",
    "CG": "Congo", "CR": "Costa Rica", "HR": "Croatia", "CU": "Cuba",
    "CY": "Cyprus", "CZ": "Czech Republic", "DK": "Denmark", "DJ": "Djibouti",
    "DO": "Dominican Republic", "EC": "Ecuador", "EG": "Egypt",
    "SV": "El Salvador", "EE": "Estonia", "ET": "Ethiopia", "FI": "Finland",
    "FR": "France", "GA": "Gabon", "GM": "Gambia", "GE": "Georgia",
    "DE": "Germany", "GH": "Ghana", "GR": "Greece", "GT": "Guatemala",
    "GN": "Guinea", "GY": "Guyana", "HT": "Haiti", "HN": "Honduras",
    "HK": "Hong Kong", "HU": "Hungary", "IS": "Iceland", "IN": "India",
    "ID": "Indonesia", "IR": "Iran", "IQ": "Iraq", "IE": "Ireland",
    "IL": "Israel", "IT": "Italy", "JM": "Jamaica", "JP": "Japan",
    "JO": "Jordan", "KZ": "Kazakhstan", "KE": "Kenya", "KW": "Kuwait",
    "KG": "Kyrgyzstan", "LA": "Laos", "LV": "Latvia", "LB": "Lebanon",
    "LY": "Libya", "LT": "Lithuania", "LU": "Luxembourg", "MK": "North Macedonia",
    "MG": "Madagascar", "MW": "Malawi", "MY": "Malaysia", "MV": "Maldives",
    "ML": "Mali", "MT": "Malta", "MX": "Mexico", "MD": "Moldova",
    "MC": "Monaco", "MN": "Mongolia", "ME": "Montenegro", "MA": "Morocco",
    "MZ": "Mozambique", "MM": "Myanmar", "NA": "Namibia", "NP": "Nepal",
    "NL": "Netherlands", "NZ": "New Zealand", "NI": "Nicaragua", "NE": "Niger",
    "NG": "Nigeria", "NO": "Norway", "OM": "Oman", "PK": "Pakistan",
    "PA": "Panama", "PY": "Paraguay", "PE": "Peru", "PH": "Philippines",
    "PL": "Poland", "PT": "Portugal", "QA": "Qatar", "RO": "Romania",
    "RU": "Russia", "RW": "Rwanda", "SA": "Saudi Arabia", "SN": "Senegal",
    "RS": "Serbia", "SG": "Singapore", "SK": "Slovakia", "SI": "Slovenia",
    "SO": "Somalia", "ZA": "South Africa", "KR": "South Korea",
    "SS": "South Sudan", "ES": "Spain", "LK": "Sri Lanka", "SD": "Sudan",
    "SE": "Sweden", "CH": "Switzerland", "SY": "Syria", "TW": "Taiwan",
    "TJ": "Tajikistan", "TZ": "Tanzania", "TH": "Thailand", "TG": "Togo",
    "TT": "Trinidad and Tobago", "TN": "Tunisia", "TR": "Turkey",
    "TM": "Turkmenistan", "UG": "Uganda", "UA": "Ukraine",
    "AE": "United Arab Emirates", "GB": "United Kingdom",
    "US": "United States", "UY": "Uruguay", "UZ": "Uzbekistan",
    "VE": "Venezuela", "VN": "Vietnam", "YE": "Yemen", "ZM": "Zambia",
    "ZW": "Zimbabwe",
}

# Country code -> flag emoji
def country_flag(code: str) -> str:
    if not code or len(code) != 2:
        return "🌍"
    return chr(0x1F1E6 + ord(code[0].upper()) - ord('A')) + chr(0x1F1E6 + ord(code[1].upper()) - ord('A'))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_json(path: str) -> list:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_json(path: str, data: list):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_carrier_name(pn) -> str:
    """Get carrier from phonenumbers lib."""
    from phonenumbers import carrier
    name = carrier.name_for_number(pn, "en")
    return name if name else "Unknown"


def get_timezone(pn) -> list:
    from phonenumbers import timezone as tz
    zones = tz.time_zones_for_number(pn)
    return list(zones) if zones else []


def get_location(pn) -> str:
    from phonenumbers import geocoder
    loc = geocoder.description_for_number(pn, "en")
    return loc if loc else "Unknown"


def get_number_type_label(pn) -> str:
    ntype = phonenumbers.number_type(pn)
    type_map = {
        phonenumbers.PhoneNumberType.MOBILE: "Mobile",
        phonenumbers.PhoneNumberType.FIXED_LINE: "Landline",
        phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "Landline/Mobile",
        phonenumbers.PhoneNumberType.TOLL_FREE: "Toll-Free",
        phonenumbers.PhoneNumberType.PREMIUM_RATE: "Premium Rate",
        phonenumbers.PhoneNumberType.VOIP: "VoIP",
        phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "Personal",
        phonenumbers.PhoneNumberType.PAGER: "Pager",
        phonenumbers.PhoneNumberType.UAN: "UAN",
        phonenumbers.PhoneNumberType.SHARED_COST: "Shared Cost",
    }
    return type_map.get(ntype, "Unknown")


async def get_live_carrier_data(phone_number: str) -> dict | None:
    """Call NumVerify API for enhanced carrier data.
    Free tier: 100 lookups/month. Sign up at numverify.com.
    """
    if not NUMVERIFY_KEY:
        return None
    try:
        # Remove + prefix for NumVerify
        clean_number = phone_number.lstrip("+")
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(NUMVERIFY_URL, params={
                "access_key": NUMVERIFY_KEY,
                "number": clean_number,
            })
            if resp.status_code == 200:
                data = resp.json()
                if data.get("valid"):
                    return data
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/trace")
async def trace_number(number: str = Query(..., description="Phone number to trace (with country code, e.g. +14158586273)")):
    """Trace a phone number — validate, get carrier/country/type, check spam reports."""

    # Clean input
    raw = number.strip()
    if not raw.startswith("+"):
        raw = "+" + raw

    # Parse with phonenumbers
    try:
        pn = phonenumbers.parse(raw, None)
    except phonenumbers.NumberParseException:
        raise HTTPException(status_code=400, detail="Invalid phone number format. Include country code, e.g. +14158586273")

    is_valid = phonenumbers.is_valid_number(pn)
    is_possible = phonenumbers.is_possible_number(pn)
    country_code = phonenumbers.region_code_for_number(pn)
    country_name = COUNTRY_MAP.get(country_code, country_code or "Unknown")
    flag = country_flag(country_code)
    formatted_intl = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    formatted_national = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.NATIONAL)

    # Offline data from phonenumbers library (original carrier — may not reflect MNP)
    offline_carrier = get_carrier_name(pn)
    location = get_location(pn)
    timezones = get_timezone(pn)
    line_type = get_number_type_label(pn)

    # Try NumVerify API for accurate current carrier
    carrier_name = offline_carrier
    carrier_source = "offline"
    live_data = await get_live_carrier_data(raw)
    if live_data:
        live_carrier = live_data.get("carrier", "").strip()
        if live_carrier:
            carrier_name = live_carrier
            carrier_source = "live"
        live_type = live_data.get("line_type", "").strip()
        if live_type:
            line_type = live_type.capitalize()

    # Check community reports
    reports = load_json(REPORTS_FILE)
    # Normalize number for matching
    normalized = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
    matching_reports = [r for r in reports if r.get("number") == normalized]

    result = {
        "number": raw,
        "formatted_international": formatted_intl,
        "formatted_national": formatted_national,
        "e164": normalized,
        "valid": is_valid,
        "possible": is_possible,
        "country_code": country_code,
        "country_name": country_name,
        "flag": flag,
        "location": location,
        "carrier": carrier_name,
        "original_carrier": offline_carrier,
        "carrier_source": carrier_source,  # "live" = Veriphone, "offline" = phonenumbers lib
        "line_type": line_type,
        "timezones": timezones,
        "spam_reports": len(matching_reports),
        "reports": matching_reports[-5:],  # last 5
    }

    # Save to history
    history = load_json(HISTORY_FILE)
    history.insert(0, {
        "number": normalized,
        "formatted": formatted_intl,
        "country": country_name,
        "flag": flag,
        "carrier": carrier_name,
        "line_type": line_type,
        "location": location,
        "valid": is_valid,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    history = history[:50]  # keep last 50
    save_json(HISTORY_FILE, history)

    return result


class ReportRequest(BaseModel):
    number: str
    type: str  # spam, scam, fraud, telemarketer, robocall, other
    description: str = ""


@app.post("/api/report")
async def report_number(req: ReportRequest):
    """Submit a spam/scam report for a number."""
    raw = req.number.strip()
    if not raw.startswith("+"):
        raw = "+" + raw

    try:
        pn = phonenumbers.parse(raw, None)
    except phonenumbers.NumberParseException:
        raise HTTPException(status_code=400, detail="Invalid phone number format.")

    normalized = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)

    reports = load_json(REPORTS_FILE)
    reports.append({
        "number": normalized,
        "type": req.type,
        "description": req.description,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    save_json(REPORTS_FILE, reports)

    return {"message": "Report submitted successfully", "total_reports_for_number": len([r for r in reports if r["number"] == normalized])}


@app.get("/api/recent")
async def recent_lookups():
    """Get recent lookup history."""
    history = load_json(HISTORY_FILE)
    return history[:20]


# ---------------------------------------------------------------------------
# AI-Powered Endpoints
# ---------------------------------------------------------------------------
from ai_service import analyze_number as ai_analyze, chat as ai_chat, get_llm_status


class AIAnalyzeRequest(BaseModel):
    trace_data: dict


class AIChatRequest(BaseModel):
    message: str
    history: list = []


@app.post("/api/ai/analyze")
async def ai_analyze_endpoint(req: AIAnalyzeRequest):
    """AI-powered threat analysis for a traced phone number."""
    trace_data = req.trace_data

    # Fetch matching reports for deeper analysis
    reports = load_json(REPORTS_FILE)
    e164 = trace_data.get("e164", "")
    matching_reports = [r for r in reports if r.get("number") == e164] if e164 else []

    result = ai_analyze(trace_data, matching_reports)
    return result


@app.post("/api/ai/chat")
async def ai_chat_endpoint(req: AIChatRequest):
    """AI safety chatbot — ask questions about phone scams, safety tips, etc."""
    result = ai_chat(req.message, req.history)
    return result


@app.get("/api/ai/status")
async def ai_model_status():
    """Check the current LLM model status."""
    return get_llm_status()


@app.get("/api/health")
async def health():
    return {"status": "ok"}
