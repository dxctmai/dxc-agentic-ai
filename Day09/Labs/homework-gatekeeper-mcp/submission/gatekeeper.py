"""AskIT Gatekeeper v1."""
import re

_TEAMS = [
    ("Security", ("phishing", "malware", "breach", "suspicious", "ransomware")),
    ("Access", ("password", "locked", "login", "mfa", "access")),
    ("Network", ("vpn", "wifi", "network", "internet")),
    ("Hardware", ("laptop", "printer", "screen", "keyboard", "phone")),
]

READ_ACTIONS = {"search_kb", "get_ticket"}
WRITE_ACTIONS = {"reset_password", "update_ticket", "grant_access"}
VIP_USERS = {"EMP-1001", "EMP-1012", "EMP-1023"}


def _has_word(text: str, word: str) -> bool:
    return re.search(r"\b" + re.escape(word) + r"\b", text, re.IGNORECASE) is not None


def route(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    for team, words in _TEAMS:
        if any(_has_word(text, word) for word in words):
            return team
    return "General"


def _is_night(hour: int) -> bool:
    return hour >= 20 or hour < 8


def needs_approval(action: str, user_id: str, hour: int) -> dict:
    if action not in READ_ACTIONS and action not in WRITE_ACTIONS:
        raise ValueError(f"unknown action: {action!r}")
    if not isinstance(hour, int) or isinstance(hour, bool) or hour < 0 or hour > 23:
        raise ValueError("hour must be an int from 0 to 23")

    vip = user_id in VIP_USERS
    if action in READ_ACTIONS:
        if vip:
            return {"approval": False, "approver": "none"}
        return {"approval": False, "approver": "none"}

    if vip:
        return {"approval": True, "approver": "it manager"}
    if _is_night(hour):
        return {"approval": True, "approver": "on-call"}
    return {"approval": True, "approver": "service desk lead"}


def safe_to_remember(text: str) -> bool:
    if not isinstance(text, str) or not text.strip():
        return False
    if any(_has_word(text, word) for word in ("password", "passcode", "otp", "pin", "address")):
        return False
    if _has_word(text, "home") and _has_word(text, "address"):
        return False
    compact = re.sub(r"[\s-]", "", text)
    if re.search(r"\d{6,}", compact):
        return False
    return True
