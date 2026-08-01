import os
import logging
import pandas as pd
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolve dataset directory reliably by navigating up from this file's location
# code/src/load_data.py -> code/src -> code -> repo_root -> dataset
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATASET_DIR = str((REPO_ROOT / "dataset").resolve())

def load_csv_safely(file_path: str) -> pd.DataFrame:
    """
    Loads a CSV file safely.
    Returns an empty DataFrame if the file doesn't exist or is unreadable.
    """
    if not os.path.exists(file_path):
        logger.warning(f"Dataset not found at {file_path}. Returning an empty DataFrame.")
        return pd.DataFrame()
    
    try:
        # Read CSV and handle basic parsing
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} rows from {os.path.basename(file_path)}")
        return df
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return pd.DataFrame()

def load_all_datasets(dataset_dir: str = DEFAULT_DATASET_DIR) -> Dict[str, pd.DataFrame]:
    """
    Loads all historical datasets and incoming messages from the dataset directory.
    
    Returns:
        A dictionary containing all DataFrames required by the pipeline.
    """
    datasets = {}
    
    # Resolve absolute or relative paths gracefully
    base_dir = os.path.abspath(dataset_dir)
    
    # File paths based on the problem statement requirements
    files_to_load = {
        'message_history': 'message_history.csv',
        'message_events': 'message_events.csv',
        'group_members': 'group_members.csv',
        'user_business_history': 'user_business_history.csv',
        'daily_summary': 'daily_notification_summary.csv',
        'incoming_messages': 'messages.csv'
    }
    
    # Load each dataset
    for key, filename in files_to_load.items():
        full_path = os.path.join(base_dir, filename)
        datasets[key] = load_csv_safely(full_path)
        
    return datasets
