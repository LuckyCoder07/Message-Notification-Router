# Message Notification Router

## Project Overview
The **Message Notification Router** is a high-performance message routing pipeline built for the HackerRank Orchestrate 2026 challenge. It analyzes incoming multimodal messages and intelligently routes them into three actionable categories: `notify`, `digest`, or `mute`. 

Additionally, it categorizes messages into specific types (e.g., personal, urgent, payment, spam, scam) and generates confidence scores, detailed reasoning, and historical evidence IDs to ensure complete explainability.

## Design Decisions
### Modular Rule-Based Architecture vs. Monolithic Classifier
This system leverages a highly modular, rule-based architecture orchestrated by a central router, explicitly avoiding a monolithic black-box classifier (such as a massive LLM prompt or a single complex deep learning model). 

**Why this approach?**
1. **Explainability & Trust:** In a consumer messaging application, users must know *why* a message was muted or prioritized. Independent rules generate distinct evidence scores and clear text reasons, providing a transparent audit trail.
2. **Determinism:** A rule-based scoring engine ensures that specific critical triggers (e.g., OTPs or severe Scam keywords) consistently result in the same strict action, passing automated evaluations perfectly without the risk of hallucination.
3. **Blazing Fast Performance:** Nested dictionary lookups (`O(1)` time complexity) and regex-based feature extraction execute in microseconds. This is vastly more efficient and scalable than running heavy machine learning inference on every single incoming message.
4. **Maintainability:** New routing behaviors can be introduced simply by dropping a new isolated `rule_*` function into `rules.py` without retraining models, breaking existing logic, or managing complex dependency injection.

## Architecture
The system is divided into strict, decoupled modules. The router orchestrates the flow without containing any business logic, while the business logic lives entirely inside the independent rules.

### Folder Structure
```text
message-router/
│
├── dataset/             # Contains historical CSVs, message data, and media
├── src/
│   ├── load_data.py     # Safely loads Pandas DataFrames and validates paths
│   ├── preprocess.py    # Extracts keywords, flags, and normalizes text
│   ├── history.py       # Fast dictionary-based historical indexing engine
│   ├── media.py         # OCR and Audio Speech-to-Text extraction
│   ├── rules.py         # Independent routing rules providing evidence scores
│   ├── router.py        # Central orchestrator handling the execution flow
│   ├── output.py        # Generates the exact HackerRank output format
│   └── utils.py         # Shared utility functions
├── tests/               # Unit testing directory
├── outputs/             # Generated CSV outputs
├── requirements.txt     # Python dependencies
├── main.py              # Execution entry point
└── README.md            # Project documentation
```

## Pipeline Flow
1. **Load Datasets:** Historical contexts (group info, business relations, user behavior) and incoming messages are loaded into memory.
2. **Build Indexes:** `history.py` parses historical DataFrames to construct rapid `O(1)` dictionary lookups, completely preventing slow DataFrame filtering during the routing loop.
3. **Preprocess:** `preprocess.py` extracts URLs, money, dates, phones, and standardizes text structure without making routing decisions.
4. **Media Handling:** `media.py` extracts text from images (OCR via Tesseract) and voice notes (Whisper). It uses `try/except` blocks to fail gracefully if dependencies are missing, keeping the pipeline robust.
5. **Rule Engine:** `rules.py` executes 19 independent scoring rules against the message, generating scores (e.g., +100 for OTP, -100 for Scam).
6. **Conflict Resolution:** `router.py` gathers all triggered rules, sorts by absolute score magnitude to resolve conflicts (the highest impact wins), and generates confidence metrics.
7. **Output Generation:** `output.py` formats the final `output.csv`, rigorously maintaining original message ordering and column schemas.

## How to Run

### Requirements
The core pipeline depends only on Python standard libraries and Pandas. 
Optional dependencies are provided for multimodal media extraction:
- `pandas` (Core Requirement)
- `pytesseract` & `Pillow` (Optional: Image OCR)
- `openai-whisper` (Optional: Audio Transcription)

### Execution
Ensure you are in the project root directory, then run the pipeline directly:
```bash
python3 main.py
```
This will automatically process the incoming messages against the historical datasets, print an execution summary to standard output, and place the final generated results at `outputs/output.csv`.

## Future Improvements
- **NLP Sentiment Analysis:** Integrating lightweight local NLP models (like VADER) into the preprocessing step for baseline semantic understanding (e.g., detecting anger or urgency through tone).
- **Dynamic Rule Weights:** Instead of static hardcoded scores, rules could fetch weights from an external JSON configuration file to allow non-engineers to tune the system.
- **Timezone Awareness:** Refining `rule_quiet_hours` to utilize the local timezone of the specific user receiving the message, rather than relying on UTC server time heuristics.
