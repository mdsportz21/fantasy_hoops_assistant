
import csv
import io
import subprocess
from pathlib import Path

import pandas as pd

CSV_FILE = Path(__file__).parent / "free_agents.csv"
COLUMNS = ["player_name", "yahoo_id", "row_data"]


def main():
    # Read the CSV copied by your Chrome Console script.
    result = subprocess.run(
        ["pbpaste"],
        capture_output=True,
        text=True,
        check=True
    )
    clipboard_text = result.stdout.strip()

    if not clipboard_text:
        print("Clipboard is empty. Run the Yahoo export script first.")
        return

    # Parse clipboard CSV.
    new = pd.read_csv(
        io.StringIO(clipboard_text),
        dtype=str,
        keep_default_na=False
    )

    missing = [col for col in COLUMNS if col not in new.columns]
    if missing:
        print(f"Clipboard CSV is missing columns: {missing}")
        return

    new = new[COLUMNS].copy()
    new["yahoo_id"] = new["yahoo_id"].str.strip()
    new = new[new["yahoo_id"] != ""]
    new = new.drop_duplicates(subset="yahoo_id", keep="last")

    # Load existing data, if present.
    if CSV_FILE.exists() and CSV_FILE.stat().st_size:
        old = pd.read_csv(
            CSV_FILE,
            dtype=str,
            keep_default_na=False
        )[COLUMNS]

        combined = pd.concat([old, new], ignore_index=True)
    else:
        combined = new.copy()

    # Keep one row per Yahoo ID. New clipboard data takes precedence.
    before = len(combined)
    combined = combined.drop_duplicates(
        subset="yahoo_id",
        keep="last"
    )
    removed = before - len(combined)

    # Save updated CSV.
    combined.to_csv(CSV_FILE, index=False, quoting=csv.QUOTE_MINIMAL)

    print(f"Clipboard players processed: {len(new)}")
    print(f"Duplicate rows replaced/removed: {removed}")
    print(f"Total unique players: {len(combined)}")
    print(f"Updated file: {CSV_FILE}")


if __name__ == "__main__":
    main()
