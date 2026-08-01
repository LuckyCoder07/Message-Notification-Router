import pandas as pd
from typing import Dict, Any, List
from collections import defaultdict

class HistoryIndex:
    """
    A simple container for historical indexes to enable O(1) lookups
    without polluting the global namespace excessively.
    """
    def __init__(self):
        # user_id -> stats
        self.user_events: Dict[str, Dict[str, int]] = defaultdict(lambda: {"opens": 0, "replies": 0, "dismissals": 0, "reports": 0})
        
        # user_id -> sender_id -> stats
        self.sender_interactions: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(lambda: defaultdict(lambda: {"opens": 0, "replies": 0, "dismissals": 0, "reports": 0}))
        
        # user_id -> promotion_stats
        self.user_promotion_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"opens": 0, "dismissals": 0})
        
        # user_id -> group_id -> stats
        self.group_status: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(lambda: {"is_member": False, "is_muted": False, "role": "member"}))
        
        # user_id -> business_id -> stats
        self.business_relations: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(lambda: {"is_verified": False, "recent_orders": 0, "total_spent": 0.0}))
        
        # user_id -> count
        self.daily_load: Dict[str, int] = defaultdict(int)
        
        # user_id -> list of message dicts
        self.user_messages: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

# Global instance for procedural module usage
_INDEX = HistoryIndex()

def build_history_indexes(
    message_history_df: pd.DataFrame,
    message_events_df: pd.DataFrame,
    group_members_df: pd.DataFrame,
    user_business_history_df: pd.DataFrame,
    daily_summary_df: pd.DataFrame
) -> None:
    """
    Builds efficient dictionary-based indexes from DataFrames.
    Must be called once at initialization to populate the history engine.
    """
    global _INDEX
    _INDEX = HistoryIndex()
    
    # 1. Process message_events
    if not message_events_df.empty:
        for _, row in message_events_df.iterrows():
            user = str(row.get('user_id', ''))
            sender = str(row.get('sender_id', ''))
            event = str(row.get('event_type', '')).lower()
            msg_type = str(row.get('message_type', '')).lower() # If available
            
            if user and event:
                if event == 'open':
                    _INDEX.user_events[user]['opens'] += 1
                    if sender: _INDEX.sender_interactions[user][sender]['opens'] += 1
                    if msg_type == 'promotion': _INDEX.user_promotion_stats[user]['opens'] += 1
                elif event == 'reply':
                    _INDEX.user_events[user]['replies'] += 1
                    if sender: _INDEX.sender_interactions[user][sender]['replies'] += 1
                elif event == 'dismiss':
                    _INDEX.user_events[user]['dismissals'] += 1
                    if sender: _INDEX.sender_interactions[user][sender]['dismissals'] += 1
                    if msg_type == 'promotion': _INDEX.user_promotion_stats[user]['dismissals'] += 1
                elif event == 'report':
                    _INDEX.user_events[user]['reports'] += 1
                    if sender: _INDEX.sender_interactions[user][sender]['reports'] += 1

    # 2. Process group_members
    if not group_members_df.empty:
        for _, row in group_members_df.iterrows():
            user = str(row.get('user_id', ''))
            group = str(row.get('group_id', ''))
            if user and group:
                _INDEX.group_status[user][group] = {
                    "is_member": True,
                    "is_muted": bool(row.get('is_muted', False)),
                    "role": str(row.get('role', 'member'))
                }

    # 3. Process user_business_history
    if not user_business_history_df.empty:
        for _, row in user_business_history_df.iterrows():
            user = str(row.get('user_id', ''))
            biz = str(row.get('business_id', ''))
            if user and biz:
                _INDEX.business_relations[user][biz] = {
                    "is_verified": bool(row.get('is_verified', False)),
                    "recent_orders": int(row.get('recent_orders', 0)),
                    "total_spent": float(row.get('total_spent', 0.0))
                }

    # 4. Process daily_notification_summary
    if not daily_summary_df.empty:
        for _, row in daily_summary_df.iterrows():
            user = str(row.get('user_id', ''))
            count = int(row.get('notifications_sent', 0))
            if user:
                _INDEX.daily_load[user] = count
                
    # 5. Process message_history
    if not message_history_df.empty:
        for _, row in message_history_df.iterrows():
            user = str(row.get('user_id', ''))
            if user:
                _INDEX.user_messages[user].append(row.to_dict())

def get_user_history(user_id: str) -> Dict[str, Any]:
    """Retrieves overall historical engagement for a user."""
    u_id = str(user_id)
    stats = _INDEX.user_events.get(u_id, {"opens": 0, "replies": 0, "dismissals": 0, "reports": 0})
    promo = _INDEX.user_promotion_stats.get(u_id, {"opens": 0, "dismissals": 0})
    daily = _INDEX.daily_load.get(u_id, 0)
    
    # Reason about promotion dismissals
    dismisses_promotions = (promo["dismissals"] > 0) and (promo["dismissals"] > promo["opens"])
    
    return {
        "user_id": u_id,
        "total_opens": stats["opens"],
        "total_replies": stats["replies"],
        "total_dismissals": stats["dismissals"],
        "total_reports": stats["reports"],
        "daily_notification_load": daily,
        "dismisses_promotions": dismisses_promotions
    }

