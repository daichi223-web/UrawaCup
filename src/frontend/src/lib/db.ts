/**
 * 浦和カップ トーナメント管理システム - IndexedDB設定
 *
 * Dexie.jsを使用してオフラインデータ管理を実現
 * - 試合データのローカルキャッシュ
 * - オフライン時の入力保持
 * - オンライン復帰時の同期キュー
 */

import Dexie, { type Table } from 'dexie';
import type {
  Match,
  Team,
  Goal,
  Standing,
  Venue,
  Tournament,
  Player,
} from '@/types';

// ============================================
// オフライン専用の型定義
// ============================================

/**
 * 同期キューアイテム
 * オフライン時の操作を保存し、オンライン復帰時に同期
 */
export interface SyncQueueItem {
  id?: number;
  /** 操作種別 */
  operation: 'create' | 'update' | 'delete';
  /** エンティティ種別 */
  entityType: 'match' | 'goal' | 'team' | 'player' | 'standing';
  /** エンティティID（更新・削除の場合） */
  entityId?: number;
  /** リクエストデータ */
  payload: unknown;
  /** APIエンドポイント */
  endpoint: string;
  /** HTTPメソッド */
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  /** 作成日時 */
  createdAt: Date;
  /** リトライ回数 */
  retryCount: number;
  /** 最後のエラーメッセージ */
  lastError?: string;
  /** 同期ステータス */
  status: 'pending' | 'syncing' | 'failed' | 'synced';
}

/**
 * キャッシュメタデータ
 * APIレスポンスのキャッシュ情報を管理
 */
export interface CacheMetadata {
  key: string;
  /** キャッシュ日時 */
  cachedAt: Date;
  /** 有効期限 */
  expiresAt: Date;
  /** ETagまたはLast-Modified */
  etag?: string;
}

/**
 * 競合データ
 * サーバーとローカルのデータが異なる場合に保存
 */
export interface ConflictItem {
  id?: number;
  /** エンティティ種別 */
  entityType: 'match' | 'goal';
  /** エンティティID */
  entityId: number;
  /** ローカルデータ */
  localData: unknown;
  /** サーバーデータ */
  serverData: unknown;
  /** ローカル更新日時 */
  localUpdatedAt: Date;
  /** サーバー更新日時 */
  serverUpdatedAt: Date;
  /** 競合検出日時 */
  detectedAt: Date;
  /** 解決ステータス */
  status: 'pending' | 'resolved_local' | 'resolved_server' | 'resolved_merged';
}

// ============================================
// Dexieデータベース定義
// ============================================

/**
 * 浦和カップ IndexedDBデータベース
 */
export class UrawaCupDatabase extends Dexie {
  // テーブル定義
  tournaments!: Table<Tournament & { _localUpdatedAt?: Date }, number>;
  teams!: Table<Team & { _localUpdatedAt?: Date }, number>;
  players!: Table<Player & { _localUpdatedAt?: Date }, number>;
  venues!: Table<Venue & { _localUpdatedAt?: Date }, number>;
  matches!: Table<Match & { _localUpdatedAt?: Date }, number>;
  goals!: Table<Goal & { _localUpdatedAt?: Date }, number>;
  standings!: Table<Standing & { _localUpdatedAt?: Date }, number>;

  // 同期関連テーブル
  syncQueue!: Table<SyncQueueItem, number>;
  cacheMetadata!: Table<CacheMetadata, string>;
  conflicts!: Table<ConflictItem, number>;

  constructor() {
    super('UrawaCupDB');

    // バージョン1: 初期スキーマ
    this.version(1).stores({
      // 大会データ
      tournaments: '++id, year, startDate',
      // チームデータ
      teams: '++id, tournament_id, group_id, name, team_type',
      // 選手データ
      players: '++id, teamId, number, name',
      // 会場データ
      venues: '++id, tournament_id, group_id, name',
      // 試合データ（最も頻繁にアクセス）
      matches: '++id, tournament_id, group_id, venue_id, home_team_id, away_team_id, match_date, status, stage',
      // 得点データ
      goals: '++id, matchId, teamId, playerId, minute',
      // 順位データ
      standings: '++id, tournament_id, group_id, team_id, rank',

      // 同期キュー
      syncQueue: '++id, entityType, entityId, status, createdAt',
      // キャッシュメタデータ
      cacheMetadata: 'key, cachedAt, expiresAt',
      // 競合データ
      conflicts: '++id, entityType, entityId, status, detectedAt',
    });
  }
}

