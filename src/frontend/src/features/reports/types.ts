// src/features/reports/types.ts
// 報告書型定義

export type ReportFormat = 'pdf' | 'excel';
export type ReportType = 'daily' | 'venue' | 'final';

export interface ReportGenerateInput {
  tournamentId: number;
  reportType: ReportType;
  format: ReportFormat;
  matchDate?: string;
  venueId?: number;
}

export interface ReportJob {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  url?: string;
  error?: string;
  createdAt: string;
  completedAt?: string;
}

export interface ReportRecipient {
  id: number;
  tournamentId: number;
  name: string;
  email?: string;
  fax?: string;
  isActive: boolean;
}

export interface SenderSettings {
  senderOrganization: string | null;
  senderName: string | null;
  senderContact: string | null;
}

export interface SenderSettingsUpdate {
  senderOrganization?: string;
  senderName?: string;
  senderContact?: string;
}
