from typing import Dict, Any

def _default_response() -> Dict[str, Any]:
    """Helper to return an empty unmatched rule response."""
    return {
        "matched": False,
        "score": 0,
        "action": "none",
        "message_type": "unknown",
        "reason": ""
    }

def rule_payment(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('contains_payment', False) or features.get('contains_money', False):
        res.update({
            "matched": True,
            "score": 80,
            "action": "notify",
            "message_type": "payment",
            "reason": "Payment or currency keywords detected in the message."
        })
    return res

def rule_business_update(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    # E.g., looking at order status keywords
    text = features.get('clean_text', '')
    if any(k in text for k in ['order', 'shipped', 'delivery', 'arriving', 'update']):
        res.update({
            "matched": True,
            "score": 70,
            "action": "notify",
            "message_type": "business_update",
            "reason": "Order or delivery update keywords found."
        })
    return res

def rule_verified_business(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    biz_hist = history.get('business', {})
    if biz_hist.get('is_verified', False):
        res.update({
            "matched": True,
            "score": 85,
            "action": "notify", # Verified business updates usually warrant notification
            "message_type": "business_update",
            "reason": "Sender is a verified business."
        })
    return res

def rule_personal(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    sender_hist = history.get('sender', {})
    if sender_hist.get('has_interaction', False) and sender_hist.get('replies', 0) > 0:
        res.update({
            "matched": True,
            "score": 90,
            "action": "notify",
            "message_type": "personal",
            "reason": "High historical interaction and replies with this sender."
        })
    return res

def rule_family(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    text = features.get('clean_text', '')
    family_words = ['mom', 'dad', 'brother', 'sister', 'aunt', 'uncle', 'grandma', 'grandpa', 'family']
    if any(w in text for w in family_words):
        res.update({
            "matched": True,
            "score": 85,
            "action": "notify",
            "message_type": "personal",
            "reason": "Family-related keywords detected in the message."
        })
    return res

def rule_school(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    text = features.get('clean_text', '')
    if any(w in text for w in ['school', 'class', 'homework', 'teacher', 'exam', 'assignment']):
        res.update({
            "matched": True,
            "score": 70,
            "action": "notify",
            "message_type": "event", # Or generic depending on routing
            "reason": "School or education related keywords detected."
        })
    return res

def rule_event(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('contains_event', False):
        res.update({
            "matched": True,
            "score": 75,
            "action": "notify",
            "message_type": "event",
            "reason": "Event invitation or planning keywords detected."
        })
    return res

def rule_meeting(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    text = features.get('clean_text', '')
    if any(w in text for w in ['meeting', 'zoom', 'teams', 'call', 'sync']):
        res.update({
            "matched": True,
            "score": 80,
            "action": "notify",
            "message_type": "event",
            "reason": "Work or meeting related keywords detected."
        })
    return res

def rule_forward(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('is_forwarded', False):
        res.update({
            "matched": True,
            "score": -30, # Forwards generally lower priority
            "action": "digest",
            "message_type": "forward",
            "reason": "Message is marked as forwarded."
        })
    return res

def rule_promotion(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('contains_promotion', False):
        res.update({
            "matched": True,
            "score": -50,
            "action": "digest",
            "message_type": "promotion",
            "reason": "Promotional keywords like sale or discount detected."
        })
    return res

def rule_spam(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('contains_spam', False):
        res.update({
            "matched": True,
            "score": -80,
            "action": "mute",
            "message_type": "spam",
            "reason": "High density of spam keywords detected."
        })
    return res

def rule_scam(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('contains_scam', False):
        res.update({
            "matched": True,
            "score": -100,
            "action": "mute",
            "message_type": "scam",
            "reason": "Severe scam or phishing keywords detected."
        })
    return res

def rule_otp(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('contains_otp', False):
        res.update({
            "matched": True,
            "score": 100,
            "action": "notify",
            "message_type": "urgent",
            "reason": "One-Time Password (OTP) or verification code detected."
        })
    return res

def rule_voice(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if media.get('media_type') in ['voice', 'audio']:
        res.update({
            "matched": True,
            "score": 50,
            "action": "notify",
            "message_type": "personal",
            "reason": "Contains a voice note which implies personal communication."
        })
    return res

def rule_image(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if media.get('media_type') == 'image':
        res.update({
            "matched": True,
            "score": 20,
            "action": "none",
            "message_type": "unknown",
            "reason": "Contains an image attachment."
        })
    return res

def rule_muted_group(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    group_hist = history.get('group', {})
    if group_hist.get('is_muted', False):
        res.update({
            "matched": True,
            "score": -90,
            "action": "mute",
            "message_type": "unknown",
            "reason": "Message belongs to a group the user has explicitly muted."
        })
    return res

def rule_quiet_hours(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    # A simple heuristic: check if message timestamp hour is very late or very early
    # In reality, this would check against the user's local timezone preferences
    timestamp = message.get('timestamp')
    if isinstance(timestamp, str) and len(timestamp) > 10:
        # Assuming simple ISO format parsing for hour roughly
        try:
            hour = int(timestamp[11:13])
            if hour >= 22 or hour <= 6:
                res.update({
                    "matched": True,
                    "score": -40,
                    "action": "digest",
                    "message_type": "unknown",
                    "reason": "Message received during typical quiet hours (10 PM to 6 AM)."
                })
        except:
            pass
    return res

def rule_recent_reply(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    sender_hist = history.get('sender', {})
    if sender_hist.get('replies', 0) > 3:
        res.update({
            "matched": True,
            "score": 60,
            "action": "notify",
            "message_type": "personal",
            "reason": "User has frequently replied to this sender recently."
        })
    return res

def rule_recent_reports(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    sender_hist = history.get('sender', {})
    # If the user has reported this sender
    if sender_hist.get('reports', 0) > 0:
        res.update({
            "matched": True,
            "score": -100,
            "action": "mute",
            "message_type": "spam",
            "reason": "User has previously reported this sender."
        })
    return res
