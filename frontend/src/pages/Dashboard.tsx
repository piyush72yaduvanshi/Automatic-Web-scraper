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
  HardDrive,
  Cpu,
  Workflow,
  Sparkles,
  TrendingUp,
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
      gradient: 'from-blue-600/20 to-cyan-600/20',
      border: 'border-blue-500/30',
      iconColor: 'text-blue-400',
      iconBg: 'bg-blue-500/15',
    },
    {
      title: 'Open Pipeline Value',
      value: overview?.pipeline?.open_pipeline_value
        ? `$${overview.pipeline.open_pipeline_value.toLocaleString()}`
        : '$0',
      icon: Kanban,
      gradient: 'from-emerald-600/20 to-teal-600/20',
      border: 'border-emerald-500/30',
      iconColor: 'text-emerald-400',
      iconBg: 'bg-emerald-500/15',
    },
    {
      title: 'Verified Emails',
      value: stats?.emails_found || 0,
      icon: Mail,
      gradient: 'from-indigo-600/20 to-purple-600/20',
      border: 'border-indigo-500/30',
      iconColor: 'text-indigo-400',
      iconBg: 'bg-indigo-500/15',
    },
    {
      title: 'Phone Numbers',
      value: stats?.phones_found || 0,
      icon: Phone,
      gradient: 'from-amber-600/20 to-orange-600/20',
      border: 'border-amber-500/30',
      iconColor: 'text-amber-400',
      iconBg: 'bg-amber-500/15',
    },
    {
      title: 'Pending Approvals',
      value: overview?.tasks_and_calendar?.pending_approvals || 0,
      icon: Send,
      gradient: 'from-rose-600/20 to-pink-600/20',
      border: 'border-rose-500/30',
      iconColor: 'text-rose-400',
      iconBg: 'bg-rose-500/15',
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />;
      case 'FAILED':
        return <XCircle className="w-3.5 h-3.5 text-rose-400" />;
      case 'RUNNING':
      case 'QUEUED':
        return <Clock className="w-3.5 h-3.5 text-cyan-400 animate-spin" />;
      default:
        return null;
    }
  };

  if (statsLoading || jobsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-9 h-9 border-3 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-medium text-slate-400">Loading intelligence command center...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Hero Command Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#131B34] via-[#0E1528] to-[#0A0E1A] border border-indigo-500/20 p-6 md:p-8 shadow-2xl shadow-indigo-950/40">
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-indigo-500/10 via-blue-500/5 to-transparent rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-64 h-64 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5 shadow-sm">
                <Sparkles className="w-3 h-3 text-indigo-400" />
                Autonomous Sales OS
              </span>
              <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/25 flex items-center gap-1">
                <HardDrive className="w-3 h-3 text-emerald-400" />
                MinIO Connected
              </span>
              <span className="px-2.5 py-0.5 text-[10px] font-bold uppercase rounded-full bg-cyan-500/15 text-cyan-400 border border-cyan-500/25 flex items-center gap-1">
                <Cpu className="w-3 h-3 text-cyan-400" />
                pgvector RAG Active
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Enterprise Revenue &amp; GTM Command Center
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl leading-relaxed">
              Autonomous prospect discovery, ICP evaluation, deal orchestration, native multi-platform social marketing, and verified outbound sequences.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <Link
              to="/discovery"
              className="px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/25 hover:shadow-indigo-600/40 transition-all flex items-center gap-2 group"
            >
              <span>Launch Discovery</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
            <Link
              to="/outreach"
              className="px-4 py-2.5 bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold transition-colors flex items-center gap-2"
            >
              <Send className="w-3.5 h-3.5 text-indigo-400" />
              <span>Approvals ({overview?.tasks_and_calendar?.pending_approvals || 0})</span>
            </Link>
            <Link
              to="/pipeline"
              className="px-4 py-2.5 bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 rounded-xl text-xs font-semibold transition-colors flex items-center gap-2"
            >
              <Kanban className="w-3.5 h-3.5 text-emerald-400" />
              <span>Kanban</span>
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.title}
              className={`relative overflow-hidden rounded-xl bg-gradient-to-b ${stat.gradient} bg-[#0E1424] border ${stat.border} p-5 shadow-lg transition-all hover:scale-[1.01] hover:border-slate-600`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{stat.title}</p>
                  <p className="text-2xl font-black text-white mt-2 tracking-tight">
                    {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
                  </p>
                </div>
                <div className={`${stat.iconBg} ${stat.iconColor} p-2.5 rounded-xl border border-white/5`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-[10px] text-slate-400">
                <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                  <TrendingUp className="w-3 h-3" /> Live Engine
                </span>
                <span>Real-time DB</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Operational Highlights Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: Pipeline Highlights */}
        <div className="rounded-xl bg-[#0E1424] border border-slate-800 p-5 space-y-4 shadow-md">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Kanban className="w-4 h-4 text-emerald-400" /> Pipeline &amp; Revenue
            </h3>
            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              Active
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Active Deals:</span>
              <span className="font-bold text-white">{overview?.pipeline?.active_deals_count || 0}</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Won Revenue:</span>
              <span className="font-bold text-emerald-400">
                ${overview?.pipeline?.won_value?.toLocaleString() || 0}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Pending Actions:</span>
              <span className="font-bold text-amber-400">
                {overview?.tasks_and_calendar?.pending_tasks || 0} tasks due
              </span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-400">Scheduled Meetings:</span>
              <span className="font-bold text-indigo-400">
                {overview?.tasks_and_calendar?.scheduled_meetings || 0} calls
              </span>
            </div>
          </div>

          <Link
            to="/pipeline"
            className="text-xs text-indigo-400 font-semibold inline-flex items-center gap-1.5 hover:text-indigo-300 transition-colors pt-1"
          >
            <span>Open Kanban Board</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Card 2: AI Autonomous Agents */}
        <div className="rounded-xl bg-[#0E1424] border border-slate-800 p-5 space-y-4 shadow-md">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Bot className="w-4 h-4 text-indigo-400" /> AI Agent Swarm
            </h3>
            <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
              15 Agents
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Specialized Agents:</span>
              <span className="font-bold text-white">15 Registered</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Execution Success Rate:</span>
              <span className="font-bold text-emerald-400">
                {overview?.ai_telemetry?.success_rate || '100%'}
              </span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Total Telemetry Runs:</span>
              <span className="font-bold text-white">{overview?.ai_telemetry?.total_agent_runs || 0}</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-400">Failover Mode:</span>
              <span className="font-bold text-cyan-400">Gemini + OpenRouter + Heuristic</span>
            </div>
          </div>

          <Link
            to="/agents"
            className="text-xs text-indigo-400 font-semibold inline-flex items-center gap-1.5 hover:text-indigo-300 transition-colors pt-1"
          >
            <span>Manage AI Agents</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Card 3: Architecture & Security */}
        <div className="rounded-xl bg-[#0E1424] border border-slate-800 p-5 space-y-4 shadow-md">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" /> Architecture &amp; Governance
            </h3>
            <span className="text-[10px] font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
              Verified
            </span>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Automation Engine:</span>
              <span className="font-bold text-emerald-400">Native Python (Zero n8n)</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Object Store (Images):</span>
              <span className="font-bold text-emerald-400">MinIO S3 Compatible</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Vector Search (RAG):</span>
              <span className="font-bold text-emerald-400">pgvector Cosine Distance</span>
            </div>
            <div className="flex justify-between py-1.5">
              <span className="text-slate-400">Deliverability Kill-Switch:</span>
              <span className="font-bold text-emerald-400">Armed &amp; Ready</span>
            </div>
          </div>

          <Link
            to="/integrations"
            className="text-xs text-indigo-400 font-semibold inline-flex items-center gap-1.5 hover:text-indigo-300 transition-colors pt-1"
          >
            <span>Inspect System Health</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Recent Discovery Jobs */}
      <div className="rounded-xl bg-[#0E1424] border border-slate-800 shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/40">
          <div className="flex items-center gap-2.5">
            <Workflow className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-bold text-white tracking-tight">Recent Discovery &amp; Scraping Jobs</h2>
          </div>
          <Link
            to="/jobs"
            className="text-xs text-indigo-400 font-semibold hover:text-indigo-300 transition-colors flex items-center gap-1"
          >
            <span>View All Jobs</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="p-5">
          {recentJobs && recentJobs.items.length > 0 ? (
            <div className="divide-y divide-slate-800/60">
              {recentJobs.items.map((job) => (
                <div key={job.id} className="py-3.5 flex items-center justify-between first:pt-0 last:pb-0">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="text-xs font-bold text-white">{job.search_query}</p>
                      {getStatusIcon(job.status)}
                    </div>
                    <p className="text-[11px] text-slate-400">{job.location}</p>
                  </div>
                  <div className="text-right text-xs">
                    <p className="font-bold text-white">{job.total_found} leads found</p>
                    <p className="text-[11px] text-slate-400">{job.total_enriched} fully enriched</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 space-y-2">
              <p className="text-slate-400 text-xs">No active discovery jobs logged yet.</p>
              <Link
                to="/discovery"
                className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-semibold"
              >
                Launch your first business scan &rarr;
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
