/**
 * 浦和カップ トーナメント管理システム - 共通型定義
 *
 * このファイルはフロントエンド（TypeScript/React）と
 * バックエンド（Python/FastAPI）で共通の型定義を提供します。
 */

// ============================================
// 基本型・列挙型
// ============================================

/** チーム区分: 地元チーム / 招待チーム */
export type TeamType = 'local' | 'invited';

/** グループ名: A, B, C, D の4グループ固定 */
export type GroupName = 'A' | 'B' | 'C' | 'D';

/** 試合ステージ */
export type MatchStage =
  | 'preliminary'    // 予選リーグ（Day1-2）
  | 'semifinal'      // 準決勝（Day3）
  | 'third_place'    // 3位決定戦（Day3）
  | 'final'          // 決勝（Day3）
  | 'training';      // 研修試合（Day3、2〜6位）

/** 試合ステータス */
export type MatchStatus =
  | 'scheduled'      // 予定
  | 'in_progress'    // 試合中
  | 'completed'      // 完了
  | 'cancelled';     // 中止

/** 試合結果 */
export type MatchResult = 'home_win' | 'away_win' | 'draw';

/** 承認ステータス */
export type ApprovalStatus =
  | 'pending'        // 承認待ち
  | 'approved'       // 承認済み
  | 'rejected';      // 却下

/** ユーザー権限 */
export type UserRole =
  | 'admin'          // 管理者（全機能）
  | 'venue_staff'    // 会場担当者（担当会場の入力のみ）
  | 'viewer';        // 閲覧者（閲覧のみ）

// ============================================
// Tournament（大会）
// ============================================

/** 大会情報 */
export interface Tournament {
  id: number;
  /** 大会名 */
  name: string;
  /** 開催回数（第○回） */
  edition: number;
  /** 開催年度 */
  year: number;
  /** 大会略称 */
  shortName?: string;
  /** 開始日 (YYYY-MM-DD) */
  startDate: string;
  /** 終了日 (YYYY-MM-DD) */
  endDate: string;
  /** 試合時間（分）デフォルト: 50 */
  matchDuration: number;
  /** ハーフタイム（分）デフォルト: 25 */
  halfDuration: number;
  /** 試合間インターバル（分）デフォルト: 15 */
  intervalMinutes: number;
  /** 作成日時 */
  createdAt: string;
  /** 更新日時 */
  updatedAt: string;
}

/** 大会作成リクエスト */
export interface TournamentCreate {
  name: string;
  edition?: number;
  year: number;
  startDate: string;
  endDate: string;
  matchDuration?: number;
  halfDuration?: number;
  intervalMinutes?: number;
}

/** 大会更新リクエスト */
export interface TournamentUpdate {
  name?: string;
  shortName?: string;
  edition?: number;
  year?: number;
  startDate?: string;
  endDate?: string;
  matchDuration?: number;
  halfDuration?: number;
  intervalMinutes?: number;
}

// ============================================
// Team（チーム）
// ============================================

/**
 * チーム情報
 *
 * 会場担当校は各グループの1番に固定配置:
 * - A1: 浦和南
 * - B1: 市立浦和
 * - C1: 浦和学院
 * - D1: 武南
 */
export interface Team {
  id: number;
  tournamentId: number;
  /** チーム名 */
  name: string;
  /** チーム略称（報告書用、任意） */
  shortName?: string;
  /** 地元/招待の区分 */
  teamType: TeamType;
  /** 会場担当校フラグ（4校のみtrue） */
  isVenueHost: boolean;
  /** 所属グループ（A, B, C, D） */
  groupId?: string;
  /** グループ内番号（1-6）*/
  groupOrder?: number;
  /** 都道府県 */
  prefecture?: string;
  /** 備考 */
  notes?: string;
  /** 作成日時 */
  createdAt: string;
  /** 更新日時 */
  updatedAt: string;
  // Fallback for snake_case responses (backward compatibility)
  tournament_id?: number;
  short_name?: string;
  team_type?: TeamType;
  is_venue_host?: boolean;
  group_id?: string;
  group_order?: number;
  created_at?: string;
  updated_at?: string;
}

/** チーム作成リクエスト */
export interface TeamCreate {
  tournamentId: number;
  name: string;
  shortName?: string;
  teamType: TeamType;
  isVenueHost?: boolean;
  groupId?: string;
  groupOrder?: number;
  prefecture?: string;
  notes?: string;
}

