// src/features/final-day/components/TeamSlotPreview.tsx
// ドラッグ中のチームプレビュー

import type { TeamSlot } from '../types';

interface TeamSlotPreviewProps {
  team: TeamSlot;
}

export function TeamSlotPreview({ team }: TeamSlotPreviewProps) {
  return (
    <div className="px-3 py-2 bg-blue-100 border-2 border-blue-500 rounded shadow-lg">
      <div className="flex items-center gap-2">
        <span className="text-blue-600">≡</span>
        <span className="font-medium text-sm">{team.displayName}</span>
      </div>
      {team.seed && (
        <div className="text-xs text-blue-600 ml-5">{team.seed}</div>
      )}
    </div>
  );
}
