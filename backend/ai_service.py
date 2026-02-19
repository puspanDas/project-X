"""
AI Service — Hybrid: Local LLM (Qwen2.5-0.5B) + Rule-based fallback.
Auto-downloads a ~400MB GGUF model on first use. Runs 100% offline after that.
No API keys needed.
"""

import os
import re
import json
import threading
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# LLM Setup — Lazy-loaded, thread-safe
# ---------------------------------------------------------------------------
_llm = None
_llm_lock = threading.Lock()
_llm_status = {"state": "not_loaded", "error": None, "model_name": None}

MODEL_REPO = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
MODEL_FILE = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")


def get_llm_status() -> dict:
    """Return current LLM status."""
    return dict(_llm_status)


def _download_model() -> str:
    """Download the GGUF model if not present. Returns path to model file."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    local_path = os.path.join(MODEL_DIR, MODEL_FILE)

    if os.path.exists(local_path):
        return local_path

    _llm_status["state"] = "downloading"
    print(f"[AI] Downloading {MODEL_FILE} from {MODEL_REPO}...")
    print(f"[AI] This is a one-time ~400MB download. Please wait...")

    from huggingface_hub import hf_hub_download
    path = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=MODEL_FILE,
        local_dir=MODEL_DIR,
        local_dir_use_symlinks=False,
    )
    print(f"[AI] Model downloaded to: {path}")
    return path


def _load_llm():
    """Load the LLM model. Called lazily on first AI request."""
    global _llm
    with _llm_lock:
        if _llm is not None:
            return _llm

        try:
            model_path = _download_model()
            _llm_status["state"] = "loading"
            print(f"[AI] Loading model into memory...")

            from llama_cpp import Llama
            _llm = Llama(
                model_path=model_path,
                n_ctx=2048,        # Context window
                n_threads=4,       # CPU threads
                n_gpu_layers=0,    # CPU only
                verbose=False,
            )
            _llm_status["state"] = "ready"
            _llm_status["model_name"] = MODEL_FILE
            print(f"[AI] ✅ Model loaded! (~500MB RAM)")
            return _llm

        except Exception as e:
            _llm_status["state"] = "error"
            _llm_status["error"] = str(e)
            print(f"[AI] ⚠️ Failed to load LLM: {e}")
            print(f"[AI] Falling back to rule-based engine.")
            return None


def _llm_generate(system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str | None:
    """Generate text using the local LLM. Returns None if LLM unavailable."""
    llm = _load_llm()
    if llm is None:
        return None

    try:
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[AI] LLM generation error: {e}")
        return None


# ---------------------------------------------------------------------------
# Country risk tiers (based on known telecom fraud hotspots)
# ---------------------------------------------------------------------------
HIGH_RISK_COUNTRIES = {
    "NG", "GH", "CI", "CM", "SN",  # West Africa
    "PK", "BD", "IN",              # South Asia (high volume)
    "RU", "UA",                     # Eastern Europe
    "PH", "ID",                     # SE Asia
}

MEDIUM_RISK_COUNTRIES = {
    "CN", "BR", "MX", "CO", "VE",  # Latin America / East Asia
    "EG", "DZ", "MA", "TN",        # North Africa
    "TR", "IR", "IQ",              # Middle East
    "RO", "BG", "AL",             # Balkans
}

# ---------------------------------------------------------------------------
# Threat keywords in report descriptions
# ---------------------------------------------------------------------------
SEVERE_KEYWORDS = [
    "bank", "account", "password", "ssn", "social security", "irs", "fbi",
    "arrest", "warrant", "court", "wire transfer", "bitcoin", "crypto",
    "gift card", "western union", "moneygram", "ransom", "blackmail",
    "threaten", "kidnap", "extort",
]

MODERATE_KEYWORDS = [
    "spam", "robot", "automated", "recording", "press 1", "free",
    "winner", "congratulations", "prize", "vacation", "offer",
    "insurance", "warranty", "extend", "solar", "energy",
    "debt", "loan", "credit", "rate", "lower",
]

# ---------------------------------------------------------------------------
# Report type severity weights
# ---------------------------------------------------------------------------
REPORT_SEVERITY = {
    "fraud": 30,
    "scam": 28,
    "phishing": 25,
    "harassment": 20,
    "robocall": 12,
    "telemarketer": 10,
    "spam": 8,
    "other": 5,
}


def analyze_number(trace_data: dict, reports: list) -> dict:
    """
    Hybrid AI analysis: rule-based scoring + LLM-generated insights.
    """
    score = 0
    factors = []

    # --- Factor 1: Community reports (0-35 points) ---
    spam_count = trace_data.get("spam_reports", 0)
    if spam_count >= 10:
        score += 35
        factors.append(f"Extremely high report volume ({spam_count} reports)")
    elif spam_count >= 5:
        score += 25
        factors.append(f"High number of community reports ({spam_count})")
    elif spam_count >= 2:
        score += 15
        factors.append(f"Multiple community reports ({spam_count})")
    elif spam_count == 1:
        score += 8
        factors.append("1 community report filed")

    report_type_scores = 0
    for r in reports:
        rtype = r.get("type", "other").lower()
        report_type_scores += REPORT_SEVERITY.get(rtype, 5)
        desc = r.get("description", "").lower()
        for kw in SEVERE_KEYWORDS:
            if kw in desc:
                score += 5
                factors.append(f"Severe keyword detected: '{kw}' in report")
                break
        for kw in MODERATE_KEYWORDS:
            if kw in desc:
                score += 2
                break

    if report_type_scores > 0:
        score += min(report_type_scores, 20)

    # --- Factor 2: Number validity (0-15 points) ---
    if not trace_data.get("valid", True):
        score += 15
        factors.append("Number flagged as invalid/not active")
    elif not trace_data.get("possible", True):
        score += 10
        factors.append("Number format is not possible for this region")

    # --- Factor 3: Line type analysis (0-15 points) ---
    line_type = (trace_data.get("line_type") or "").lower()
    if line_type == "voip":
        score += 15
        factors.append("VoIP number — commonly used for spoofing and scam calls")
    elif line_type == "premium rate":
        score += 12
        factors.append("Premium rate number — may incur unexpected charges")
    elif line_type == "toll-free":
        score += 5
        factors.append("Toll-free number — sometimes used by telemarketers")
    elif "landline" in line_type:
        score -= 3
        factors.append("Landline number — generally lower risk")

    # --- Factor 4: Country risk (0-15 points) ---
    country_code = trace_data.get("country_code", "")
    if country_code in HIGH_RISK_COUNTRIES:
        score += 15
        factors.append(f"Originates from high-risk telecom fraud region ({trace_data.get('country_name', country_code)})")
    elif country_code in MEDIUM_RISK_COUNTRIES:
        score += 8
        factors.append(f"Originates from medium-risk region ({trace_data.get('country_name', country_code)})")
    else:
        factors.append(f"Country risk: normal ({trace_data.get('country_name', 'Unknown')})")

    # --- Factor 5: Carrier analysis (0-10 points) ---
    carrier = (trace_data.get("carrier") or "").lower()
    if carrier == "unknown" or not carrier:
        score += 10
        factors.append("Carrier is unknown — may indicate a virtual or disposable number")
    elif "virtual" in carrier or "voip" in carrier or "internet" in carrier:
        score += 8
        factors.append(f"Virtual/internet-based carrier detected: {trace_data.get('carrier')}")

    # --- Factor 6: Number porting (0-5 points) ---
    original = trace_data.get("original_carrier", "")
    current = trace_data.get("carrier", "")
    if original and current and original != current and current.lower() != "unknown":
        score += 5
        factors.append(f"Number was ported from {original} to {current}")

    # Clamp
    score = max(0, min(100, score))

    # Risk level
    if score >= 70:
        risk_level = "Critical"
    elif score >= 45:
        risk_level = "High"
    elif score >= 25:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    threat_type = _determine_threat_type(trace_data, reports, score)

    # --- Try LLM for analysis + recommendation ---
    llm_analysis = None
    llm_recommendation = None

    llm_prompt = (
        f"Phone number: {trace_data.get('formatted_international', 'Unknown')}\n"
        f"Country: {trace_data.get('country_name', 'Unknown')}\n"
        f"Carrier: {trace_data.get('carrier', 'Unknown')}\n"
        f"Line type: {trace_data.get('line_type', 'Unknown')}\n"
        f"Valid: {trace_data.get('valid', 'Unknown')}\n"
        f"Risk score: {score}/100 ({risk_level})\n"
        f"Threat type: {threat_type}\n"
        f"Spam reports: {spam_count}\n"
        f"Risk factors: {'; '.join(factors[:4])}\n\n"
        f"Write a 2-3 sentence security analysis of this phone number, "
        f"followed by a specific safety recommendation. Be concise."
    )

    llm_result = _llm_generate(
        system_prompt=(
            "You are a phone security analyst. Analyze the phone number data and provide "
            "a brief, actionable security assessment. Be direct and helpful. "
            "Write in plain language, not technical jargon."
        ),
        user_prompt=llm_prompt,
        max_tokens=200,
    )

    if llm_result:
        # Split LLM output into analysis and recommendation
        parts = llm_result.split("\n\n", 1)
        llm_analysis = parts[0].strip()
        llm_recommendation = parts[1].strip() if len(parts) > 1 else None

    # Use LLM output or fallback to rule-based
    analysis = llm_analysis or _generate_analysis(trace_data, factors, risk_level, score)
    recommendation = llm_recommendation or _generate_recommendation(risk_level, threat_type, trace_data)

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "threat_type": threat_type,
        "factors": factors[:6],
        "analysis": analysis,
        "recommendation": recommendation,
        "ai_source": "llm" if llm_analysis else "rule-based",
        "model": MODEL_FILE if llm_analysis else None,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


def _determine_threat_type(trace_data: dict, reports: list, score: int) -> str:
    report_types = [r.get("type", "").lower() for r in reports]
    if "fraud" in report_types or "phishing" in report_types:
        return "Fraud / Phishing"
    if "scam" in report_types:
        return "Scam"
    if "harassment" in report_types:
        return "Harassment"
    if "robocall" in report_types or "telemarketer" in report_types:
        return "Telemarketing"
    if "spam" in report_types:
        return "Spam"
    line_type = (trace_data.get("line_type") or "").lower()
    if line_type == "voip" and score >= 30:
        return "Suspicious VoIP"
    if line_type == "premium rate":
        return "Premium Rate"
    if score >= 45:
        return "Suspicious"
    if score >= 25:
        return "Potentially Unwanted"
    return "Clean"


def _generate_analysis(trace_data: dict, factors: list, risk_level: str, score: int) -> str:
    """Fallback rule-based analysis."""
    number = trace_data.get("formatted_international", trace_data.get("number", "Unknown"))
    country = trace_data.get("country_name", "Unknown")
    carrier = trace_data.get("carrier", "Unknown")
    line_type = trace_data.get("line_type", "Unknown")

    if risk_level == "Critical":
        opener = f"⚠️ This number ({number}) shows strong indicators of malicious activity."
    elif risk_level == "High":
        opener = f"This number ({number}) has several concerning risk factors."
    elif risk_level == "Medium":
        opener = f"This number ({number}) has some risk indicators worth noting."
    else:
        opener = f"This number ({number}) appears to be relatively safe."

    details = f"It is a {line_type} number from {country}"
    if carrier and carrier != "Unknown":
        details += f", operated by {carrier}"
    details += "."

    if factors:
        key_factors = " Key findings: " + "; ".join(factors[:3]) + "."
    else:
        key_factors = " No significant risk factors detected."

    return opener + " " + details + key_factors


def _generate_recommendation(risk_level: str, threat_type: str, trace_data: dict) -> str:
    """Fallback rule-based recommendation."""
    if risk_level == "Critical":
        return (
            "🚫 Do NOT answer or return calls from this number. "
            "Block it immediately on your device. If you've shared any personal information, "
            "contact your bank and monitor your accounts. Consider filing a report with local authorities."
        )
    elif risk_level == "High":
        return (
            "⚠️ Exercise extreme caution with this number. "
            "Do not share personal information if they contact you. "
            "Block the number and report it if you receive suspicious calls."
        )
    elif risk_level == "Medium":
        return (
            "⚡ Be cautious when interacting with this number. "
            "Verify the caller's identity before sharing any information. "
            "If unsolicited, consider blocking and reporting."
        )
    else:
        return (
            "✅ This number appears safe based on available data. "
            "As always, never share sensitive personal information over the phone "
            "unless you initiated the call to a verified number."
        )


# ---------------------------------------------------------------------------
# AI Safety Chatbot — LLM-powered with knowledge base fallback
# ---------------------------------------------------------------------------
PHONE_SAFETY_CONTEXT = """You are an AI phone safety assistant for the PhoneTracer app.
You help users understand phone scams, spam calls, VoIP numbers, caller ID spoofing,
phishing, robocalls, privacy protection, and how to block/report unwanted calls.

