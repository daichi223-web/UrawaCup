// src/features/staff/types.ts
// スタッフ型定義

export interface Staff {
  id: number;
  teamId: number;
  name: string;
  nameKana: string | null;
  role: string;
  phone: string | null;
  email: string | null;
  isPrimary: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateStaffInput {
  teamId: number;
  name: string;
  nameKana?: string;
  role: string;
  phone?: string;
  email?: string;
  isPrimary?: boolean;
}

export interface UpdateStaffInput {
  name?: string;
  nameKana?: string;
  role?: string;
  phone?: string;
  email?: string;
  isPrimary?: boolean;
}

export type StaffRole = '監督' | 'コーチ' | 'マネージャー' | 'トレーナー' | '帯同審判';

export const STAFF_ROLES: StaffRole[] = ['監督', 'コーチ', 'マネージャー', 'トレーナー', '帯同審判'];