/** チーム更新リクエスト */
export interface TeamUpdate {
  name?: string;
  shortName?: string;
  teamType?: TeamType;
  isVenueHost?: boolean;
  groupId?: string;
  groupOrder?: number;
  prefecture?: string;
  notes?: string;
}

/** チームCSVインポート形式 */
export interface TeamCsvRow {
  name: string;
  shortName?: string;
  teamType: TeamType;
  isVenueHost: boolean;
  prefecture?: string;
  notes?: string;
}

/** チーム詳細（関連データ含む） */
export interface TeamWithDetails extends Team {
  players: Player[];
  group?: Group;
}

// ============================================
// Player（選手）
// ============================================

/** 選手情報 */
export interface Player {
  id: number;
  teamId: number;
  /** 背番号 */
  number: number;
  /** 選手名 */
  name: string;
  /** 学年（1-3） */
  grade?: number;
  /** 備考 */
  notes?: string;
  /** 作成日時 */
  createdAt: string;
  /** 更新日時 */
  updatedAt: string;
}

/** 選手作成リクエスト */
export interface PlayerCreate {
  teamId: number;
  number: number;
  name: string;
  grade?: number;
  notes?: string;
}

/** 選手更新リクエスト */
export interface PlayerUpdate {
  number?: number;
  name?: string;
  grade?: number;
  notes?: string;
}

/** 選手CSVインポート形式 */
export interface PlayerCsvRow {
  teamName: string;
  number: number;
  name: string;
  grade?: number;
}

/** 選手サジェスト用（得点者入力） */
export interface PlayerSuggestion {
  id: number;
  teamId: number;
  number: number;
  name: string;
  displayText: string;
}

// ============================================
// Group（グループ）
// ============================================

/** グループ情報 */
export interface Group {
  id: string;
  tournamentId: number;
  /** グループ名（表示用） */
  name: string;
  /** 担当会場ID */
  venueId?: number;
  /** 作成日時 */
  createdAt: string;
  /** 更新日時 */
  updatedAt: string;
  // Fallback for snake_case responses (backward compatibility)
  tournament_id?: number;
  venue_id?: number;
  created_at?: string;
  updated_at?: string;
}

/** グループ作成リクエスト */
export interface GroupCreate {
  id: string;
  tournamentId: number;
  name: string;
  venueId?: number;
}

/** グループ詳細（チーム・順位含む） */
export interface GroupWithDetails extends Group {
  teams: Team[];
  standings: Standing[];
  venue?: Venue;
}

// ============================================
// Venue（会場）
// ============================================

/** 会場情報 */
export interface Venue {
  id: number;
  tournamentId: number;
  /** 会場名 */
  name: string;
  /** 住所 */
  address?: string;
  /** 担当グループID */
  groupId?: string;
  /** 1日あたり最大試合数（デフォルト: 6） */
  maxMatchesPerDay: number;
  /** 予選用フラグ */
  forPreliminary: boolean;
  /** 最終日用フラグ */
  forFinalDay: boolean;
  /** 備考 */
  notes?: string;
  /** 作成日時 */
  createdAt: string;
  /** 更新日時 */
  updatedAt: string;
  // Fallback for snake_case responses (backward compatibility)
  tournament_id?: number;
  group_id?: string;
  max_matches_per_day?: number;
  for_preliminary?: boolean;
  for_final_day?: boolean;
  created_at?: string;
  updated_at?: string;
}

/** 会場作成リクエスト */
export interface VenueCreate {
  tournamentId: number;
  name: string;
  address?: string;
  groupId?: string;
  maxMatchesPerDay?: number;
  forPreliminary?: boolean;
  forFinalDay?: boolean;
  notes?: string;
}

/** 会場更新リクエスト */
export interface VenueUpdate {
  name?: string;
  address?: string;
  groupId?: string;
  maxMatchesPerDay?: number;
  forPreliminary?: boolean;
  forFinalDay?: boolean;
  notes?: string;
}

/** 会場の日程情報 */
export interface VenueSchedule {
  venueId: number;
  date: string;
  startTime: string;
  endTime: string;
  matchCount: number;
}

// ============================================
// Match（試合）
// ============================================

