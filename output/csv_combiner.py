import pandas as pd
from pathlib import Path

files = sorted(Path(".").glob("free_agents_page*.csv"))

if not files:
    raise FileNotFoundError("No free_agents_page*.csv files found.")

df = pd.concat(
    [pd.read_csv(file) for file in files],
    ignore_index=True
)

# Remove rows without a Yahoo player ID, then deduplicate.
df["yahoo_id"] = df["yahoo_id"].astype(str)
df = df[df["yahoo_id"].str.strip().ne("")]
df = df.drop_duplicates(subset="yahoo_id", keep="last")

df.to_csv("free_agents.csv", index=False)

print(f"Combined {len(files)} files.")
print(f"Saved {len(df)} unique players to free_agents.csv.")
