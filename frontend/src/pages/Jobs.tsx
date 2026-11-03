import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  Trash2,
  Briefcase,
  Plus,
} from 'lucide-react';
import { useJobs } from '../hooks/useJobs';
import { JobStatus } from '../types';
import api from '../services/api';
import { useQueryClient } from '@tanstack/react-query';

const Jobs = () => {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, refetch, isFetching } = useJobs({ page, page_size: 20 });
  const queryClient = useQueryClient();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDeleteJob = async (jobId: string) => {
    if (!window.confirm('Are you sure you want to delete this discovery job?')) return;
    setDeletingId(jobId);
    try {
      await api.delete(`/discovery/jobs/${jobId}`);
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    } catch (err) {
      console.error('Failed to delete job:', err);
    } finally {
      setDeletingId(null);
    }
  };

  const getStatusBadge = (status?: string) => {
    const norm = (status || 'QUEUED').toUpperCase() as JobStatus;

    const styles: Record<string, string> = {
      COMPLETED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      FAILED: 'bg-red-500/10 text-red-400 border-red-500/20',
      RUNNING: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20 animate-pulse',
      QUEUED: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      CANCELLED: 'bg-slate-800 text-slate-400 border-slate-700',
    };

    const icons: Record<string, any> = {
      COMPLETED: CheckCircle,
      FAILED: XCircle,
      RUNNING: Clock,
      QUEUED: AlertCircle,
      CANCELLED: XCircle,
    };

    const Icon = icons[norm] || Clock;
    const styleClass = styles[norm] || 'bg-slate-800 text-slate-400 border-slate-700';

    return (
      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${styleClass}`}>
        <Icon className="w-3.5 h-3.5 mr-1" />
        {norm}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 bg-[#0E1424] rounded-2xl border border-slate-800">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent" />
        <p className="text-xs text-slate-400 font-medium">Loading discovery jobs...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8 bg-red-950/40 border border-red-500/30 rounded-2xl text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-red-400 mx-auto" />
        <h3 className="text-lg font-bold text-red-200">Failed to load discovery jobs</h3>
        <p className="text-xs text-red-300 max-w-md mx-auto">
          {(error as any)?.message || 'Could not connect to the backend server. Please verify your connection.'}
        </p>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-xl text-xs font-semibold hover:bg-red-700 shadow-md"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry Now
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
              <span className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Briefcase className="w-5 h-5" />
              </span>
              Discovery Jobs Queue
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              {data?.total || 0} Total Runs
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1.5">
            Track and manage your multi-source lead extraction runs, worker task states, and enrichment yields.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="inline-flex items-center px-3.5 py-2 bg-[#0E1424] hover:bg-[#131B2E] text-slate-300 border border-slate-800 rounded-xl text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isFetching ? 'animate-spin text-indigo-400' : ''}`} />
            Refresh
          </button>

          <Link
            to="/discovery"
            className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white text-xs font-semibold rounded-xl shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            New Discovery
          </Link>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="bg-[#0E1424] rounded-2xl shadow-sm border border-slate-800 overflow-hidden">
        {data && data.items && data.items.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-800/80">
                <thead className="bg-[#131B2E]/70">
                  <tr>
                    <th className="px-6 py-3.5 text-left text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Search Query
                    </th>
                    <th className="px-6 py-3.5 text-left text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3.5 text-left text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3.5 text-left text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Results Found / Enriched
                    </th>
                    <th className="px-6 py-3.5 text-left text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Created At
                    </th>
                    <th className="px-6 py-3.5 text-right text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/70">
                  {data.items.map((job) => (
                    <tr key={job.id} className="hover:bg-[#131B2E]/60 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-bold text-white text-sm">{job.search_query}</div>
                        <div className="text-xs text-slate-400 capitalize mt-0.5">
                          Provider: <span className="font-semibold text-indigo-400">{job.provider}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-xs font-medium text-slate-300">
                        {job.location}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(job.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-xs font-bold text-white">
                          {job.total_found || 0} candidates found
                        </div>
                        <div className="text-xs font-medium text-emerald-400 mt-0.5">
                          {job.total_enriched || 0} enriched with contacts
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-400">
                        {job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-xs space-x-2">
                        <Link
                          to={`/leads?search=${encodeURIComponent(job.search_query)}`}
                          className="inline-flex items-center px-2.5 py-1.5 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 font-semibold rounded-lg border border-indigo-500/30 transition-colors"
                        >
                          <span>View Leads</span>
                          <ExternalLink className="w-3 h-3 ml-1" />
                        </Link>

                        <button
                          onClick={() => handleDeleteJob(job.id)}
                          disabled={deletingId === job.id}
                          className="inline-flex items-center px-2 py-1.5 bg-slate-800/60 hover:bg-red-500/20 text-slate-400 hover:text-red-400 font-medium rounded-lg border border-slate-700/60 transition-colors disabled:opacity-50"
                          title="Delete Job"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {(data.total_pages || 1) > 1 && (
              <div className="px-6 py-4 border-t border-slate-800 flex items-center justify-between">
                <div className="text-xs font-semibold text-slate-400">
                  Showing page {data.page} of {data.total_pages} ({data.total} total jobs)
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={data.page === 1}
                    className="px-3.5 py-1.5 text-xs font-bold text-slate-300 bg-[#131B2E] border border-slate-700 rounded-xl hover:bg-slate-800 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed transition-all inline-flex items-center"
                  >
                    &larr; Previous
                  </button>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={data.page >= (data.total_pages || 1)}
                    className="px-3.5 py-1.5 text-xs font-bold text-slate-300 bg-[#131B2E] border border-slate-700 rounded-xl hover:bg-slate-800 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed transition-all inline-flex items-center"
                  >
                    Next &rarr;
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-16">
            <Clock className="mx-auto h-12 w-12 text-slate-600" />
            <h3 className="mt-2 text-base font-bold text-white">No jobs found</h3>
            <p className="mt-1 text-xs text-slate-400">Get started by running your first discovery job.</p>
            <div className="mt-4">
              <Link
                to="/discovery"
                className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-xs font-semibold shadow-md"
              >
                Go to Discovery
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Jobs;
