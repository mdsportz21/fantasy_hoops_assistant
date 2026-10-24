# Fantasy Hoops Add/Drop Assistant

A personal-use Streamlit prototype for a Yahoo NBA 9-category league. Yahoo exports supply your roster/free-agent list, and an optional RotoBaller projection export improves the add/drop comparison.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Files

- `roster.csv`: example/current Yahoo roster export.
- `free_agents.csv`: example/current Yahoo free-agent export.
- `export_rotoballer_projections.js`: paste into Chrome DevTools Console while the RotoBaller NBA projections table is visible.
- `projections_template.csv`: header template for the optional projections upload.

## Import RotoBaller projections

1. Open the RotoBaller NBA rankings/projections page: https://www.rotoballer.com/fantasy-basketball-rankings-projections-nba
2. Make sure the player projections table is visible and set to projections.
3. Open Chrome DevTools → Console.
4. Paste the contents of `export_rotoballer_projections.js` and run it. It copies a CSV to your clipboard.
5. Paste the clipboard into a plain-text editor and save it as `rotoballer_projections.csv` (ensure the file is saved as CSV, not rich text).
6. In the Streamlit app, upload that file in **RotoBaller projections CSV (optional)**.

The expected columns are `player_name, PTS, REB, AST, STL, BLK, 3PM, FG%, FT%, TO`. The app accepts `3PM` or `3PTM`. Update the CSV whenever you want to refresh projections. If the site changes its table layout and the exporter cannot find the table, inspect the table headers shown in the browser console.

## How projections are used

- Projected per-game counting stats (3PM, PTS, REB, AST, STL, BLK, TO) are used for players matched by normalized name.
- RotoBaller FG% and FT% are used as projected rates. Because the public table does not include projected FGM/FGA and FTM/FTA in the displayed columns, Yahoo-export FGA/FTA are used as approximate volume weights for team percentage impact.
- If a player does not match the projection CSV, the app falls back to that player's parsed Yahoo export stats. The app shows match counts and warns about unmatched players.
- Without an uploaded projections file, the app retains its original Yahoo-stat heuristic.

## Important limitations

This is a heuristic add/drop helper, not a validated projection or matchup model. Check the RotoBaller projection update date, confirm player-name matching, and verify Yahoo's exported stats view before acting. The current score is a rough comparison of per-game category differences; it does not fully model games played, injuries, weekly schedule, roster limits, or category standings. Use it as decision support, not an automatic roster decision.
