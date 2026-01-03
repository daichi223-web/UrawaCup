/**
 * インストールプロンプト
 *
 * PWAインストールを促すプロンプト
 */

import React, { useState } from 'react';
import { Download, X, Smartphone } from 'lucide-react';
import { useInstallPrompt } from '@/hooks/usePWA';
import { cn } from '@/utils/cn';

interface InstallPromptProps {
  className?: string;
  /** 自動的に表示するか（初回訪問時など） */
  autoShow?: boolean;
}

export const InstallPrompt: React.FC<InstallPromptProps> = ({
  className,
  autoShow = false,
}) => {
  const { canInstall, isInstalled, promptInstall } = useInstallPrompt();
  const [isDismissed, setIsDismissed] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  // 表示条件
  const shouldShow = canInstall && !isDismissed && !isInstalled && (autoShow || true);

  if (!shouldShow) {
    return null;
  }

  const handleInstall = async () => {
    setIsInstalling(true);
    try {
      const result = await promptInstall();
      if (result) {
        setIsDismissed(true);
      }
    } finally {
      setIsInstalling(false);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    // 24時間後に再表示
    const dismissedUntil = Date.now() + 24 * 60 * 60 * 1000;
    localStorage.setItem('pwa-install-dismissed-until', dismissedUntil.toString());
  };

  return (
    <div
      className={cn(
        'fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96',
        'bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-4',
        'animate-slide-up z-50',
        className
      )}
      role="dialog"
      aria-labelledby="install-prompt-title"
    >
      <div className="flex items-start gap-3">
        <div className="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
          <Smartphone className="w-6 h-6 text-red-600 dark:text-red-400" />
        </div>
        <div className="flex-1">
          <h3
            id="install-prompt-title"
            className="font-semibold text-gray-900 dark:text-white mb-1"
          >
            アプリをインストール
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            ホーム画面に追加すると、オフラインでも素早くアクセスできます。
          </p>
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleInstall}
              disabled={isInstalling}
              className={cn(
                'flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md font-medium',
                'hover:bg-red-700 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              <Download className="w-4 h-4" />
              {isInstalling ? 'インストール中...' : 'インストール'}
            </button>
            <button
              onClick={handleDismiss}
              className={cn(
                'px-4 py-2 text-gray-600 dark:text-gray-400 rounded-md',
                'hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors',
                'focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2'
              )}
            >
              今はしない
            </button>
          </div>
        </div>
        <button
          onClick={handleDismiss}
          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
          aria-label="閉じる"
        >
          <X className="w-4 h-4 text-gray-500" />
        </button>
      </div>
    </div>
  );
};

export default InstallPrompt;
