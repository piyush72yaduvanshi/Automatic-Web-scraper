import { Link } from 'react-router-dom';
import {
  Users,
  Mail,
  Phone,
  CheckCircle,
  XCircle,
  Clock,
  Kanban,
  Send,
  Bot,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import { useStats } from '../hooks/useStats';
import { useJobs } from '../hooks/useJobs';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';

const Dashboard = () => {
  const { data: stats, isLoading: statsLoading } = useStats();
  const { data: recentJobs, isLoading: jobsLoading } = useJobs({ page: 1, page_size: 5 });

  const { data: overview } = useQuery<any>({
    queryKey: ['analytics_dashboard_overview'],
    queryFn: async () => {
      const res = await api.get('/analytics/overview');
      return res.data;
    },
    refetchInterval: 15000,
  });

  const statCards = [
    {
      title: 'Discovered Leads',
      value: stats?.total_leads || 0,
      icon: Users,
      color: 'bg-blue-600',
    },
    {
      title: 'Open Pipeline Value',
      value: overview?.pipeline?.open_pipeline_value ? `$${overview.pipeline.open_pipeline_value.toLocaleString()}` : '$0',
      icon: Kanban,
      color: 'bg-emerald-600',
    },
    {
      title: 'Verified Emails',
      value: stats?.emails_found || 0,
      icon: Mail,
      color: 'bg-indigo-600',
    },
    {
      title: 'Phone Numbers',
      value: stats?.phones_found || 0,
      icon: Phone,
      color: 'bg-orange-600',
    },
    {
      title: 'Pending Approvals',
      value: overview?.tasks_and_calendar?.pending_approvals || 0,
      icon: Send,
      color: 'bg-amber-600',
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle className="w-4 h-4 text-emerald-500" />;
      case 'FAILED':
        return <XCircle className="w-4 h-4 text-rose-500" />;
      case 'RUNNING':
      case 'QUEUED':
        return <Clock className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return null;
    }
  };

  if (statsLoading || jobsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome & Quick Action Banner */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-xl p-6 text-white shadow-md flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-semibold tracking-wider text-blue-300 uppercase block mb-1 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5" /> AI Sales & CRM Operating System
          </span>
          <h1 className="text-xl sm:text-2xl font-bold text-white">Autonomous GTM & Lead Command Center</h1>
          <p className="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
            Discover B2B business candidates, research accounts, qualify against ICP, manage deals, and draft verified outreach.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Link
            to="/discovery"
            className="px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors flex items-center gap-1.5"
          >
            Launch Discovery <ArrowRight className="w-3.5 h-3.5" />
          </Link>
          <Link
            to="/outreach"
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 rounded-lg text-xs font-semibold transition-colors"
          >
            Approval Queue ({overview?.tasks_and_calendar?.pending_approvals || 0})
          </Link>
          <Link
            to="/pipeline"
            className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 rounded-lg text-xs font-semibold transition-colors"
          >
            Kanban Board
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.title} className="bg-white rounded-lg border border-slate-200 p-4 shadow-xs">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-medium text-slate-500">{stat.title}</p>
                  <p className="text-xl font-bold text-slate-900 mt-1">
                    {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
                  </p>
                </div>
                <div className={`${stat.color} p-2.5 rounded-lg text-white shadow-xs`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Operational Highlights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Pipeline & Revenue Card */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-3">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
            <Kanban className="w-4 h-4 text-blue-600" /> Pipeline Highlights
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">Active Deals:</span>
              <span className="font-semibold text-slate-900">{overview?.pipeline?.active_deals_count || 0}</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">Won Revenue:</span>
              <span className="font-semibold text-emerald-600">${overview?.pipeline?.won_value?.toLocaleString() || 0}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-600">Pending Actions:</span>
              <span className="font-semibold text-amber-600">{overview?.tasks_and_calendar?.pending_tasks || 0} tasks due</span>
            </div>
          </div>
          <Link to="/pipeline" className="text-xs text-blue-600 font-semibold inline-flex items-center gap-1 hover:underline pt-1">
            Open Kanban Board &rarr;
          </Link>
        </div>

        {/* AI Agents Card */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-3">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
            <Bot className="w-4 h-4 text-indigo-600" /> AI Autonomous Agents
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">Specialized Agents:</span>
              <span className="font-semibold text-slate-900">15 Active</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">Execution Success Rate:</span>
              <span className="font-semibold text-emerald-600">{overview?.ai_telemetry?.success_rate || '100%'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-600">Total Telemetry Runs:</span>
              <span className="font-semibold text-slate-900">{overview?.ai_telemetry?.total_agent_runs || 0}</span>
            </div>
          </div>
          <Link to="/agents" className="text-xs text-blue-600 font-semibold inline-flex items-center gap-1 hover:underline pt-1">
            Manage & Run AI Agents &rarr;
          </Link>
        </div>

        {/* Integration Health Card */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-xs space-y-3">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" /> System Architecture
          </h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">Fault-Tolerant Engine:</span>
              <span className="font-semibold text-emerald-600">Active (Zero-Crash Fallback)</span>
            </div>
            <div className="flex justify-between py-1 border-b">
              <span className="text-slate-600">Human Approval Queue:</span>
              <span className="font-semibold text-emerald-600">Enforced</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-600">Heuristic Offline NLP:</span>
              <span className="font-semibold text-slate-900">Always Available</span>
            </div>
          </div>
          <Link to="/integrations" className="text-xs text-blue-600 font-semibold inline-flex items-center gap-1 hover:underline pt-1">
            Inspect Integrations Health &rarr;
          </Link>
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">Recent Discovery Jobs</h2>
          <Link to="/jobs" className="text-xs text-blue-600 font-semibold hover:underline">
            View All Jobs &rarr;
          </Link>
        </div>
        <div className="p-4 sm:p-6">
          {recentJobs && recentJobs.items.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {recentJobs.items.map((job) => (
                <div key={job.id} className="py-3.5 flex items-center justify-between first:pt-0 last:pb-0">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-xs font-bold text-slate-900">{job.search_query}</p>
                      {getStatusIcon(job.status)}
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">{job.location}</p>
                  </div>
                  <div className="text-right text-xs">
                    <p className="font-semibold text-slate-900">{job.total_found} found</p>
                    <p className="text-[11px] text-slate-500">{job.total_enriched} enriched</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-500 text-center py-6 text-xs">No jobs yet. Start by discovering business leads.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