/** 試合情報 */
export interface Match {
  id: number;
  tournamentId: number;
  /** グループID（予選リーグの場合） */
  groupId?: string;
  /** 会場ID */
  venueId: number;
  /** ホームチームID */
  homeTeamId: number;
  /** アウェイチームID */
  awayTeamId: number;
  /** 試合日 (YYYY-MM-DD) */
  matchDate: string;
  /** キックオフ予定時刻 (HH:mm) */
  matchTime: string;
  /** 当日の試合順（会場内通し番号） */
  matchOrder: number;
  /** 試合ステージ */
  stage: MatchStage;
  /** 試合ステータス */
  status: MatchStatus;

  // スコア情報
  /** ホームチーム前半得点 */
  homeScoreHalf1?: number;
  /** ホームチーム後半得点 */
  homeScoreHalf2?: number;
  /** ホームチーム合計得点 */
  homeScoreTotal?: number;
  /** アウェイチーム前半得点 */
  awayScoreHalf1?: number;
  /** アウェイチーム後半得点 */
  awayScoreHalf2?: number;
  /** アウェイチーム合計得点 */
  awayScoreTotal?: number;

  // PK戦（3位決定戦・決勝のみ）
  /** ホームチームPK得点 */
  homePK?: number;
  /** アウェイチームPK得点 */
  awayPK?: number;
  /** PK戦実施フラグ */
  hasPenaltyShootout: boolean;

  /** 試合結果 */
  result?: MatchResult;
  /** 編集ロックフラグ */
  isLocked: boolean;
  /** ロックしたユーザーID */
  lockedBy?: number;
  /** ロック日時 */
  lockedAt?: string;
  /** 入力者ID */
  enteredBy?: number;
  /** 入力日時 */
  enteredAt?: string;

  // 承認関連フィールド
  /** 承認ステータス */
  approvalStatus?: ApprovalStatus;
  /** 承認者ID */
  approvedBy?: number;
  /** 承認日時 */
  approvedAt?: string;
  /** 却下理由 */
  rejectionReason?: string;

  /** 備考 */
  notes?: string;
  /** 作成日時 */
  createdAt: string;
  /** 更新日時 */
  updatedAt: string;

  // Fallback for snake_case responses (backward compatibility)
  tournament_id?: number;
  group_id?: string;
  venue_id?: number;
  home_team_id?: number;
  away_team_id?: number;
  match_date?: string;
  match_time?: string;
  match_order?: number;
  home_score_half1?: number;
  home_score_half2?: number;
  home_score_total?: number;
  away_score_half1?: number;
  away_score_half2?: number;
  away_score_total?: number;
  home_pk?: number;
  away_pk?: number;
  has_penalty_shootout?: boolean;
  is_locked?: boolean;
  locked_by?: number;
  locked_at?: string;
  entered_by?: number;
  entered_at?: string;
  approval_status?: ApprovalStatus;
  approved_by?: number;
  approved_at?: string;
  rejection_reason?: string;
  created_at?: string;
  updated_at?: string;
}

/** 試合作成リクエスト */
export interface MatchCreate {
  tournamentId: number;
  groupId?: string;
  venueId: number;
  homeTeamId: number;
  awayTeamId: number;
  matchDate: string;
  matchTime: string;
  matchOrder: number;
  stage: MatchStage;
  status?: MatchStatus;
}

/** 試合結果入力リクエスト */
export interface MatchScoreInput {
  homeScoreHalf1: number;
  homeScoreHalf2: number;
  awayScoreHalf1: number;
  awayScoreHalf2: number;
  homePK?: number;
  awayPK?: number;
  hasPenaltyShootout?: boolean;
  goals: GoalInput[];
}

/** 試合更新リクエスト */
export interface MatchUpdate {
  groupId?: string;
  venueId?: number;
  homeTeamId?: number;
  awayTeamId?: number;
  matchDate?: string;
  matchTime?: string;
  matchOrder?: number;
  stage?: MatchStage;
  status?: MatchStatus;
  homeScoreHalf1?: number;
  homeScoreHalf2?: number;
  awayScoreHalf1?: number;
  awayScoreHalf2?: number;
  homePK?: number;
  awayPK?: number;
  hasPenaltyShootout?: boolean;
  notes?: string;
}

/** 試合詳細（関連データ含む） */
export interface MatchWithDetails extends Match {
  homeTeam: Team;
  awayTeam: Team;
  venue: Venue;
  group?: Group;
  goals: Goal[];
  // Fallback for snake_case responses (backward compatibility)
  home_team?: Team;
  away_team?: Team;
}

