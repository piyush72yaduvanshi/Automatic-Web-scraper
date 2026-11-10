import React, { useState, useEffect } from 'react';
import {
  Clock,
  CheckCircle,
  XCircle,
  Loader,
  Target,
  TrendingUp,
  AlertCircle,
} from 'lucide-react';

interface DiscoveryRun {
  id: string;
  scheduleId: string;
  scheduleName: string;
  status: 'running' | 'completed' | 'failed';
  leadsFound: number;
  targetsUsed: number;
  duration?: number;
  timestamp: string;
  error?: string;
}

const DiscoveryRunHistory: React.FC = () => {
  const [runs, setRuns] = useState<DiscoveryRun[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRunHistory();
  }, []);

  const fetchRunHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/discovery/runs');
      if (response.ok) {
        const data = await response.json();
        setRuns(data);
      }
    } catch (error) {
      console.error('Failed to fetch run history:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: DiscoveryRun['status']) => {
    const configs = {
      running: {
        color: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        icon: Loader,
        label: 'Running',
      },
      completed: {
        color: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
        icon: CheckCircle,
        label: 'Completed',
      },
      failed: {
        color: 'bg-red-500/20 text-red-400 border-red-500/30',
        icon: XCircle,
        label: 'Failed',
      },
    };

    const config = configs[status];
    const Icon = config.icon;

    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold border ${config.color}`}
      >
        <Icon className={`w-3.5 h-3.5 ${status === 'running' ? 'animate-spin' : ''}`} />
        {config.label}
      </span>
    );
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m ${seconds % 60}s`;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-indigo-400" />
              Discovery Run History
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Recent automated discovery executions
            </p>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-800/50 border-b border-slate-700">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                Schedule
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                Leads Found
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                Targets Used
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                Duration
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-300 uppercase tracking-wide">
                Timestamp
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center">
                  <div className="flex items-center justify-center">
                    <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
                  </div>
                </td>
              </tr>
            ) : runs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center">
                  <Target className="w-10 h-10 text-slate-600 mx-auto mb-2" />
                  <p className="text-slate-400 text-sm">No discovery runs yet</p>
                  <p className="text-slate-500 text-xs mt-1">
                    Create a schedule and trigger a run to see history
                  </p>
                </td>
              </tr>
            ) : (
              runs.map((run) => (
                <tr
                  key={run.id}
                  className="hover:bg-slate-800/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="text-sm font-medium text-white">
                      {run.scheduleName}
                    </div>
                    {run.error && (
                      <div className="flex items-center gap-1 text-xs text-red-400 mt-1">
                        <AlertCircle className="w-3 h-3" />
                        <span className="truncate max-w-xs">{run.error}</span>
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">{getStatusBadge(run.status)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-semibold text-emerald-400">
                        {run.leadsFound}
                      </span>
                      <span className="text-xs text-slate-500">leads</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <Target className="w-3.5 h-3.5 text-indigo-400" />
                      <span className="text-sm text-slate-300">{run.targetsUsed}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span className="text-sm text-slate-400">
                        {formatDuration(run.duration)}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400">
                    {formatTimestamp(run.timestamp)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {runs.length > 0 && (
        <div className="px-6 py-3 bg-slate-800/30 border-t border-slate-700 text-center">
          <button
            onClick={fetchRunHistory}
            className="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
          >
            Refresh History
          </button>
        </div>
      )}
    </div>
  );
};

export default DiscoveryRunHistory;
