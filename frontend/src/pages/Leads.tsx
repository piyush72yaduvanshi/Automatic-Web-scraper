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
    if (!scanForm.business_name.trim()) return;

    setIsScanningNew(true);
    setScanStatusMsg('Scanning website, Google Maps, and AI verification...');

    try {
      const res = await api.post('/leads/scan-new', scanForm);
      setScanStatusMsg(`Discovery completed: "${res.data.business_name}" saved!`);
      await refetch();
      setTimeout(() => {
        setIsModalOpen(false);
        setScanStatusMsg('');
        setScanForm({ business_name: '', website: '', city: '', category: 'Dentist' });
      }, 1500);
    } catch (err: any) {
      setScanStatusMsg(`Scan error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsScanningNew(false);
    }
  };

  if (isError) {
    return (
      <div className="p-8 bg-red-950/40 border border-red-500/30 rounded-2xl text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-red-400 mx-auto" />
        <h3 className="text-lg font-bold text-red-200">Failed to load leads</h3>
        <p className="text-sm text-red-300 max-w-md mx-auto">
          {(error as any)?.message || 'Could not connect to the backend server. Please verify your connection.'}
        </p>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-semibold hover:bg-red-700 shadow-md"
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
                <Search className="w-5 h-5" />
              </span>
              Discovered Business Leads
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              {data?.total || 0} Total Leads
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1.5">
            Verified business leads with enriched phones, emails, decision-maker profiles, and social footprints.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="inline-flex items-center px-3.5 py-2 bg-[#0E1424] hover:bg-[#131B2E] text-slate-300 border border-slate-800 rounded-xl text-xs font-semibold shadow-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isFetching ? 'animate-spin text-indigo-400' : ''}`} />
            Refresh
          </button>

          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white font-semibold rounded-xl text-xs shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all"
          >
            <Plus className="w-3.5 h-3.5 mr-1.5" />
            Quick Scan Business
          </button>

          <button
            onClick={handleExport}
            className="inline-flex items-center px-3.5 py-2 bg-emerald-600/90 hover:bg-emerald-600 text-white rounded-xl font-semibold text-xs shadow-md transition-colors"
          >
            <Download className="w-3.5 h-3.5 mr-1.5" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="bg-[#0E1424] rounded-2xl shadow-sm border border-slate-800 p-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Search</label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => {
                setPage(1);
                setFilters({ ...filters, search: e.target.value });
              }}
              placeholder="Business name or category..."
              className="w-full px-3.5 py-2.5 bg-[#131B2E] text-white placeholder-slate-500 border border-slate-700 rounded-xl text-xs font-medium focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">City</label>
            <input
              type="text"
              value={filters.city}
              onChange={(e) => {
                setPage(1);
                setFilters({ ...filters, city: e.target.value });
              }}
              placeholder="Filter by city (e.g. Lucknow, Austin)..."
              className="w-full px-3.5 py-2.5 bg-[#131B2E] text-white placeholder-slate-500 border border-slate-700 rounded-xl text-xs font-medium focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Has Email</label>
            <select
              value={filters.has_email === undefined ? '' : String(filters.has_email)}
              onChange={(e) => {
                setPage(1);
                setFilters({
                  ...filters,
                  has_email: e.target.value === '' ? undefined : e.target.value === 'true',
                });
              }}
              className="w-full px-3.5 py-2.5 bg-[#131B2E] text-white border border-slate-700 rounded-xl text-xs font-medium focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-sm"
            >
              <option value="">All</option>
              <option value="true">Yes (Verified Emails)</option>
              <option value="false">No</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">Has Phone</label>
            <select
              value={filters.has_phone === undefined ? '' : String(filters.has_phone)}
              onChange={(e) => {
                setPage(1);
                setFilters({
                  ...filters,
                  has_phone: e.target.value === '' ? undefined : e.target.value === 'true',
                });
              }}
              className="w-full px-3.5 py-2.5 bg-[#131B2E] text-white border border-slate-700 rounded-xl text-xs font-medium focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-sm"
            >
              <option value="">All</option>
              <option value="true">Yes (Verified Phone)</option>
              <option value="false">No</option>
            </select>
          </div>
        </div>
      </div>

      {/* Leads Table */}
      <div className="bg-[#0E1424] rounded-2xl shadow-sm border border-slate-800 overflow-hidden">
        {isLoading ? (
          <div className="p-16 text-center text-sm text-slate-400 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
            <span>Synchronizing business directory...</span>
          </div>
        ) : data && data.items && data.items.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-800/80">
                <thead className="bg-[#131B2E]/70">
                  <tr>
                    <th className="px-6 py-3.5 text-left text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Business Details
                    </th>
                    <th className="px-6 py-3.5 text-left text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Location
                    </th>
                    <th className="px-6 py-3.5 text-left text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Discovered Contacts
                    </th>
                    <th className="px-6 py-3.5 text-left text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Source
                    </th>
                    <th className="px-6 py-3.5 text-right text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/70">
                  {data.items.map((lead) => (
                    <tr key={lead.id} className="hover:bg-[#131B2E]/60 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-bold text-white text-sm hover:text-indigo-400 transition-colors">
                          <Link to={`/leads/${lead.id}`}>{lead.business_name}</Link>
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">{lead.category || 'General Business'}</div>
                        {lead.website && (
                          <a
                            href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[11px] text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-1 mt-1 transition-colors"
                          >
                            <span>Website</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        )}
                      </td>

                      <td className="px-6 py-4 text-xs text-slate-300">
                        <div className="font-medium text-white">{lead.city || 'N/A'}</div>
                        <div className="text-slate-400 text-[11px]">
                          {[lead.state, lead.country].filter(Boolean).join(', ')}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 text-xs">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-md font-semibold text-[11px] ${
                              (lead.email_count || 0) > 0
                                ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                                : 'bg-slate-800 text-slate-500'
                            }`}
                          >
                            <Mail className="w-3 h-3 mr-1" />
                            {lead.email_count || 0}
                          </span>

                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-md font-semibold text-[11px] ${
                              (lead.phone_count || 0) > 0
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-slate-800 text-slate-500'
                            }`}
                          >
                            <Phone className="w-3 h-3 mr-1" />
                            {lead.phone_count || 0}
                          </span>

                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-md font-semibold text-[11px] ${
                              (lead.social_count || 0) > 0
                                ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                                : 'bg-slate-800 text-slate-500'
                            }`}
                          >
                            <Share2 className="w-3 h-3 mr-1" />
                            {lead.social_count || 0}
                          </span>
                        </div>
                      </td>

                      <td className="px-6 py-4 text-xs">
                        <span className="px-2.5 py-1 bg-slate-800 text-slate-300 font-semibold rounded-full border border-slate-700/80 text-[10px]">
                          {lead.source_provider}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-right text-xs space-x-2 whitespace-nowrap">
                        <button
                          onClick={() => handleScanRow(lead.id)}
                          disabled={scanningLeadId === lead.id}
                          className="inline-flex items-center px-2.5 py-1.5 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 rounded-lg font-semibold border border-indigo-500/30 transition-colors disabled:opacity-50"
                        >
                          {scanningLeadId === lead.id ? (
                            <>
                              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                              Scanning...
                            </>
                          ) : (
                            <>
                              <Zap className="w-3 h-3 mr-1 text-indigo-400 fill-indigo-400" />
                              Scan
                            </>
                          )}
                        </button>

                        <Link
                          to={`/leads/${lead.id}`}
                          className="inline-flex items-center px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-semibold border border-slate-700/80 transition-colors"
                        >
                          Details
                        </Link>

                        <button
                          onClick={() => handleDeleteRow(lead.id)}
                          disabled={deletingLeadId === lead.id}
                          className="inline-flex items-center px-2 py-1.5 bg-slate-800/60 hover:bg-red-500/20 text-slate-400 hover:text-red-400 rounded-lg border border-slate-700/60 transition-colors disabled:opacity-50"
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
              <div className="px-6 py-4 border-t border-slate-800 flex items-center justify-between">
                <div className="text-xs font-semibold text-slate-400">
                  Showing page {data.page} of {data.total_pages} ({data.total} total leads)
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
            <Search className="mx-auto h-12 w-12 text-slate-600" />
            <h3 className="mt-2 text-base font-bold text-white">No leads found</h3>
            <p className="mt-1 text-xs text-slate-400">
              Try adjusting your search filters or use "Quick Scan Business" to extract leads.
            </p>
          </div>
        )}
      </div>

      {/* Quick Scan Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4">
          <div className="bg-[#0E1424] rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-800 relative animate-in fade-in zoom-in-95 text-white">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 mb-5 border-b border-slate-800/80 pb-4">
              <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Instant Multi-Source Scan</h3>
                <p className="text-xs text-slate-400">Scan any business or website across Google Maps, Web, & AI.</p>
              </div>
            </div>

            <form onSubmit={handleQuickScanSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Business Name *</label>
                <input
                  type="text"
                  required
                  value={scanForm.business_name}
                  onChange={(e) => setScanForm({ ...scanForm, business_name: e.target.value })}
                  placeholder="e.g. Apex Dental Hospital"
                  className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Website URL (Optional)</label>
                <input
                  type="text"
                  value={scanForm.website}
                  onChange={(e) => setScanForm({ ...scanForm, website: e.target.value })}
                  placeholder="https://example.com"
                  className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">City / Region</label>
                  <input
                    type="text"
                    value={scanForm.city}
                    onChange={(e) => setScanForm({ ...scanForm, city: e.target.value })}
                    placeholder="e.g. Lucknow"
                    className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">Category</label>
                  <input
                    type="text"
                    value={scanForm.category}
                    onChange={(e) => setScanForm({ ...scanForm, category: e.target.value })}
                    placeholder="e.g. Dentist"
                    className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {scanStatusMsg && (
                <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-xs text-indigo-300 font-medium">
                  {scanStatusMsg}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-slate-700 rounded-xl text-xs font-semibold text-slate-300 hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={isScanningNew}
                  className="inline-flex items-center px-5 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-xs font-semibold shadow-md transition-all disabled:opacity-50"
                >
                  {isScanningNew ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" />
                      Scanning Sources...
                    </>
                  ) : (
                    <>
                      <Zap className="w-3.5 h-3.5 mr-1.5 fill-white" />
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
