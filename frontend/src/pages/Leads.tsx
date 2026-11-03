import { useState, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Mail,
  Phone,
  Share2,
  ExternalLink,
  Download,
  Search,
  Zap,
  Loader2,
  Sparkles,
  X,
  Plus,
  RefreshCw,
  AlertCircle,
  Trash2,
} from 'lucide-react';
import { useLeads } from '../hooks/useLeads';
import api from '../services/api';

const Leads = () => {
  const [searchParams] = useSearchParams();
  const initialSearch = searchParams.get('search') || '';

  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({
    search: initialSearch,
    city: '',
    has_email: undefined as boolean | undefined,
    has_phone: undefined as boolean | undefined,
  });

  // Only pass non-empty filter parameters
  const queryParams = useMemo(() => {
    const p: Record<string, any> = { page, page_size: 20 };
    if (filters.search.trim()) p.search = filters.search.trim();
    if (filters.city.trim()) p.city = filters.city.trim();
    if (filters.has_email !== undefined) p.has_email = filters.has_email;
    if (filters.has_phone !== undefined) p.has_phone = filters.has_phone;
    return p;
  }, [page, filters]);

  const { data, isLoading, isError, error, refetch, isFetching } = useLeads(queryParams);

  // Quick Scan Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [scanForm, setScanForm] = useState({
    business_name: '',
    website: '',
    city: '',
    category: 'Dentist',
  });
  const [isScanningNew, setIsScanningNew] = useState(false);
  const [scanStatusMsg, setScanStatusMsg] = useState('');

  // Row-level Scanning State
  const [scanningLeadId, setScanningLeadId] = useState<string | null>(null);
  const [deletingLeadId, setDeletingLeadId] = useState<string | null>(null);

  const handleExport = () => {
    const params = new URLSearchParams();
    if (filters.search.trim()) params.append('search', filters.search.trim());
    if (filters.city.trim()) params.append('city', filters.city.trim());
    if (filters.has_email !== undefined) params.append('has_email', String(filters.has_email));
    if (filters.has_phone !== undefined) params.append('has_phone', String(filters.has_phone));

    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    window.open(`${apiUrl}/leads/export/csv?${params.toString()}`, '_blank');
  };

  // Re-scan a single row
  const handleScanRow = async (leadId: string) => {
    setScanningLeadId(leadId);
    try {
      await api.post(`/leads/${leadId}/scan`);
      await refetch();
    } catch (err) {
      console.error('Scan error:', err);
    } finally {
      setScanningLeadId(null);
    }
  };

  // Delete a single lead
  const handleDeleteRow = async (leadId: string) => {
    if (!window.confirm('Delete this lead?')) return;
    setDeletingLeadId(leadId);
    try {
      await api.delete(`/leads/${leadId}`);
      await refetch();
    } catch (err) {
      console.error('Delete error:', err);
    } finally {
      setDeletingLeadId(null);
    }
  };

  // Quick Scan New Business via Modal
  const handleQuickScanSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scanForm.business_name && !scanForm.website) return;

    setIsScanningNew(true);
    setScanStatusMsg('⚡ Initiating multi-source scan across Google Maps, Web, and AI...');

    try {
      await api.post('/leads/quick-scan', scanForm);
      setScanStatusMsg('✅ Business scanned and enriched successfully!');
      setTimeout(() => {
        setIsModalOpen(false);
        setIsScanningNew(false);
        setScanStatusMsg('');
        setScanForm({ business_name: '', website: '', city: '', category: 'Dentist' });
        refetch();
      }, 1000);
    } catch (err: any) {
      setScanStatusMsg(`❌ Error: ${err.response?.data?.detail || err.message}`);
      setIsScanningNew(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
        <p className="text-sm text-gray-500 font-medium">Loading discovered leads...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8 bg-red-50 border border-red-200 rounded-2xl text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto" />
        <h3 className="text-lg font-bold text-red-900">Failed to load leads</h3>
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
          <h1 className="text-2xl font-bold text-gray-900">Discovered Business Leads</h1>
          <p className="text-gray-600 mt-1">
            {data?.total || 0} total verified business leads with phones, emails, and social footprints
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

          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-xl shadow-sm text-sm"
          >
            <Plus className="w-4 h-4 mr-1.5" />
            ⚡ Quick Scan Business
          </button>

          <button
            onClick={handleExport}
            className="inline-flex items-center px-4 py-2 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 font-semibold text-sm shadow-sm"
          >
            <Download className="w-4 h-4 mr-1.5" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-5">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">Search</label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => {
                setPage(1);
                setFilters({ ...filters, search: e.target.value });
              }}
              placeholder="Business name or category"
              className="w-full px-3.5 py-2.5 bg-white text-gray-900 placeholder-gray-400 border border-gray-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">City</label>
            <input
              type="text"
              value={filters.city}
              onChange={(e) => {
                setPage(1);
                setFilters({ ...filters, city: e.target.value });
              }}
              placeholder="Filter by city (e.g. Lucknow, Mumbai)"
              className="w-full px-3.5 py-2.5 bg-white text-gray-900 placeholder-gray-400 border border-gray-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">Has Email</label>
            <select
              value={filters.has_email === undefined ? '' : String(filters.has_email)}
              onChange={(e) => {
                setPage(1);
                setFilters({
                  ...filters,
                  has_email: e.target.value === '' ? undefined : e.target.value === 'true',
                });
              }}
              className="w-full px-3.5 py-2.5 bg-white text-gray-900 border border-gray-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
            >
              <option value="">All</option>
              <option value="true">Yes (Verified Emails)</option>
              <option value="false">No</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1">Has Phone</label>
            <select
              value={filters.has_phone === undefined ? '' : String(filters.has_phone)}
              onChange={(e) => {
                setPage(1);
                setFilters({
                  ...filters,
                  has_phone: e.target.value === '' ? undefined : e.target.value === 'true',
                });
              }}
              className="w-full px-3.5 py-2.5 bg-white text-gray-900 border border-gray-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
            >
              <option value="">All</option>
              <option value="true">Yes (Verified Phone)</option>
              <option value="false">No</option>
            </select>
          </div>
        </div>
      </div>

      {/* Leads Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        {data && data.items && data.items.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50/80">
                  <tr>
                    <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Business Details
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Discovered Contacts
                    </th>
                    <th className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Source
                    </th>
                    <th className="px-6 py-3.5 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.items.map((lead) => (
                    <tr key={lead.id} className="hover:bg-blue-50/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-bold text-gray-900 text-sm hover:text-blue-600">
                          <Link to={`/leads/${lead.id}`}>{lead.business_name}</Link>
                        </div>
                        <div className="text-xs text-gray-500 mt-0.5">{lead.category || 'General'}</div>
                        {lead.website && (
                          <a
                            href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:text-blue-800 inline-flex items-center gap-0.5 mt-1"
                          >
                            <span>Website</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </td>

                      <td className="px-6 py-4 text-xs text-gray-900">
                        <div className="font-medium">{lead.city || 'N/A'}</div>
                        <div className="text-gray-500">{[lead.state, lead.country].filter(Boolean).join(', ')}</div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3 text-xs">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-md font-semibold ${
                              (lead.email_count || 0) > 0
                                ? 'bg-blue-100 text-blue-800'
                                : 'bg-gray-100 text-gray-500'
                            }`}
                          >
                            <Mail className="w-3.5 h-3.5 mr-1" />
                            {lead.email_count || 0}
                          </span>

                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-md font-semibold ${
                              (lead.phone_count || 0) > 0
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-gray-100 text-gray-500'
                            }`}
                          >
                            <Phone className="w-3.5 h-3.5 mr-1" />
                            {lead.phone_count || 0}
                          </span>

                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-md font-semibold ${
                              (lead.social_count || 0) > 0
                                ? 'bg-purple-100 text-purple-800'
                                : 'bg-gray-100 text-gray-500'
                            }`}
                          >
                            <Share2 className="w-3.5 h-3.5 mr-1" />
                            {lead.social_count || 0}
                          </span>
                        </div>
                      </td>

                      <td className="px-6 py-4 text-xs">
                        <span className="px-2.5 py-1 bg-slate-100 text-slate-700 font-semibold rounded-full border border-slate-200">
                          {lead.source_provider}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-right text-xs space-x-2 whitespace-nowrap">
                        <button
                          onClick={() => handleScanRow(lead.id)}
                          disabled={scanningLeadId === lead.id}
                          className="inline-flex items-center px-2.5 py-1.5 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 rounded-lg font-semibold border border-indigo-200 transition-colors disabled:opacity-50"
                        >
                          {scanningLeadId === lead.id ? (
                            <>
                              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                              Scanning...
                            </>
                          ) : (
                            <>
                              <Zap className="w-3 h-3 mr-1 text-indigo-600 fill-indigo-600" />
                              Scan
                            </>
                          )}
                        </button>

                        <Link
                          to={`/leads/${lead.id}`}
                          className="inline-flex items-center px-2.5 py-1.5 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg font-semibold border border-gray-200"
                        >
                          Details
                        </Link>

                        <button
                          onClick={() => handleDeleteRow(lead.id)}
                          disabled={deletingLeadId === lead.id}
                          className="inline-flex items-center px-2 py-1.5 bg-gray-50 hover:bg-red-50 text-gray-400 hover:text-red-600 rounded-lg border border-gray-200 transition-colors disabled:opacity-50"
                          title="Delete Lead"
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
                  Showing page {data.page} of {data.total_pages} ({data.total} total leads)
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
            <Search className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-base font-bold text-gray-900">No leads found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search filters or use "Quick Scan Business" to extract leads.
            </p>
          </div>
        )}
      </div>

      {/* Quick Scan Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-200 relative animate-in fade-in zoom-in-95">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 bg-blue-100 rounded-xl text-blue-600">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-gray-900">⚡ Instant Multi-Source Scan</h3>
                <p className="text-xs text-gray-500">Scan any business or website across Google Maps, Web, & AI.</p>
              </div>
            </div>

            <form onSubmit={handleQuickScanSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Business Name *</label>
                <input
                  type="text"
                  required
                  value={scanForm.business_name}
                  onChange={(e) => setScanForm({ ...scanForm, business_name: e.target.value })}
                  placeholder="e.g. Apex Dental Hospital"
                  className="w-full px-3.5 py-2 border border-gray-300 rounded-xl text-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Website URL (Optional)</label>
                <input
                  type="text"
                  value={scanForm.website}
                  onChange={(e) => setScanForm({ ...scanForm, website: e.target.value })}
                  placeholder="https://example.com"
                  className="w-full px-3.5 py-2 border border-gray-300 rounded-xl text-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">City / Region</label>
                  <input
                    type="text"
                    value={scanForm.city}
                    onChange={(e) => setScanForm({ ...scanForm, city: e.target.value })}
                    placeholder="e.g. Lucknow"
                    className="w-full px-3.5 py-2 border border-gray-300 rounded-xl text-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Category</label>
                  <input
                    type="text"
                    value={scanForm.category}
                    onChange={(e) => setScanForm({ ...scanForm, category: e.target.value })}
                    placeholder="e.g. Dentist"
                    className="w-full px-3.5 py-2 border border-gray-300 rounded-xl text-sm focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {scanStatusMsg && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-800 font-medium">
                  {scanStatusMsg}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-xl text-sm font-semibold hover:bg-gray-50"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={isScanningNew}
                  className="inline-flex items-center px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold shadow-md disabled:opacity-50"
                >
                  {isScanningNew ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Scanning Sources...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 mr-1.5 fill-white" />
                      Start Instant Scan
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Leads;