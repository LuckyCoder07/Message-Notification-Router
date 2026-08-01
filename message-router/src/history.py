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
        self.user_events: Dict[str, Dict[str, int]] = defaultdict(lambda: {"opens": 0, "replies": 0, "dismissals": 0, "reports": 0, "mutes": 0})
        
        # user_id -> sender_id -> stats
        self.sender_interactions: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(lambda: defaultdict(lambda: {"opens": 0, "replies": 0, "dismissals": 0, "reports": 0}))
        
        # user_id -> promotion_stats
        self.user_promotion_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"opens": 0, "dismissals": 0})
        
        # user_id -> group_id -> stats
        self.group_status: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(lambda: {"is_member": False, "is_muted": False, "role": "member"}))
        
        # user_id -> business_id -> stats
        self.business_relations: Dict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(lambda: {
            "is_verified": False, "has_ordered_recently": False, "activity_count": 0,
            "messages_opened": 0, "messages_dismissed": 0, "messages_replied": 0,
            "allows_promotions": False, "relationship": "unknown"
        }))
        
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
    
    Handles the actual dataset schema:
    - message_events has binary columns: message_opened, message_replied, 
      notification_dismissed, message_reported, muted_after_message
    - group_members has: group_muted_by_user (not is_muted)
    - user_business_history has: activity_count_180d, messages_opened_30d, etc.
    """
    global _INDEX
    _INDEX = HistoryIndex()
    
    # 1. Process message_history — build user_messages index for similarity search
    #    Also link message_id -> sender for cross-referencing with events
    msg_sender_map: Dict[str, str] = {}  # message_id -> sender_user_id
    msg_biz_map: Dict[str, str] = {}     # message_id -> conversation_type
    
    if not message_history_df.empty:
        for _, row in message_history_df.iterrows():
            user = str(row.get('user_id', ''))
            msg_id = str(row.get('message_id', ''))
            sender = str(row.get('sender_user_id', ''))
            conv_type = str(row.get('conversation_type', ''))
            
            if user:
                _INDEX.user_messages[user].append(row.to_dict())
                
            if msg_id and sender and sender != 'nan':
                msg_sender_map[msg_id] = sender
            if msg_id:
                msg_biz_map[msg_id] = conv_type

    # 2. Process message_events — binary columns, not event_type
    #    Cross-reference with message_history to get sender_user_id per event
    if not message_events_df.empty:
        for _, row in message_events_df.iterrows():
            user = str(row.get('user_id', ''))
            msg_id = str(row.get('message_id', ''))
            
            if not user:
                continue
            
            opened = int(row.get('message_opened', 0))
            replied = int(row.get('message_replied', 0))
            dismissed = int(row.get('notification_dismissed', 0))
            reported = int(row.get('message_reported', 0))
            muted = int(row.get('muted_after_message', 0))
            
            # Aggregate at the user level
            _INDEX.user_events[user]['opens'] += opened
            _INDEX.user_events[user]['replies'] += replied
            _INDEX.user_events[user]['dismissals'] += dismissed
            _INDEX.user_events[user]['reports'] += reported
            _INDEX.user_events[user]['mutes'] += muted
            
            # Cross-reference sender from the message_history map
            sender = msg_sender_map.get(msg_id, '')
            if sender and sender != 'nan':
                _INDEX.sender_interactions[user][sender]['opens'] += opened
                _INDEX.sender_interactions[user][sender]['replies'] += replied
                _INDEX.sender_interactions[user][sender]['dismissals'] += dismissed
                _INDEX.sender_interactions[user][sender]['reports'] += reported
                
            # Track promotion engagement if the event came from a business conversation
            conv_type = msg_biz_map.get(msg_id, '')
            if conv_type == 'business':
                _INDEX.user_promotion_stats[user]['opens'] += opened
                _INDEX.user_promotion_stats[user]['dismissals'] += dismissed

    # 3. Process group_members — uses group_muted_by_user, not is_muted
    if not group_members_df.empty:
        for _, row in group_members_df.iterrows():
            user = str(row.get('user_id', ''))
            group = str(row.get('group_id', ''))
            if user and group:
                _INDEX.group_status[user][group] = {
                    "is_member": True,
                    "is_muted": bool(int(row.get('group_muted_by_user', row.get('is_muted', 0)))),
                    "role": str(row.get('role', 'member')),
                    "messages_read_30d": int(row.get('messages_read_30d', 0)),
                    "replies_sent_30d": int(row.get('replies_sent_30d', 0)),
                    "notifications_dismissed_30d": int(row.get('notifications_dismissed_30d', 0))
                }

    # 4. Process user_business_history — no is_verified/recent_orders; derive from schema
    if not user_business_history_df.empty:
        for _, row in user_business_history_df.iterrows():
            user = str(row.get('user_id', ''))
            biz = str(row.get('business_id', ''))
            if user and biz:
                relationship = str(row.get('why_user_knows_account', 'unknown'))
                activity_count = int(row.get('activity_count_180d', 0))
                msgs_opened = int(row.get('messages_opened_30d', 0))
                msgs_dismissed = int(row.get('messages_dismissed_30d', 0))
                msgs_replied = int(row.get('messages_replied_30d', 0))
                allows_promotions = bool(int(row.get('allows_promotions', 0)))
                
                # Derive is_verified: active accounts (bank, subscription, booking) are "verified"
                active_keywords = ['active', 'recent', 'confirmed', 'upcoming', 'monthly']
                is_verified = any(kw in relationship for kw in active_keywords)
                
                # Derive has_ordered_recently from activity count and relationship
                has_ordered_recently = activity_count >= 3 or 'recent' in relationship
                
                _INDEX.business_relations[user][biz] = {
                    "is_verified": is_verified,
                    "has_ordered_recently": has_ordered_recently,
                    "activity_count": activity_count,
                    "messages_opened": msgs_opened,
                    "messages_dismissed": msgs_dismissed,
                    "messages_replied": msgs_replied,
                    "allows_promotions": allows_promotions,
                    "relationship": relationship
                }

    # 5. Process daily_notification_summary
    if not daily_summary_df.empty:
        for _, row in daily_summary_df.iterrows():
            user = str(row.get('user_id', ''))
            count = int(row.get('notifications_sent', 0))
            if user:
                # Accumulate total across all days in the dataset
                _INDEX.daily_load[user] += count

def get_user_history(user_id: str) -> Dict[str, Any]:
    """Retrieves overall historical engagement for a user."""
    u_id = str(user_id)
    stats = _INDEX.user_events.get(u_id, {"opens": 0, "replies": 0, "dismissals": 0, "reports": 0, "mutes": 0})
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
    
    if s_id and s_id != 'nan' and s_id in _INDEX.sender_interactions.get(u_id, {}):
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
    if g_id and g_id != 'nan' and g_id in _INDEX.group_status.get(u_id, {}):
        return _INDEX.group_status[u_id][g_id]
    return {"is_member": False, "is_muted": False, "role": "none"}

def get_business_history(user_id: str, business_id: str) -> Dict[str, Any]:
    """Retrieves the historical relationship between a user and a business."""
    u_id, b_id = str(user_id), str(business_id)
    if b_id and b_id != 'nan' and b_id in _INDEX.business_relations.get(u_id, {}):
        return _INDEX.business_relations[u_id][b_id]
        
    return {
        "is_verified": False, 
        "has_ordered_recently": False,
        "activity_count": 0,
        "messages_opened": 0,
        "messages_dismissed": 0,
        "messages_replied": 0,
        "allows_promotions": False,
        "relationship": "unknown"
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
        # Handle both 'message_text' and 'text' column names
        raw_text = msg.get('message_text', msg.get('text', ''))
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
        # Handle both 'sender_user_id' and 'sender_id' column names
        msg_sender = str(msg.get('sender_user_id', msg.get('sender_id', '')))
        if msg_sender == s_id:
            related.append(msg)
            
    # Return up to 10 most recent (reverse for latest first)
    return related[::-1][:10]

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
        # Handle both column name conventions
        m_sender = str(msg.get('sender_user_id', msg.get('sender_id', '')))
        m_group = str(msg.get('group_id', ''))
        m_id = str(msg.get('message_id', ''))
        
        if not m_id or m_id == 'nan':
            continue
            
        if sender_id and sender_id != 'nan' and m_sender == str(sender_id):
            evidence_ids.append(m_id)
        elif group_id and group_id != 'nan' and m_group == str(group_id):
            evidence_ids.append(m_id)
            
        if len(evidence_ids) >= 5: # Limit to top 5 evidence IDs
            break
            
    return evidence_ids
