import re
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fantasy Hoops Add/Drop Assistant", layout="wide")
st.title("Fantasy Hoops Add/Drop Assistant")
st.caption("Yahoo 9-category league · personal-use prototype")

ROOT = Path(__file__).parent
CATEGORIES = ["FG%", "FT%", "3PTM", "PTS", "REB", "AST", "STL", "BLK", "TO"]

def read_csv_upload(uploaded, default_name):
    if uploaded is not None:
        return pd.read_csv(uploaded, dtype=str).fillna("")
    path = ROOT / default_name
    if path.exists():
        return pd.read_csv(path, dtype=str).fillna("")
    return pd.DataFrame()


def parse_player_row(row):
    """Parse a single Yahoo row_data string using shooting-attempt cells as anchors."""
    raw = str(row if row is not None else "")
    cells = [
        x.strip()
        for x in raw.replace("\r", "\n").replace("\n", " | ").split("|")
    ]
    cells = [
        re.sub(r"\s+", " ", x).strip()
        for x in cells
    ]

    attempts = [
        i for i, cell in enumerate(cells)
        if re.fullmatch(r"\d+(?:\.\d+)?/\d+(?:\.\d+)?", cell)
    ]

    if len(attempts) < 2:
        return None

    i_fg, i_ft = attempts[0], attempts[1]

    try:
        fgm, fga = map(float, cells[i_fg].split("/"))
        fg_pct = float(cells[i_fg + 1])

        ftm, fta = map(float, cells[i_ft].split("/"))
        ft_cell = cells[i_ft + 1]
        ft_pct = (
            float(ft_cell)
            if ft_cell not in ("-", "")
            else (ftm / fta if fta else 0.0)
        )

        tail = [
            float(cells[j])
            for j in range(i_ft + 2, i_ft + 9)
        ]

        if len(tail) != 7:
            return None

        threes, pts, reb, ast, stl, blk, tov = tail

        return {
            "FGM": fgm, "FGA": fga, "FG%": fg_pct,
            "FTM": ftm, "FTA": fta, "FT%": ft_pct,
            "3PTM": threes, "PTS": pts, "REB": reb,
            "AST": ast, "STL": stl, "BLK": blk, "TO": tov,
        }

    except (ValueError, IndexError):
        return None


def clean_and_parse(df, is_roster=False):
    if df.empty:
        return pd.DataFrame()
    df = df.copy().fillna("")
    for col in ["player_name", "yahoo_id", "row_data"]:
        if col not in df.columns:
            df[col] = ""
    df["player_name"] = df["player_name"].astype(str).str.strip()
    df["yahoo_id"] = df["yahoo_id"].astype(str).str.strip()
    df = df[(df.player_name != "") & (df.player_name.str.lower() != "player_name")]
    df = df[(df.yahoo_id != "") & (df.yahoo_id.str.lower() != "yahoo_id")]
    df = df.drop_duplicates(subset=["yahoo_id"], keep="first")
    parsed = df["row_data"].apply(parse_player_row)
    stats = pd.DataFrame(parsed.tolist(), index=df.index)
    out = pd.concat([df, stats], axis=1)
    out = out[out["PTS"].notna()] if "PTS" in out.columns else out.iloc[0:0]
    if "roster_slot" not in out.columns:
        out["roster_slot"] = ""
    return out.reset_index(drop=True)

def pct_impact(add, drop, cat):
    # Percentage categories are volume-weighted: compare aggregate makes/attempts.
    if cat == "FG%":
        makes = roster["FGM"].sum() - drop["FGM"] + add["FGM"]
        attempts = roster["FGA"].sum() - drop["FGA"] + add["FGA"]
        old_makes, old_attempts = roster["FGM"].sum(), roster["FGA"].sum()
    else:
        makes = roster["FTM"].sum() - drop["FTM"] + add["FTM"]
        attempts = roster["FTA"].sum() - drop["FTA"] + add["FTA"]
        old_makes, old_attempts = roster["FTM"].sum(), roster["FTA"].sum()
    old = old_makes / old_attempts if old_attempts else 0
    new = makes / attempts if attempts else 0
    return new - old

