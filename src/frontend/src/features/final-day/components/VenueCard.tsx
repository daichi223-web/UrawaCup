// src/features/final-day/components/VenueCard.tsx
// 会場カードコンポーネント

import type { VenueSchedule, FinalMatch } from '../types';
import { MatchRow } from './MatchRow';

interface VenueCardProps {
  venue: VenueSchedule;
  onMatchClick?: (match: FinalMatch) => void;
}

export function VenueCard({ venue, onMatchClick }: VenueCardProps) {
  return (
    <div className="border rounded-lg overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow">
      {/* 会場名ヘッダー */}
      <div className="bg-gray-100 px-3 py-2 font-semibold text-center border-b text-sm">
        {venue.name}
      </div>

      {/* 試合テーブル */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50 text-xs">
              <th className="px-2 py-1 w-8"></th>
              <th className="px-2 py-1 w-16">KO</th>
              <th className="px-2 py-1">対 戦</th>
              <th className="px-2 py-1 w-20">審 判</th>
            </tr>
          </thead>
          <tbody>
            {venue.matches.length > 0 ? (
              venue.matches.map((match) => (
                <MatchRow
                  key={match.id}
                  match={match}
                  onMatchClick={onMatchClick}
                />
              ))
            ) : (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                  試合がありません
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* 会場担当 */}
      {venue.manager && (
        <div className="px-3 py-2 bg-gray-50 border-t text-xs">
          会場担当: <span className="font-medium">{venue.manager}</span>
        </div>
      )}
    </div>
  );
}
