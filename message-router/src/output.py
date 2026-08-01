import pandas as pd
from typing import List, Dict, Any
from src.router import route_message

def generate_predictions(incoming_messages_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Iterates through incoming messages in exact order, runs them through the router,
    and returns a list of prediction dictionaries formatted for output.
    """
    predictions = []
    
    if incoming_messages_df.empty:
        return predictions
        
    # Iterate while preserving order
    for _, row in incoming_messages_df.iterrows():
        message_id = row.get('message_id', '')
        
        # Route the message through the entire pipeline
        route_result = route_message(row)
        
        # Format evidence_message_ids as a comma-separated string for CSV compatibility
        evidence_ids = route_result.get('evidence_message_ids', [])
        if isinstance(evidence_ids, list):
            evidence_str = ",".join(str(e) for e in evidence_ids)
        else:
            evidence_str = str(evidence_ids)
            
        predictions.append({
            "message_id": message_id,
            "action": route_result.get('action', 'none'),
            "message_type": route_result.get('message_type', 'unknown'),
            "reason": route_result.get('reason', ''),
            "confidence": route_result.get('confidence', 0.0),
            "evidence_message_ids": evidence_str
        })
        
    return predictions

def write_output_csv(predictions: List[Dict[str, Any]], output_path: str) -> None:
    """
    Writes the predictions to a CSV file matching the exact HackerRank schema.
    """
    required_columns = [
        'message_id', 
        'action', 
        'message_type', 
        'reason', 
        'confidence', 
        'evidence_message_ids'
    ]
    
    # Load into DataFrame
    df = pd.DataFrame(predictions)
    
    # Ensure all required columns exist (important if the predictions list was empty)
    for col in required_columns:
        if col not in df.columns:
            df[col] = None
            
    # Enforce exact column ordering
    df = df[required_columns]
    
    # Write to CSV without the pandas index to ensure valid formatting
    df.to_csv(output_path, index=False)
