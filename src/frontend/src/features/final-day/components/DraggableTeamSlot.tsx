// src/features/final-day/components/DraggableTeamSlot.tsx
// クリック入れ替え可能なチーム枠

import type { TeamSlot } from '../types';

interface DraggableTeamSlotProps {
  matchId: number;
  side: 'home' | 'away';
  team: TeamSlot;
  disabled?: boolean;
  onClick?: () => void;
  /** クリック入れ替えモードで選択されているか */
  isSelected?: boolean;
}

export function DraggableTeamSlot({
  matchId,
  side,
  team,
  disabled = false,
  onClick,
  isSelected = false,
}: DraggableTeamSlotProps) {
  // クリック不可の条件
  const isClickDisabled = disabled || team.type === 'winner' || team.type === 'loser';

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isClickDisabled && onClick) {
      onClick();
    }
  };

  return (
    <div
      className={`
        px-2 py-1 min-w-[70px] text-center text-xs
        border rounded select-none
        transition-all duration-150
        ${isClickDisabled
          ? 'cursor-not-allowed opacity-60 bg-gray-100 border-gray-300'
          : 'cursor-pointer hover:bg-gray-50 hover:border-gray-400 border-gray-300'
        }
        ${isSelected ? 'ring-2 ring-blue-500 bg-blue-100 border-blue-500' : ''}
      `}
      onClick={handleClick}
    >
      {/* チーム名 */}
      <div className="font-medium truncate">
        {team.displayName}
      </div>
      {/* シード表示 */}
      {team.seed && (
        <div className="text-[10px] text-gray-500">
          {team.seed}
        </div>
      )}
      {/* ロックアイコン（勝者/敗者枠） */}
      {(team.type === 'winner' || team.type === 'loser') && (
        <div className="text-[10px] text-gray-400">
          {team.type === 'winner' ? '(勝者)' : '(敗者)'}
        </div>
      )}
    </div>
  );
}
