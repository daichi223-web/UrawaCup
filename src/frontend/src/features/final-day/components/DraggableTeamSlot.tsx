// src/features/final-day/components/DraggableTeamSlot.tsx
// ドラッグ可能なチーム枠

import { useDraggable, useDroppable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import type { TeamSlot, DragItem, DropTarget } from '../types';

interface DraggableTeamSlotProps {
  matchId: number;
  side: 'home' | 'away';
  team: TeamSlot;
  disabled?: boolean;
  onClick?: () => void;
}

export function DraggableTeamSlot({
  matchId,
  side,
  team,
  disabled = false,
  onClick,
}: DraggableTeamSlotProps) {
  const id = `${matchId}-${side}`;

  // ドラッグ不可の条件
  const isDragDisabled = disabled || team.type === 'winner' || team.type === 'loser';

  // ドラッグ設定
  const {
    attributes,
    listeners,
    setNodeRef: setDragRef,
    transform,
    isDragging,
  } = useDraggable({
    id,
    data: {
      type: 'team',
      matchId,
      side,
      team,
    } as DragItem,
    disabled: isDragDisabled,
  });

  // ドロップ設定（同じ要素がドロップ先にもなる）
  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id,
    data: {
      matchId,
      side,
    } as DropTarget,
    disabled: isDragDisabled,
  });

  // 両方のrefを結合
  const setNodeRef = (node: HTMLElement | null) => {
    setDragRef(node);
    setDropRef(node);
  };

  const style = {
    transform: CSS.Translate.toString(transform),
  };

  const handleClick = (e: React.MouseEvent) => {
    if (!isDragDisabled && onClick) {
      e.stopPropagation();
      onClick();
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        px-2 py-1 min-w-[70px] text-center text-xs
        border rounded select-none
        transition-all duration-150
        ${isDragDisabled
          ? 'cursor-not-allowed opacity-60 bg-gray-100 border-gray-300'
          : 'cursor-grab active:cursor-grabbing hover:bg-gray-50 hover:border-gray-400 border-gray-300'
        }
        ${isDragging ? 'opacity-50 border-blue-500 bg-blue-50 z-50' : ''}
        ${isOver && !isDragDisabled ? 'border-green-500 bg-green-50 border-dashed border-2' : ''}
      `}
      onClick={handleClick}
      {...attributes}
      {...listeners}
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
