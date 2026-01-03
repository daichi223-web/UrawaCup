// src/features/matches/index.ts
export { matchApi } from './api';
export {
  useMatches,
  useMatch,
  useCreateMatch,
  useUpdateMatchScore,
  useDeleteMatch,
  useGenerateMatchSchedule,
  useGenerateTrainingMatches,
  useGenerateFinals,
  useApproveMatch,
  useRejectMatch,
  usePendingApprovalMatches,
  useLockMatch,
  useUnlockMatch,
} from './hooks';
export type {
  Match,
  Goal,
  MatchScoreInput,
  CreateMatchInput,
  MatchGenerateScheduleInput,
  MatchStage,
  MatchStatus,
  ApprovalStatus,
  MatchLock,
} from './types';