def get_sender_history(user_id: str, sender_id: str) -> Dict[str, Any]:
    """Retrieves historical interaction between a user and a specific sender."""
    u_id, s_id = str(user_id), str(sender_id)
    if s_id in _INDEX.sender_interactions.get(u_id, {}):
        stats = _INDEX.sender_interactions[u_id][s_id]
        
        opens = stats["opens"]
        replies = stats["replies"]
        dismissals = stats["dismissals"]
        reports = stats["reports"]
        total_interactions = opens + replies + dismissals + reports
        
        # Historical reasoning flags
        has_replied_recently = replies > 0
        has_ignored = (dismissals > opens) and (dismissals > 0)
        has_been_reported = reports > 0
        usually_opens = (opens / total_interactions > 0.5) if total_interactions > 0 else False
        
        return {
            "has_interaction": True,
            "opens": opens,
            "replies": replies,
            "dismissals": dismissals,
            "reports": reports,
            "has_replied_recently": has_replied_recently,
            "has_ignored": has_ignored,
            "has_been_reported": has_been_reported,
            "usually_opens": usually_opens
        }
        
    return {
        "has_interaction": False,
        "opens": 0,
        "replies": 0,
        "dismissals": 0,
        "reports": 0,
        "has_replied_recently": False,
        "has_ignored": False,
        "has_been_reported": False,
        "usually_opens": False
    }

def get_group_history(user_id: str, group_id: str) -> Dict[str, Any]:
    """Retrieves a user's status and history within a specific group."""
    u_id, g_id = str(user_id), str(group_id)
    if g_id in _INDEX.group_status.get(u_id, {}):
        return _INDEX.group_status[u_id][g_id]
    return {"is_member": False, "is_muted": False, "role": "none"}

def get_business_history(user_id: str, business_id: str) -> Dict[str, Any]:
    """Retrieves the historical relationship between a user and a business."""
    u_id, b_id = str(user_id), str(business_id)
    if b_id in _INDEX.business_relations.get(u_id, {}):
        biz_data = _INDEX.business_relations[u_id][b_id]
        
        # Historical reasoning flags
        recent_orders = biz_data.get("recent_orders", 0)
        has_ordered_recently = recent_orders > 0
        
        return {
            "is_verified": biz_data.get("is_verified", False),
            "recent_orders": recent_orders,
            "total_spent": biz_data.get("total_spent", 0.0),
            "has_ordered_recently": has_ordered_recently
        }
        
    return {
        "is_verified": False, 
        "recent_orders": 0, 
        "total_spent": 0.0,
        "has_ordered_recently": False
    }

def find_similar_messages(user_id: str, text: str, threshold: float = 0.8) -> List[Dict[str, Any]]:
    """
    Finds historically similar messages for the user using fast Jaccard similarity.
    """
    u_id = str(user_id)
    if not text or u_id not in _INDEX.user_messages:
        return []
    
    words_target = set(str(text).lower().split())
    if not words_target:
        return []
        
    similar = []
    for msg in _INDEX.user_messages[u_id]:
        raw_text = msg.get('text', '')
        if not isinstance(raw_text, str) or not raw_text.strip():
            continue
            
        msg_text = raw_text.lower()
        words_msg = set(msg_text.split())
            
        intersection = len(words_target.intersection(words_msg))
        union = len(words_target.union(words_msg))
        score = intersection / union if union > 0 else 0.0
        
        if score >= threshold:
            similar.append(msg)
            
    return similar

def find_recent_related_messages(user_id: str, sender_id: str) -> List[Dict[str, Any]]:
    """
    Finds recent messages from the same sender to the user.
    """
    u_id, s_id = str(user_id), str(sender_id)
    if u_id not in _INDEX.user_messages:
        return []
        
    related = []
    for msg in _INDEX.user_messages[u_id]:
        if str(msg.get('sender_id', '')) == s_id:
            related.append(msg)
            
    # Sort by timestamp if it exists, otherwise just return as is (latest first assumption)
    return related[::-1][:10] # Return up to 10 most recent

def get_evidence_message_ids(user_id: str, sender_id: str = None, group_id: str = None) -> List[str]:
    """
    Gathers past message IDs that serve as evidence for routing decisions.
    """
    u_id = str(user_id)
    if u_id not in _INDEX.user_messages:
        return []
        
    evidence_ids = []
    # Traverse in reverse to get most recent first
    for msg in reversed(_INDEX.user_messages[u_id]):
        m_sender = str(msg.get('sender_id', ''))
        m_group = str(msg.get('group_id', ''))
        m_id = str(msg.get('message_id', ''))
        
        if not m_id:
            continue
            
        if sender_id and m_sender == str(sender_id):
            evidence_ids.append(m_id)
        elif group_id and m_group == str(group_id):
            evidence_ids.append(m_id)
            
        if len(evidence_ids) >= 5: # Limit to top 5 evidence IDs
            break
            
    return evidence_ids
