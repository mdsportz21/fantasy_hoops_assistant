import re
import unicodedata
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Fantasy Hoops Add/Drop Assistant", layout="wide")
st.title("Fantasy Hoops Add/Drop Assistant")
st.caption("Yahoo 9-category league · RotoBaller overall-rank add/drop radar")

ROOT = Path(__file__).parent


def read_csv_upload(uploaded, default_name):
    if uploaded is not None:
        return pd.read_csv(uploaded, dtype=str).fillna("")
    path = ROOT / default_name
    if path.exists():
        return pd.read_csv(path, dtype=str).fillna("")
    return pd.DataFrame()


def parse_player_row(row):
    """Parse Yahoo's exported row_data, used only for roster context."""
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
        return {"FGM": fgm, "FGA": fga, "FG%": fg_pct, "FTM": ftm, "FTA": fta,
                "FT%": ft_pct, "3PTM": threes, "PTS": pts, "REB": reb,
                "AST": ast, "STL": stl, "BLK": blk, "TO": tov}
    except (ValueError, IndexError):
        return None


def clean_and_parse(df):
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
    stats = pd.DataFrame(df["row_data"].apply(parse_player_row).tolist(), index=df.index)
    out = pd.concat([df, stats], axis=1)
    if "PTS" in out.columns:
        out = out[out["PTS"].notna()]
    if "roster_slot" not in out.columns:
        out["roster_slot"] = ""
    return out.reset_index(drop=True)


