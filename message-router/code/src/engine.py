"""
src/engine.py — PredictionEngine
=================================

A stateful wrapper around the complete prediction pipeline.
Importing this module has zero side effects.
All I/O and computation happen only when the caller invokes the methods.

Intended usage
--------------

    engine = PredictionEngine()
    engine.load()
    predictions = engine.predict()
    engine.write(predictions)

Or in a single call:

    predictions = PredictionEngine().load().predict()

The engine is designed so every step is independently reusable:
- load()    → loads datasets, builds history indexes
- predict() → runs all messages through the routing pipeline
- write()   → serialises predictions to the output CSV
- route()   → routes a single raw message dict (useful for testing)
"""

import logging
import pandas as pd
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PredictionEngine:
    """
    Encapsulates the full message routing prediction pipeline.

    The engine holds no global state of its own — it delegates to the
    individual procedural modules (history, router, output, etc.) which
    manage their own module-level state.  This class exists purely to
    provide a clean, importable API with no module-level side effects.
    """

    from pathlib import Path
    
    _BASE_DIR = Path(__file__).resolve().parent.parent
    _REPO_ROOT = _BASE_DIR.parent
    
    DEFAULT_DATASET_DIR: str = str((_REPO_ROOT / "dataset").resolve())
    DEFAULT_OUTPUT_PATH: str = str((_BASE_DIR / "outputs" / "output.csv").resolve())

    def __init__(
        self,
        dataset_dir: str = DEFAULT_DATASET_DIR,
        output_path: str = DEFAULT_OUTPUT_PATH,
    ) -> None:
        self.dataset_dir = dataset_dir
        self.output_path = output_path

        # DataFrames populated by load()
        self._datasets: Dict[str, pd.DataFrame] = {}
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, dataset_dir: Optional[str] = None) -> "PredictionEngine":
        """
        Load all datasets from disk and build the history indexes.

        Defers all heavy I/O to this explicit call so that importing
        the engine never triggers file reads or DataFrame construction.

        Args:
            dataset_dir: Override the dataset directory path if needed.

        Returns:
            self, to allow method chaining: engine.load().predict()
        """
        # Import here, not at module level — keeps top-level import side-effect free
        from src.load_data import load_all_datasets
        from src.history import build_history_indexes

        directory = dataset_dir or self.dataset_dir
        logger.info(f"PredictionEngine: loading datasets from '{directory}'…")

        self._datasets = load_all_datasets(directory)

        logger.info("PredictionEngine: building history indexes…")
        build_history_indexes(
            message_history_df=self._datasets.get("message_history", pd.DataFrame()),
            message_events_df=self._datasets.get("message_events", pd.DataFrame()),
            group_members_df=self._datasets.get("group_members", pd.DataFrame()),
            user_business_history_df=self._datasets.get("user_business_history", pd.DataFrame()),
            daily_summary_df=self._datasets.get("daily_summary", pd.DataFrame()),
        )

        self._loaded = True
        return self

    def predict(self) -> List[Dict[str, Any]]:
        """
        Run the routing pipeline over every incoming message.

        Must be called after load().

        Returns:
            A list of prediction dicts, one per incoming message,
            in the original dataset order.
        """
        self._require_loaded("predict")

        from src.output import generate_predictions

        incoming = self._datasets.get("incoming_messages", pd.DataFrame())
        logger.info(f"PredictionEngine: generating predictions for {len(incoming)} messages…")
        return generate_predictions(incoming)

    def write(self, predictions: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
        """
        Write predictions to a CSV file matching the HackerRank schema.

        Args:
            predictions: The list returned by predict().
            output_path:  Override the default output path if needed.

        Returns:
            The absolute path written to.
        """
        from src.output import write_output_csv

        path = output_path or self.output_path
        logger.info(f"PredictionEngine: writing {len(predictions)} predictions to '{path}'…")
        write_output_csv(predictions, path)
        return path

    def route(self, message: Dict[str, Any], explain: bool = False) -> Dict[str, Any]:
        """
        Route a single message dict through the full pipeline.

        Useful for unit testing individual messages without running the
        entire batch, or for integrating the engine into a real-time
        service that processes one message at a time.

        Args:
            message: A dict with the same schema as a row in messages.csv.
            explain: If True, include detailed internal state for debugging.

        Returns:
            A prediction dict: {action, message_type, reason, confidence,
            evidence_message_ids, [_explanation]}
        """
        from src.router import route_message

        return route_message(message, explain=explain)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        """True after load() has been called successfully."""
        return self._loaded

    @property
    def incoming_messages(self) -> pd.DataFrame:
        """The raw incoming messages DataFrame (available after load())."""
        self._require_loaded("incoming_messages")
        return self._datasets.get("incoming_messages", pd.DataFrame())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _require_loaded(self, caller: str) -> None:
        if not self._loaded:
            raise RuntimeError(
                f"PredictionEngine.{caller}() called before load(). "
                "Call engine.load() first."
            )
