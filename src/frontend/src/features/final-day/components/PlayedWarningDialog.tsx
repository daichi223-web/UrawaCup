// src/features/final-day/components/PlayedWarningDialog.tsx
// 対戦済みチーム警告ダイアログ

import { AlertTriangle, X } from 'lucide-react';

interface PlayedWarningDialogProps {
  isOpen: boolean;
  team1Name: string;
  team2Name: string;
  matchDate?: string | null;
  score?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export function PlayedWarningDialog({
  isOpen,
  team1Name,
  team2Name,
  matchDate,
  score,
  onConfirm,
  onCancel,
}: PlayedWarningDialogProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* オーバーレイ */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onCancel}
      />

      {/* ダイアログ */}
      <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden">
        {/* ヘッダー */}
        <div className="bg-amber-500 px-4 py-3 flex items-center gap-3">
          <AlertTriangle className="text-white" size={24} />
          <h3 className="text-lg font-semibold text-white">対戦済みの組み合わせ</h3>
          <button
            onClick={onCancel}
            className="ml-auto text-white/80 hover:text-white"
          >
            <X size={20} />
          </button>
        </div>

        {/* 本文 */}
        <div className="p-4">
          <p className="text-gray-700 mb-4">
            <span className="font-semibold">{team1Name}</span> と{' '}
            <span className="font-semibold">{team2Name}</span> は
            <span className="text-amber-600 font-semibold">予選リーグで対戦済み</span>です。
          </p>

          {matchDate && (
            <div className="bg-gray-50 rounded-lg p-3 mb-4">
              <div className="text-sm text-gray-500">予選での対戦結果</div>
              <div className="text-gray-800">
                {matchDate}
                {score && <span className="ml-2 font-semibold">({score})</span>}
              </div>
            </div>
          )}

          <p className="text-sm text-gray-600">
            研修試合では未対戦のチーム同士が推奨されます。
            この組み合わせを強制的に確定しますか？
          </p>
        </div>

        {/* フッター */}
        <div className="bg-gray-50 px-4 py-3 flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 border rounded hover:bg-gray-100"
          >
            キャンセル
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 bg-amber-500 text-white rounded hover:bg-amber-600"
          >
            強制確定
          </button>
        </div>
      </div>
    </div>
  );
}
