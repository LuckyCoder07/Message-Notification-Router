import pandas as pd
from typing import List, Dict, Any
from src.router import route_message

import logging

logger = logging.getLogger(__name__)

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
        
        # Format evidence_message_ids as a semicolon-separated string or "none"
        evidence_ids = route_result.get('evidence_message_ids', [])
        if isinstance(evidence_ids, list) and evidence_ids:
            evidence_str = ";".join(str(e) for e in evidence_ids)
        elif evidence_ids and str(evidence_ids).strip() != "":
            evidence_str = str(evidence_ids).replace(',', ';')
        else:
            evidence_str = "none"
            
        reason = route_result.get('reason', '')
        if not reason or str(reason).strip() == "" or pd.isna(reason):
            reason = "Default fallback reason applied."
            
        confidence = route_result.get('confidence', 0.60)
        if pd.isna(confidence):
            confidence = 0.60
            
        predictions.append({
            "message_id": message_id,
            "action": route_result.get('action', 'digest'),
            "message_type": route_result.get('message_type', 'unknown'),
            "reason": reason,
            "confidence": float(confidence),
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
    
    # Validation step as required by Task 3
    for idx, pred in enumerate(predictions):
        missing = [col for col in required_columns if pred.get(col) is None or str(pred.get(col)).strip() == "" or pd.isna(pred.get(col))]
        if missing:
            logger.error(f"Validation failed at row {idx}. Missing required fields: {missing}. Row data: {pred}")
            raise ValueError(f"Output validation failed: missing {missing} in prediction row.")
            
    # Load into DataFrame
    df = pd.DataFrame(predictions)
    
    # Enforce exact column ordering
    df = df[required_columns]
    
    # Write to CSV without the pandas index to ensure valid formatting
    df.to_csv(output_path, index=False)
