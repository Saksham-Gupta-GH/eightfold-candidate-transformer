import phonenumbers
import pycountry
from typing import Optional

def normalize_phone(phone_str: str, default_region: str = "US") -> Optional[str]:
    """Normalize phone number to E.164 format."""
    if not phone_str:
        return None
    try:
        parsed = phonenumbers.parse(phone_str, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        pass
    return None

def normalize_country(country_str: str) -> Optional[str]:
    """Normalize country to ISO-3166 alpha-2."""
    if not country_str:
        return None
    try:
        # Try direct lookup
        country = pycountry.countries.lookup(country_str)
        return country.alpha_2
    except LookupError:
        # Simple heuristics for edge cases
        if country_str.lower() in ["usa", "united states", "us"]:
            return "US"
        if country_str.lower() in ["uk", "united kingdom"]:
            return "GB"
    return None

def canonicalize_skill(skill_str: str) -> str:
    """Normalize skill names to a canonical representation."""
    if not skill_str:
        return ""
    
    s = skill_str.strip().lower()
    
    # Very basic synonym mapping
    synonyms = {
        "js": "javascript",
        "react.js": "react",
        "reactjs": "react",
        "node.js": "node",
        "nodejs": "node",
        "ts": "typescript",
        "k8s": "kubernetes",
        "cpp": "c++"
    }
    
    return synonyms.get(s, s)

from dateutil import parser as date_parser

def normalize_date(date_str: str) -> Optional[str]:
    """Normalize date to YYYY-MM format."""
    if not date_str:
        return None
    try:
        dt = date_parser.parse(date_str)
        return dt.strftime("%Y-%m")
    except (ValueError, TypeError):
        return None

