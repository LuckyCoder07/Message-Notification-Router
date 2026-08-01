import re
from typing import Dict, Any, List, Union

def clean_text(text: Any) -> str:
    """
    Lowercases, normalizes whitespace, safely handles NaN, and removes 
    unnecessary punctuation without destroying URLs or emails.
    """
    if not isinstance(text, str):
        return ""
    
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove punctuation except those commonly used in URLs, emails, or currency
    # Keep: a-z0-9 . : / ? = & % - _ @ $ £ € ₹ , +
    text = re.sub(r'[^\w\s\.\:\/\?\=\&\%\-\_\@\$\£\€\₹\,\+]', '', text)
    
    return text

def tokenize(text: str) -> List[str]:
    """Splits text into tokens based on whitespace."""
    return text.split()

def extract_keywords(text: str) -> List[str]:
    """Extracts alphanumeric keywords, ignoring very short words."""
    tokens = tokenize(text)
    return [t for t in tokens if t.isalnum() and len(t) > 2]

def detect_urls(text: str) -> bool:
    """Detects URLs in text."""
    return bool(re.search(r'https?://\S+|www\.\S+', text))

def detect_email(text: str) -> bool:
    """Detects email addresses in text."""
    return bool(re.search(r'\S+@\S+\.\S+', text))

def detect_phone_numbers(text: str) -> bool:
    """Detects phone numbers in text."""
    # Matches international format like +1234567890 or typical lengths
    return bool(re.search(r'\+?\d[\d\-\s]{7,15}\d', text))

def detect_money(text: str) -> bool:
    """Detects currency amounts in text."""
    return bool(re.search(
        r'[\$\£\€\₹]\s*\d+(?:[\.\,]\d+)?|\b\d+(?:[\.\,]\d+)?\s*(?:usd|eur|gbp|inr|rs|bucks|dollars)\b', 
        text, 
        re.IGNORECASE
    ))

def detect_dates(text: str) -> bool:
    """Detects dates in text."""
    return bool(re.search(
        r'\b(?:today|tomorrow|yesterday|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})\b', 
        text, 
        re.IGNORECASE
    ))

def detect_time(text: str) -> bool:
    """Detects time in text."""
    return bool(re.search(r'\b\d{1,2}(?:\:\d{2})?\s*(?:am|pm)\b|\b\d{1,2}\:\d{2}\b', text, re.IGNORECASE))

def detect_forwarded(text: str, forwarded_count: Any = None) -> bool:
    """Detects if a message was forwarded based on text or metadata."""
    if isinstance(forwarded_count, (int, float)) and forwarded_count > 0:
        return True
    return bool(re.search(r'\bforwarded\b', text, re.IGNORECASE))

def detect_otp(text: str) -> bool:
    """Detects OTP (One Time Passwords) or verification codes."""
    return bool(re.search(
        r'\b(?:otp|code|pin|password)\b(?:\s+is)?\s*[\:\-]?\s*\d{4,8}\b|\b\d{4,8}\b(?=\s+is\s+(?:your|the)\s+(?:otp|code|pin|password))', 
        text, 
        re.IGNORECASE
    ))

def _contains_keywords(text: str, keywords: List[str]) -> bool:
    """Helper to check if any keyword exists in text."""
    pattern = r'\b(?:' + '|'.join(re.escape(k) for k in keywords) + r')\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

def detect_payment_keywords(text: str) -> bool:
    """Detects keywords related to payments."""
    keywords = [
        'pay', 'payment', 'paid', 'invoice', 'transfer', 'transferred', 
        'bill', 'receipt', 'due', 'amount', 'transaction'
    ]
    return _contains_keywords(text, keywords)

def detect_promotion_keywords(text: str) -> bool:
    """Detects promotional keywords."""
    keywords = [
        'discount', 'offer', 'sale', 'promo', 'deal', 'cheap', 
        'save', 'coupon', 'exclusive', 'free'
    ]
    return _contains_keywords(text, keywords)

def detect_event_keywords(text: str) -> bool:
    """Detects event related keywords."""
    keywords = [
        'event', 'party', 'meeting', 'wedding', 'birthday', 'celebration', 
        'invite', 'invitation', 'rsvp', 'venue', 'schedule'
    ]
    return _contains_keywords(text, keywords)

def detect_urgent_keywords(text: str) -> bool:
    """Detects urgency keywords."""
    keywords = ['urgent', 'emergency', 'asap', 'immediately', 'important', 'alert', 'hurry', 'quick']
    return _contains_keywords(text, keywords)

def detect_spam_keywords(text: str) -> bool:
    """Detects common spam keywords."""
    keywords = [
        'win', 'winner', 'lottery', 'prize', 'cash', 'earn', 
        'guarantee', 'risk-free', 'click', 'subscribe', 'unsubscribe'
    ]
    return _contains_keywords(text, keywords)

def detect_scam_keywords(text: str) -> bool:
    """Detects potential scam keywords."""
    keywords = [
        'bank', 'account', 'verify', 'update', 'suspend', 'blocked', 
        'login', 'password', 'security', 'unauthorized', 'fraud', 'ssn'
    ]
    return _contains_keywords(text, keywords)

def build_features(message_row: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """
    Builds a dictionary of extracted features from a message row.
    
    Args:
        message_row: A dictionary or pandas Series representing a single message.
                     Expected to contain 'text' and optionally 'forwarded_count'.
    
    Returns:
        A dictionary of boolean flags and extracted text/keywords for the router.
    """
    # Safely extract values whether it's a dict or an object (like a pandas namedtuple/series)
    if isinstance(message_row, dict):
        raw_text = message_row.get('text', '')
        forwarded_count = message_row.get('forwarded_count', 0)
    else:
        raw_text = getattr(message_row, 'text', '')
        forwarded_count = getattr(message_row, 'forwarded_count', 0)
        
    cleaned = clean_text(raw_text)
    
    features = {
        "clean_text": cleaned,
        "keywords": extract_keywords(cleaned),
        "contains_url": detect_urls(cleaned),
        "contains_email": detect_email(cleaned),
        "contains_phone": detect_phone_numbers(cleaned),
        "contains_money": detect_money(cleaned),
        "contains_date": detect_dates(cleaned),
        "contains_time": detect_time(cleaned),
        "contains_otp": detect_otp(cleaned),
        "contains_payment": detect_payment_keywords(cleaned),
        "contains_promotion": detect_promotion_keywords(cleaned),
        "contains_event": detect_event_keywords(cleaned),
        "contains_urgent": detect_urgent_keywords(cleaned),
        "contains_spam": detect_spam_keywords(cleaned),
        "contains_scam": detect_scam_keywords(cleaned),
        "is_forwarded": detect_forwarded(cleaned, forwarded_count)
    }
    
    return features
