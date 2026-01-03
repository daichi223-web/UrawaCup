/**
 * 浦和カップ トーナメント管理システム - フロントエンド型定義
 *
 * 共有型定義を再エクスポート + フロントエンド固有の型を定義
 */

// 共有型定義をすべて再エクスポート
export * from '@shared/types';

// ============================================
// フロントエンド固有の型定義
// ============================================

/**
 * フォームの状態
 */
export type FormStatus = 'idle' | 'submitting' | 'success' | 'error';

/**
 * フォームのコンテキスト
 */
export interface FormContext<T> {
  data: T;
  errors: Record<string, string>;
  status: FormStatus;
  isDirty: boolean;
}

/**
 * ナビゲーション項目
 */
export interface NavItem {
  path: string;
  label: string;
  icon?: string;
  badge?: number;
  children?: NavItem[];
}

/**
 * トースト通知の種類
 */
export type ToastType = 'success' | 'error' | 'info' | 'warning';

/**
 * トースト通知
 */
export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

/**
 * モーダルの状態
 */
export interface ModalState {
  isOpen: boolean;
  title?: string;
  content?: React.ReactNode;
  onConfirm?: () => void;
  onCancel?: () => void;
}

/**
 * フィルター条件
 */
export interface FilterParams {
  search?: string;
  groupId?: string;
  venueId?: number;
  stage?: string;
  status?: string;
  date?: string;
}

/**
 * ソート設定
 */
export interface SortParams {
  field: string;
  direction: 'asc' | 'desc';
}

/**
 * テーブル表示設定
 */
export interface TableConfig {
  pageSize: number;
  currentPage: number;
  filters: FilterParams;
  sort?: SortParams;
}

/**
 * ドラッグ&ドロップのアイテム
 */
export interface DragItem {
  id: string | number;
  type: string;
  data: unknown;
}

/**
 * ドラッグ&ドロップ結果
 */
export interface DropResult {
  source: {
    droppableId: string;
    index: number;
  };
  destination?: {
    droppableId: string;
    index: number;
  };
  draggableId: string;
}

/**
 * 入力フィールドのベースProps
 */
export interface BaseInputProps {
  name: string;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  error?: string;
  helperText?: string;
}

/**
 * セレクトオプション
 */
export interface SelectOption {
  value: string | number;
  label: string;
  disabled?: boolean;
}

/**
 * 日程表示用の試合情報
 */
export interface ScheduleDisplayMatch {
  id: number;
  time: string;
  homeTeam: string;
  awayTeam: string;
  score?: string;
  status: string;
  venue: string;
}

/**
 * グループ表示用のデータ
 */
export interface GroupDisplayData {
  groupId: string;
  groupName: string;
  teams: {
    id: number;
    name: string;
    rank: number;
    played: number;
    won: number;
    drawn: number;
    lost: number;
    goalsFor: number;
    goalsAgainst: number;
    goalDifference: number;
    points: number;
  }[];
}

/**
 * 得点入力フォームの状態
 */
export interface GoalFormState {
  teamId: number | null;
  playerName: string;
  playerId?: number;
  minute: number;
  half: 1 | 2;
  isOwnGoal: boolean;
  isPenalty: boolean;
}

/**
 * 試合結果入力フォームの状態
 */
export interface MatchResultFormState {
  homeScoreHalf1: number;
  homeScoreHalf2: number;
  awayScoreHalf1: number;
  awayScoreHalf2: number;
  homePK?: number;
  awayPK?: number;
  hasPenaltyShootout: boolean;
  goals: GoalFormState[];
}

/**
 * 報告書プレビューの設定
 */
export interface ReportPreviewConfig {
  showHeader: boolean;
  showFooter: boolean;
  showGoalDetails: boolean;
  showRecipients: boolean;
}

/**
 * オフラインキューのアイテム
 */
export interface OfflineQueueItem {
  id: string;
  operation: 'create' | 'update' | 'delete';
  endpoint: string;
  data: unknown;
  createdAt: string;
  retryCount: number;
}

/**
 * アプリケーションの状態
 */
export interface AppState {
  isOnline: boolean;
  isSyncing: boolean;
  pendingOperations: number;
  lastSyncAt?: string;
  currentTournament?: number;
  currentUser?: {
    id: number;
    username: string;
    displayName: string;
    role: string;
  };
}
