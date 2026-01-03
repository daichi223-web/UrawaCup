// src/features/final-day/components/MatchEditModal.tsx
// 試合編集モーダル

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import type { FinalMatch, TeamSlot } from '../types';
import type { Team } from '@shared/types';

interface MatchEditModalProps {
  match: FinalMatch;
  teams: Team[];
  onSave: (match: FinalMatch) => void;
  onDelete?: (matchId: number) => void;
  onClose: () => void;
}

export function MatchEditModal({
  match,
  teams,
  onSave,
  onDelete,
  onClose,
}: MatchEditModalProps) {
  const [kickoffTime, setKickoffTime] = useState(match.kickoffTime);
  const [homeTeamId, setHomeTeamId] = useState<number | undefined>(match.homeTeam.teamId);
  const [awayTeamId, setAwayTeamId] = useState<number | undefined>(match.awayTeam.teamId);

  const isCompleted = match.status === 'completed';

  // 試合種別のラベル
  const getMatchTypeLabel = () => {
    switch (match.matchType) {
      case 'semifinal':
        return '準決勝';
      case 'third_place':
        return '3位決定戦';
      case 'final':
        return '決勝';
      case 'training':
        return '研修試合';
      default:
        return '試合';
    }
  };

  const handleSave = () => {
    if (!homeTeamId || !awayTeamId) return;
    if (homeTeamId === awayTeamId) return;

    const homeTeam = teams.find((t) => t.id === homeTeamId);
    const awayTeam = teams.find((t) => t.id === awayTeamId);

    if (!homeTeam || !awayTeam) return;

    const updatedMatch: FinalMatch = {
      ...match,
      kickoffTime,
      homeTeam: {
        type: 'fixed',
        teamId: homeTeamId,
        teamName: homeTeam.name,
        displayName: homeTeam.shortName || homeTeam.name,
      },
      awayTeam: {
        type: 'fixed',
        teamId: awayTeamId,
        teamName: awayTeam.name,
        displayName: awayTeam.shortName || awayTeam.name,
      },
    };

    onSave(updatedMatch);
  };

  const handleDelete = () => {
    if (onDelete && confirm('この試合を削除しますか？')) {
      onDelete(match.id);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        {/* ヘッダー */}
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <h3 className="font-semibold">試合編集</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X size={20} />
          </button>
        </div>

        {/* 本体 */}
        <div className="p-4 space-y-4">
          {/* 種別表示 */}
          <div className="text-sm text-gray-600">
            種別: <span className="font-medium">{getMatchTypeLabel()}</span>
          </div>

          {/* キックオフ時刻 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              キックオフ
            </label>
            <input
              type="time"
              value={kickoffTime}
              onChange={(e) => setKickoffTime(e.target.value)}
              disabled={isCompleted}
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            />
          </div>

          {/* ホームチーム */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              ホーム
            </label>
            <select
              value={homeTeamId || ''}
              onChange={(e) => setHomeTeamId(Number(e.target.value))}
              disabled={isCompleted || match.homeTeam.type === 'winner' || match.homeTeam.type === 'loser'}
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            >
              <option value="">選択してください</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name} {team.groupId ? `(${team.groupId}組)` : ''}
                </option>
              ))}
            </select>
            {match.homeTeam.seed && (
              <div className="text-xs text-gray-500 mt-1">
                シード: {match.homeTeam.seed}
              </div>
            )}
          </div>

          {/* アウェイチーム */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              アウェイ
            </label>
            <select
              value={awayTeamId || ''}
              onChange={(e) => setAwayTeamId(Number(e.target.value))}
              disabled={isCompleted || match.awayTeam.type === 'winner' || match.awayTeam.type === 'loser'}
              className="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            >
              <option value="">選択してください</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name} {team.groupId ? `(${team.groupId}組)` : ''}
                </option>
              ))}
            </select>
            {match.awayTeam.seed && (
              <div className="text-xs text-gray-500 mt-1">
                シード: {match.awayTeam.seed}
              </div>
            )}
          </div>

          {/* バリデーションエラー */}
          {homeTeamId && awayTeamId && homeTeamId === awayTeamId && (
            <div className="text-red-600 text-sm">
              同一チーム同士は対戦できません
            </div>
          )}

          {/* 完了済み警告 */}
          {isCompleted && (
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
              この試合は完了済みのため編集できません
            </div>
          )}
        </div>

        {/* フッター */}
        <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
          <div>
            {onDelete && !isCompleted && (
              <button
                onClick={handleDelete}
                className="px-3 py-1.5 text-red-600 hover:bg-red-50 rounded text-sm"
              >
                削除
              </button>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 border rounded hover:bg-gray-100 text-sm"
            >
              キャンセル
            </button>
            <button
              onClick={handleSave}
              disabled={isCompleted || !homeTeamId || !awayTeamId || homeTeamId === awayTeamId}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              保存
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
