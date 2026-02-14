# Post-generation compliance filter (Design Doc Section 14)
import re

BLOCKLIST = {
    "guaranteed", "moon", "easy money", "get rich", "sure thing",
    "100% win", "risk-free", "can't lose", "cannot lose", "will profit",
    "no risk", "free money", "guaranteed profit", "guaranteed return",
    "sure win", "always wins", "never lose", "zero risk",
}

COPY_TRADING_BLOCKLIST = {
    "guaranteed returns", "always profitable", "risk-free copying",
    "passive income guaranteed", "copy and forget",
}

PREDICTION_PATTERNS = [
    r"\b(will (hit|reach|go to|rise|fall|drop|crash|surge|pump))\b",
    r"\bprice (will|going to|is going to)\b",
    r"\b(you should|i recommend|must) (buy|sell|enter|exit)\b",
    r"\b(definitely|certainly|undoubtedly) (going|will)\b",
]

DISCLAIMER = "📊 Analysis by TradeIQ | Not financial advice"
DISCLAIMER_COPYTRADING = "📊 Past performance does not guarantee future results | Not financial advice"
DISCLAIMER_TRADING = "📊 Demo account — virtual money only | Not financial advice"


def check_compliance(text: str) -> tuple[bool, list[str]]:
    """Return (passed, list of violations)."""
    violations = []
    lower = text.lower()
    for word in BLOCKLIST:
        if word in lower:
            violations.append(f"Blocklisted term: {word}")
    for pattern in PREDICTION_PATTERNS:
        if re.search(pattern, lower):
            violations.append("Prediction language detected")
            break
    return (len(violations) == 0, violations)


def check_copytrading_compliance(text: str) -> tuple[bool, list[str]]:
    """Additional compliance check for copy trading content."""
    passed, violations = check_compliance(text)
    lower = text.lower()
    for word in COPY_TRADING_BLOCKLIST:
        if word in lower:
            violations.append(f"Copy trading blocklisted: {word}")
            passed = False
    return (passed, violations)


def check_demo_trading_compliance(text: str) -> tuple[bool, list[str]]:
    """Check demo trading compliance — must mention demo/virtual."""
    passed, violations = check_compliance(text)
    lower = text.lower()
    if "real money" in lower or "real account" in lower:
        violations.append("Demo trading must not reference real money")
        passed = False
    return (passed, violations)


def append_disclaimer(text: str, context: str = "market") -> str:
    """Append context-appropriate disclaimer."""
    if context == "copytrading":
        disclaimer = DISCLAIMER_COPYTRADING
    elif context == "trading":
        disclaimer = DISCLAIMER_TRADING
    else:
        disclaimer = DISCLAIMER
    return f"{text}\n\n{disclaimer}"


def sanitize_token(token: str) -> str:
    """Redact API tokens for logging — show only first 4 and last 4 chars."""
    if not token or len(token) < 12:
        return "***"
    return f"{token[:4]}...{token[-4:]}"
