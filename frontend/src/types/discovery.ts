export interface DiscoverySchedule {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
  schedule_type: 'HOURLY' | 'DAILY' | 'WEEKLY' | 'CUSTOM';
  cron_expression?: string;
  interval_hours?: number;
  max_leads_per_run: number;
  last_run_at?: string;
  next_run_at?: string;
  created_at: string;
}

export interface DiscoveryScheduleCreate {
  name: string;
  description?: string;
  is_active?: boolean;
  schedule_type: 'HOURLY' | 'DAILY' | 'WEEKLY' | 'CUSTOM';
  cron_expression?: string;
  interval_hours?: number;
  max_leads_per_run?: number;
}

export interface DiscoveryScheduleUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
  schedule_type?: 'HOURLY' | 'DAILY' | 'WEEKLY' | 'CUSTOM';
  cron_expression?: string;
  interval_hours?: number;
  max_leads_per_run?: number;
}

export interface DiscoveryTarget {
  id: string;
  schedule_id: string;
  target_type: 'CITY' | 'STATE' | 'COUNTRY' | 'INDUSTRY' | 'CATEGORY';
  target_value: string;
  priority: number;
}

export interface DiscoveryTargetCreate {
  target_type: 'CITY' | 'STATE' | 'COUNTRY' | 'INDUSTRY' | 'CATEGORY';
  target_value: string;
  priority?: number;
}

export interface DiscoveryRun {
  id: string;
  schedule_id?: string;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED';
  leads_discovered: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  workflow_name: string;
  trigger_event: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'RETRYING';
  current_step_index: number;
  current_step_name?: string;
  retry_count: number;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

export interface WorkflowExecutionFilters {
  workflowId?: string;
  status?: string;
  triggerEvent?: string;
}