st.write(
    "Upload your latest Yahoo exports, or use the included files as a starting point. "
    "The parser extracts FG/FT makes and attempts plus the seven counting categories."
)
c1, c2 = st.columns(2)
with c1:
    roster_upload = st.file_uploader("Roster CSV", type="csv", key="roster")
with c2:
    fa_upload = st.file_uploader("Free agents CSV", type="csv", key="free_agents")

roster_raw = read_csv_upload(roster_upload, "roster.csv")
fa_raw = read_csv_upload(fa_upload, "free_agents.csv")
roster = clean_and_parse(roster_raw, True)
free_agents = clean_and_parse(fa_raw, False)

# Keep only players whose IDs are not already on the roster.
if not roster.empty and not free_agents.empty:
    roster_ids = set(roster["yahoo_id"].astype(str))
    free_agents = free_agents[~free_agents["yahoo_id"].astype(str).isin(roster_ids)].copy()

m1, m2, m3 = st.columns(3)
m1.metric("Roster players parsed", len(roster))
m2.metric("Free agents parsed", len(free_agents))
m3.metric("Raw free-agent CSV rows", len(fa_raw))

if roster.empty or free_agents.empty:
    st.warning("Upload CSVs with player_name, yahoo_id, and row_data columns. Make sure each batch is appended under a single header.")
    st.stop()

with st.expander("Parsed roster stats", expanded=False):
    show_cols = ["player_name", "roster_slot", "FG%", "FT%", "3PTM", "PTS", "REB", "AST", "STL", "BLK", "TO"]
    st.dataframe(roster[[c for c in show_cols if c in roster.columns]], use_container_width=True, hide_index=True)
with st.expander("Parsed free-agent stats", expanded=False):
    show_cols = ["player_name", "FG%", "FT%", "3PTM", "PTS", "REB", "AST", "STL", "BLK", "TO"]
    st.dataframe(free_agents[[c for c in show_cols if c in free_agents.columns]], use_container_width=True, hide_index=True)

st.subheader("Your category profile")
profile = []
for cat in CATEGORIES:
    if cat == "FG%":
        val = roster["FGM"].sum() / roster["FGA"].sum() if roster["FGA"].sum() else 0
        display = f"{val:.3f} ({roster['FGM'].sum():.1f}/{roster['FGA'].sum():.1f})"
    elif cat == "FT%":
        val = roster["FTM"].sum() / roster["FTA"].sum() if roster["FTA"].sum() else 0
        display = f"{val:.3f} ({roster['FTM'].sum():.1f}/{roster['FTA'].sum():.1f})"
    else:
        val = roster[cat].sum()
        display = f"{val:.1f}" + (" (lower is better)" if cat == "TO" else "")
    profile.append({"Category": cat, "Roster sum / weighted rate": display})
st.dataframe(pd.DataFrame(profile), use_container_width=True, hide_index=True)

st.subheader("Add/drop shortlist")
st.caption(
    "Heuristic, not a projection model: compares each free agent with each roster player using the supplied per-game-looking stats. "
    "FG% and FT% use makes/attempts to avoid incorrectly averaging percentages. Counting stats are treated as higher-is-better except TO."
)
st.warning(
    "Data quality note: Yahoo's row export contains page metadata mixed into each row. This app anchors on the FGM/FGA and FTM/FTA cells, "
    "but verify the selected Yahoo stats view before acting. These figures may not be season averages or projections."
)

# Estimate each category's value in roster context using robust standardization across available player pool.
pool = pd.concat([roster.assign(_source="roster"), free_agents.assign(_source="free agent")], ignore_index=True)
directions = {"FG%": 1, "FT%": 1, "3PTM": 1, "PTS": 1, "REB": 1, "AST": 1, "STL": 1, "BLK": 1, "TO": -1}
raw_cols = {"FG%": "FG%", "FT%": "FT%", "3PTM": "3PTM", "PTS": "PTS", "REB": "REB", "AST": "AST", "STL": "STL", "BLK": "BLK", "TO": "TO"}
# Use standard deviation across players as a rough scale for unlike categories.
scales = {}
for cat, col in raw_cols.items():
    s = pd.to_numeric(pool[col], errors="coerce").dropna()
    scales[cat] = float(s.std()) if len(s) > 1 and float(s.std()) > 1e-9 else 1.0