Key facts you know:
- VoIP numbers are internet-based and can be used for spoofing
- Wangiri scams use one-ring missed calls from international numbers
- Users should never share SSN, bank details, or passwords over the phone
- Common scam tactics: urgency, threats, prize offers, impersonation
- Users can report spam to FTC (US), FCC (US), ICO (UK), TRAI (India)
- Phone blocking: iPhone (Settings > Phone > Silence Unknown Callers), Android (Phone app > Block)
- MNP (Mobile Number Portability) means carriers can change
- Caller ID can be spoofed using VoIP services

Be helpful, concise, and practical. Use bullet points for lists.
If asked something unrelated to phone safety, politely redirect."""

KNOWLEDGE_BASE = [
    {
        "patterns": ["scam", "how to identify", "recognize", "spot", "tell if"],
        "response": (
            "🔍 **How to Identify Scam Calls:**\n\n"
            "1. **Urgency tactics** — They pressure you to act immediately\n"
            "2. **Requesting payment** via gift cards, wire transfers, or crypto\n"
            "3. **Threatening arrest** or legal action if you don't pay\n"
            "4. **Spoofed caller ID** — The number looks local but isn't\n"
            "5. **Asking for SSN/bank details** — Legitimate organizations never do this by phone\n"
            "6. **\"You've won a prize\"** — If you didn't enter, you didn't win\n\n"
            "💡 **Tip:** If in doubt, hang up and call the organization directly using the number on their official website."
        ),
    },
    {
        "patterns": ["voip", "virtual number", "internet number", "online number"],
        "response": (
            "📡 **About VoIP Numbers:**\n\n"
            "VoIP (Voice over Internet Protocol) numbers are phone numbers that work over the internet "
            "instead of traditional phone lines.\n\n"
            "**Legitimate uses:** Businesses, remote workers, international calls\n"
            "**Risk factor:** VoIP numbers are easy to obtain anonymously, making them popular with scammers "
            "for spoofing and robocalls.\n\n"
            "⚠️ A VoIP number isn't automatically dangerous, but exercise more caution with unknown VoIP callers."
        ),
    },
    {
        "patterns": ["block", "how to block", "stop calls", "prevent"],
        "response": (
            "🛡️ **How to Block Unwanted Calls:**\n\n"
            "**iPhone:**\n"
            "• Open Recent Calls → tap ⓘ next to the number → \"Block this Caller\"\n"
            "• Settings → Phone → Silence Unknown Callers\n\n"
            "**Android:**\n"
            "• Open Phone app → tap the number → \"Block/Report spam\"\n"
            "• Settings → Blocked Numbers → Add a number\n\n"
            "**Additional steps:**\n"
            "• Register on your country's Do Not Call list\n"
            "• Use spam filtering apps (Truecaller, Hiya, etc.)\n"
            "• Report to PhoneTracer to help the community!"
        ),
    },
    {
        "patterns": ["report", "how to report", "file complaint", "ftc", "fcc", "authority"],
        "response": (
            "📋 **How to Report Scam/Spam Numbers:**\n\n"
            "1. **PhoneTracer** — Use our Report page to warn the community\n"
            "2. **FTC** (US) — reportfraud.ftc.gov\n"
            "3. **FCC** (US) — fcc.gov/consumers/guides/stop-unwanted-calls\n"
            "4. **ICO** (UK) — ico.org.uk/make-a-complaint\n"
            "5. **TRAI** (India) — Report via DND app\n"
            "6. **Your carrier** — Most carriers have spam reporting via text (e.g., forward to 7726/SPAM)\n\n"
            "💡 The more reports filed, the faster these numbers get blocked globally."
        ),
    },
    {
        "patterns": ["safe", "is it safe", "should i answer", "unknown number", "missed call"],
        "response": (
            "📱 **Should You Answer Unknown Numbers?**\n\n"
            "**General rule:** If you don't recognize the number, let it go to voicemail.\n\n"
            "**Red flags for callbacks:**\n"
            "• International numbers you don't expect\n"
            "• Premium rate numbers (starting with 900, 0900, etc.)\n"
            "• Missed calls that ring only once (\"Wangiri\" scam)\n\n"
            "**Safe to answer if:**\n"
            "• You're expecting a delivery or appointment call\n"
            "• The number matches a local area code you recognize\n"
            "• You can verify the number on PhoneTracer first! 🔍"
        ),
    },
    {
        "patterns": ["phishing", "sms phishing", "smishing", "text scam", "fake text"],
        "response": (
            "🎣 **Phishing & SMS Scams (Smishing):**\n\n"
            "**What is it?** Fraudulent texts pretending to be from banks, delivery services, or government agencies.\n\n"
            "**Common examples:**\n"
            "• \"Your package is held — click here to reschedule\"\n"
            "• \"Unusual activity on your account — verify now\"\n"
            "• \"You owe taxes — pay immediately to avoid arrest\"\n\n"
            "**How to protect yourself:**\n"
            "• Never click links in unexpected text messages\n"
            "• Don't reply with personal information\n"
            "• Go directly to the official website/app instead\n"
            "• Forward suspicious texts to 7726 (SPAM)"
        ),
    },
    {
        "patterns": ["robocall", "automated", "robot", "recording", "press 1"],
        "response": (
            "🤖 **About Robocalls:**\n\n"
            "Robocalls are automated pre-recorded phone calls. While some are legitimate "
            "(appointment reminders, flight alerts), most unsolicited robocalls are illegal.\n\n"
            "**Illegal robocall signs:**\n"
            "• Selling something without your written permission\n"
            "• Using fake caller ID (spoofing)\n"
            "• No opt-out option provided\n\n"
            "**Protection tips:**\n"
            "• Don't press any buttons — it confirms your number is active\n"
            "• Register on the Do Not Call list\n"
            "• Use call-blocking apps\n"
            "• Block and report on PhoneTracer"
        ),
    },
    {
        "patterns": ["caller id", "spoofing", "fake number", "disguise", "pretend"],
        "response": (
            "🎭 **Caller ID Spoofing:**\n\n"
            "Spoofing is when callers deliberately falsify the phone number displayed on your caller ID "
            "to disguise their identity.\n\n"
            "**How it works:**\n"
            "• Scammers use VoIP services to set any number as their outgoing caller ID\n"
            "• They often use numbers similar to yours (\"neighbor spoofing\")\n"
            "• Even government agency numbers can be spoofed\n\n"
            "**Protection:**\n"
            "• Never trust caller ID alone\n"
            "• If a \"bank\" calls, hang up and call the number on your card\n"
            "• Use PhoneTracer to check the real origin"
        ),
    },
    {
        "patterns": ["privacy", "data", "personal information", "protect", "security"],
        "response": (
            "🔒 **Phone Privacy & Data Protection:**\n\n"
            "**Never share over the phone:**\n"
            "• Social Security / National ID numbers\n"
            "• Bank account or credit card details\n"
            "• Passwords or OTP codes\n"
            "• Home address to unknown callers\n\n"
            "**Best practices:**\n"
            "• Use different passwords for each account\n"
            "• Enable two-factor authentication everywhere\n"
            "• Review app permissions regularly\n"
            "• Be cautious with public Wi-Fi for calls/texts\n"
            "• Use PhoneTracer to verify unknown numbers before calling back"
        ),
    },
    {
        "patterns": ["wangiri", "one ring", "callback scam", "international missed call"],
        "response": (
            "☎️ **Wangiri (One Ring) Scam:**\n\n"
            "**How it works:**\n"
            "• You receive a missed call from an international number\n"
            "• The phone rings only once or twice to create a missed call\n"
            "• If you call back, you're connected to a premium-rate number\n"
            "• You get charged high per-minute fees\n\n"
            "**Protection:**\n"
            "• Never call back unknown international numbers\n"
            "• Look up the number on PhoneTracer first\n"
            "• Block the number immediately\n"
            "• Numbers from small island nations are common sources"
        ),
    },
    {
        "patterns": ["hello", "hi", "hey", "help", "what can you do", "start"],
        "response": (
            "👋 **Hello! I'm your Phone Safety AI Assistant.**\n\n"
            "I can help you with:\n\n"
            "• 🔍 How to identify scam and spam calls\n"
            "• 🛡️ How to block unwanted numbers\n"
            "• 📋 How and where to report fraud\n"
            "• 📡 Understanding VoIP and virtual numbers\n"
            "• 🎭 Caller ID spoofing explained\n"
            "• 🔒 Phone privacy and data protection tips\n"
            "• 🤖 Handling robocalls\n"
            "• 🎣 Phishing and SMS scam awareness\n\n"
            "Just ask me anything about phone safety! 💬"
        ),
    },
]

DEFAULT_RESPONSE = (
    "🤔 I'm not sure about that specific topic, but here are some things I can help with:\n\n"
    "• **\"How to identify scam calls\"** — Learn the warning signs\n"
    "• **\"How to block numbers\"** — Step-by-step for iPhone & Android\n"
    "• **\"What is VoIP\"** — Understanding virtual numbers\n"
    "• **\"How to report spam\"** — Where to file complaints\n"
    "• **\"Caller ID spoofing\"** — How scammers fake numbers\n"
    "• **\"Phone privacy tips\"** — Protect your data\n\n"
    "Try asking about any of these topics! 💡"
)


def chat(message: str, history: list = None) -> dict:
    """
    Hybrid chatbot: tries LLM first, falls back to knowledge base pattern matching.
    """
    msg_lower = message.lower().strip()

    # --- Try LLM first ---
    llm_response = _llm_generate(
        system_prompt=PHONE_SAFETY_CONTEXT,
        user_prompt=message,
        max_tokens=350,
    )

    if llm_response and len(llm_response) > 20:
        return {
            "response": llm_response,
            "confidence": 0.9,
            "ai_source": "llm",
            "model": MODEL_FILE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # --- Fallback: pattern matching ---
    best_score = 0
    best_response = DEFAULT_RESPONSE

    for entry in KNOWLEDGE_BASE:
        score = 0
        for pattern in entry["patterns"]:
            if pattern in msg_lower:
                score += len(pattern)
        if score > best_score:
            best_score = score
            best_response = entry["response"]

    return {
        "response": best_response,
        "confidence": min(best_score / 10, 1.0),
        "ai_source": "rule-based",
        "model": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
