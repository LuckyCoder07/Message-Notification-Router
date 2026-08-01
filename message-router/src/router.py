import inspect
from typing import Dict, Any, Union

from src.preprocess import build_features
from src.media import process_media
from src.history import (
    get_user_history, 
    get_sender_history, 
    get_group_history, 
    get_business_history, 
    get_evidence_message_ids
)
import src.rules as rules_module

# Cache all rule functions once at startup to avoid per-message inspection overhead
ALL_RULES = [
    func for name, func in inspect.getmembers(rules_module, inspect.isfunction)
    if name.startswith('rule_')
]

def _get_priority(result: Dict[str, Any]) -> int:
    """
    Returns an integer priority for a matched rule. Lower is higher priority.
    Priority order:
    1. OTP / Urgent
    2. Scam
    3. Recent reports / Spam
    4. Payment due today
    5. Personal
    6. Business update
    7. Event
    8. Group
    9. Promotion
    10. Forward / Repeated
    11. Default / Digest
    """
    m_type = result.get('message_type', '')
    action = result.get('action', '')
    reason = result.get('reason', '').lower()
    
    if m_type == 'urgent' or 'otp' in reason or 'verification code' in reason:
        return 1
    if m_type == 'scam':
        return 2
    if m_type == 'spam' or 'reported' in reason:
        return 3
    if m_type == 'payment' and action == 'notify':
        return 4
    if m_type == 'personal':
        return 5
    if m_type == 'business_update':
        return 6
    if m_type == 'event':
        return 7
    if m_type == 'group':
        return 8
    if m_type == 'promotion':
        return 9
    if m_type in ('forward', 'repeated', 'media') or 'forward' in reason:
        return 10
        
    return 11

def route_message(message_row: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """
    Coordinates the entire routing pipeline for a single incoming message.
    It calls the preprocessing, media extraction, historical lookups, and runs all rules.
    Does NOT contain business logic.
    """
    
    # Ensure message is dictionary-like for easy internal passing
    msg_dict = message_row if isinstance(message_row, dict) else (message_row.to_dict() if hasattr(message_row, 'to_dict') else {})
    
    # 1. Preprocess
    features = build_features(message_row)
    
    # 2. Media Extraction
    media = process_media(message_row)
    
    # 3. History Lookup (Handle dataset compatibility with sender_user_id vs sender_id)
    user_id = str(msg_dict.get('user_id', ''))
    sender_id = str(msg_dict.get('sender_user_id', msg_dict.get('sender_id', '')))
    group_id = str(msg_dict.get('group_id', ''))
    business_id = str(msg_dict.get('business_id', ''))
    
    history = {
        "user": get_user_history(user_id) if user_id else {},
        "sender": get_sender_history(user_id, sender_id) if user_id and sender_id else {},
        "group": get_group_history(user_id, group_id) if user_id and group_id else {},
        "business": get_business_history(user_id, business_id) if user_id and business_id else {}
    }
    
    # 4. Run Every Rule
    matched_results = []
    for rule_func in ALL_RULES:
        result = rule_func(message=msg_dict, features=features, history=history, media=media)
        if result.get("matched", False):
            matched_results.append(result)
            
    # 5. Resolve Conflicts & Choose highest scoring
    final_action = "digest"  # Default fallback action
    final_message_type = "unknown"
    final_reason = "No specific rules matched. Defaulting to standard digest."
    confidence = 0.60
    
    if matched_results:
        # Sort by priority tier, then absolute score as a tiebreaker
        matched_results.sort(key=lambda x: (_get_priority(x), -abs(x.get("score", 0))))
        
        best_match = matched_results[0]
        final_action = best_match.get("action", "digest")
        final_message_type = best_match.get("message_type", "unknown")
        
        # Return only the primary explanation to avoid concatenated clutter
        final_reason = best_match.get("reason", final_reason)
        
        # Map confidence using defined ranges
        score = abs(best_match.get("score", 0))
        if score >= 95:
            confidence = 0.98
        elif score >= 85:
            confidence = 0.92
        elif score >= 75:
            confidence = 0.86
        elif score >= 60:
            confidence = 0.78
        elif score >= 45:
            confidence = 0.70
        else:
            confidence = 0.60
        
    # 6. Generate evidence message IDs from history (limited to top 3)
    evidence_ids = get_evidence_message_ids(user_id, sender_id, group_id)[:3] if user_id else []
    
    # 7. Return Final Output
    return {
        "action": final_action,
        "message_type": final_message_type,
        "reason": final_reason,
        "confidence": confidence,
        "evidence_message_ids": evidence_ids
    }
