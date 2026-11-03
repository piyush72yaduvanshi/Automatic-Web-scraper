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
      COMPLETED: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      FAILED: 'bg-red-100 text-red-800 border-red-200',
      RUNNING: 'bg-blue-100 text-blue-800 border-blue-200 animate-pulse',
      QUEUED: 'bg-amber-100 text-amber-800 border-amber-200',
      CANCELLED: 'bg-gray-100 text-gray-800 border-gray-200',
    };

    const icons: Record<string, any> = {
      COMPLETED: CheckCircle,
      FAILED: XCircle,
      RUNNING: Clock,
      QUEUED: AlertCircle,
      CANCELLED: XCircle,
    };

    const Icon = icons[norm] || Clock;
    const styleClass = styles[norm] || 'bg-gray-100 text-gray-800 border-gray-200';

    return (
      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${styleClass}`}>
        <Icon className="w-3.5 h-3.5 mr-1" />
        {norm}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
        <p className="text-sm text-gray-500 font-medium">Loading discovery jobs...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8 bg-red-50 border border-red-200 rounded-2xl text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
        <h3 className="text-lg font-bold text-red-900">Failed to load discovery jobs</h3>
        <p className="text-sm text-red-700 max-w-md mx-auto">
          {(error as any)?.message || 'Could not connect to the backend server. Please verify your connection.'}
        </p>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-semibold hover:bg-red-700"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry Now
        </button>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-0 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Discovery Jobs</h1>
          <p className="text-gray-600 mt-1">
            Track and manage your multi-source lead extraction runs ({data?.total || 0} total)
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="inline-flex items-center px-3.5 py-2 bg-white text-gray-700 border border-gray-300 rounded-xl hover:bg-gray-50 text-sm font-semibold shadow-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-1.5 ${isFetching ? 'animate-spin text-blue-600' : ''}`} />
            Refresh
          </button>

          <Link
            to="/discovery"
            className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-xl shadow-sm"
          >
            <Briefcase className="w-4 h-4 mr-1.5" />
            + New Discovery
          </Link>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        {data && data.items && data.items.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50/80">
                  <tr>
                    <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Search Query
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Results Found / Enriched
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Created At
                    </th>
                    <th className="px-6 py-3.5 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.items.map((job) => (
                    <tr key={job.id} className="hover:bg-blue-50/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-bold text-gray-900 text-sm">{job.search_query}</div>
                        <div className="text-xs text-gray-500 capitalize mt-0.5">
                          Provider: <span className="font-semibold text-gray-700">{job.provider}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-xs font-medium text-gray-800">
                        {job.location}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(job.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-xs font-bold text-gray-900">
                          {job.total_found || 0} candidates found
                        </div>
                        <div className="text-xs font-medium text-emerald-600 mt-0.5">
                          ✅ {job.total_enriched || 0} enriched with contacts
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                        {job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-xs space-x-2">
                        <Link
                          to={`/leads?search=${encodeURIComponent(job.search_query)}`}
                          className="inline-flex items-center px-2.5 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold rounded-lg border border-blue-200 transition-colors"
                        >
                          <span>View Leads</span>
                          <ExternalLink className="w-3 h-3 ml-1" />
                        </Link>

                        <button
                          onClick={() => handleDeleteJob(job.id)}
                          disabled={deletingId === job.id}
                          className="inline-flex items-center px-2 py-1.5 bg-gray-50 hover:bg-red-50 text-gray-500 hover:text-red-600 font-medium rounded-lg border border-gray-200 transition-colors disabled:opacity-50"
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
              <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                <div className="text-xs font-semibold text-gray-700">
                  Showing page {data.page} of {data.total_pages} ({data.total} total jobs)
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={data.page === 1}
                    className="px-4 py-2 text-xs font-bold text-gray-900 bg-white border border-gray-300 rounded-xl hover:bg-gray-100 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed transition-all inline-flex items-center"
                  >
                    &larr; Previous
                  </button>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={data.page >= (data.total_pages || 1)}
                    className="px-4 py-2 text-xs font-bold text-gray-900 bg-white border border-gray-300 rounded-xl hover:bg-gray-100 shadow-sm disabled:opacity-40 disabled:cursor-not-allowed transition-all inline-flex items-center"
                  >
                    Next &rarr;
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-16">
            <Clock className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-base font-bold text-gray-900">No jobs found</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by running your first discovery job.</p>
            <div className="mt-4">
              <Link
                to="/discovery"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700"
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