/** 試合ロック情報 */
export interface MatchLock {
  matchId: number;
  isLocked: boolean;
  lockedBy?: number;
  lockedByName?: string;
  lockedAt?: string;
}

// ============================================
// MatchApproval（承認フロー）
// ============================================

/** 試合承認リクエスト */
export interface MatchApproveRequest {
  userId: number;
}

/** 試合却下リクエスト */
export interface MatchRejectRequest {
  userId: number;
  reason: string;
}

/** 試合承認レスポンス */
export interface MatchApprovalResponse {
  matchId: number;
  approvalStatus: ApprovalStatus;
  approvedBy?: number;
  approvedByName?: string;
  approvedAt?: string;
  rejectionReason?: string;
  message: string;
}

/** 承認待ち試合一覧レスポンス */
export interface PendingMatchesResponse {
  matches: MatchWithDetails[];
  total: number;
}

// ============================================
// MatchExclusion（対戦除外設定）
// ============================================

/**
 * 対戦除外設定（変則リーグ用）
 *
 * 6チーム変則リーグでは各チーム4試合（2チームとは対戦しない）
 * 対戦しないペアを手動で設定する
 */
export interface ExclusionPair {
  id: number;
  tournamentId: number;
  /** グループID */
  groupId: string;
  /** 除外チーム1のID */
  team1Id: number;
  /** 除外チーム2のID */
  team2Id: number;
  /** 除外理由 */
  reason?: string;
  /** 作成日時 */
  createdAt: string;
}

/** 対戦除外設定リクエスト */
export interface ExclusionPairCreate {
  tournamentId: number;
  groupId: string;
  team1Id: number;
  team2Id: number;
  reason?: string;
}

/** グループの除外設定一覧 */
export interface GroupExclusions {
  groupId: string;
  exclusions: ExclusionPair[];
  /** 各チームの除外数マップ */
  teamExclusionCount: Record<number, number>;
  /** 設定完了フラグ */
  isComplete: boolean;
}

// ============================================
// Goal（得点）
// ============================================

/** 得点情報 */
export interface Goal {
  id: number;
  matchId: number;
  /** 得点チームID */
  teamId: number;
  /** 得点者ID（登録選手の場合） */
  playerId?: number;
  /** 得点者名（自由入力、登録外選手も可） */
  playerName: string;
  /** 得点時間（分） */
  minute: number;
  /** 前半=1, 後半=2 */
  half: 1 | 2;
  /** オウンゴールフラグ */
  isOwnGoal: boolean;
  /** PK得点フラグ */
  isPenalty: boolean;
  /** 備考 */
  notes?: string;
  /** 作成日時 */
  createdAt: string;
  /** 更新日時 */
  updatedAt: string;
}

/** 得点入力フォーム */
export interface GoalInput {
  teamId: number;
  playerId?: number;
  playerName: string;
  minute: number;
  half: 1 | 2;
  isOwnGoal?: boolean;
  isPenalty?: boolean;
  notes?: string;
}

/** 得点作成リクエスト */
export interface GoalCreate {
  matchId: number;
  teamId: number;
  playerId?: number;
  playerName: string;
  minute: number;
  half: 1 | 2;
  isOwnGoal?: boolean;
  isPenalty?: boolean;
  notes?: string;
}

/** 得点更新リクエスト */
export interface GoalUpdate {
  teamId?: number;
  playerId?: number;
  playerName?: string;
  minute?: number;
  half?: 1 | 2;
  isOwnGoal?: boolean;
  isPenalty?: boolean;
  notes?: string;
}

/** 得点詳細（報告書用） */
export interface GoalDetail extends Goal {
  teamName: string;
  isHome: boolean;
}

// ============================================
// Standing（順位表）
// ============================================

/**
 * 順位情報
 *
 * 順位決定ルール（優先順位）:
 * 1. 勝点（勝利=3点、引分=1点、敗北=0点）
 * 2. 得失点差
 * 3. 総得点
 * 4. 当該チーム間の対戦成績
 * 5. 抽選
 */
