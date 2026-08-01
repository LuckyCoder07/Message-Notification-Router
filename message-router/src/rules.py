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
        text = features.get('clean_text', '')
        if 'today' in text or 'urgent' in text:
            res.update({
                "matched": True,
                "score": 90,
                "action": "notify",
                "message_type": "payment",
                "reason": "Bill or payment is due today."
            })
        else:
            res.update({
                "matched": True,
                "score": -30,
                "action": "digest",
                "message_type": "payment",
                "reason": "Standard invoice or payment record."
            })
    return res

def rule_business_update(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    text = features.get('clean_text', '')
    conv_type = str(message.get('conversation_type', '')).lower()
    is_business_msg = conv_type == 'business'
    has_update_keywords = any(k in text for k in ['order', 'shipped', 'delivery', 'arriving', 'update', 'tracking', 'dispatch'])
    
    if is_business_msg or has_update_keywords:
        if 'today' in text or 'now' in text or 'arriving' in text:
            res.update({
                "matched": True,
                "score": 85,
                "action": "notify",
                "message_type": "business_update",
                "reason": "Delivery is arriving today."
            })
        elif has_update_keywords:
            res.update({
                "matched": True,
                "score": 30,
                "action": "digest",
                "message_type": "business_update",
                "reason": "Generic shipping update."
            })
    return res

def rule_verified_business(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    biz_hist = history.get('business', {})
    if biz_hist.get('is_verified', False):
        if features.get('contains_promotion', False):
            res.update({
                "matched": True,
                "score": -40,
                "action": "digest",
                "message_type": "promotion",
                "reason": "Verified business sent a promotion."
            })
        elif biz_hist.get('has_ordered_recently', False):
            res.update({
                "matched": True,
                "score": 60,
                "action": "notify",
                "message_type": "business_update",
                "reason": "Update from an actively used business."
            })
        else:
            res.update({
                "matched": True,
                "score": 40,
                "action": "digest",
                "message_type": "business_update",
                "reason": "Standard business update."
            })
    return res

def rule_personal(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    sender_hist = history.get('sender', {})
    
    score = 0
    if sender_hist.get('has_replied_recently', False):
        score += 60
    if sender_hist.get('usually_opens', False):
        score += 30
        
    if score >= 60:
        res.update({
            "matched": True,
            "score": score,
            "action": "notify",
            "message_type": "personal",
            "reason": "Strong personal interaction history."
        })
    elif score > 0:
        res.update({
            "matched": True,
            "score": score,
            "action": "digest",
            "message_type": "personal",
            "reason": "Standard personal interaction history."
        })
    return res

def rule_family(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    # Do not trigger on forwarded chain messages that happen to mention family
    if features.get('is_forwarded', False):
        return res
    text = features.get('clean_text', '')
    family_words = ['mom', 'dad', 'brother', 'sister', 'aunt', 'uncle', 'grandma', 'grandpa', 'family']
    if any(w in text for w in family_words):
        res.update({
            "matched": True,
            "score": 85,
            "action": "notify",
            "message_type": "personal",
            "reason": "Family-related keywords detected."
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
            "message_type": "event",
            "reason": "School or education update."
        })
    return res

def rule_event(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('contains_event', False):
        text = features.get('clean_text', '')
        if 'today' in text or 'now' in text:
            res.update({
                "matched": True,
                "score": 90,
                "action": "notify",
                "message_type": "event",
                "reason": "Event happening today."
            })
        else:
            res.update({
                "matched": True,
                "score": 40,
                "action": "digest",
                "message_type": "event",
                "reason": "Future event planning."
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
            "reason": "Meeting or sync request."
        })
    return res

def rule_forward(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('is_forwarded', False):
        try:
            fwd_count = int(message.get('forwarded_count', 1))
        except (ValueError, TypeError):
            fwd_count = 1
        
        if fwd_count >= 5:
            # Viral chain-forwards are almost always spam/scam — hard mute
            res.update({
                "matched": True,
                "score": -300,
                "action": "mute",
                "message_type": "spam",
                "reason": f"Viral chain-forward (forwarded {fwd_count} times)."
            })
        else:
            res.update({
                "matched": True,
                "score": -70,
                "action": "digest",
                "message_type": "forward",
                "reason": "Message is forwarded."
            })
    return res

def rule_promotion(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('contains_promotion', False):
        biz_hist = history.get('business', {})
        sender_hist = history.get('sender', {})
        
        if biz_hist.get('has_ordered_recently', False) or sender_hist.get('usually_opens', False):
            res.update({
                "matched": True,
                "score": -40,
                "action": "digest",
                "message_type": "promotion",
                "reason": "Promotion from an engaged business."
            })
        else:
            res.update({
                "matched": True,
                "score": -80,
                "action": "mute",
                "message_type": "promotion",
                "reason": "Unwanted promotion."
            })
    return res

def rule_spam(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('contains_spam', False):
        res.update({
            "matched": True,
            "score": -200,
            "action": "mute",
            "message_type": "spam",
            "reason": "Spam content detected."
        })
    return res

def rule_scam(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('contains_scam', False):
        res.update({
            "matched": True,
            "score": -1000,
            "action": "mute",
            "message_type": "scam",
            "reason": "Severe scam or phishing attempt."
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
            "reason": "Verification code detected."
        })
    return res

def rule_voice(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if media.get('media_type') in ['voice', 'audio']:
        sender_hist = history.get('sender', {})
        if sender_hist.get('has_replied_recently', False):
            res.update({
                "matched": True,
                "score": 75,
                "action": "notify",
                "message_type": "personal",
                "reason": "Voice note from an active contact."
            })
        else:
            res.update({
                "matched": True,
                "score": 30,
                "action": "digest",
                "message_type": "personal",
                "reason": "Voice note from a standard contact."
            })
    return res

def rule_image(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if media.get('media_type') == 'image':
        res.update({
            "matched": True,
            "score": 20,
            "action": "digest",
            "message_type": "media",
            "reason": "Message contains an image."
        })
    return res

def rule_muted_group(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    group_hist = history.get('group', {})
    if group_hist.get('is_muted', False):
        res.update({
            "matched": True,
            "score": -60,
            "action": "digest",
            "message_type": "unknown",
            "reason": "Message from a muted group."
        })
    return res

def rule_quiet_hours(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    timestamp = message.get('created_at', message.get('timestamp'))
    if isinstance(timestamp, str) and len(timestamp) > 10:
        try:
            hour = int(timestamp[11:13])
            if hour >= 22 or hour <= 6:
                res.update({
                    "matched": True,
                    "score": -40,
                    "action": "digest",
                    "message_type": "unknown",
                    "reason": "Message received during quiet hours."
                })
        except:
            pass
    return res

def rule_recent_reports(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    sender_hist = history.get('sender', {})
    if sender_hist.get('has_been_reported', False):
        res.update({
            "matched": True,
            "score": -1000,
            "action": "mute",
            "message_type": "spam",
            "reason": "Sender has been reported previously."
        })
    return res
    
def rule_similar_history(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    from src.history import find_similar_messages
    res = _default_response()
    user_id = str(message.get('user_id', ''))
    text = features.get('clean_text', '')
    if user_id and text:
        similar = find_similar_messages(user_id, text, threshold=0.85)
        if similar:
            res.update({
                "matched": True,
                "score": 30,
                "action": "digest",
                "message_type": "repeated",
                "reason": "Highly similar message received previously."
            })
    return res

def rule_recent_reply(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    sender_hist = history.get('sender', {})
    if sender_hist.get('has_replied_recently', False) and sender_hist.get('usually_opens', False):
        res.update({
            "matched": True,
            "score": 65,
            "action": "notify",
            "message_type": "personal",
            "reason": "Active conversation with this sender."
        })
    return res

def rule_urgent(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    res = _default_response()
    if features.get('contains_urgent', False) and not features.get('contains_promotion', False):
        text = features.get('clean_text', '')
        # Only fire for genuinely urgent content, not promotional urgency
        if any(w in text for w in ['urgent', 'immediately', 'asap', 'deadline', 'expires']):
            res.update({
                "matched": True,
                "score": 80,
                "action": "notify",
                "message_type": "urgent",
                "reason": "Urgent action required."
            })
    return res

def rule_conversation_type(message: Dict[str, Any], features: Dict[str, Any], history: Dict[str, Any], media: Dict[str, Any]) -> Dict[str, Any]:
    """Provides a baseline classification based on the conversation_type field."""
    res = _default_response()
    conv_type = str(message.get('conversation_type', '')).lower()
    
    if conv_type == 'personal':
        res.update({
            "matched": True,
            "score": 55,
            "action": "notify",
            "message_type": "personal",
            "reason": "Direct personal message."
        })
    elif conv_type == 'group':
        res.update({
            "matched": True,
            "score": 25,
            "action": "digest",
            "message_type": "group",
            "reason": "Group conversation message."
        })
    elif conv_type == 'business':
        biz_hist = history.get('business', {})
        if biz_hist.get('is_verified', False):
            res.update({
                "matched": True,
                "score": 40,
                "action": "digest",
                "message_type": "business_update",
                "reason": "Business message from known account."
            })
        else:
            res.update({
                "matched": True,
                "score": 20,
                "action": "digest",
                "message_type": "business_update",
                "reason": "Business message."
            })
    return res
