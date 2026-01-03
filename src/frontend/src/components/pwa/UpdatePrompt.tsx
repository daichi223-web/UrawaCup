/**
 * アップデートプロンプト
 *
 * 新しいバージョンが利用可能な時に表示するプロンプト
 */

import React from 'react';
import { RefreshCw, X } from 'lucide-react';
import { useServiceWorker } from '@/hooks/usePWA';
import { cn } from '@/utils/cn';

interface UpdatePromptProps {
  className?: string;
}

export const UpdatePrompt: React.FC<UpdatePromptProps> = ({ className }) => {
  const { needRefresh, updateServiceWorker, skipWaiting } = useServiceWorker();

  if (!needRefresh) {
    return null;
  }

  return (
    <div
      className={cn(
        'fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96',
        'bg-blue-600 text-white rounded-lg shadow-lg p-4',
        'animate-slide-up z-50',
        className
      )}
      role="alert"
      aria-live="polite"
    >
      <div className="flex items-start gap-3">
        <RefreshCw className="w-5 h-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <h3 className="font-semibold mb-1">新しいバージョンが利用可能です</h3>
          <p className="text-sm text-blue-100">
            アプリを更新して最新の機能を利用しましょう。
          </p>
          <div className="flex gap-2 mt-3">
            <button
              onClick={updateServiceWorker}
              className={cn(
                'px-4 py-2 bg-white text-blue-600 rounded-md font-medium',
                'hover:bg-blue-50 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-blue-600'
              )}
            >
              今すぐ更新
            </button>
            <button
              onClick={skipWaiting}
              className={cn(
                'px-4 py-2 text-blue-100 rounded-md',
                'hover:bg-blue-700 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-blue-600'
              )}
            >
              後で
            </button>
          </div>
        </div>
        <button
          onClick={skipWaiting}
          className="p-1 hover:bg-blue-700 rounded transition-colors"
          aria-label="閉じる"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default UpdatePrompt;
