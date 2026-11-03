import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { BusinessLead, LeadDetail, PaginatedResponse } from '../types';

interface UseLeadsParams {
  page?: number;
  page_size?: number;
  search?: string;
  category?: string;
  city?: string;
  has_email?: boolean;
  has_phone?: boolean;
  has_social?: boolean;
}

export const useLeads = (params: UseLeadsParams) => {
  return useQuery({
    queryKey: ['leads', params],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<BusinessLead>>('/leads', { params });
      return data;
    },
  });
};

export const useLead = (id: string) => {
  return useQuery({
    queryKey: ['lead', id],
    queryFn: async () => {
      const { data } = await api.get<LeadDetail>(`/leads/${id}`);
      return data;
    },
    enabled: !!id,
  });
};

export const useEnrichLead = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (leadId: string) => {
      const { data } = await api.post(`/leads/${leadId}/enrich`);
      return data;
    },
    onSuccess: (_, leadId) => {
      queryClient.invalidateQueries({ queryKey: ['lead', leadId] });
      queryClient.invalidateQueries({ queryKey: ['leads'] });
    },
  });
};
