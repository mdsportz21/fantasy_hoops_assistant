(() => {
  const tableIndex = 1;
  const table = document.querySelectorAll("table")[tableIndex];

  if (!table) {
    console.error("Could not find the roster table.");
    return;
  }

  const records = [...table.querySelectorAll("tr")]
    .map(row => {
      const cells = [...row.querySelectorAll("th, td")];
      const playerLink = [...row.querySelectorAll("a")].find(a =>
        /\/nba\/players\/\d+/.test(a.href)
      );

      // Ignore headers and rows without a player link.
      if (!playerLink) return null;

      const match = playerLink.href.match(/\/nba\/players\/(\d+)/);
      if (!match) return null;

      return {
        player: playerLink.innerText.trim(),
        yahoo_player_id: match[1],
        roster_position: cells[0]?.innerText.trim() ?? "",
        cells: cells.map(cell =>
          cell.innerText.trim().replace(/\s+/g, " ")
        )
      };
    })
    .filter(Boolean);

  if (!records.length) {
    console.error("No player rows found. Check the table index.");
    return;
  }

  const maxCells = Math.max(...records.map(r => r.cells.length));
  const headers = [
    "player",
    "yahoo_player_id",
    "roster_position",
    ...Array.from({ length: maxCells }, (_, i) => `cell_${i}`)
  ];

  const escapeCSV = value =>
    `"${String(value ?? "").replace(/"/g, '""')}"`;

// Instead of downloading a file, print the CSV for copying.
    const csv = [
      ["player_name", "yahoo_id", "roster_slot", "row_data"].join(","),
      ...Array.from(document.querySelectorAll("table")[1].querySelectorAll("tr"))
        .slice(2)
        .map(row => {
          const cells = Array.from(row.querySelectorAll("th, td"));
          const link = row.querySelector('a[href*="/nba/players/"]');

          if (!link) return null;

          const name = link.innerText.trim();
          const id = link.href.match(/\/nba\/players\/(\d+)/)?.[1] || "";
          const slot = cells[0]?.innerText.trim() || "";
          const rowData = cells.map(c => c.innerText.trim()).join(" | ");

          return [name, id, slot, rowData]
            .map(value => `"${String(value).replace(/"/g, '""')}"`)
            .join(",");
        })
        .filter(Boolean)
    ].join("\n");

    console.log(csv);
    copy(csv);
})();