def cat_score(player, cat):
    if cat in ("FG%", "FT%"):
        # Use percentage itself for per-player contribution proxy; pair-specific impact is separately volume weighted.
        return float(player[cat]) * directions[cat]
    return float(player[cat]) * directions[cat]

# Category preference lets the user emphasize categories they want to win.
with st.expander("Customize category priorities", expanded=True):
    priorities = {}
    cols = st.columns(3)
    default_priority = {"FG%": 1.0, "FT%": 1.0, "3PTM": 1.0, "PTS": 1.0, "REB": 1.0, "AST": 1.0, "STL": 1.0, "BLK": 1.0, "TO": 1.0}
    for i, cat in enumerate(CATEGORIES):
        priorities[cat] = cols[i % 3].slider(cat, 0.0, 2.0, 1.0, 0.25, key=f"priority_{cat}")

def pair_score(add, drop):
    score = 0.0
    details = []
    for cat in CATEGORIES:
        if cat in ("FG%", "FT%"):
            delta = pct_impact(add, drop, cat)
            # Scale percentage-point differences to a comparable rough contribution.
            scaled = delta / 0.02
            score += scaled * priorities[cat]
            details.append((cat, delta, scaled))
        else:
            delta = directions[cat] * (float(add[cat]) - float(drop[cat]))
            scaled = delta / scales[cat]
            score += scaled * priorities[cat]
            details.append((cat, delta, scaled))
    return score, details

results = []
for _, add in free_agents.iterrows():
    for _, drop in roster.iterrows():
        score, details = pair_score(add, drop)
        improved = [cat for cat, delta, _ in details if delta > 0]
        harmed = [cat for cat, delta, _ in details if delta < 0]
        results.append({
            "Add": add["player_name"], "Drop": drop["player_name"], "Score": score,
            "Add Yahoo ID": add["yahoo_id"], "Drop slot": drop.get("roster_slot", ""),
            "Improved categories": ", ".join(improved) or "—",
            "Potential costs": ", ".join(harmed) or "—",
            "_add": add, "_drop": drop, "_details": details
        })
results.sort(key=lambda x: x["Score"], reverse=True)

# De-duplicate to show top candidate per add, then offer all pairings.
best_by_add = {}
for r in results:
    if r["Add"] not in best_by_add:
        best_by_add[r["Add"]] = r
top = sorted(best_by_add.values(), key=lambda x: x["Score"], reverse=True)
view = pd.DataFrame([{
    "Add": r["Add"], "Drop": r["Drop"], "Roster slot": r["Drop slot"],
    "Heuristic score": round(r["Score"], 2),
    "Categories helped": r["Improved categories"],
    "Possible sacrifices": r["Potential costs"]
} for r in top[:20]])
st.dataframe(view, use_container_width=True, hide_index=True)

chosen = st.selectbox("Inspect a suggested move", [f"{r['Add']}  ⇄  {r['Drop']}" for r in top[:50]])
if chosen:
    selected = next(r for r in top[:50] if f"{r['Add']}  ⇄  {r['Drop']}" == chosen)
    st.markdown(f"**Add {selected['Add']} for {selected['Drop']}**")
    detail_rows = []
    for cat, delta, scaled in selected["_details"]:
        if cat in ("FG%", "FT%"):
            label = f"{delta:+.3f} weighted rate"
        else:
            label = f"{delta:+.1f} per-game stat delta"
        detail_rows.append({"Category": cat, "Estimated direction": label, "Weighted contribution": round(scaled * priorities[cat], 2)})
    st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)

st.caption("Scores are ranking heuristics, not guaranteed matchup outcomes. Use your league standings, games played, injuries, and weekly schedule before making a move.")
