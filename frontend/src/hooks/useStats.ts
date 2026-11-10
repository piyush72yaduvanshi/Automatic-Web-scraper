import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { Stats } from '../types';

export const useStats = () => {
  return useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const { data } = await api.get<Stats>('/stats');
      return data;
    },
    staleTime: 30 * 1000, // 30 seconds - more frequent updates for dashboard stats
  });
};
