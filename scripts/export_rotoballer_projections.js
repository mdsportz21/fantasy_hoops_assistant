// RotoBaller uses div-based player cards, not a conventional HTML table.
// On the RotoBaller NBA rankings/projections page, select Proj (not Stats),
// open Chrome DevTools > Console, paste this script, and run it.
// Copies CSV with overall_rank, position, position_rank, and projection stats.
// https://www.rotoballer.com/fantasy-basketball-rankings-projections-nba

(() => {
  const cards = [...document.querySelectorAll(".rb-mc-card")];
  if (!cards.length) {
    console.error("No .rb-mc-card player cards found. Open the RotoBaller rankings/projections page and ensure the player list is loaded.");
    return;
  }
  const clean = value => String(value ?? "").replace(/\s+/g, " ").trim();
  const isNumber = value => /^-?\d+(?:\.\d+)?$/.test(clean(value).replace(/,/g, ""));
  const records = [];
  const skipped = [];

  for (const card of cards) {
    const name = clean(card.querySelector(".rb-mc-nm")?.innerText);
    const lines = (card.innerText || "").split("\n").map(clean).filter(Boolean);
    const nameIndex = lines.findIndex(line => line === name);
    const rankCandidates = nameIndex > 0 ? lines.slice(0, nameIndex).filter(line => /^\d+$/.test(line)) : [];
    const overallRank = rankCandidates.length ? Number(rankCandidates[rankCandidates.length - 1]) : NaN;
    if (!name || nameIndex < 0 || !Number.isFinite(overallRank)) {
      skipped.push({name: name || "(no name)", reason: "could not identify overall rank/name", text: lines.join(" | ")});
      continue;
    }

    const afterName = lines.slice(nameIndex + 1);
    const posIndex = afterName.findIndex(line => /^(PG|SG|SF|PF|C)(\/(PG|SG|SF|PF|C))*$/i.test(line));
    const position = posIndex >= 0 ? afterName[posIndex] : "";
    const positionRank = afterName.find(line => /^(PG|SG|SF|PF|C)\d+$/i.test(line)) || "";
    // Stats are the nine plain numeric values after position / P-Rank:
    // PTS, REB, AST, STL, BLK, 3PM, FG%, FT%, TO.
    const numericStats = afterName.filter(isNumber).map(value => clean(value).replace(/,/g, ""));
    if (numericStats.length < 9) {
      skipped.push({name, overallRank, reason: "no complete projection stats", text: lines.join(" | ")});
      continue;
    }
    const stats = numericStats.slice(-9);
    records.push({
      player_name: name,
      overall_rank: overallRank,
      position,
      position_rank: positionRank,
      PTS: stats[0], REB: stats[1], AST: stats[2], STL: stats[3], BLK: stats[4],
      "3PM": stats[5], "FG%": stats[6], "FT%": stats[7], TO: stats[8]
    });
  }

  const columns = ["player_name", "overall_rank", "position", "position_rank", "PTS", "REB", "AST", "STL", "BLK", "3PM", "FG%", "FT%", "TO"];
  const quote = value => `"${String(value ?? "").replace(/"/g, '""')}"`;
  const csv = [columns.map(quote).join(","), ...records.map(row => columns.map(col => quote(row[col])).join(","))].join("\n");
  copy(csv);
  console.log(`Copied ${records.length} ranked players with projection stats. Skipped ${skipped.length} cards without complete projections or rank data.`);
  console.table(records.slice(0, 10));
  if (skipped.length) {
    console.log("Skipped cards (often players with no published projections):");
    console.table(skipped);
  }
})();
