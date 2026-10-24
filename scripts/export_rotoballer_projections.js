// On the RotoBaller NBA projections page, click "Proj", open Chrome DevTools > Console
// and paste this script. It copies the visible projection table to your clipboard.
// Expected output columns are compatible with the app's optional projections upload.
// https://www.rotoballer.com/fantasy-basketball-rankings-projections-nba

(async () => {
  const headers = [
    "player_name", "PTS", "REB", "AST", "STL", "BLK",
    "3PM", "FG%", "FT%", "TO"
  ];

  const cards = [...document.querySelectorAll(".rb-mc-card")];
  const output = [];
  const skipped = [];

  for (const card of cards) {
    const playerName = card.querySelector(".rb-mc-nm")?.innerText?.trim();

    if (!playerName) {
      skipped.push({ reason: "Missing player name", text: card.innerText });
      continue;
    }

    const lines = (card.innerText || "")
      .split("\n")
      .map(s => s.trim())
      .filter(Boolean);

    const nameIndex = lines.findIndex(line => line === playerName);

    if (nameIndex === -1) {
      skipped.push({ playerName, reason: "Name not found in card text" });
      continue;
    }

    // Read the values in their displayed order after the name.
    // Expected: POS, TEAM, P-RANK, PTS, REB, AST, STL, BLK, 3PM, FG%, FT%, TO
    const afterName = lines.slice(nameIndex + 1);

    // Locate the numeric projection sequence after the position/team/rank fields.
    // The first three values are position, team, and player rank, not projections.
    const numeric = afterName
      .map(s => s.replace(/,/g, ""))
      .filter(s => /^-?\d+(?:\.\d+)?$/.test(s))
      .map(Number);

    if (numeric.length < 9) {
      skipped.push({
        playerName,
        reason: `Only ${numeric.length} numeric values found`,
        cardText: lines.join(" | ")
      });
      continue;
    }

    // Use the final nine numeric values as the requested fantasy projections.
    const stats = numeric.slice(-9);
    output.push([playerName, ...stats]);
  }

  const csvEscape = value => {
    const s = String(value ?? "");
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };

  const csv = [
    headers.join(","),
    ...output.map(row => row.map(csvEscape).join(","))
  ].join("\n");

  console.log("Cards found:", cards.length);
  console.log("Rows exported:", output.length);
  console.log("Rows skipped:", skipped.length);
  console.log("Yaxel exported:", output.some(r => /yaxel lendeborg/i.test(r[0])));
  console.table(skipped);

  try {
    await navigator.clipboard.writeText(csv);
    console.log("CSV copied to clipboard.");
  } catch (e) {
    console.warn("Clipboard access failed. Copy the CSV from the output below.");
    console.log(csv);
  }
})();