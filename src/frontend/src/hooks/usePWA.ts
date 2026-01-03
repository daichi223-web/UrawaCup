/**
 * 浦和カップ トーナメント管理システム - PWAフック
 *
 * PWA機能を利用するためのカスタムフック
 * - Service Worker登録
 * - オンライン/オフライン状態管理
 * - インストールプロンプト
 */

import { useState, useEffect, useCallback } from 'react';
import { registerSW } from 'virtual:pwa-register';

// ============================================
// Service Worker登録フック
// ============================================

interface UseServiceWorkerResult {
  /** 更新が利用可能か */
  needRefresh: boolean;
  /** オフラインで使用可能か */
  offlineReady: boolean;
  /** 更新を適用 */
  updateServiceWorker: () => Promise<void>;
  /** 更新をスキップ */
  skipWaiting: () => void;
}

/**
 * Service Workerの登録と更新を管理するフック
 */
export function useServiceWorker(): UseServiceWorkerResult {
  const [needRefresh, setNeedRefresh] = useState(false);
  const [offlineReady, setOfflineReady] = useState(false);
  const [updateSW, setUpdateSW] = useState<(() => Promise<void>) | undefined>();

  useEffect(() => {
    const registrationPromise = registerSW({
      immediate: true,
      onNeedRefresh() {
        setNeedRefresh(true);
        console.log('[PWA] 新しいバージョンが利用可能です');
      },
      onOfflineReady() {
        setOfflineReady(true);
        console.log('[PWA] オフラインで使用できます');
      },
      onRegisteredSW(swUrl, registration) {
        console.log('[PWA] Service Worker登録完了:', swUrl);
        // 定期的に更新をチェック（1時間ごと）
        if (registration) {
          setInterval(() => {
            registration.update();
          }, 60 * 60 * 1000);
        }
      },
      onRegisterError(error) {
        console.error('[PWA] Service Worker登録エラー:', error);
      },
    });

    setUpdateSW(() => registrationPromise);
  }, []);

  const updateServiceWorker = useCallback(async () => {
    if (updateSW) {
      await updateSW();
      setNeedRefresh(false);
    }
  }, [updateSW]);

  const skipWaiting = useCallback(() => {
    setNeedRefresh(false);
  }, []);

  return {
    needRefresh,
    offlineReady,
    updateServiceWorker,
    skipWaiting,
  };
}

// ============================================
// オンライン状態フック
// ============================================

/**
 * オンライン/オフライン状態を監視するフック
 */
export function useOnlineStatus(): boolean {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      console.log('[PWA] オンラインになりました');
    };

    const handleOffline = () => {
      setIsOnline(false);
      console.log('[PWA] オフラインになりました');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}

// ============================================
// インストールプロンプトフック
// ============================================

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

interface UseInstallPromptResult {
  /** インストール可能か */
  canInstall: boolean;
  /** インストール済みか */
  isInstalled: boolean;
  /** インストールを促す */
  promptInstall: () => Promise<boolean>;
}

/**
 * PWAインストールプロンプトを管理するフック
 */
export function useInstallPrompt(): UseInstallPromptResult {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    // すでにインストール済みかチェック
    const checkInstalled = () => {
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
      const isInWebApp = (window.navigator as { standalone?: boolean }).standalone === true;
      setIsInstalled(isStandalone || isInWebApp);
    };

    checkInstalled();

    // インストールプロンプトイベントをキャッチ
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      console.log('[PWA] インストール可能です');
    };

    // インストール完了イベント
    const handleAppInstalled = () => {
      setDeferredPrompt(null);
      setIsInstalled(true);
      console.log('[PWA] アプリがインストールされました');
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const promptInstall = useCallback(async (): Promise<boolean> => {
    if (!deferredPrompt) {
      return false;
    }

    try {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log('[PWA] インストール選択:', outcome);

      if (outcome === 'accepted') {
        setDeferredPrompt(null);
        return true;
      }
      return false;
    } catch (error) {
      console.error('[PWA] インストールエラー:', error);
      return false;
    }
  }, [deferredPrompt]);

  return {
    canInstall: deferredPrompt !== null && !isInstalled,
    isInstalled,
    promptInstall,
  };
}

// ============================================
// 同期状態フック
// ============================================

import { subscribeSyncState, getSyncState, syncAll } from '@/lib/syncService';

interface SyncState {
  isSyncing: boolean;
  lastSyncAt: Date | null;
  pendingCount: number;
  conflictCount: number;
  error: string | null;
}

interface UseSyncStateResult extends SyncState {
  /** 手動で同期を実行 */
  sync: () => Promise<void>;
}

/**
 * オフライン同期状態を監視するフック
 */
export function useSyncState(): UseSyncStateResult {
  const [state, setState] = useState<SyncState>(getSyncState());

  useEffect(() => {
    const unsubscribe = subscribeSyncState((newState) => {
      setState(newState);
    });

    return unsubscribe;
  }, []);

  const sync = useCallback(async () => {
    await syncAll();
  }, []);

  return {
    ...state,
    sync,
  };
}

// ============================================
// ネットワーク状態の詳細フック
// ============================================

interface NetworkInfo {
  isOnline: boolean;
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
  saveData?: boolean;
}

interface NavigatorConnection extends EventTarget {
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
  saveData?: boolean;
}

declare global {
  interface Navigator {
    connection?: NavigatorConnection;
    mozConnection?: NavigatorConnection;
    webkitConnection?: NavigatorConnection;
  }
}

/**
 * ネットワーク情報を取得するフック
 */
export function useNetworkInfo(): NetworkInfo {
  const isOnline = useOnlineStatus();
  const [networkInfo, setNetworkInfo] = useState<NetworkInfo>({
    isOnline,
  });

  useEffect(() => {
    const connection =
      navigator.connection ||
      navigator.mozConnection ||
      navigator.webkitConnection;

    if (!connection) {
      setNetworkInfo({ isOnline });
      return;
    }

    const updateNetworkInfo = () => {
      setNetworkInfo({
        isOnline,
        effectiveType: connection.effectiveType,
        downlink: connection.downlink,
        rtt: connection.rtt,
        saveData: connection.saveData,
      });
    };

    updateNetworkInfo();
    connection.addEventListener('change', updateNetworkInfo);

    return () => {
      connection.removeEventListener('change', updateNetworkInfo);
    };
  }, [isOnline]);

  return networkInfo;
}
