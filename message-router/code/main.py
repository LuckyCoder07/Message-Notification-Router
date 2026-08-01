import time
import sys
import logging
import pandas as pd

from src.load_data import load_all_datasets
from src.history import build_history_indexes
from src.output import generate_predictions, write_output_csv

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_summary(predictions: list, execution_time: float) -> None:
    """Prints a clear summary of the pipeline execution."""
    total = len(predictions)
    notify = sum(1 for p in predictions if p.get('action') == 'notify')
    digest = sum(1 for p in predictions if p.get('action') == 'digest')
    mute = sum(1 for p in predictions if p.get('action') == 'mute')
    avg_conf = sum(p.get('confidence', 0.0) for p in predictions) / total if total > 0 else 0.0
    
    logger.info("========================================")
    logger.info("PIPELINE SUMMARY")
    logger.info("========================================")
    logger.info(f"Execution Time    : {execution_time:.2f} seconds")
    logger.info(f"Total Messages    : {total}")
    logger.info(f"Notify Count      : {notify}")
    logger.info(f"Digest Count      : {digest}")
    logger.info(f"Mute Count        : {mute}")
    logger.info(f"Average Confidence: {avg_conf:.2f}")
    logger.info("========================================")

def main():
    start_time = time.time()
    logger.info("Starting Message Notification Router Pipeline...")
    
    try:
        # 1. Load Data
        logger.info("Loading datasets...")
        # Assuming load_all_datasets returns a dict of DataFrames
        datasets = load_all_datasets() 
        
        message_history_df = datasets.get('message_history', pd.DataFrame())
        message_events_df = datasets.get('message_events', pd.DataFrame())
        group_members_df = datasets.get('group_members', pd.DataFrame())
        user_business_history_df = datasets.get('user_business_history', pd.DataFrame())
        daily_summary_df = datasets.get('daily_summary', pd.DataFrame())
        incoming_messages_df = datasets.get('incoming_messages', pd.DataFrame())
        
        # 2. Build Indexes
        logger.info("Building historical indexes for fast lookups...")
        build_history_indexes(
            message_history_df=message_history_df,
            message_events_df=message_events_df,
            group_members_df=group_members_df,
            user_business_history_df=user_business_history_df,
            daily_summary_df=daily_summary_df
        )
        
        # 3. Generate Predictions
        logger.info(f"Generating predictions for {len(incoming_messages_df)} incoming messages...")
        predictions = generate_predictions(incoming_messages_df)
        
        # 4. Write Output
        import os
        from pathlib import Path
        BASE_DIR = Path(__file__).resolve().parent
        output_path = str(BASE_DIR / "outputs" / "output.csv")
        logger.info(f"Writing predictions to {output_path}...")
        write_output_csv(predictions, output_path)
        
        # 5. Print Summary
        execution_time = time.time() - start_time
        print_summary(predictions, execution_time)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed due to a critical exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
