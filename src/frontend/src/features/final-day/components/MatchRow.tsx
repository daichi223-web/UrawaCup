// src/features/final-day/components/MatchRow.tsx
// 試合行コンポーネント

import type { FinalMatch } from '../types';
import { DraggableTeamSlot } from './DraggableTeamSlot';

interface MatchRowProps {
  match: FinalMatch;
  onMatchClick?: (match: FinalMatch) => void;
  showLabel?: boolean;
}

export function MatchRow({ match, onMatchClick, showLabel = false }: MatchRowProps) {
  const isCompleted = match.status === 'completed';

  const handleRowClick = () => {
    if (onMatchClick) {
      onMatchClick(match);
    }
  };

  // 試合種別のラベル
  const getMatchLabel = () => {
    switch (match.matchType) {
      case 'semifinal':
        return '準決勝';
      case 'third_place':
        return '3位決';
      case 'final':
        return '決勝';
      case 'training':
        return match.notes || '研修';
      default:
        return '';
    }
  };

  return (
    <tr
      className="border-b hover:bg-blue-50 cursor-pointer transition-colors duration-150"
      onClick={handleRowClick}
    >
      {/* 試合番号 */}
      <td className="px-2 py-2 text-center w-8 text-gray-500 text-xs">
        {match.matchOrder}
      </td>

      {/* キックオフ時刻 */}
      <td className="px-2 py-2 text-center w-16 font-medium text-sm">
        {match.kickoffTime}
      </td>

      {/* 試合種別（オプション） */}
      {showLabel && (
        <td className="px-2 py-2 text-center w-16">
          <span className={`
            text-xs px-1.5 py-0.5 rounded
            ${match.matchType === 'final' ? 'bg-yellow-100 text-yellow-800' : ''}
            ${match.matchType === 'third_place' ? 'bg-orange-100 text-orange-800' : ''}
            ${match.matchType === 'semifinal' ? 'bg-blue-100 text-blue-800' : ''}
            ${match.matchType === 'training' ? 'bg-gray-100 text-gray-600' : ''}
          `}>
            {getMatchLabel()}
          </span>
        </td>
      )}

      {/* 対戦カード */}
      <td className="px-2 py-2" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-center gap-2">
          <DraggableTeamSlot
            matchId={match.id}
            side="home"
            team={match.homeTeam}
            disabled={isCompleted}
          />
          <span className="text-gray-400 text-sm">-</span>
          <DraggableTeamSlot
            matchId={match.id}
            side="away"
            team={match.awayTeam}
            disabled={isCompleted}
          />
        </div>
      </td>

      {/* スコア（完了時のみ） */}
      {isCompleted && (
        <td className="px-2 py-2 text-center w-20">
          <span className="font-bold">
            {match.homeScore} - {match.awayScore}
          </span>
        </td>
      )}

      {/* 審判情報 */}
      <td className="px-2 py-2 text-xs text-gray-600 w-20">
        <div>主: {match.referee?.main || '当該'}</div>
        <div>副: {match.referee?.assistant || '当該'}</div>
      </td>
    </tr>
  );
}
