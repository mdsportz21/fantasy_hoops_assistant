// https://basketball.fantasysports.yahoo.com/nba/59643/players
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
  const rows = [...table.querySelectorAll("tr")];

  const records = rows.map(row => {
    const link = [...row.querySelectorAll('a[href*="/nba/players/"]')]
      .find(a => a.href.match(/\/nba\/players\/\d+/));

    if (!link) return null;

    const cells = [...row.querySelectorAll("th, td")];
    const id = link.href.match(/\/nba\/players\/(\d+)/)?.[1] || "";
    const name = link.innerText.trim();
    const values = cells.map(c => c.innerText.trim());

    return { name, id, values };
  }).filter(Boolean);

  const quote = value =>
    `"${String(value ?? "").replace(/"/g, '""')}"`;

  const csv = [
    ["player_name", "yahoo_id", "row_data"].map(quote).join(","),
    ...records.map(p =>
      [p.name, p.id, p.values.join(" | ")].map(quote).join(",")
    )
  ].join("\n");

  copy(csv);
  console.log(`Copied ${records.length} player rows to clipboard.`);
  console.table(records.slice(0, 5).map(p => ({
    name: p.name,
    yahoo_id: p.id,
    row: p.values.join(" | ").slice(0, 120)
  })));
}