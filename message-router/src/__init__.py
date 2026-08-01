"""
Message Notification Router — Prediction Engine
================================================

This package exposes the complete routing engine as an importable library.
It does NOT execute the pipeline on import. All side effects are deferred
until the caller explicitly initialises and runs the engine.

Public API
----------

Quick start (high-level):

    from src import PredictionEngine

    engine = PredictionEngine()
    engine.load()          # Load datasets and build indexes
    predictions = engine.predict()
    engine.write(predictions)

Low-level (individual modules):

    from src.preprocess import build_features
    from src.history import build_history_indexes, get_user_history
    from src.rules import rule_scam, rule_payment
    from src.router import route_message
    from src.output import generate_predictions, write_output_csv
    from src.media import process_media
    from src.load_data import load_all_datasets
"""

from src.engine import PredictionEngine

__all__ = ["PredictionEngine"]
