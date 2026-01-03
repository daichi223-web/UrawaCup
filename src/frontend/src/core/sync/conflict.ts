// src/core/sync/conflict.ts
// 競合解決ロジック
import type { ConflictData } from './types';

export type ConflictResolution = 'local' | 'server' | 'merge';

export interface MergeResult {
  merged: Record<string, unknown>;
  conflicts: string[]; // マージできなかったフィールド
}

/**
 * 自動マージを試みる
 * 両方で変更されたフィールドがなければマージ可能
 */
export function tryAutoMerge(conflict: ConflictData): MergeResult | null {
  const { localData, serverData } = conflict;
  const merged: Record<string, unknown> = { ...serverData };
  const unresolvedConflicts: string[] = [];

  // ローカルの変更を適用
  for (const [key, localValue] of Object.entries(localData)) {
    const serverValue = serverData[key];

    // サーバーと同じ値ならスキップ
    if (JSON.stringify(localValue) === JSON.stringify(serverValue)) {
      continue;
    }

    // 元データがない場合（新規フィールド）
    if (serverValue === undefined) {
      merged[key] = localValue;
      continue;
    }

    // 両方で異なる値に変更された場合は競合
    unresolvedConflicts.push(key);
  }

  if (unresolvedConflicts.length > 0) {
    return {
      merged,
      conflicts: unresolvedConflicts,
    };
  }

  return {
    merged,
    conflicts: [],
  };
}

/**
 * 競合データを比較用に整形
 */
export function formatConflictForDisplay(conflict: ConflictData): {
  field: string;
  local: unknown;
  server: unknown;
}[] {
  const differences: { field: string; local: unknown; server: unknown }[] = [];

  const allKeys = new Set([
    ...Object.keys(conflict.localData),
    ...Object.keys(conflict.serverData),
  ]);

  for (const key of allKeys) {
    const localValue = conflict.localData[key];
    const serverValue = conflict.serverData[key];

    if (JSON.stringify(localValue) !== JSON.stringify(serverValue)) {
      differences.push({
        field: key,
        local: localValue,
        server: serverValue,
      });
    }
  }

  return differences;
}

/**
 * 特定のフィールドについてどちらの値を採用するか選択してマージ
 */
export function mergeWithSelections(
  conflict: ConflictData,
  selections: Record<string, ConflictResolution>
): Record<string, unknown> {
  const merged: Record<string, unknown> = {};

  const allKeys = new Set([
    ...Object.keys(conflict.localData),
    ...Object.keys(conflict.serverData),
  ]);

  for (const key of allKeys) {
    const selection = selections[key] || 'server'; // デフォルトはサーバー優先

    switch (selection) {
      case 'local':
        merged[key] = conflict.localData[key];
        break;
      case 'server':
        merged[key] = conflict.serverData[key];
        break;
      case 'merge':
        // 配列の場合はマージ、それ以外はサーバー優先
        if (Array.isArray(conflict.localData[key]) && Array.isArray(conflict.serverData[key])) {
          merged[key] = [
            ...new Set([
              ...conflict.serverData[key] as unknown[],
              ...conflict.localData[key] as unknown[],
            ]),
          ];
        } else {
          merged[key] = conflict.serverData[key];
        }
        break;
    }
  }

  return merged;
}