export interface Standing {
  id: number;
  tournamentId: number;
  groupId: string;
  teamId: number;
  /** 順位 */
  rank: number;
  /** 試合数 */
  played: number;
  /** 勝利数 */
  won: number;
  /** 引分数 */
  drawn: number;
  /** 敗北数 */
  lost: number;
  /** 総得点 */
  goalsFor: number;
  /** 総失点 */
  goalsAgainst: number;
  /** 得失点差 */
  goalDifference: number;
  /** 勝点 */
  points: number;
  /** 順位決定理由（同勝点時に記録） */
  rankReason?: string;
  /** 最終更新日時 */
  updatedAt: string;
}

/** 順位表（チーム情報付き） */
export interface StandingWithTeam extends Standing {
  team: Team;
}

/** グループ順位表 */
export interface GroupStanding {
  group: Group;
  standings: StandingWithTeam[];
}

/** 直接対決成績（同勝点時の順位決定用）- API returns snake_case, but frontend uses camelCase */
export interface HeadToHead {
  team1Id: number;
  team2Id: number;
  team1Wins: number;
  team2Wins: number;
  draws: number;
  team1Goals: number;
  team2Goals: number;
}

// ============================================
// User（ユーザー認証）
// ============================================

/** ユーザー情報 */
export interface User {
  id: number;
  /** ユーザー名（ログイン用） */
  username: string;
  /** 表示名 */
  displayName: string;
  /** メールアドレス */
  email?: string;
  /** 権限 */
  role: UserRole;
  /** 担当会場ID（venue_staffの場合） */
  venueId?: number;
  /** 有効フラグ */
  isActive: boolean;
  /** 作成日時 */
  createdAt: string;
  /** 更新日時 */
  updatedAt: string;
}

/** ユーザー作成リクエスト */
export interface UserCreate {
  username: string;
  password: string;
  displayName: string;
  email?: string;
  role: UserRole;
  venueId?: number;
}

/** ログインリクエスト */
export interface LoginRequest {
  username: string;
  password: string;
}

/** ログインレスポンス */
export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  user: User;
}

/** 認証済みユーザー情報 */
export interface AuthUser {
  id: number;
  username: string;
  displayName: string;
  role: UserRole;
  venueId?: number;
}

// ============================================
// ReportRecipient（報告書送信先）
// ============================================

/** 報告書送信先 */
export interface ReportRecipient {
  id: number;
  tournamentId: number;
  /** 送信先名 */
  name: string;
  /** メールアドレス */
  email?: string;
  /** FAX番号 */
  fax?: string;
  /** 備考 */
  notes?: string;
  /** 作成日時 */
  createdAt: string;
}

/** 報告書送信先作成リクエスト */
export interface ReportRecipientCreate {
  tournamentId: number;
  name: string;
  email?: string;
  fax?: string;
  notes?: string;
}

// ============================================
// Report（報告書）
// ============================================

/** 報告書出力パラメータ */
export interface ReportParams {
  tournamentId: number;
  /** 日付（指定日の報告書を生成） */
  date: string;
  /** 会場ID（指定しない場合は全会場） */
  venueId?: number;
  /** 出力形式 */
  format: 'pdf' | 'excel';
}

/** 報告書データ */
export interface ReportData {
  tournament: Tournament;
  date: string;
  venue?: Venue;
  matches: MatchWithDetails[];
  recipients: ReportRecipient[];
  generatedAt: string;
  generatedBy: string;
}

/** 試合報告書（1試合分） */
export interface MatchReport {
  matchNumber: number;
  kickoffTime: string;
  homeTeamName: string;
  awayTeamName: string;
  scoreHalf1: string;
  scoreHalf2: string;
  scoreTotal: string;
  scorePK?: string;
  goals: GoalReport[];
}

/** 得点報告（報告書用） */
export interface GoalReport {
  minute: number;
  half: 1 | 2;
  teamName: string;
  playerName: string;
  displayText: string;
}

// ============================================
// Schedule（日程生成）
// ============================================

/** 日程生成パラメータ */
export interface ScheduleGenerationParams {
  tournamentId: number;
  groupId: string;
  /** 開始日 (YYYY-MM-DD) */
  startDate: string;
  /** 開始時刻 (HH:mm) */
  startTime: string;
  /** 試合時間（分）デフォルト: 50 */
  matchDuration?: number;
  /** インターバル（分）デフォルト: 15 */
  intervalMinutes?: number;
  /** 1日あたり試合数 デフォルト: 6 */
  matchesPerDay?: number;
}

/** 生成された日程 */
export interface GeneratedSchedule {
  groupId: string;
  matches: ScheduleMatch[];
  totalMatches: number;
  daysRequired: number;
}

