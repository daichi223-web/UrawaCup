// src/core/config/index.ts
// 環境設定

export const config = {
  // API設定
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 10000,
  },

  // 大会固定情報
  tournament: {
    name: 'さいたま市招待高校サッカーフェスティバル浦和カップ',
    teamsCount: 24,
    groups: ['A', 'B', 'C', 'D'] as const,
    teamsPerGroup: 6,
    matchDuration: 50,
    halfDuration: 25,
    interval: 15,
    matchesPerDay: 6,
    days: 3,
  },

  // 会場担当校
  venueHosts: {
    A: '浦和南',
    B: '市立浦和',
    C: '浦和学院',
    D: '武南',
  } as const,

  // 順位決定ルール
  standingRules: [
    '勝点（勝利=3点、引分=1点、敗北=0点）',
    '得失点差',
    '総得点',
    '当該チーム間の対戦成績',
    '抽選',
  ],
} as const;

export type GroupName = (typeof config.tournament.groups)[number];
