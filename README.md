# Fantasy Hoops Add/Drop Assistant

A personal-use Streamlit helper for a Yahoo NBA 9-category league. Recommendations now use **RotoBaller overall rankings directly** instead of a custom category-weighted heuristic.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Files

- `roster.csv`: Yahoo roster export (example/current data).
- `free_agents.csv`: Yahoo free-agent export (example/current data).
- `export_rotoballer_projections.js`: exports RotoBaller overall rank, position rank, and projections from the page's player cards.
- `projections_template.csv`: example of the required ranking CSV columns.

## Refresh RotoBaller ranks

1. Open the RotoBaller NBA rankings/projections page: https://www.rotoballer.com/fantasy-basketball-rankings-projections-nba
2. Select **Proj**, not **Stats**, and wait for the player cards to load.
3. Open Chrome DevTools → Console.
4. Paste the contents of `export_rotoballer_projections.js` and run it. It copies CSV to the clipboard.
5. Paste the clipboard into a plain-text editor and save as `rotoballer_projections.csv`.
6. Upload that file in the app's **RotoBaller rankings CSV** field.

The CSV must include `player_name` and `overall_rank`. The supplied exporter also includes `position`, `position_rank`, and the projection statistics. Players with no projection data are skipped and shown as unranked if they appear in the Yahoo roster/free-agent list.

## How recommendations work

- Lower overall rank numbers are better. A free agent ranked 35 beats a roster player ranked 80 by 45 places.
- The app compares every ranked free agent against every ranked roster player and shows pairs meeting the selected minimum rank improvement (default 10 places).
- You can download the complete set of qualifying add/drop pairs as CSV.
- Players without a RotoBaller overall rank are listed separately and are not treated as the worst players.
- Player matching normalizes punctuation, suffixes, and accents (for example, `Moussa Diabaté` matches `Moussa Diabate`).

## Limitations

This is a simple ranking comparison, not a category-needs or matchup model. It does not account for injuries, games played, weekly schedule, league category standings, or roster constraints. Verify the ranking view and update date before making a move.