/** 日程上の試合（生成結果） */
export interface ScheduleMatch {
  matchOrder: number;
  day: number;
  date: string;
  time: string;
  homeTeamId: number;
  homeTeamName: string;
  awayTeamId: number;
  awayTeamName: string;
}

// ============================================
// FinalTournament（決勝トーナメント）
// ============================================

/** 決勝トーナメント組み合わせ */
export interface FinalTournamentBracket {
  /** 準決勝1: A1位 vs B1位 */
  semifinal1: TournamentMatch;
  /** 準決勝2: C1位 vs D1位 */
  semifinal2: TournamentMatch;
  /** 3位決定戦 */
  thirdPlace: TournamentMatch;
  /** 決勝 */
  final: TournamentMatch;
}

/** トーナメント戦の対戦 */
export interface TournamentMatch {
  matchId?: number;
  team1Id?: number;
  team1Name?: string;
  team1Source?: string;
  team2Id?: number;
  team2Name?: string;
  team2Source?: string;
  winnerId?: number;
  loserId?: number;
}

/** 研修試合組み合わせ */
export interface TrainingMatchProposal {
  groupRank: number;
  matches: TrainingMatchPair[];
}

/** 研修試合ペア */
export interface TrainingMatchPair {
  team1Id: number;
  team1Name: string;
  team1Group: string;
  team2Id: number;
  team2Name: string;
  team2Group: string;
  /** 予選で対戦済みの場合はtrue（警告表示用） */
  hasPlayedInPreliminary: boolean;
}

// ============================================
// API共通
// ============================================

/** API成功レスポンス */
export interface ApiResponse<T> {
  success: true;
  data: T;
  message?: string;
}

/** APIエラーレスポンス */
export interface ApiErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}

/** ページネーションリクエスト */
export interface PaginationParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

/** ページネーション付きレスポンス */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// ============================================
// WebSocket イベント
// ============================================

/** WebSocketイベント種別 */
export type WebSocketEventType =
  | 'match_started'
  | 'match_updated'
  | 'match_completed'
  | 'goal_added'
  | 'goal_removed'
  | 'goal_updated'
  | 'standing_updated'
  | 'match_locked'
  | 'match_unlocked';

/** WebSocketイベント */
export interface WebSocketEvent<T = unknown> {
  type: WebSocketEventType;
  payload: T;
  timestamp: string;
}

/** 試合更新イベント */
export interface MatchUpdatedEvent {
  matchId: number;
  match: Match;
}

/** 得点追加イベント */
export interface GoalAddedEvent {
  matchId: number;
  goal: Goal;
}

/** 順位更新イベント */
export interface StandingUpdatedEvent {
  groupId: string;
  standings: Standing[];
}

/** 試合ロックイベント */
export interface MatchLockedEvent {
  matchId: number;
  lockedBy: number;
  lockedByName: string;
}

// ============================================
// Dashboard（ダッシュボード）
// ============================================

/** ダッシュボードサマリー */
export interface DashboardSummary {
  tournament: Tournament;
  /** 進行状況 */
  progress: {
    totalMatches: number;
    completedMatches: number;
    inProgressMatches: number;
    scheduledMatches: number;
    progressPercent: number;
  };
  /** 日別・会場別試合数 */
  matchesByVenueAndDate: VenueDateMatchCount[];
  /** グループ別順位 */
  groupStandings: GroupStanding[];
  /** 最近の試合結果 */
  recentMatches: MatchWithDetails[];
  /** 本日の試合予定 */
  todayMatches: MatchWithDetails[];
}

/** 会場・日付別試合数 */
export interface VenueDateMatchCount {
  venueId: number;
  venueName: string;
  date: string;
  totalMatches: number;
  completedMatches: number;
}

// ============================================
// オフライン対応
// ============================================

/** オフライン時の保留操作 */
export interface PendingOperation {
  id: string;
  type: 'create' | 'update' | 'delete';
  entity: 'match' | 'goal';
  data: unknown;
  timestamp: string;
  syncStatus: 'pending' | 'syncing' | 'synced' | 'failed';
  retryCount: number;
}

/** 同期ステータス */
export interface SyncStatus {
  lastSyncAt?: string;
  pendingOperations: number;
  isOnline: boolean;
  isSyncing: boolean;
}
