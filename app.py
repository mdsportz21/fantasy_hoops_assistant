import re
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fantasy Hoops Add/Drop Assistant", layout="wide")
st.title("Fantasy Hoops Add/Drop Assistant")
st.caption("Yahoo 9-category league · Yahoo Current-rank add/drop radar")

ROOT = Path(__file__).parent


def read_csv_upload(uploaded, default_name):
    if uploaded is not None:
        return pd.read_csv(uploaded, dtype=str).fillna("")
    path = ROOT / default_name
    if path.exists():
        return pd.read_csv(path, dtype=str).fillna("")
    return pd.DataFrame()


def parse_player_row(row):
    """Parse Yahoo's exported row_data to retain the roster's category context."""
    raw = str(row if row is not None else "")
    cells = [x.strip() for x in raw.replace("\r", "\n").replace("\n", " | ").split("|")]
    cells = [re.sub(r"\s+", " ", x).strip() for x in cells]
    attempts = [i for i, cell in enumerate(cells) if re.fullmatch(r"\d+(?:\.\d+)?/\d+(?:\.\d+)?", cell)]
    if len(attempts) < 2:
        return None
    i_fg, i_ft = attempts[0], attempts[1]
    try:
        fgm, fga = [float(x) for x in cells[i_fg].split("/")]
        fg_pct = float(cells[i_fg + 1])
        ftm, fta = [float(x) for x in cells[i_ft].split("/")]
        ft_cell = cells[i_ft + 1]
        ft_pct = float(ft_cell) if ft_cell not in ("-", "") else (ftm / fta if fta else 0.0)
        tail = [float(cells[j]) for j in range(i_ft + 2, i_ft + 9)]
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



def extract_current_rank(row):
    """Extract Yahoo Current rank from row_data when the CSV has no rank column."""
    raw = str(row if row is not None else "")
    cells = [x.strip() for x in raw.replace("\r", "\n").replace("\n", " | ").split("|")]
    cells = [re.sub(r"\s+", " ", x).strip() for x in cells]

    # Yahoo's row_data has a pair like 60 | 59 | 84% | 95%; 59 is Current rank.
    for i in range(len(cells) - 3):
        if (
            re.fullmatch(r"\d+", cells[i])
            and re.fullmatch(r"\d+", cells[i + 1])
            and re.fullmatch(r"\d+(?:\.\d+)?%", cells[i + 2])
            and re.fullmatch(r"\d+(?:\.\d+)?%", cells[i + 3])
        ):
            return int(cells[i + 1])
    return None

def clean_and_parse(df):
    if df.empty:
        return pd.DataFrame()
    df = df.copy().fillna("")
    for col in ["player_name", "yahoo_id", "row_data", "current_rank"]:
        if col not in df.columns:
            df[col] = ""

    df["player_name"] = df["player_name"].astype(str).str.strip()
    df["yahoo_id"] = df["yahoo_id"].astype(str).str.strip()
    df = df[(df.player_name != "") & (df.player_name.str.lower() != "player_name")]
    df = df[(df.yahoo_id != "") & (df.yahoo_id.str.lower() != "yahoo_id")]
    df = df.drop_duplicates(subset=["yahoo_id"], keep="first")
    df["current_rank"] = pd.to_numeric(
        df["current_rank"].astype(str).str.strip().str.replace("#", "", regex=False),
        errors="coerce",
    )
    # Existing exports may store rank only inside row_data, not as a CSV column.
    extracted_ranks = df["row_data"].apply(extract_current_rank)
    df["current_rank"] = df["current_rank"].fillna(extracted_ranks)

    stats = pd.DataFrame(df["row_data"].apply(parse_player_row).tolist(), index=df.index)
    out = pd.concat([df, stats], axis=1)
    if "PTS" in out.columns:
        out = out[out["PTS"].notna()]
    if "roster_slot" not in out.columns:
        out["roster_slot"] = ""
    return out.reset_index(drop=True)


st.write(
    "Upload your Yahoo roster and free-agent exports. Recommendations use Yahoo's "
    "Current ranking from the Remaining Games projected-stats view; lower rank numbers are better. "
    "The app compares ranks directly and does not calculate a custom 9-category score."
)
c1, c2 = st.columns(2)
with c1:
    roster_upload = st.file_uploader("Yahoo roster CSV (rank can be inside row_data)", type="csv", key="roster")
with c2:
    fa_upload = st.file_uploader("Yahoo free agents CSV (rank can be inside row_data)", type="csv", key="free_agents")

roster_raw = read_csv_upload(roster_upload, "output/roster.csv")
fa_raw = read_csv_upload(fa_upload, "output/free_agents.csv")
roster = clean_and_parse(roster_raw)
free_agents = clean_and_parse(fa_raw)

