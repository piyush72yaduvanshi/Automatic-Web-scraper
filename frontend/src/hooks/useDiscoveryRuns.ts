import { useQuery } from '@tanstack/react-query';
import { DiscoveryRun } from '../types/discovery';

export const useDiscoveryRuns = (scheduleId?: string) => {
  const runs = useQuery<DiscoveryRun[]>({
    queryKey: ['discovery-runs', scheduleId],
    queryFn: async () => {
      const url = scheduleId
        ? `/api/v1/discovery/runs?schedule_id=${scheduleId}`
        : '/api/v1/discovery/runs';
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error('Failed to fetch discovery runs');
      }
      return res.json();
    },
  });

  return { runs };
};
