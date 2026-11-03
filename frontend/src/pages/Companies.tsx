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
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Building2 className="w-6 h-6 text-blue-600" />
            Companies & Accounts
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Accounts managed in the CRM with contact linkages, deals, and activity histories.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold shadow-sm"
        >
          <Plus className="w-4 h-4" /> Add Company
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        <input
          type="text"
          placeholder="Search by company name or domain..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-xs focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Companies List */}
      <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading companies...</div>
        ) : companies?.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            No companies found. Create one above or convert an enriched lead from the Leads Directory.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {companies?.map((c) => (
              <div key={c.id} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/60">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-slate-900">{c.name}</h3>
                    <span className="text-[10px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                      {c.status}
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                    {c.domain && (
                      <span className="flex items-center gap-1">
                        <Globe className="w-3.5 h-3.5 text-slate-400" /> {c.domain}
                      </span>
                    )}
                    {c.industry && (
                      <span className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded text-[11px] font-medium">
                        {c.industry}
                      </span>
                    )}
                    {c.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" /> {c.location}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-4 text-xs text-slate-600">
                  <div className="flex items-center gap-1">
                    <Users className="w-4 h-4 text-slate-400" />
                    <span>{c.contacts_count} contacts</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Briefcase className="w-4 h-4 text-slate-400" />
                    <span>{c.deals_count} deals</span>
                  </div>
                  <span className="text-slate-400 text-[11px]">Added {new Date(c.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Company Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Add New Company</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Company Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Domain or Website</label>
                <input
                  type="text"
                  placeholder="e.g. acme.com"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Industry</label>
                <input
                  type="text"
                  placeholder="e.g. Healthcare, Software, Retail"
                  value={industry}
                  onChange={(e) => setIndustry(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Location</label>
                <input
                  type="text"
                  placeholder="e.g. Bangalore, India"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <button onClick={() => setShowCreateModal(false)} className="px-3 py-1.5 border rounded text-xs text-slate-700">
                Cancel
              </button>
              <button
                onClick={() => name && createMutation.mutate({ name, domain, industry, location })}
                disabled={!name || createMutation.isPending}
                className="px-4 py-1.5 bg-blue-600 text-white rounded text-xs font-semibold hover:bg-blue-700"
              >
                Save Account
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Companies;