if not roster.empty and not free_agents.empty:
    roster_ids = set(roster["yahoo_id"].astype(str))
    free_agents = free_agents[~free_agents["yahoo_id"].astype(str).isin(roster_ids)].copy()

m1, m2, m3 = st.columns(3)
m1.metric("Roster players parsed", len(roster))
m2.metric("Free agents parsed", len(free_agents))
m3.metric(
    "Players with Yahoo Current rank",
    int(roster["current_rank"].notna().sum()) + int(free_agents["current_rank"].notna().sum()),
)

if roster.empty or free_agents.empty:
    st.warning(
        "Upload Yahoo CSVs with player_name, yahoo_id, and row_data columns (rank can be extracted from row_data), "
        "or put them in output/roster.csv and output/free_agents.csv beside app.py."
    )
    st.stop()

roster_ranked_count = int(roster["current_rank"].notna().sum())
fa_ranked_count = int(free_agents["current_rank"].notna().sum())
st.success(
    f"Yahoo Current ranks loaded: ranked {roster_ranked_count}/{len(roster)} roster players "
    f"and {fa_ranked_count}/{len(free_agents)} free agents."
)
if roster_ranked_count < len(roster) or fa_ranked_count < len(free_agents):
    st.warning(
        "Players without a numeric Yahoo Current rank are unranked and will not be included "
        "in add/drop comparisons. Check that the Current column was visible when exporting both CSVs."
    )

with st.expander("Roster with Yahoo Current ranks", expanded=False):
    roster_view = roster[["player_name", "roster_slot", "current_rank"]].copy()
    roster_view["current_rank"] = roster_view["current_rank"].apply(
        lambda x: int(x) if pd.notna(x) else None
    )
    st.dataframe(
        roster_view.sort_values("current_rank", na_position="last"),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Highest-ranked available free agents", expanded=False):
    fa_view = free_agents[["player_name", "current_rank"]].copy()
    fa_view["current_rank"] = fa_view["current_rank"].apply(
        lambda x: int(x) if pd.notna(x) else None
    )
    st.dataframe(
        fa_view.sort_values("current_rank", na_position="last").head(50),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Potential add/drop moves")
min_gain = st.slider(
    "Minimum Yahoo Current rank improvement",
    min_value=0,
    max_value=100,
    value=10,
    step=5,
    help="For example, a free agent ranked 35 versus a roster player ranked 80 is a 45-place improvement.",
)
ranked_roster = roster[roster["current_rank"].notna()].copy()
ranked_fa = free_agents[free_agents["current_rank"].notna()].copy()
results = []
for _, add in ranked_fa.iterrows():
    for _, drop in ranked_roster.iterrows():
        gain = float(drop["current_rank"]) - float(add["current_rank"])
        if gain >= min_gain:
            results.append({
                "Free agent to add": add["player_name"],
                "FA Yahoo Current rank": int(add["current_rank"]),
                "Roster player to consider dropping": drop["player_name"],
                "Roster Yahoo Current rank": int(drop["current_rank"]),
                "Rank improvement": int(gain),
                "Drop roster slot": drop.get("roster_slot", ""),
            })

if results:
    result_df = pd.DataFrame(results).sort_values(
        ["Rank improvement", "FA Yahoo Current rank"], ascending=[False, True]
    ).reset_index(drop=True)
    st.caption(
        f"Showing {len(result_df)} add/drop pair(s) meeting the {min_gain}-place improvement threshold. "
        "These are rank-based flags, not automatic drop instructions."
    )
    st.dataframe(result_df.head(100), use_container_width=True, hide_index=True)
    st.download_button(
        "Download all suggested add/drop pairs as CSV",
        result_df.to_csv(index=False),
        file_name="yahoo_current_add_drop_suggestions.csv",
        mime="text/csv",
    )
else:
    st.info("No ranked free agent beats a roster player by the selected rank-improvement threshold.")

unranked_roster = roster[roster["current_rank"].isna()][["player_name", "roster_slot"]]
unranked_fa = free_agents[free_agents["current_rank"].isna()][["player_name"]]
if not unranked_roster.empty or not unranked_fa.empty:
    with st.expander("Unranked players (not included in comparisons)", expanded=False):
        if not unranked_roster.empty:
            st.write("**Roster players without a Yahoo Current rank**")
            st.dataframe(unranked_roster, use_container_width=True, hide_index=True)
        if not unranked_fa.empty:
            st.write("**Free agents without a Yahoo Current rank**")
            st.dataframe(unranked_fa, use_container_width=True, hide_index=True)

st.caption(
    "Yahoo Current rankings are used as a general ranking signal and may not be tailored specifically "
    "to 9-category scoring. This comparison does not account for category needs, injuries, games played, "
    "schedule, or roster constraints. Review context before making a move."
)
