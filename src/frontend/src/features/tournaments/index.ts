// src/features/tournaments/index.ts
export { tournamentApi } from './api';
export {
  useTournaments,
  useTournament,
  useTournamentGroups,
  useTournamentSettings,
  useCreateTournament,
  useUpdateTournament,
  useDeleteTournament,
  useUpdateTournamentSettings,
  useGenerateSchedule,
  useGenerateFinalSchedule,
  useChangeTournamentStatus,
} from './hooks';
export type {
  Tournament,
  TournamentStatus,
  CreateTournamentInput,
  UpdateTournamentInput,
  TournamentGroup,
  TournamentSettings,
  TiebreakerRule,
  GenerateScheduleInput,
  GenerateFinalScheduleInput,
} from './types';
