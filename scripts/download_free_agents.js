// Yahoo Fantasy Basketball Free-Agent Exporter
// Go to:
// https://basketball.fantasysports.yahoo.com/nba/59643/players
//
// Set
//
//
// Exports:
// player_name, yahoo_id, current_rank, row_data
//
// IMPORTANT:
// Based on the inspected Yahoo table:
//   cell index 6 = Pre-Season
//   cell index 7 = Current
//
// Copies the CSV to the clipboard using Chrome DevTools' copy() function.

const tables = [...document.querySelectorAll("table")];

const table = tables
  .filter(t => t.querySelectorAll('a[href*="/nba/players/"]').length > 0)
  .sort((a, b) =>
    b.querySelectorAll('a[href*="/nba/players/"]').length -
    a.querySelectorAll('a[href*="/nba/players/"]').length
  )[0];

if (!table) {
  console.error("No player table found.");
} else {

  const rows = [...table.querySelectorAll("tbody tr")];

  const records = rows.map(row => {
    const link = [...row.querySelectorAll('a[href*="/nba/players/"]')]
      .find(a => a.href.match(/\/nba\/players\/\d+/));

    if (!link) return null;

    const cells = [...row.querySelectorAll("th, td")];
    const id = link.href.match(/\/nba\/players\/(\d+)/)?.[1] || "";

    // Extract the player name, removing Yahoo's appended note text.
    const name = link.innerText
      .trim()
      .replace(/\s*(?:Player Note|New Player Note|No new player Notes).*$/is, "")
      .trim();

    const values = cells.map(cell =>
      cell.innerText.trim().replace(/\s+/g, " ")
    );

    const currentRankText = (values[7] || "").trim();
    const currentRank = /^\d+$/.test(currentRankText)
      ? Number(currentRankText)
      : null;

    return {
      name,
      id,
      current_rank: currentRank,
      values
    };
  }).filter(Boolean);

  const quote = value =>
    `"${String(value ?? "").replace(/"/g, '""')}"`;

  const csv = [
    ["player_name", "yahoo_id", "current_rank", "row_data"]
      .map(quote)
      .join(","),

    ...records.map(player =>
      [
        player.name,
        player.id,
        player.current_rank ?? "",
        player.values.join(" | ")
      ].map(quote).join(",")
    )
  ].join("\n");

  copy(csv);

  const rankedCount = records.filter(
    player => player.current_rank !== null
  ).length;

  console.log(
    `Copied ${records.length} player rows to clipboard; ` +
    `${rankedCount} have a numeric Current ranking.`
  );

  console.table(records.slice(0, 10).map(player => ({
    player_name: player.name,
    yahoo_id: player.id,
    current_rank: player.current_rank,
    row_data: player.values.join(" | ").slice(0, 120)
  })));
}