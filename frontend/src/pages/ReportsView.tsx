import React, { useState, useEffect } from 'react';
import {
  FileBarChart,
  RefreshCw,
  Sparkles,
  Calendar,
  CheckCircle2,
} from 'lucide-react';
import { ReportSnapshotItem } from '../types';

export const ReportsView: React.FC = () => {
  const [reports, setReports] = useState<ReportSnapshotItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [generating, setGenerating] = useState<boolean>(false);
  const [genType, setGenType] = useState<string>('DAILY');
  const [message, setMessage] = useState<string | null>(null);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/reports');
      if (res.ok) setReports(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      const res = await fetch('/api/v1/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_type: genType }),
      });
      if (res.ok) {
        setMessage(`${genType} operational report generated successfully!`);
        fetchReports();
      }
    } catch {
      setMessage('Failed to generate report.');
    } finally {
      setGenerating(false);
    }
  };

  const filtered = selectedType === 'ALL'
    ? reports
    : reports.filter((r) => r.report_type === selectedType);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-gray-900 border border-gray-800 p-6 rounded-xl">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <FileBarChart className="w-7 h-7 text-indigo-400" />
              Daily, Weekly &amp; Monthly Reports
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              100% Real Database Metrics
            </span>
          </div>
          <p className="text-gray-400 text-sm mt-1">
            Automated operational snapshots, conversion velocity, pipeline contribution, and strategic AI optimization advice.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={genType}
            onChange={(e) => setGenType(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-xs text-white"
          >
            <option value="DAILY">Daily Report (Last 24h)</option>
            <option value="WEEKLY">Weekly Report (Last 7d)</option>
            <option value="MONTHLY">Monthly Report (Last 30d)</option>
          </select>
          <button
            onClick={handleGenerateReport}
            disabled={generating}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50 whitespace-nowrap"
          >
            <Sparkles className="w-3.5 h-3.5" />
            {generating ? 'Synthesizing...' : 'Generate Snapshot'}
          </button>
          <button
            onClick={fetchReports}
            className="p-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {message && (
        <div className="p-4 bg-indigo-950/60 border border-indigo-500/40 rounded-lg text-indigo-200 text-sm flex justify-between items-center">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-indigo-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {['ALL', 'DAILY', 'WEEKLY', 'MONTHLY'].map((t) => (
          <button
            key={t}
            onClick={() => setSelectedType(t)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              selectedType === t
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-900 hover:bg-gray-800 text-gray-400'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Snapshots List */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading report archives...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-gray-500 bg-gray-900 border border-gray-800 rounded-xl p-8">
          No reports generated yet. Click 'Generate Snapshot' above!
        </div>
      ) : (
        <div className="space-y-6">
          {filtered.map((r) => (
            <div key={r.id} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 pb-3 border-b border-gray-800">
                <div className="flex items-center gap-2.5">
                  <span className="px-2.5 py-0.5 text-xs font-bold rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {r.report_type} REPORT
                  </span>
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    Period: {new Date(r.period_start).toLocaleDateString()} — {new Date(r.period_end).toLocaleDateString()}
                  </span>
                </div>
                <span className="text-xs text-gray-500">
                  Generated: {new Date(r.created_at).toLocaleString()}
                </span>
              </div>

              {/* Executive Summary */}
              <div className="bg-gray-800/40 p-4 rounded-lg border border-gray-700/60">
                <div className="text-xs font-semibold text-gray-400 uppercase mb-1">Executive Summary</div>
                <p className="text-sm text-gray-200 leading-relaxed">{r.executive_summary}</p>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 text-center">
                <div className="bg-gray-800/30 p-3 rounded">
                  <div className="text-[11px] text-gray-400">Leads Discovered</div>
                  <div className="text-lg font-bold text-white mt-1">{r.metrics.leads_discovered || 0}</div>
                </div>
                <div className="bg-gray-800/30 p-3 rounded">
                  <div className="text-[11px] text-gray-400">Leads Qualified</div>
                  <div className="text-lg font-bold text-indigo-400 mt-1">{r.metrics.leads_qualified || 0}</div>
                </div>
                <div className="bg-gray-800/30 p-3 rounded">
                  <div className="text-[11px] text-gray-400">Outreach Sent</div>
                  <div className="text-lg font-bold text-white mt-1">{r.metrics.outreach_sent || 0}</div>
                </div>
                <div className="bg-gray-800/30 p-3 rounded">
                  <div className="text-[11px] text-gray-400">Replies Received</div>
                  <div className="text-lg font-bold text-emerald-400 mt-1">{r.metrics.inbound_replies || 0}</div>
                </div>
                <div className="bg-gray-800/30 p-3 rounded">
                  <div className="text-[11px] text-gray-400">Meetings Booked</div>
                  <div className="text-lg font-bold text-indigo-300 mt-1">{r.metrics.meetings_scheduled || 0}</div>
                </div>
                <div className="bg-gray-800/30 p-3 rounded">
                  <div className="text-[11px] text-gray-400">Revenue Won</div>
                  <div className="text-lg font-bold text-emerald-400 mt-1">${(r.metrics.revenue_won || 0).toLocaleString()}</div>
                </div>
              </div>

              {/* AI Strategic Recommendations */}
              {r.recommendations?.length > 0 && (
                <div className="pt-2">
                  <div className="text-xs font-semibold text-indigo-300 uppercase mb-2 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" /> AI Optimization Recommendations
                  </div>
                  <ul className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {r.recommendations.map((rec: string, idx: number) => (
                      <li key={idx} className="bg-gray-800/40 border border-gray-700/50 p-3 rounded text-xs text-gray-300 flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
