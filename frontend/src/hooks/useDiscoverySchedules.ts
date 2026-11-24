import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DiscoverySchedule,
  DiscoveryScheduleCreate,
  DiscoveryScheduleUpdate,
  DiscoveryTargetCreate,
} from '../types/discovery';

export const useDiscoverySchedules = () => {
  const queryClient = useQueryClient();

  const schedules = useQuery<DiscoverySchedule[]>({
    queryKey: ['discovery-schedules'],
    queryFn: async () => {
      const res = await fetch('/api/v1/discovery/schedules');
      if (!res.ok) {
        throw new Error('Failed to fetch discovery schedules');
      }
      return res.json();
    },
  });

  const createSchedule = useMutation({
    mutationFn: async (data: DiscoveryScheduleCreate) => {
      const res = await fetch('/api/v1/discovery/schedules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        throw new Error('Failed to create discovery schedule');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-schedules'] });
    },
  });

  const updateSchedule = useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: DiscoveryScheduleUpdate;
    }) => {
      const res = await fetch(`/api/v1/discovery/schedules/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        throw new Error('Failed to update discovery schedule');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-schedules'] });
    },
  });

  const deleteSchedule = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`/api/v1/discovery/schedules/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        throw new Error('Failed to delete discovery schedule');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-schedules'] });
    },
  });

  const addTarget = useMutation({
    mutationFn: async ({
      scheduleId,
      data,
    }: {
      scheduleId: string;
      data: DiscoveryTargetCreate;
    }) => {
      const res = await fetch(
        `/api/v1/discovery/schedules/${scheduleId}/targets`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        }
      );
      if (!res.ok) {
        throw new Error('Failed to add discovery target');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-schedules'] });
    },
  });

  const deleteTarget = useMutation({
    mutationFn: async ({
      scheduleId,
      targetId,
    }: {
      scheduleId: string;
      targetId: string;
    }) => {
      const res = await fetch(
        `/api/v1/discovery/schedules/${scheduleId}/targets/${targetId}`,
        {
          method: 'DELETE',
        }
      );
      if (!res.ok) {
        throw new Error('Failed to delete discovery target');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-schedules'] });
    },
  });

  const triggerRun = useMutation({
    mutationFn: async (scheduleId: string) => {
      const res = await fetch(
        `/api/v1/discovery/schedules/${scheduleId}/trigger`,
        {
          method: 'POST',
        }
      );
      if (!res.ok) {
        throw new Error('Failed to trigger discovery run');
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['discovery-runs'] });
      queryClient.invalidateQueries({ queryKey: ['discovery-schedules'] });
    },
  });

  return {
    schedules,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    addTarget,
    deleteTarget,
    triggerRun,
  };
};
