const fs = require("fs");
const data = JSON.parse(fs.readFileSync("matches_tmp.json", "utf8"));
const matches = data.matches;

// 日付ごとにグループ化
const matchesByDate = {};
matches.forEach(m => {
  if (!matchesByDate[m.matchDate]) {
    matchesByDate[m.matchDate] = [];
  }
  matchesByDate[m.matchDate].push(m);
});

console.log("=== 日付別試合数 ===");
Object.keys(matchesByDate).sort().forEach(date => {
  const dateMatches = matchesByDate[date];
  console.log(date + ": " + dateMatches.length + "試合");
  const stageCounts = {};
  dateMatches.forEach(m => {
    stageCounts[m.stage] = (stageCounts[m.stage] || 0) + 1;
  });
  Object.entries(stageCounts).forEach(([stage, count]) => {
    console.log("  - " + stage + ": " + count);
  });
});

// 最終日（最大の日付）の試合構成を確認
const dates = Object.keys(matchesByDate).sort();
const finalDay = dates[dates.length - 1];
console.log("\n=== 最終日 (" + finalDay + ") の試合構成 ===");
const finalDayMatches = matchesByDate[finalDay];
const finalDayStages = {};
finalDayMatches.forEach(m => {
  finalDayStages[m.stage] = (finalDayStages[m.stage] || 0) + 1;
});

console.log("期待値: semifinal=2, third_place=1, final=1, training=複数");
console.log("実際の値:");
Object.entries(finalDayStages).sort().forEach(([stage, count]) => {
  console.log("  " + stage + ": " + count);
});

// 決勝トーナメントの会場確認
console.log("\n=== 決勝トーナメント（semifinal, third_place, final）の会場確認 ===");
const knockoutStages = ["semifinal", "third_place", "final"];
matches.filter(m => knockoutStages.includes(m.stage)).forEach(m => {
  console.log("試合ID: " + m.id + ", ステージ: " + m.stage + ", 会場: " + (m.venue ? m.venue.name : "N/A") + ", isFinalsVenue: " + (m.venue ? m.venue.isFinalsVenue : "N/A"));
});