def normalized_name(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip().replace("&", "and")
    value = re.sub(r"[^a-z0-9 ]", "", value)
    value = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", value)
    return re.sub(r"\s+", " ", value).strip()


def load_rankings(uploaded, raw):
    if uploaded is None and raw is None:
        return pd.DataFrame()
    try:
        df = pd.read_csv(uploaded, dtype=str).fillna("") if uploaded is not None else raw
    except Exception as exc:
        st.error(f"Could not read RotoBaller CSV: {exc}")
        return pd.DataFrame()
    aliases = {
        "player": "player_name", "name": "player_name", "player name": "player_name",
        "player_name": "player_name", "rank": "overall_rank", "overall rank": "overall_rank",
        "overall_rank": "overall_rank", "pos": "position", "position": "position",
        "p-rank": "position_rank", "position rank": "position_rank", "position_rank": "position_rank",
    }
    rename = {}
    for col in df.columns:
        key = re.sub(r"\s+", " ", str(col).strip().lower())
        if key in aliases:
            rename[col] = aliases[key]
    df = df.rename(columns=rename)
    if "player_name" not in df.columns or "overall_rank" not in df.columns:
        st.error("The RotoBaller CSV needs player_name and overall_rank columns. Re-run the updated exporter and upload its new CSV.")
        return pd.DataFrame()
    df["overall_rank"] = pd.to_numeric(df["overall_rank"].astype(str).str.replace("#", "", regex=False), errors="coerce")
    df = df[df["player_name"].astype(str).str.strip().ne("") & df["overall_rank"].notna()].copy()
    df["_name_key"] = df["player_name"].map(normalized_name)
    df = df[df["_name_key"].ne("")].drop_duplicates("_name_key", keep="last")
    for col in ["position", "position_rank"]:
        if col not in df.columns:
            df[col] = ""
    return df[["player_name", "overall_rank", "position", "position_rank", "_name_key"]]


st.write(
    "Upload your Yahoo roster and free-agent exports plus the RotoBaller rankings CSV. "
    "Recommendations are based on RotoBaller overall rank: a lower rank number is better. "
    "The app does not calculate a custom category score."
)
c1, c2 = st.columns(2)
with c1:
    roster_upload = st.file_uploader("Yahoo roster CSV", type="csv", key="roster")
with c2:
    fa_upload = st.file_uploader("Yahoo free agents CSV", type="csv", key="free_agents")
ranking_upload = st.file_uploader("RotoBaller rankings CSV (must include overall_rank)", type="csv", key="rankings")

roster_raw = read_csv_upload(roster_upload, "output/roster.csv")
fa_raw = read_csv_upload(fa_upload, "output/free_agents.csv")
ranking_raw = read_csv_upload(ranking_upload, "output/rotoballer_projections.csv")
roster = clean_and_parse(roster_raw)
free_agents = clean_and_parse(fa_raw)
rankings = load_rankings(ranking_upload, ranking_raw)

if not roster.empty and not free_agents.empty:
    roster_ids = set(roster["yahoo_id"].astype(str))
    free_agents = free_agents[~free_agents["yahoo_id"].astype(str).isin(roster_ids)].copy()

m1, m2, m3 = st.columns(3)
m1.metric("Roster players parsed", len(roster))
m2.metric("Free agents parsed", len(free_agents))
m3.metric("Ranked players in CSV", len(rankings))

if roster.empty or free_agents.empty:
    st.warning("Upload Yahoo CSVs with player_name, yahoo_id, and row_data columns, or put them beside app.py.")
    st.stop()
if rankings.empty:
    st.info("Upload a RotoBaller CSV exported with the updated script. The CSV must include overall_rank.")
    st.stop()

roster["_name_key"] = roster["player_name"].map(normalized_name)
free_agents["_name_key"] = free_agents["player_name"].map(normalized_name)
roster = roster.merge(rankings, on="_name_key", how="left", suffixes=("", "_roto"))
free_agents = free_agents.merge(rankings, on="_name_key", how="left", suffixes=("", "_roto"))

roster_matches = int(roster["overall_rank"].notna().sum())
fa_matches = int(free_agents["overall_rank"].notna().sum())
st.success(f"RotoBaller rankings loaded: matched {roster_matches}/{len(roster)} roster players and {fa_matches}/{len(free_agents)} free agents.")
if roster_matches < len(roster) or fa_matches < len(free_agents):
    st.warning("Players without a RotoBaller overall rank are shown as unranked and are not treated as the worst-ranked players.")

with st.expander("Roster with RotoBaller ranks", expanded=False):
    roster_view = roster[["player_name", "roster_slot", "overall_rank", "position", "position_rank"]].copy()
    roster_view["overall_rank"] = roster_view["overall_rank"].apply(lambda x: int(x) if pd.notna(x) else None)
    st.dataframe(roster_view.sort_values("overall_rank", na_position="last"), use_container_width=True, hide_index=True)

with st.expander("Highest-ranked available free agents", expanded=False):
    fa_view = free_agents[["player_name", "overall_rank", "position", "position_rank"]].copy()
    fa_view["overall_rank"] = fa_view["overall_rank"].apply(lambda x: int(x) if pd.notna(x) else None)
    st.dataframe(fa_view.sort_values("overall_rank", na_position="last").head(50), use_container_width=True, hide_index=True)

st.subheader("Potential add/drop moves")
min_gain = st.slider("Minimum overall-rank improvement", min_value=0, max_value=100, value=10, step=5,
                     help="For example, a free agent ranked 35 versus a roster player ranked 80 is a 45-place improvement.")
ranked_roster = roster[roster["overall_rank"].notna()].copy()
ranked_fa = free_agents[free_agents["overall_rank"].notna()].copy()
results = []
for _, add in ranked_fa.iterrows():
    for _, drop in ranked_roster.iterrows():
        gain = float(drop["overall_rank"]) - float(add["overall_rank"])
        if gain >= min_gain:
            results.append({
                "Free agent to add": add["player_name"],
                "FA rank": int(add["overall_rank"]),
                "Roster player to consider dropping": drop["player_name"],
                "Roster rank": int(drop["overall_rank"]),
                "Rank improvement": int(gain),
                "Drop roster slot": drop.get("roster_slot", ""),
                "FA position": add.get("position", ""),
                "Roster position": drop.get("position", ""),
            })

if results:
    result_df = pd.DataFrame(results).sort_values(
        ["Rank improvement", "FA rank"], ascending=[False, True]
    ).reset_index(drop=True)
    st.caption(f"Showing {len(result_df)} ranked add/drop pair(s) meeting the {min_gain}-place improvement threshold. These are rank-based flags, not automatic drop instructions.")
    st.dataframe(result_df.head(100), use_container_width=True, hide_index=True)
    st.download_button("Download all suggested add/drop pairs as CSV", result_df.to_csv(index=False),
                       file_name="rotoballer_add_drop_suggestions.csv", mime="text/csv")
else:
    st.info("No ranked free agent beats a roster player by the selected rank-improvement threshold.")

unranked_roster = roster[roster["overall_rank"].isna()][["player_name", "roster_slot"]]
unranked_fa = free_agents[free_agents["overall_rank"].isna()][["player_name"]]
if not unranked_roster.empty or not unranked_fa.empty:
    with st.expander("Unranked players (not included in comparisons)", expanded=False):
        if not unranked_roster.empty:
            st.write("**Roster players without an overall rank**")
            st.dataframe(unranked_roster, use_container_width=True, hide_index=True)
        if not unranked_fa.empty:
            st.write("**Free agents without an overall rank**")
            st.dataframe(unranked_fa, use_container_width=True, hide_index=True)

st.caption("Rankings reflect the selected RotoBaller view and update time. This comparison does not account for category needs, injuries, games played, schedule, or roster constraints. Review context before making a move.")
