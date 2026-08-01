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
    # Improved URL regex to catch various formats and domains
    return bool(re.search(r'(?:https?:\/\/)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)', text, re.IGNORECASE))

def detect_email(text: str) -> bool:
    """Detects email addresses in text."""
    # Standard email format detection
    return bool(re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text))

def detect_phone_numbers(text: str) -> bool:
    """Detects phone numbers in text."""
    # Improved phone regex to catch local/international numbers with or without spaces/dashes
    return bool(re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text))

def detect_money(text: str) -> bool:
    """Detects currency amounts in text."""
    # Improved money regex to catch formats like $10, 10 USD, Rs 500, €1.50, 50k
    return bool(re.search(r'(?:[\$\£\€\₹]\s*\d+(?:[\.\,]\d{1,2})?(?:\s*[kKmMbB])?)|(?:\b\d+(?:[\.\,]\d{1,2})?\s*(?:usd|eur|gbp|inr|rs|bucks|dollars|rupees)\b)', text, re.IGNORECASE))

def detect_dates(text: str) -> bool:
    """Detects dates in text."""
    # Improved date regex for multiple formats (e.g., DD/MM/YYYY, Jan 5, 1st of May, today)
    return bool(re.search(r'\b(?:today|tomorrow|yesterday)\b|\b\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}\b|\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?\b|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b', text, re.IGNORECASE))

def detect_time(text: str) -> bool:
    """Detects time in text."""
    # Improved time regex to catch 12h/24h formats robustly
    return bool(re.search(r'\b(?:[01]?\d|2[0-3])(?::[0-5]\d)?\s*(?:[aA][mM]|[pP][mM])\b|\b(?:[01]\d|2[0-3]):[0-5]\d(?:[:][0-5]\d)?\b', text))

def detect_forwarded(text: str, forwarded_count: Any = None) -> bool:
    """Detects if a message was forwarded based on text or metadata."""
    if isinstance(forwarded_count, (int, float)) and forwarded_count > 0:
        return True
    return bool(re.search(r'\bforwarded\b', text, re.IGNORECASE))

def detect_otp(text: str) -> bool:
    """Detects OTP (One Time Passwords) or verification codes."""
    return bool(re.search(r'\b(?:otp|code|pin|password)\b.*?\b\d{4,8}\b|\b\d{4,8}\b.*?\b(?:otp|code|pin|password)\b', text, re.IGNORECASE))

def _contains_keywords(text: str, keywords: List[str]) -> bool:
    """Helper to check if any keyword exists in text. Supports multi-word keywords."""
    pattern = r'\b(?:' + '|'.join(re.escape(k) for k in keywords) + r')\b'
    return bool(re.search(pattern, text, re.IGNORECASE))

def detect_payment_keywords(text: str) -> bool:
    """Detects keywords related to payments."""
    keywords = [
        'invoice', 'upi', 'bank', 'account', 'payment', 'due', 'bill',
        'electricity', 'rent', 'salary', 'refund', 'credited', 'debited', 'wallet'
    ]
    return _contains_keywords(text, keywords)

def detect_promotion_keywords(text: str) -> bool:
    """Detects promotional keywords."""
    keywords = [
        'offer', 'sale', 'discount', 'cashback', 'coupon', 'deal',
        'limited time', 'exclusive', 'buy now', 'free', 'festival offer'
    ]
    return _contains_keywords(text, keywords)

def detect_event_keywords(text: str) -> bool:
    """Detects event related keywords."""
    keywords = [
        'meeting', 'birthday', 'wedding', 'party', 'event', 'function',
        'seminar', 'webinar', 'maintenance', 'society', 'notice', 'class'
    ]
    return _contains_keywords(text, keywords)

def detect_urgent_keywords(text: str) -> bool:
    """Detects urgency keywords."""
    keywords = [
        'urgent', 'immediately', 'asap', 'today', 'tomorrow', 'deadline',
        'last date', 'expires', 'otp', 'verification'
    ]
    return _contains_keywords(text, keywords)

def detect_spam_keywords(text: str) -> bool:
    """Detects common spam keywords."""
    keywords = [
        'subscribe', 'winner', 'claim', 'gift', 'lottery', 'congratulations', 'bonus'
    ]
    return _contains_keywords(text, keywords)

def detect_scam_keywords(text: str) -> bool:
    """Detects potential scam keywords."""
    keywords = [
        'kyc', 'verify account', 'click link', 'bank suspended', 'prize money',
        'investment', 'double money', 'crypto', 'earn daily'
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
    if isinstance(message_row, dict):
        raw_text = message_row.get('message_text', message_row.get('text', ''))
        forwarded_count = message_row.get('forwarded_count', 0)
    else:
        raw_text = getattr(message_row, 'message_text', getattr(message_row, 'text', ''))
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