// データベースインスタンス（シングルトン）
export const db = new UrawaCupDatabase();

// ============================================
// ユーティリティ関数
// ============================================

/**
 * 同期キューにアイテムを追加
 */
export async function addToSyncQueue(item: Omit<SyncQueueItem, 'id' | 'createdAt' | 'retryCount' | 'status'>): Promise<number> {
  return await db.syncQueue.add({
    ...item,
    createdAt: new Date(),
    retryCount: 0,
    status: 'pending',
  });
}

/**
 * 保留中の同期アイテムを取得
 */
export async function getPendingSyncItems(): Promise<SyncQueueItem[]> {
  return await db.syncQueue
    .where('status')
    .anyOf(['pending', 'failed'])
    .filter((item) => item.retryCount < 5) // 最大5回リトライ
    .toArray();
}

/**
 * 同期アイテムのステータスを更新
 */
export async function updateSyncItemStatus(
  id: number,
  status: SyncQueueItem['status'],
  error?: string
): Promise<void> {
  await db.syncQueue.update(id, {
    status,
    lastError: error,
    retryCount: status === 'failed' ? (await db.syncQueue.get(id))!.retryCount + 1 : undefined,
  });
}

/**
 * 同期済みアイテムを削除
 */
export async function clearSyncedItems(): Promise<number> {
  return await db.syncQueue.where('status').equals('synced').delete();
}

/**
 * 競合を追加
 */
export async function addConflict(conflict: Omit<ConflictItem, 'id' | 'detectedAt' | 'status'>): Promise<number> {
  return await db.conflicts.add({
    ...conflict,
    detectedAt: new Date(),
    status: 'pending',
  });
}

/**
 * 未解決の競合を取得
 */
export async function getPendingConflicts(): Promise<ConflictItem[]> {
  return await db.conflicts.where('status').equals('pending').toArray();
}

/**
 * 競合を解決
 */
export async function resolveConflict(
  id: number,
  resolution: 'resolved_local' | 'resolved_server' | 'resolved_merged'
): Promise<void> {
  await db.conflicts.update(id, { status: resolution });
}

/**
 * キャッシュが有効かどうかを確認
 */
export async function isCacheValid(key: string): Promise<boolean> {
  const metadata = await db.cacheMetadata.get(key);
  if (!metadata) return false;
  return new Date() < metadata.expiresAt;
}

/**
 * キャッシュメタデータを更新
 */
export async function updateCacheMetadata(
  key: string,
  ttlSeconds: number = 300, // デフォルト5分
  etag?: string
): Promise<void> {
  const now = new Date();
  await db.cacheMetadata.put({
    key,
    cachedAt: now,
    expiresAt: new Date(now.getTime() + ttlSeconds * 1000),
    etag,
  });
}

/**
 * 期限切れのキャッシュをクリア
 */
export async function clearExpiredCache(): Promise<void> {
  const now = new Date();
  const expiredKeys = await db.cacheMetadata
    .where('expiresAt')
    .below(now)
    .toArray();

  await Promise.all(
    expiredKeys.map((item) => db.cacheMetadata.delete(item.key))
  );
}

/**
 * データベースをクリア（デバッグ用）
 */
export async function clearDatabase(): Promise<void> {
  await Promise.all([
    db.tournaments.clear(),
    db.teams.clear(),
    db.players.clear(),
    db.venues.clear(),
    db.matches.clear(),
    db.goals.clear(),
    db.standings.clear(),
    db.syncQueue.clear(),
    db.cacheMetadata.clear(),
    db.conflicts.clear(),
  ]);
}

/**
 * 保留中の操作数を取得
 */
export async function getPendingOperationsCount(): Promise<number> {
  return await db.syncQueue
    .where('status')
    .anyOf(['pending', 'syncing'])
    .count();
}

/**
 * 競合数を取得
 */
export async function getPendingConflictsCount(): Promise<number> {
  return await db.conflicts.where('status').equals('pending').count();
}

export default db;
