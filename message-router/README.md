# Message Notification Router

## Overview

Modern digital communication produces an overwhelming volume of messages from personal contacts, business updates, groups, promotions, and spam. To prevent alert fatigue and ensure critical information is never missed, notification routing requires intelligent personalization. A one-size-fits-all approach fails because a message that is vital to one user (e.g., a delivery update from a frequently used business) might be annoying spam to another.

The **Message Notification Router** is a high-performance routing pipeline built for the HackerRank Orchestrate challenge. It analyzes incoming text and multimodal messages, correlates them with rich historical behavioral data, and intelligently categorizes them into one of three strict actions: `notify`, `digest`, or `mute`. 

## Features

This project implements a deterministic, highly explainable routing framework equipped with the following capabilities:

- **Rule-Based Routing Engine:** Evaluates messages against prioritized, independent rules to determine the optimal notification action.
- **Historical User Behavior Analysis:** Leverages past interaction data (opens, replies, dismissals) to predict user intent.
- **Business Relationship Analysis:** Distinguishes between trusted, verified businesses with active transaction histories versus unsolicited promotional spam.
- **Group Behavior Analysis:** Respects user roles and mute states across group conversations.
- **Spam and Scam Detection:** Identifies malicious keywords, viral chain-forwards, and previously reported senders to automatically mute harmful content.
- **Payment & Event Detection:** Prioritizes urgent transactional and temporal messages (e.g., OTPs, bills due today, imminent meetings).
- **Promotion Handling:** Silences low-value marketing content into daily digests unless the user has strong historical engagement with the brand.
- **Confidence Scoring:** Calculates bounded confidence metrics for every routing decision based on rule strength and priority resolution.
- **Evidence Message Retrieval:** Surfaces historical message IDs that justify the routing decision.
- **Modular Architecture:** Cleanly separates data loading, feature extraction, historical indexing, business logic (rules), and output formatting.

## Architecture

The system avoids monolithic deep-learning classifiers in favor of an easily extensible, modular pipeline. Data flows sequentially from loading, to preprocessing, through the rule engine, and finally to strict output generation.

- **`preprocess.py`**: Extracts normalized features from raw message text (e.g., detecting URLs, money formatting, dates, phone numbers, and semantic keywords).
- **`history.py`**: Constructs highly optimized `$O(1)$` dictionary indexes from raw relational CSVs (events, group members, business interactions), ensuring lightning-fast lookup during the routing phase without slow Pandas filtering.
- **`media.py`**: Provides structural placeholders and safe fallbacks for multimodal extraction (handling images and audio) without breaking if dependencies are missing.
- **`rules.py`**: The core business logic layer containing independent scoring functions (e.g., `rule_urgent`, `rule_scam`, `rule_verified_business`). Each rule acts as an isolated heuristic.
- **`router.py`**: The central orchestrator. It runs the incoming message through all rules, resolves priority conflicts (e.g., Scam overrides Business Update), and calculates the final confidence and reason.
- **`output.py`**: Enforces strict schema constraints, validates data integrity, and generates the final CSV submission.
- **`engine.py`**: A side-effect-free, stateful wrapper around the pipeline that allows the system to be imported cleanly by other interfaces (like the CLI).
- **`main.py`**: The primary execution entry point that automatically runs the end-to-end pipeline.

## Folder Structure

```text
message-router/
├── dataset/                     # Historical behavior and incoming message CSVs
├── outputs/                     # Target directory for generated output.csv
├── src/
│   ├── cli/                     # Interactive terminal framework
│   ├── __init__.py
│   ├── engine.py                # Reusable prediction engine API
│   ├── history.py               # O(1) historical indexing logic
│   ├── load_data.py             # CSV loading utilities
│   ├── media.py                 # Multimodal fallback handling
│   ├── output.py                # HackerRank schema validation & writing
│   ├── preprocess.py            # Regex and keyword feature extraction
│   ├── router.py                # Conflict resolution and orchestration
│   ├── rules.py                 # Independent routing rules
│   └── utils.py
├── interactive.py               # Interactive CLI for debugging and simulation
├── main.py                      # Automated batch execution entry point
├── pre_submission_audit.md      # QA audit report
└── requirements.txt             # Python dependencies
```

## Installation

It is recommended to run this project inside a Python virtual environment.

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

To run the full automated prediction pipeline, you must execute the script from the `code/` directory (or use its path):

```bash
cd code
python3 main.py
```

The system will load the data, execute the rules, print a console summary, and generate the final predictions at `code/outputs/output.csv`.

To explore the pipeline interactively, you can launch the CLI:

```bash
cd code
python3 interactive.py
```
*(Available commands include `predict`, `explain`, `debug`, `insights`, `simulate`, `inspect`, and `analytics`.)*

## Design Decisions

- **Modular Rule Engine over Monolithic Classifier:** A rule-based architecture was chosen explicitly to guarantee **explainability** and **determinism**. While an LLM or deep neural network might offer fuzzy categorization, they are prone to hallucination and lack clear audit trails. In a notification router, it is critical to know *exactly why* an urgent OTP was prioritized or a scam message was muted. The modular engine provides concrete reasons and exact confidence scores.
- **Historical Personalization:** Static keyword rules are insufficient because user intent varies. By indexing behavioral history (like how often a user dismisses promotions or if they recently purchased from a brand), the system creates a dynamic context that drastically reduces false positives and over-notification.
- **Explainability as a Core Tenet:** Trust is paramount. Generating a plain-text `reason` and linking specific `evidence_message_ids` allows end-users (or QA engineers) to verify the routing logic. The `interactive.py` tool heavily leverages this to provide detailed debug traces.

## Performance

The pipeline is optimized for speed. Rather than performing expensive `DataFrame.merge()` or `.loc[]` lookups for every incoming message, `history.py` parses the entire historical dataset upfront upon initialization. It builds deeply nested Python dictionaries, allowing the router to fetch complex historical relationships (e.g., `sender_interactions[user_id][sender_id]`) in constant `$O(1)$` time. As a result, the entire evaluation pipeline for all incoming messages executes in fractions of a second.

## Future Improvements

While this system is feature-complete for the HackerRank Orchestrate baseline, realistic future improvements could include:

- **LLM-Powered Explanations:** Integrating a lightweight local LLM to generate highly fluid, natural-language explanations of the routing logic for end-user dashboards.
- **Better Multimodal Processing:** Integrating robust OCR engines (Tesseract) and ASR models (Whisper) directly into `media.py` for full text-extraction on images and voice notes.
- **Learning-Based Ranking:** Replacing the static integer rule scores with weights learned dynamically via logistic regression based on ongoing user interactions.
- **Web Dashboard:** Wrapping the prediction engine in a FastAPI server to provide a visual React dashboard for live analytics and simulated routing testing.
