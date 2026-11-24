import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { CompanyItem } from '../types';
import {
  Building2,
  Plus,
  Search,
  Users,
  Briefcase,
  MapPin,
  Globe,
  Sparkles,
} from 'lucide-react';

const Companies: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [name, setName] = useState('');
  const [domain, setDomain] = useState('');
  const [industry, setIndustry] = useState('');
  const [location, setLocation] = useState('');

  const { data: companies, isLoading } = useQuery<CompanyItem[]>({
    queryKey: ['crm_companies', search],
    queryFn: async () => {
      const res = await api.get(`/crm/companies${search ? `?search=${search}` : ''}`);
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (payload: any) => {
      await api.post('/crm/companies', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm_companies'] });
      setShowCreateModal(false);
      setName('');
      setDomain('');
      setIndustry('');
      setLocation('');
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
              <span className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Building2 className="w-5 h-5" />
              </span>
              Companies & Accounts
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              {companies?.length || 0} Accounts
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1.5">
            Accounts managed in the CRM with contact linkages, deals, and activity histories.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all"
        >
          <Plus className="w-4 h-4" /> Add Company
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        <input
          type="text"
          placeholder="Search by company name or domain..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-[#0E1424] border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-sm"
        />
      </div>

      {/* Companies List */}
      <div className="bg-[#0E1424] border border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-16 text-center text-sm text-slate-400 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
            <span>Loading accounts...</span>
          </div>
        ) : companies?.length === 0 ? (
          <div className="p-16 text-center text-slate-500 text-xs">
            No companies found. Create one above or convert an enriched lead from the Leads Directory.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {companies?.map((c) => (
              <div
                key={c.id}
                className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-[#131B2E]/60 transition-colors"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2.5">
                    <h3 className="text-sm font-bold text-white tracking-tight">{c.name}</h3>
                    <span className="text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded-full">
                      {c.status || 'Active'}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                    {c.domain && (
                      <span className="flex items-center gap-1 text-slate-300">
                        <Globe className="w-3.5 h-3.5 text-indigo-400" /> {c.domain}
                      </span>
                    )}
                    {c.industry && (
                      <span className="bg-slate-800/80 text-indigo-300 border border-slate-700/60 px-2 py-0.5 rounded-md text-[11px] font-medium">
                        {c.industry}
                      </span>
                    )}
                    {c.location && (
                      <span className="flex items-center gap-1 text-slate-400">
                        <MapPin className="w-3.5 h-3.5 text-slate-500" /> {c.location}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-5 text-xs text-slate-400">
                  <div className="flex items-center gap-1.5 bg-[#131B2E] border border-slate-800 px-2.5 py-1 rounded-lg">
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-slate-300 font-semibold">{c.contacts_count}</span>
                    <span className="text-[11px] text-slate-500">contacts</span>
                  </div>
                  <div className="flex items-center gap-1.5 bg-[#131B2E] border border-slate-800 px-2.5 py-1 rounded-lg">
                    <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-slate-300 font-semibold">{c.deals_count}</span>
                    <span className="text-[11px] text-slate-500">deals</span>
                  </div>
                  <span className="text-slate-500 text-[11px] hidden md:inline">
                    Added {new Date(c.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Company Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0E1424] border border-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-5 text-white">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Add New Company Account
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Company Name *</label>
                <input
                  type="text"
                  placeholder="e.g. Acme Corporation"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Domain or Website</label>
                <input
                  type="text"
                  placeholder="e.g. acme.com"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Industry</label>
                <input
                  type="text"
                  placeholder="e.g. Healthcare, SaaS, Logistics"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Location</label>
                <input
                  type="text"
                  placeholder="e.g. Bangalore, India"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 border border-slate-700 rounded-xl text-xs text-slate-300 hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => name && createMutation.mutate({ name, domain, industry, location })}
                disabled={!name || createMutation.isPending}
                className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-xs font-semibold shadow-md transition-all disabled:opacity-50"
              >
                {createMutation.isPending ? 'Saving...' : 'Save Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Companies;
