// src/features/teams/index.ts
export { teamApi } from './api';
export {
  useTeams,
  useTeamsByGroup,
  useTeam,
  useCreateTeam,
  useUpdateTeam,
  useDeleteTeam,
  useImportTeamsCsv,
} from './hooks';
export type { Team, CreateTeamInput, UpdateTeamInput, TeamWithPlayers, TeamType } from './types';
