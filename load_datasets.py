from pathlib import Path

import pandas as pd

base_dir = Path(__file__).resolve().parent

# Load the main datasets referenced in the request.
messages = pd.read_csv(base_dir / "dataset" / "messages.csv")
users = pd.read_csv(base_dir / "dataset" / "users.csv")
groups = pd.read_csv(base_dir / "dataset" / "groups.csv")
history = pd.read_csv(base_dir / "dataset" / "message_history.csv")

# Print the requested inspection for each dataset.
for name, df in [("messages", messages), ("users", users), ("groups", groups), ("history", history)]:
    print(f"\n===== {name.upper()} =====")
    print(df.head())
    print(df.columns)
    print(df.info())

# Also load every other CSV in the dataset folder.
for csv_path in sorted((base_dir / "dataset").glob("*.csv")):
    if csv_path.stem in {"messages", "users", "groups", "message_history"}:
        continue

    df = pd.read_csv(csv_path)
    print(f"\n===== {csv_path.stem.upper()} =====")
    print(df.head())
    print(df.columns)
    print(df.info())
