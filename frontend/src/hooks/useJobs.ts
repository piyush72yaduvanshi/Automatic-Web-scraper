import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { DiscoveryJob, DiscoveryJobCreate, PaginatedResponse, JobStatus } from '../types';

interface UseJobsParams {
  page?: number;
  page_size?: number;
  status?: JobStatus;
}

export const useJobs = (params: UseJobsParams) => {
  return useQuery({
    queryKey: ['jobs', params],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<DiscoveryJob>>('/discovery/jobs', { params });
      return data;
    },
    refetchInterval: (query) => {
      // Auto-refresh every 10 seconds if any jobs are running
      const data = query.state.data;
      const hasRunning = data?.items?.some(job => 
        job.status === 'RUNNING' || job.status === 'QUEUED'
      );
      return hasRunning ? 10000 : false;
    },
  });
};

export const useJob = (id: string) => {
  return useQuery({
    queryKey: ['job', id],
    queryFn: async () => {
      const { data } = await api.get<DiscoveryJob>(`/discovery/jobs/${id}`);
      return data;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      // Auto-refetch if job is running
      const data = query.state.data;
      if (data?.status === 'RUNNING' || data?.status === 'QUEUED') {
        return 5000; // 5 seconds
      }
      return false;
    },
  });
};

export const useCreateJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (jobData: DiscoveryJobCreate) => {
      const { data } = await api.post<DiscoveryJob>('/discovery/jobs', jobData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
};
