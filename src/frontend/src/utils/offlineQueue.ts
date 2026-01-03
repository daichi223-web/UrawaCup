
import { openDB, DBSchema, IDBPDatabase } from 'idb';

interface OfflineDB extends DBSchema {
    queue: {
        key: number;
        value: {
            url: string;
            method: string;
            data: any;
            timestamp: number;
        };
    };
}

const DB_NAME = 'urawa-cup-offline';
const STORE_NAME = 'queue';

class OfflineQueue {
    private dbPromise: Promise<IDBPDatabase<OfflineDB>>;

    constructor() {
        this.dbPromise = openDB<OfflineDB>(DB_NAME, 1, {
            upgrade(db) {
                db.createObjectStore(STORE_NAME, { keyPath: 'timestamp' });
            },
        });

        // オンライン復帰時に自動同期
        if (typeof window !== 'undefined') {
            window.addEventListener('online', () => {
                this.processQueue();
            });
        }
    }

    // リクエストをキューに追加
    async addToQueue(url: string, method: string, data: any) {
        const db = await this.dbPromise;
        await db.add(STORE_NAME, {
            url,
            method,
            data,
            timestamp: Date.now(),
        });
        console.log('Request added to offline queue:', { url, method });
    }

    // キューを処理（再送信）
    async processQueue() {
        if (!navigator.onLine) return;

        const db = await this.dbPromise;
        const requests = await db.getAll(STORE_NAME);

        if (requests.length === 0) return;

        console.log(`Processing ${requests.length} offline requests...`);

        // 依存関係があるかもしれないので、古い順に処理
        const sortedRequests = requests.sort((a, b) => a.timestamp - b.timestamp);

        for (const req of sortedRequests) {
            try {
                console.log(`Replaying: ${req.method} ${req.url}`);

                // 再送信（循環参照を防ぐため、fetchを使用、またはaxiosインスタンスを別途作成）
                const response = await fetch(req.url, {
                    method: req.method,
                    headers: {
                        'Content-Type': 'application/json',
                        // Auth header needed? Assume token is in localStorage or handled by browser cookie if available
                        // For simplified MINI, let's assume auth is separate challenge
                    },
                    body: JSON.stringify(req.data),
                });

                if (response.ok) {
                    await db.delete(STORE_NAME, req.timestamp);
                    console.log('Request replayed successfully');
                } else {
                    console.error('Replay failed:', response.status);
                    // サーバーエラーの場合はキューに残すか、一定回数で破棄するかの制御が必要
                    // ここでは簡易的に500系以外は削除する（400系はロジックエラーなので再送しても無意味）
                    if (response.status < 500) {
                        await db.delete(STORE_NAME, req.timestamp);
                    }
                }
            } catch (error) {
                console.error('Network error during replay, keeping in queue', error);
                return; // ネットワークエラーなら中断
            }
        }
    }
}

export const offlineQueue = new OfflineQueue();
