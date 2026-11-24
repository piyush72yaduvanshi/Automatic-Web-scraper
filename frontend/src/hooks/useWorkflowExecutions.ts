import { useQuery } from '@tanstack/react-query';
import { WorkflowExecution, WorkflowExecutionFilters } from '../types/discovery';

export const useWorkflowExecutions = (filters?: WorkflowExecutionFilters) => {
  const executions = useQuery<WorkflowExecution[]>({
    queryKey: ['workflow-executions', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      
      if (filters?.workflowId) {
        params.append('workflow_id', filters.workflowId);
      }
      if (filters?.status) {
        params.append('status', filters.status);
      }
      if (filters?.triggerEvent) {
        params.append('trigger_event', filters.triggerEvent);
      }

      const url = `/api/v1/workflows/executions${params.toString() ? `?${params.toString()}` : ''}`;
      const res = await fetch(url);
      
      if (!res.ok) {
        throw new Error('Failed to fetch workflow executions');
      }
      return res.json();
    },
  });

  return { executions };
};
