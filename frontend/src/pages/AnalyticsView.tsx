import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  Users,
  Cpu,
  Building2,
} from 'lucide-react';

const AnalyticsView: React.FC = () => {
  const { data: analytics, isLoading } = useQuery<any>({
    queryKey: ['analytics_overview'],
    queryFn: async () => {
      const res = await api.get('/analytics/overview');
      return res.data;
    },
    refetchInterval: 15000,
  });

  if (isLoading || !analytics) {
    return <div className="p-12 text-center text-sm text-slate-500">Loading system analytics...</div>;
  }

  const { leads, pipeline, tasks_and_calendar, outreach, ai_telemetry } = analytics;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-blue-600" />
          Sales & Platform Analytics
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Objective performance KPIs computed from stored lead records, pipeline deals, and AI execution runs.
        </p>
      </div>

      {/* Top 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
            <span>Total Discovered Leads</span>
            <Users className="w-4 h-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{leads.total}</div>
          <div className="mt-1 text-xs text-slate-500">
            <span className="font-semibold text-emerald-600">{leads.qualified}</span> Qualified ({leads.average_qualification_score} avg score)
          </div>
        </div>

        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
            <span>Open Pipeline Value</span>
            <DollarSign className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">${pipeline.open_pipeline_value.toLocaleString()}</div>
          <div className="mt-1 text-xs text-slate-500">
            {pipeline.active_deals_count} active sales deals in pipeline
          </div>
        </div>

        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
            <span>Closed Revenue Won</span>
            <TrendingUp className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-600">${pipeline.won_value.toLocaleString()}</div>
          <div className="mt-1 text-xs text-slate-500">
            {pipeline.won_deals_count} deals won ({pipeline.lost_deals_count} lost)
          </div>
        </div>

        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
            <span>AI Execution Success</span>
            <Cpu className="w-4 h-4 text-purple-600" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900">{ai_telemetry.success_rate}</div>
          <div className="mt-1 text-xs text-slate-500">
            {ai_telemetry.total_agent_runs} total runs (${ai_telemetry.estimated_cost_usd} est. cost)
          </div>
        </div>
      </div>

      {/* Middle Grid: Operational Workflows */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Reachability & Contact Endpoints */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Contact Reachability Availability</h3>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center py-1.5 border-b">
              <span className="text-slate-600">Verified Email Mailboxes</span>
              <span className="font-bold text-slate-900">{leads.total_emails}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b">
              <span className="text-slate-600">Normalized Phone Numbers</span>
              <span className="font-bold text-slate-900">{leads.total_phones}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b">
              <span className="text-slate-600">Discovered Social Profiles</span>
              <span className="font-bold text-slate-900">{leads.total_social_profiles}</span>
            </div>
            <div className="flex justify-between items-center py-1.5">
              <span className="text-slate-600">Outreach Reply Rate</span>
              <span className="font-bold text-emerald-600">{outreach.reply_rate}</span>
            </div>
          </div>
        </div>

        {/* Tasks & Scheduled Engagements */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Sales Operations</h3>
          <div className="space-y-3 text-xs">
            <div className="flex justify-between items-center py-1.5 border-b">
              <span className="text-slate-600">Human Approvals Pending</span>
              <span className="font-bold text-amber-600">{tasks_and_calendar.pending_approvals}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b">
              <span className="text-slate-600">Pending Action Tasks</span>
              <span className="font-bold text-slate-900">{tasks_and_calendar.pending_tasks}</span>
            </div>
            <div className="flex justify-between items-center py-1.5 border-b">
              <span className="text-slate-600">Scheduled Calendar Calls</span>
              <span className="font-bold text-blue-600">{tasks_and_calendar.scheduled_meetings}</span>
            </div>
            <div className="flex justify-between items-center py-1.5">
              <span className="text-slate-600">Approved Messages Sent</span>
              <span className="font-bold text-emerald-600">{outreach.approved_sent_count}</span>
            </div>
          </div>
        </div>

        {/* Top Discovery Categories */}
        <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
            <Building2 className="w-4 h-4 text-slate-500" /> Leads by Category
          </h3>
          <div className="space-y-2 text-xs">
            {leads.by_category?.map((c: any, i: number) => (
              <div key={i} className="flex justify-between items-center">
                <span className="text-slate-600 truncate max-w-[180px]">{c.category}</span>
                <span className="font-semibold text-slate-900 bg-slate-100 px-2 py-0.5 rounded text-[11px]">{c.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsView;
