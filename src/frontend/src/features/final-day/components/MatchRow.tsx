// src/features/final-day/components/MatchRow.tsx
// 試合行コンポーネント

import { AlertTriangle } from 'lucide-react';
import type { FinalMatch } from '../types';
import { DraggableTeamSlot } from './DraggableTeamSlot';

interface RematchInfo {
  groupId?: string;
  matchDate?: string;
  score?: string;
}

interface MatchRowProps {
  match: FinalMatch;
  onMatchClick?: (match: FinalMatch) => void;
  showLabel?: boolean;
  /** 再戦（予選で対戦済み）かどうか */
  isRematch?: boolean;
  /** 再戦情報（予選での対戦詳細） */
  rematchInfo?: RematchInfo;
  /** クリック入れ替えモード用: 選択中のチーム情報 */
  selectedSlot?: { matchId: number; side: 'home' | 'away' } | null;
  /** クリック入れ替えモード用: チームスロットクリック時のコールバック */
  onSlotClick?: (matchId: number, side: 'home' | 'away') => void;
}

export function MatchRow({ match, onMatchClick, showLabel = false, isRematch = false, rematchInfo, selectedSlot, onSlotClick }: MatchRowProps) {
  const isCompleted = match.status === 'completed';

  const handleRowClick = () => {
    if (onMatchClick) {
      onMatchClick(match);
    }
  };

  // 再戦時のスタイル
  const rowClassName = `border-b cursor-pointer transition-colors duration-150 ${
    isRematch
      ? 'bg-orange-50 border-l-4 border-l-orange-400 hover:bg-orange-100'
      : 'hover:bg-blue-50'
  }`;

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
      className={rowClassName}
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
        <div className="flex flex-col">
          <div className="flex items-center justify-center gap-2">
            <DraggableTeamSlot
              matchId={match.id}
              side="home"
              team={match.homeTeam}
              disabled={isCompleted}
              isSelected={selectedSlot?.matchId === match.id && selectedSlot?.side === 'home'}
              onClick={onSlotClick ? () => onSlotClick(match.id, 'home') : undefined}
            />
            <span className="text-gray-400 text-sm">-</span>
            <DraggableTeamSlot
              matchId={match.id}
              side="away"
              team={match.awayTeam}
              disabled={isCompleted}
              isSelected={selectedSlot?.matchId === match.id && selectedSlot?.side === 'away'}
              onClick={onSlotClick ? () => onSlotClick(match.id, 'away') : undefined}
            />
          </div>
          {/* 再戦警告 */}
          {isRematch && (
            <div className="flex items-center justify-center gap-1 mt-1 text-xs text-orange-600">
              <AlertTriangle className="w-3 h-3" />
              <span>
                予選{rematchInfo?.groupId ? `${rematchInfo.groupId}組` : ''}で対戦済み
                {rematchInfo?.score && ` (${rematchInfo.score})`}
              </span>
            </div>
          )}
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
