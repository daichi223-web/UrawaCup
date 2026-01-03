// src/features/venues/api.ts
// 会場管理API呼び出し
import { httpClient } from '@/core/http';
import type {
  Venue,
  CreateVenueInput,
  UpdateVenueInput,
  VenueStaff,
  AssignVenueStaffInput,
  VenueSchedule,
} from './types';

export const venueApi = {
  // 会場一覧取得
  getByTournament: async (tournamentId: number): Promise<Venue[]> => {
    const response = await httpClient.get<Venue[]>('/venues', {
      params: { tournamentId },
    });
    return response.data;
  },

  // 会場詳細取得
  getById: async (id: number): Promise<Venue> => {
    const response = await httpClient.get<Venue>(`/venues/${id}`);
    return response.data;
  },

  // 会場作成
  create: async (data: CreateVenueInput): Promise<Venue> => {
    const response = await httpClient.post<Venue>('/venues', data);
    return response.data;
  },

  // 会場更新
  update: async (data: UpdateVenueInput): Promise<Venue> => {
    const { id, ...rest } = data;
    const response = await httpClient.put<Venue>(`/venues/${id}`, rest);
    return response.data;
  },

  // 会場削除
  delete: async (id: number): Promise<void> => {
    await httpClient.delete(`/venues/${id}`);
  },

  // 会場スタッフ一覧
  getStaff: async (venueId: number): Promise<VenueStaff[]> => {
    const response = await httpClient.get<VenueStaff[]>(
      `/venues/${venueId}/staff`
    );
    return response.data;
  },

  // スタッフ割り当て
  assignStaff: async (data: AssignVenueStaffInput): Promise<VenueStaff> => {
    const response = await httpClient.post<VenueStaff>(
      `/venues/${data.venueId}/staff`,
      data
    );
    return response.data;
  },

  // スタッフ削除
  removeStaff: async (venueId: number, userId: number): Promise<void> => {
    await httpClient.delete(`/venues/${venueId}/staff/${userId}`);
  },

  // 会場スケジュール取得
  getSchedule: async (venueId: number, date: string): Promise<VenueSchedule> => {
    const response = await httpClient.get<VenueSchedule>(
      `/venues/${venueId}/schedule`,
      { params: { date } }
    );
    return response.data;
  },

  // グループに会場を紐付け
  assignToGroup: async (
    venueId: number,
    groupId: string
  ): Promise<Venue> => {
    const response = await httpClient.patch<Venue>(
      `/venues/${venueId}/assign-group`,
      { groupId }
    );
    return response.data;
  },
};
