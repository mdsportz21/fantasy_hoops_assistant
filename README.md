# Fantasy Hoops Add/Drop Assistant

Personal Streamlit prototype for Yahoo Fantasy Basketball 9-category leagues.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Included files
- `roster.csv`: the uploaded Yahoo roster export.
- `free_agents.csv`: the uploaded Yahoo free-agent export.
- `app.py`: Streamlit UI and CSV parser.

## Important limitations
- The Yahoo CSV exports are copied from a web table and include extra page text. The parser uses the FG makes/attempts and FT makes/attempts cells to find the fantasy stats.
- The included free-agent file had one repeated header row, which the app removes. It contains 25 real player rows after repeated header rows are removed; it is not proof that the entire free-agent pool has been exported.
- The scoring is a transparent heuristic, not a trained projection model. The category totals and scores should be reviewed before making real roster moves.
- Check the Yahoo page's selected stats view: the exported figures may not be true season averages or projections.
- This prototype does not connect to Yahoo or scrape pages automatically. Upload updated CSV exports when you want refreshed recommendations.
