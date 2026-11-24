import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  Filter,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader,
  Eye,
  RefreshCw,
  X,
  TrendingUp,
  Zap,
  Target,
} from 'lucide-react';

interface WorkflowExecution {
  id: string;
  workflowName: string;
  workflowId: string;
  triggerEvent: string;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED' | 'WAITING' | 'PAUSED';
  currentStep?: string;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  steps: WorkflowStep[];
  inputPayload: any;
  error?: string;
}

interface WorkflowStep {
  name: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  startedAt?: string;
  completedAt?: string;
  result?: any;
  error?: string;
}

interface WorkflowStats {
  totalExecutionsToday: number;
  successRate: number;
  activeWorkflows: number;
  avgExecutionTime: number;
}

const WorkflowMonitor: React.FC = () => {
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [stats, setStats] = useState<WorkflowStats>({
    totalExecutionsToday: 0,
    successRate: 0,
    activeWorkflows: 0,
    avgExecutionTime: 0,
  });
  const [loading, setLoading] = useState(true);
  const [selectedExecution, setSelectedExecution] = useState<WorkflowExecution | null>(null);
  const [filters, setFilters] = useState({
    workflow: 'all',
    status: 'all',
    triggerEvent: 'all',
    dateFrom: '',
    dateTo: '',
  });
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch executions and stats
  const fetchData = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filters.workflow !== 'all') params.append('workflow', filters.workflow);
      if (filters.status !== 'all') params.append('status', filters.status);
      if (filters.triggerEvent !== 'all') params.append('trigger', filters.triggerEvent);
      if (filters.dateFrom) params.append('from', filters.dateFrom);
      if (filters.dateTo) params.append('to', filters.dateTo);

      const [executionsRes, statsRes] = await Promise.all([
        fetch(`/api/workflows/executions?${params}`),
        fetch('/api/workflows/stats'),
      ]);

      if (executionsRes.ok) {
        const executionsData = await executionsRes.json();
        setExecutions(executionsData);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
    } catch (error) {
      console.error('Failed to fetch workflow data:', error);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh every 5 seconds
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchData();
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  const getStatusBadge = (status: WorkflowExecution['status']) => {
    const configs = {
      RUNNING: { color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', icon: Loader },
      COMPLETED: { color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30', icon: CheckCircle },
      FAILED: { color: 'bg-red-500/20 text-red-400 border-red-500/30', icon: XCircle },
      WAITING: { color: 'bg-amber-500/20 text-amber-400 border-amber-500/30', icon: AlertCircle },
      PAUSED: { color: 'bg-slate-500/20 text-slate-400 border-slate-500/30', icon: Clock },
    };

    const config = configs[status];
    const Icon = config.icon;

    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border ${config.color}`}
      >
        <Icon className={`w-3.5 h-3.5 ${status === 'RUNNING' ? 'animate-spin' : ''}`} />
        {status}
      </span>
    );
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ${seconds % 60}s`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ${minutes % 60}m`;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Activity className="w-7 h-7 text-indigo-400" />
            Workflow Automation Monitor
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time monitoring and execution history
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              autoRefresh
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-slate-800 text-slate-400 border border-slate-700'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-Refresh' : 'Manual'}
          </button>
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh Now
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-indigo-900/50 to-indigo-800/30 border border-indigo-700/50 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <Zap className="w-5 h-5 text-indigo-400" />
            <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wide">
              Today
            </span>
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            {stats.totalExecutionsToday}
          </div>
          <div className="text-xs text-slate-400">Total Executions</div>
        </div>

        <div className="bg-gradient-to-br from-emerald-900/50 to-emerald-800/30 border border-emerald-700/50 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
            <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wide">
              Success
            </span>
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            {stats.successRate.toFixed(1)}%
          </div>
          <div className="text-xs text-slate-400">Success Rate</div>
        </div>

        <div className="bg-gradient-to-br from-blue-900/50 to-blue-800/30 border border-blue-700/50 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <Target className="w-5 h-5 text-blue-400" />
            <span className="text-xs font-semibold text-blue-400 uppercase tracking-wide">
              Active
            </span>
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            {stats.activeWorkflows}
          </div>
          <div className="text-xs text-slate-400">Active Workflows</div>
        </div>

        <div className="bg-gradient-to-br from-purple-900/50 to-purple-800/30 border border-purple-700/50 rounded-xl p-5">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="w-5 h-5 text-purple-400" />
            <span className="text-xs font-semibold text-purple-400 uppercase tracking-wide">
              Avg Time
            </span>
          </div>
          <div className="text-3xl font-bold text-white mb-1">
            {formatDuration(stats.avgExecutionTime)}
          </div>
          <div className="text-xs text-slate-400">Execution Time</div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <span className="text-sm font-semibold text-white">Filters</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <select
            value={filters.workflow}
            onChange={(e) => setFilters({ ...filters, workflow: e.target.value })}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Workflows</option>
            <option value="qualify">Auto-Qualify Leads</option>
            <option value="unsubscribe">Enforce Suppression</option>
            <option value="reply">Escalate Reply</option>
          </select>

          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Statuses</option>
            <option value="RUNNING">Running</option>
            <option value="COMPLETED">Completed</option>
            <option value="FAILED">Failed</option>
            <option value="WAITING">Waiting</option>
          </select>

          <select
            value={filters.triggerEvent}
            onChange={(e) => setFilters({ ...filters, triggerEvent: e.target.value })}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
          >
            <option value="all">All Triggers</option>
            <option value="NEW_LEAD">New Lead</option>
            <option value="UNSUBSCRIBE">Unsubscribe</option>
            <option value="REPLY_CLASSIFIED">Reply Classified</option>
            <option value="MANUAL">Manual</option>
          </select>

          <input
            type="date"
            value={filters.dateFrom}
            onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
            placeholder="From Date"
          />

          <input
            type="date"
            value={filters.dateTo}
            onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
            className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
            placeholder="To Date"
          />
        </div>
      </div>

      {/* Execution History Table */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800/80 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                  Workflow Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                  Trigger Event
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                  Current Step
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                  Started At
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                  Duration
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center">
                    <div className="flex items-center justify-center">
                      <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                    </div>
                  </td>
                </tr>
              ) : executions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-12 text-center text-slate-400 text-sm">
                    No workflow executions found
                  </td>
                </tr>
              ) : (
                executions.map((execution) => (
                  <tr
                    key={execution.id}
                    className="hover:bg-slate-800/50 transition-colors"
                  >
                    <td className="px-4 py-3 text-sm text-white font-medium">
                      {execution.workflowName}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      <span className="px-2 py-1 bg-slate-800 rounded text-xs font-mono">
                        {execution.triggerEvent}
                      </span>
                    </td>
                    <td className="px-4 py-3">{getStatusBadge(execution.status)}</td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {execution.currentStep || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {formatTimestamp(execution.startedAt)}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-400">
                      {formatDuration(execution.duration)}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => setSelectedExecution(execution)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition-colors"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Execution Details Modal */}
      {selectedExecution && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto m-4">
            <div className="sticky top-0 bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">
                  {selectedExecution.workflowName}
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Execution ID: {selectedExecution.id}
                </p>
              </div>
              <button
                onClick={() => setSelectedExecution(null)}
                className="p-1 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Summary */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-slate-500 mb-1">Trigger Event</div>
                  <div className="text-sm font-mono text-white bg-slate-800 px-2 py-1 rounded">
                    {selectedExecution.triggerEvent}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">Status</div>
                  {getStatusBadge(selectedExecution.status)}
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">Started At</div>
                  <div className="text-sm text-white">
                    {formatTimestamp(selectedExecution.startedAt)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-500 mb-1">Duration</div>
                  <div className="text-sm text-white">
                    {formatDuration(selectedExecution.duration)}
                  </div>
                </div>
              </div>

              {/* Step Timeline */}
              <div>
                <h3 className="text-sm font-semibold text-white mb-3">Execution Timeline</h3>
                <div className="space-y-3">
                  {selectedExecution.steps.map((step, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <div className="flex flex-col items-center">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            step.status === 'COMPLETED'
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : step.status === 'FAILED'
                              ? 'bg-red-500/20 text-red-400'
                              : step.status === 'RUNNING'
                              ? 'bg-blue-500/20 text-blue-400'
                              : 'bg-slate-700 text-slate-500'
                          }`}
                        >
                          {step.status === 'COMPLETED' && <CheckCircle className="w-4 h-4" />}
                          {step.status === 'FAILED' && <XCircle className="w-4 h-4" />}
                          {step.status === 'RUNNING' && <Loader className="w-4 h-4 animate-spin" />}
                          {step.status === 'PENDING' && <Clock className="w-4 h-4" />}
                        </div>
                        {index < selectedExecution.steps.length - 1 && (
                          <div className="w-0.5 h-8 bg-slate-700"></div>
                        )}
                      </div>
                      <div className="flex-1 bg-slate-800/50 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1">
                          <div className="text-sm font-medium text-white">{step.name}</div>
                          <div className="text-xs text-slate-400">
                            {step.completedAt && formatTimestamp(step.completedAt)}
                          </div>
                        </div>
                        {step.error && (
                          <div className="text-xs text-red-400 bg-red-500/10 px-2 py-1 rounded mt-2">
                            {step.error}
                          </div>
                        )}
                        {step.result && (
                          <details className="mt-2">
                            <summary className="text-xs text-indigo-400 cursor-pointer hover:text-indigo-300">
                              View Result
                            </summary>
                            <pre className="text-xs text-slate-400 bg-slate-900 p-2 rounded mt-1 overflow-x-auto">
                              {JSON.stringify(step.result, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Input Payload */}
              {selectedExecution.inputPayload && (
                <div>
                  <h3 className="text-sm font-semibold text-white mb-2">Input Payload</h3>
                  <pre className="text-xs text-slate-400 bg-slate-800 p-3 rounded overflow-x-auto">
                    {JSON.stringify(selectedExecution.inputPayload, null, 2)}
                  </pre>
                </div>
              )}

              {/* Error Details */}
              {selectedExecution.error && (
                <div>
                  <h3 className="text-sm font-semibold text-red-400 mb-2">Error Information</h3>
                  <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                    <p className="text-sm text-red-300">{selectedExecution.error}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowMonitor;
