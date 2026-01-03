/**
 * 競合解決ダイアログ
 *
 * サーバーとローカルのデータに競合がある場合に表示
 * ユーザーがどちらのデータを採用するか選択できる
 */

import React, { useState, useEffect } from 'react';
import { AlertTriangle, Clock, Server, Smartphone } from 'lucide-react';
import { db, type ConflictItem, resolveConflict, getPendingConflicts } from '@/lib/db';
import { cn } from '@/utils/cn';
import type { Match, Goal } from '@/types';

interface ConflictResolverProps {
  className?: string;
  /** 解決完了時のコールバック */
  onResolve?: () => void;
}

export const ConflictResolver: React.FC<ConflictResolverProps> = ({
  className,
  onResolve,
}) => {
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isResolving, setIsResolving] = useState(false);

  // 競合を読み込む
  useEffect(() => {
    const loadConflicts = async () => {
      const pending = await getPendingConflicts();
      setConflicts(pending);
    };
    loadConflicts();
  }, []);

  const currentConflict = conflicts[currentIndex];

  // 競合がない場合は何も表示しない
  if (conflicts.length === 0) {
    return null;
  }

  const handleResolve = async (
    resolution: 'resolved_local' | 'resolved_server'
  ) => {
    if (!currentConflict?.id) return;

    setIsResolving(true);
    try {
      // 選択されたデータをDBに保存
      const dataToSave = resolution === 'resolved_local'
        ? currentConflict.localData
        : currentConflict.serverData;

      if (currentConflict.entityType === 'match') {
        await db.matches.update(currentConflict.entityId, dataToSave as Match);
      } else if (currentConflict.entityType === 'goal') {
        await db.goals.update(currentConflict.entityId, dataToSave as Goal);
      }

      // 競合を解決済みにマーク
      await resolveConflict(currentConflict.id, resolution);

      // 次の競合へ
      if (currentIndex < conflicts.length - 1) {
        setCurrentIndex(currentIndex + 1);
      } else {
        // すべて解決
        setConflicts([]);
        onResolve?.();
      }
    } catch (error) {
      console.error('競合解決エラー:', error);
    } finally {
      setIsResolving(false);
    }
  };

  return (
    <div
      className={cn(
        'fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50',
        className
      )}
      role="dialog"
      aria-labelledby="conflict-title"
      aria-modal="true"
    >
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        {/* ヘッダー */}
        <div className="bg-yellow-50 dark:bg-yellow-900/30 px-6 py-4 border-b border-yellow-200 dark:border-yellow-800">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
            <div>
              <h2
                id="conflict-title"
                className="font-semibold text-lg text-gray-900 dark:text-white"
              >
                データの競合を解決
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {currentIndex + 1} / {conflicts.length} 件
              </p>
            </div>
          </div>
        </div>

        {/* コンテンツ */}
        <div className="p-6 overflow-y-auto">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            同じデータがサーバーとこの端末で異なる内容に更新されました。
            どちらのデータを採用しますか？
          </p>

          <div className="grid md:grid-cols-2 gap-4">
            {/* ローカルデータ */}
            <div className="border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Smartphone className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                <h3 className="font-medium text-gray-900 dark:text-white">
                  この端末のデータ
                </h3>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-2">
                <Clock className="w-3 h-3" />
                更新日時: {formatDate(currentConflict.localUpdatedAt)}
              </div>
              <DataPreview
                entityType={currentConflict.entityType}
                data={currentConflict.localData}
              />
            </div>

            {/* サーバーデータ */}
            <div className="border border-green-200 dark:border-green-800 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Server className="w-5 h-5 text-green-600 dark:text-green-400" />
                <h3 className="font-medium text-gray-900 dark:text-white">
                  サーバーのデータ
                </h3>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-2">
                <Clock className="w-3 h-3" />
                更新日時: {formatDate(currentConflict.serverUpdatedAt)}
              </div>
              <DataPreview
                entityType={currentConflict.entityType}
                data={currentConflict.serverData}
              />
            </div>
          </div>
        </div>

        {/* フッター */}
        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-end gap-3">
            <button
              onClick={() => handleResolve('resolved_server')}
              disabled={isResolving}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-md font-medium',
                'bg-green-600 text-white hover:bg-green-700 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              <Server className="w-4 h-4" />
              サーバーを採用
            </button>
            <button
              onClick={() => handleResolve('resolved_local')}
              disabled={isResolving}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-md font-medium',
                'bg-blue-600 text-white hover:bg-blue-700 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              <Smartphone className="w-4 h-4" />
              この端末を採用
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * データプレビューコンポーネント
 */
interface DataPreviewProps {
  entityType: 'match' | 'goal';
  data: unknown;
}

const DataPreview: React.FC<DataPreviewProps> = ({ entityType, data }) => {
  if (entityType === 'match') {
    const match = data as Partial<Match>;
    return (
      <div className="bg-gray-50 dark:bg-gray-900 rounded p-3 text-sm">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <span className="text-gray-500 dark:text-gray-400">前半:</span>{' '}
            <span className="font-medium">
              {match.home_score_half1 ?? '-'} - {match.away_score_half1 ?? '-'}
            </span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">後半:</span>{' '}
            <span className="font-medium">
              {match.home_score_half2 ?? '-'} - {match.away_score_half2 ?? '-'}
            </span>
          </div>
          <div className="col-span-2">
            <span className="text-gray-500 dark:text-gray-400">合計:</span>{' '}
            <span className="font-bold text-lg">
              {match.home_score_total ?? '-'} - {match.away_score_total ?? '-'}
            </span>
          </div>
          {match.has_penalty_shootout && (
            <div className="col-span-2">
              <span className="text-gray-500 dark:text-gray-400">PK:</span>{' '}
              <span className="font-medium">
                {match.home_pk ?? '-'} - {match.away_pk ?? '-'}
              </span>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (entityType === 'goal') {
    const goal = data as Partial<Goal>;
    return (
      <div className="bg-gray-50 dark:bg-gray-900 rounded p-3 text-sm">
        <div>
          <span className="text-gray-500 dark:text-gray-400">得点者:</span>{' '}
          <span className="font-medium">{goal.playerName ?? '不明'}</span>
        </div>
        <div>
          <span className="text-gray-500 dark:text-gray-400">時間:</span>{' '}
          <span className="font-medium">
            {goal.half === 1 ? '前半' : '後半'} {goal.minute}分
          </span>
        </div>
        {goal.isOwnGoal && (
          <div className="text-red-600 dark:text-red-400 text-xs mt-1">
            オウンゴール
          </div>
        )}
        {goal.isPenalty && (
          <div className="text-blue-600 dark:text-blue-400 text-xs mt-1">
            PK
          </div>
        )}
      </div>
    );
  }

  return (
    <pre className="bg-gray-50 dark:bg-gray-900 rounded p-3 text-xs overflow-auto">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
};

/**
 * 日時をフォーマット
 */
function formatDate(date: Date): string {
  return date.toLocaleString('ja-JP', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export default ConflictResolver;
