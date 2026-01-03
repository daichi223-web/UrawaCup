// src/features/staff/api.ts
// スタッフAPI呼び出し
import { httpClient } from '@/core/http';
import type { Staff, CreateStaffInput, UpdateStaffInput } from './types';

interface StaffListResponse {
  staff: Staff[];
  total: number;
}

export const staffApi = {
  // チームのスタッフ一覧
  getByTeam: async (teamId: number): Promise<Staff[]> => {
    const response = await httpClient.get<StaffListResponse>(`/staff/team/${teamId}`);
    return response.data.staff;
  },

  // スタッフ一覧（フィルタ付き）
  getList: async (params?: {
    teamId?: number;
    tournamentId?: number;
    role?: string;
  }): Promise<Staff[]> => {
    const response = await httpClient.get<StaffListResponse>('/staff', { params });
    return response.data.staff;
  },

  // 単一スタッフ取得
  getById: async (id: number): Promise<Staff> => {
    const response = await httpClient.get<Staff>(`/staff/${id}`);
    return response.data;
  },

  // スタッフ作成
  create: async (data: CreateStaffInput): Promise<Staff> => {
    const response = await httpClient.post<Staff>('/staff', data);
    return response.data;
  },

  // スタッフ更新
  update: async (id: number, data: UpdateStaffInput): Promise<Staff> => {
    const response = await httpClient.put<Staff>(`/staff/${id}`, data);
    return response.data;
  },

  // スタッフ削除
  delete: async (id: number): Promise<void> => {
    await httpClient.delete(`/staff/${id}`);
  },
};
