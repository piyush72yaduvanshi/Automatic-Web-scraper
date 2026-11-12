/**
 * CRM API Service - Call Logs, Notes, Emails
 */

import api from './api';
import type { CallLogItem, NoteItem, EmailItem } from '../types';

// ========== Call Logs ==========

export interface CallLogCreateData {
  contact_id?: string;
  company_id?: string;
  deal_id?: string;
  direction: 'INBOUND' | 'OUTBOUND';
  duration_seconds?: number;
  phone_number?: string;
  outcome?: string;
  notes?: string;
  call_started_at?: string;
  created_by?: string;
}

export interface CallLogUpdateData {
  outcome?: string;
  notes?: string;
  transcript?: string;
  recording_url?: string;
  duration_seconds?: number;
}

export interface CallLogFilters {
  company_id?: string;
  contact_id?: string;
  deal_id?: string;
  direction?: 'INBOUND' | 'OUTBOUND';
  outcome?: string;
  skip?: number;
  limit?: number;
}

export const fetchCallLogs = async (filters?: CallLogFilters): Promise<CallLogItem[]> => {
  const params = new URLSearchParams();
  if (filters?.company_id) params.append('company_id', filters.company_id);
  if (filters?.contact_id) params.append('contact_id', filters.contact_id);
  if (filters?.deal_id) params.append('deal_id', filters.deal_id);
  if (filters?.direction) params.append('direction', filters.direction);
  if (filters?.outcome) params.append('outcome', filters.outcome);
  if (filters?.skip !== undefined) params.append('skip', filters.skip.toString());
  if (filters?.limit !== undefined) params.append('limit', filters.limit.toString());

  const response = await api.get(`/crm/call-logs?${params.toString()}`);
  return response.data;
};

export const createCallLog = async (data: CallLogCreateData): Promise<{ id: string; status: string }> => {
  const response = await api.post('/crm/call-logs', data);
  return response.data;
};

export const getCallLog = async (id: string): Promise<CallLogItem> => {
  const response = await api.get(`/crm/call-logs/${id}`);
  return response.data;
};

export const updateCallLog = async (id: string, data: CallLogUpdateData): Promise<{ id: string; status: string }> => {
  const response = await api.patch(`/crm/call-logs/${id}`, data);
  return response.data;
};

// ========== Notes ==========

export interface NoteCreateData {
  content: string;
  company_id?: string;
  contact_id?: string;
  deal_id?: string;
  lead_id?: string;
  is_pinned?: boolean;
  created_by?: string;
}

export interface NoteUpdateData {
  content?: string;
  is_pinned?: boolean;
}

export interface NoteFilters {
  company_id?: string;
  contact_id?: string;
  deal_id?: string;
  lead_id?: string;
  is_pinned?: boolean;
  skip?: number;
  limit?: number;
}

export const fetchNotes = async (filters?: NoteFilters): Promise<NoteItem[]> => {
  const params = new URLSearchParams();
  if (filters?.company_id) params.append('company_id', filters.company_id);
  if (filters?.contact_id) params.append('contact_id', filters.contact_id);
  if (filters?.deal_id) params.append('deal_id', filters.deal_id);
  if (filters?.lead_id) params.append('lead_id', filters.lead_id);
  if (filters?.is_pinned !== undefined) params.append('is_pinned', filters.is_pinned.toString());
  if (filters?.skip !== undefined) params.append('skip', filters.skip.toString());
  if (filters?.limit !== undefined) params.append('limit', filters.limit.toString());

  const response = await api.get(`/crm/notes?${params.toString()}`);
  return response.data;
};

export const createNote = async (data: NoteCreateData): Promise<{ id: string; status: string }> => {
  const response = await api.post('/crm/notes', data);
  return response.data;
};

export const getNote = async (id: string): Promise<NoteItem> => {
  const response = await api.get(`/crm/notes/${id}`);
  return response.data;
};

export const updateNote = async (id: string, data: NoteUpdateData): Promise<{ id: string; status: string }> => {
  const response = await api.patch(`/crm/notes/${id}`, data);
  return response.data;
};

export const deleteNote = async (id: string): Promise<{ id: string; status: string }> => {
  const response = await api.delete(`/crm/notes/${id}`);
  return response.data;
};

// ========== Emails ==========

export interface EmailCreateData {
  contact_id?: string;
  company_id?: string;
  deal_id?: string;
  subject?: string;
  body_text?: string;
  body_html?: string;
  direction: 'INBOUND' | 'OUTBOUND';
  status?: string;
}

export interface EmailUpdateData {
  status?: string;
  opened_at?: string;
  clicked_at?: string;
  replied_at?: string;
  sent_at?: string;
}

export interface EmailFilters {
  company_id?: string;
  contact_id?: string;
  deal_id?: string;
  direction?: 'INBOUND' | 'OUTBOUND';
  status?: string;
  skip?: number;
  limit?: number;
}

export const fetchEmails = async (filters?: EmailFilters): Promise<EmailItem[]> => {
  const params = new URLSearchParams();
  if (filters?.company_id) params.append('company_id', filters.company_id);
  if (filters?.contact_id) params.append('contact_id', filters.contact_id);
  if (filters?.deal_id) params.append('deal_id', filters.deal_id);
  if (filters?.direction) params.append('direction', filters.direction);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.skip !== undefined) params.append('skip', filters.skip.toString());
  if (filters?.limit !== undefined) params.append('limit', filters.limit.toString());

  const response = await api.get(`/crm/emails?${params.toString()}`);
  return response.data;
};

export const createEmail = async (data: EmailCreateData): Promise<{ id: string; status: string }> => {
  const response = await api.post('/crm/emails', data);
  return response.data;
};

export const getEmail = async (id: string): Promise<EmailItem> => {
  const response = await api.get(`/crm/emails/${id}`);
  return response.data;
};

export const updateEmailTracking = async (id: string, data: EmailUpdateData): Promise<{ id: string; status: string }> => {
  const response = await api.patch(`/crm/emails/${id}`, data);
  return response.data;
};
