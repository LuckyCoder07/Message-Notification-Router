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
    
    # 3. History Lookup
    user_id = str(msg_dict.get('user_id', ''))
    sender_id = str(msg_dict.get('sender_id', ''))
    group_id = str(msg_dict.get('group_id', ''))
    business_id = str(msg_dict.get('business_id', ''))
    
    history = {
        "user": get_user_history(user_id) if user_id else {},
        "sender": get_sender_history(user_id, sender_id) if user_id and sender_id else {},
        "group": get_group_history(user_id, group_id) if user_id and group_id else {},
        "business": get_business_history(user_id, business_id) if user_id and business_id else {}
    }
    
    # 4. Run Every Rule
    # Dynamically find all functions in rules.py that start with 'rule_'
    all_rules = [
        func for name, func in inspect.getmembers(rules_module, inspect.isfunction)
        if name.startswith('rule_')
    ]
    
    matched_results = []
    for rule_func in all_rules:
        result = rule_func(message=msg_dict, features=features, history=history, media=media)
        if result.get("matched", False):
            matched_results.append(result)
            
    # 5. Resolve Conflicts & Choose highest scoring
    final_action = "notify"  # Default fallback action
    final_message_type = "unknown"
    final_reason = "No specific rules matched. Defaulting to standard notification."
    confidence = 0.5
    
    if matched_results:
        # Sort by absolute score (highest impact wins)
        # e.g., a -100 (scam) overrides an 80 (payment)
        matched_results.sort(key=lambda x: abs(x.get("score", 0)), reverse=True)
        
        best_match = matched_results[0]
        final_action = best_match.get("action", "notify")
        final_message_type = best_match.get("message_type", "unknown")
        
        # Combine reasons from the top few matches for a detailed explanation
        top_reasons = [r.get("reason", "") for r in matched_results[:3] if r.get("reason")]
        final_reason = " | ".join(top_reasons)
        
        # Calculate confidence based on the magnitude of the highest score
        max_score = abs(best_match.get("score", 0))
        confidence = min(max_score / 100.0, 1.0)
        
    # 6. Generate evidence message IDs from history
    evidence_ids = get_evidence_message_ids(user_id, sender_id, group_id) if user_id else []
    
    # 7. Return Final Output
    return {
        "action": final_action,
        "message_type": final_message_type,
        "reason": final_reason,
        "confidence": round(confidence, 2),
        "evidence_message_ids": evidence_ids
    }
