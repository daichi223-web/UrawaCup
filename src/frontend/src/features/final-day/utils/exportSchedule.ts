// src/features/final-day/utils/exportSchedule.ts
// 最終日組み合わせ表のエクスポート

import type { FinalMatch, VenueSchedule } from '../types';

/**
 * 最終日スケジュールをCSV形式でエクスポート
 */
export function exportScheduleToCSV(
  trainingVenues: VenueSchedule[],
  knockoutMatches: FinalMatch[],
  knockoutVenueName: string,
  date: string
): void {
  const lines: string[] = [];

  // ヘッダー
  lines.push(`最終日組み合わせ表,${date}`);
  lines.push('');

  // 順位リーグ（研修試合）
  lines.push('【順位リーグ】');
  for (const venue of trainingVenues) {
    lines.push('');
    lines.push(`会場: ${venue.name}`);
    lines.push('No,時刻,ホーム,アウェイ');

    for (const match of venue.matches) {
      const time = match.kickoffTime || '';
      const home = match.homeTeam.displayName;
      const away = match.awayTeam.displayName;
      lines.push(`${match.matchOrder},${time},${home},${away}`);
    }
  }

  lines.push('');
  lines.push('');

  // 決勝トーナメント
  lines.push('【決勝トーナメント】');
  lines.push(`会場: ${knockoutVenueName}`);
  lines.push('No,時刻,種別,ホーム,アウェイ');

  const matchTypeLabels: Record<string, string> = {
    semifinal: '準決勝',
    third_place: '3位決定戦',
    final: '決勝',
  };

  const sortedKnockout = [...knockoutMatches].sort((a, b) => {
    const order = { semifinal: 1, third_place: 2, final: 3 };
    return (order[a.matchType] || 99) - (order[b.matchType] || 99);
  });

  for (const match of sortedKnockout) {
    const time = match.kickoffTime || '';
    const type = matchTypeLabels[match.matchType] || match.matchType;
    const home = match.homeTeam.displayName;
    const away = match.awayTeam.displayName;
    lines.push(`${match.matchOrder},${time},${type},${home},${away}`);
  }

  // BOM付きUTF-8でCSVを生成
  const bom = '\uFEFF';
  const csv = bom + lines.join('\r\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });

  // ダウンロード
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `最終日組み合わせ_${date}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * 最終日スケジュールを印刷用HTMLとして開く
 */
export function printSchedule(
  trainingVenues: VenueSchedule[],
  knockoutMatches: FinalMatch[],
  knockoutVenueName: string,
  date: string
): void {
  const matchTypeLabels: Record<string, string> = {
    semifinal: '準決勝',
    third_place: '3位決定戦',
    final: '決勝',
  };

  const sortedKnockout = [...knockoutMatches].sort((a, b) => {
    const order = { semifinal: 1, third_place: 2, final: 3 };
    return (order[a.matchType] || 99) - (order[b.matchType] || 99);
  });

  const html = `
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>最終日組み合わせ表 - ${date}</title>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    h1 { font-size: 18px; text-align: center; margin-bottom: 20px; }
    h2 { font-size: 14px; margin-top: 20px; background: #f0f0f0; padding: 5px; }
    h3 { font-size: 12px; margin: 10px 0 5px; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 10px; }
    th, td { border: 1px solid #333; padding: 4px 8px; text-align: center; font-size: 11px; }
    th { background: #e0e0e0; }
    .venue-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
    @media print { .venue-grid { grid-template-columns: repeat(2, 1fr); } }
  </style>
</head>
<body>
  <h1>最終日組み合わせ表 - ${date}</h1>

  <h2>【順位リーグ】</h2>
  <div class="venue-grid">
    ${trainingVenues.map(venue => `
      <div>
        <h3>${venue.name}</h3>
        <table>
          <tr><th>No</th><th>時刻</th><th>ホーム</th><th>vs</th><th>アウェイ</th></tr>
          ${venue.matches.map(m => `
            <tr>
              <td>${m.matchOrder}</td>
              <td>${m.kickoffTime || ''}</td>
              <td>${m.homeTeam.displayName}</td>
              <td>vs</td>
              <td>${m.awayTeam.displayName}</td>
            </tr>
          `).join('')}
        </table>
      </div>
    `).join('')}
  </div>

  <h2>【決勝トーナメント】 - ${knockoutVenueName}</h2>
  <table>
    <tr><th>No</th><th>時刻</th><th>種別</th><th>ホーム</th><th>vs</th><th>アウェイ</th></tr>
    ${sortedKnockout.map(m => `
      <tr>
        <td>${m.matchOrder}</td>
        <td>${m.kickoffTime || ''}</td>
        <td>${matchTypeLabels[m.matchType] || m.matchType}</td>
        <td>${m.homeTeam.displayName}</td>
        <td>vs</td>
        <td>${m.awayTeam.displayName}</td>
      </tr>
    `).join('')}
  </table>
</body>
</html>
  `;

  const printWindow = window.open('', '_blank');
  if (printWindow) {
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.print();
  }
}
