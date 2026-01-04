// src/features/final-day/components/VenueCard.tsx
// 会場カードコンポーネント

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import type { VenueSchedule, FinalMatch } from '../types';
import type { Team } from '@shared/types';
import { MatchRow } from './MatchRow';

interface VenueCardProps {
  venue: VenueSchedule;
  teams?: Team[];
  onMatchClick?: (match: FinalMatch) => void;
  onManagerChange?: (venueId: number, teamId: number | null) => void;
}

export function VenueCard({ venue, teams, onMatchClick, onManagerChange }: VenueCardProps) {
  const [isEditingManager, setIsEditingManager] = useState(false);

  // 会場に所属するチームをフィルタ（同じグループのチームなど）
  const availableTeams = teams || [];

  const handleManagerChange = (teamId: string) => {
    const newTeamId = teamId ? parseInt(teamId) : null;
    onManagerChange?.(venue.id, newTeamId);
    setIsEditingManager(false);
  };

  // 現在のマネージャーチームを取得
  const currentManagerTeam = availableTeams.find(t => t.name === venue.manager);

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
      <div className="px-3 py-2 bg-gray-50 border-t text-xs">
        <div className="flex items-center gap-2">
          <span className="text-gray-600">担当:</span>
          {isEditingManager && availableTeams.length > 0 ? (
            <select
              className="flex-1 px-2 py-1 text-xs border rounded focus:ring-1 focus:ring-blue-500"
              value={currentManagerTeam?.id || ''}
              onChange={(e) => handleManagerChange(e.target.value)}
              onBlur={() => setIsEditingManager(false)}
              autoFocus
            >
              <option value="">選択してください</option>
              {availableTeams.map(team => (
                <option key={team.id} value={team.id}>
                  {team.shortName || team.name}
                </option>
              ))}
            </select>
          ) : (
            <button
              onClick={() => onManagerChange && setIsEditingManager(true)}
              className={`flex-1 text-left px-2 py-1 rounded hover:bg-gray-100 flex items-center justify-between ${
                onManagerChange ? 'cursor-pointer' : 'cursor-default'
              }`}
              disabled={!onManagerChange}
            >
              <span className="font-medium">{venue.manager || '未設定'}</span>
              {onManagerChange && <ChevronDown className="w-3 h-3 text-gray-400" />}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
