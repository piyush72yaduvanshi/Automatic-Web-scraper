import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { ContactItem } from '../types';
import {
  Contact2,
  Plus,
  Search,
  Mail,
  Phone,
  Building2,
  Linkedin,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

const Contacts: React.FC = () => {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [isDecisionMaker, setIsDecisionMaker] = useState(false);
  const [companyId, setCompanyId] = useState('');

  const { data: contacts, isLoading } = useQuery<ContactItem[]>({
    queryKey: ['crm_contacts', search],
    queryFn: async () => {
      const res = await api.get(`/crm/contacts${search ? `?search=${search}` : ''}`);
      return res.data;
    },
  });

  const { data: companies } = useQuery<any[]>({
    queryKey: ['crm_companies_select'],
    queryFn: async () => {
      const res = await api.get('/crm/companies');
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (payload: any) => {
      await api.post('/crm/contacts', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm_contacts'] });
      setShowAddModal(false);
      setFirstName('');
      setLastName('');
      setEmail('');
      setPhone('');
      setJobTitle('');
      setIsDecisionMaker(false);
      setCompanyId('');
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
                <Contact2 className="w-5 h-5" />
              </span>
              Decision Makers & Contacts
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              {contacts?.length || 0} Contacts
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1.5">
            Executive directory with reachability scores, decision-maker status, and company affiliations.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all"
        >
          <Plus className="w-4 h-4" /> Add Contact
        </button>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        <input
          type="text"
          placeholder="Search by name, email, or role..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 bg-[#0E1424] border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 shadow-sm"
        />
      </div>

      {/* Contacts List */}
      <div className="bg-[#0E1424] border border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-16 text-center text-sm text-slate-400 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
            <span>Loading contacts...</span>
          </div>
        ) : contacts?.length === 0 ? (
          <div className="p-16 text-center text-slate-500 text-xs">
            No contacts recorded yet. Add one above or convert qualified leads into contacts.
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {contacts?.map((c) => (
              <div
                key={c.id}
                className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-[#131B2E]/60 transition-colors"
              >
                <div className="flex items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30 flex items-center justify-center text-xs font-bold text-indigo-300">
                    {c.first_name?.[0] || ''}
                    {c.last_name?.[0] || ''}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-white">
                        {c.first_name} {c.last_name}
                      </h3>
                      {c.is_decision_maker && (
                        <span className="text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold px-2 py-0.5 rounded-full flex items-center gap-1">
                          <ShieldCheck className="w-3 h-3 text-amber-400" /> Decision Maker
                        </span>
                      )}
                      <span className="text-[10px] bg-slate-800 text-slate-400 border border-slate-700/60 px-2 py-0.5 rounded-md">
                        {c.reachability_status || 'Verified'}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                      {c.job_title && <span className="font-medium text-slate-300">{c.job_title}</span>}
                      {c.company_name && (
                        <span className="flex items-center gap-1 text-slate-400">
                          <Building2 className="w-3.5 h-3.5 text-slate-500" /> {c.company_name}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-4 text-xs">
                  {c.email && (
                    <a
                      href={`mailto:${c.email}`}
                      className="flex items-center gap-1.5 text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-lg transition-colors"
                    >
                      <Mail className="w-3.5 h-3.5" /> {c.email}
                    </a>
                  )}
                  {c.phone && (
                    <span className="flex items-center gap-1.5 text-slate-300 bg-slate-800/80 border border-slate-700/60 px-2.5 py-1 rounded-lg">
                      <Phone className="w-3.5 h-3.5 text-slate-400" /> {c.phone}
                    </span>
                  )}
                  {c.linkedin_url && (
                    <a
                      href={c.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 text-slate-400 hover:text-indigo-400 bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 rounded-lg transition-colors"
                    >
                      <Linkedin className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Contact Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0E1424] border border-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-5 text-white">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Add New Contact
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3.5">
              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">First Name *</label>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full px-3 py-2 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">Last Name</label>
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full px-3 py-2 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Email</label>
                <input
                  type="email"
                  placeholder="contact@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Phone</label>
                <input
                  type="text"
                  placeholder="+1 (555) 000-0000"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full px-3 py-2 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Job Title</label>
                <input
                  type="text"
                  placeholder="e.g. Chief Executive Officer, VP Sales, Founder"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">Associated Company</label>
                <select
                  value={companyId}
                  onChange={(e) => setCompanyId(e.target.value)}
                  className="w-full px-3 py-2 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                >
                  <option value="">Select company (optional)...</option>
                  {companies?.map((cmp) => (
                    <option key={cmp.id} value={cmp.id}>
                      {cmp.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2 pt-1.5">
                <input
                  type="checkbox"
                  id="dm-check"
                  checked={isDecisionMaker}
                  onChange={(e) => setIsDecisionMaker(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-700 bg-[#131B2E] text-indigo-600 focus:ring-indigo-500"
                />
                <label htmlFor="dm-check" className="text-xs text-slate-300 font-medium cursor-pointer">
                  Verified Decision Maker (has budget/signing authority)
                </label>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 border border-slate-700 rounded-xl text-xs text-slate-300 hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  firstName &&
                  createMutation.mutate({
                    first_name: firstName,
                    last_name: lastName,
                    email: email || undefined,
                    phone: phone || undefined,
                    job_title: jobTitle || undefined,
                    is_decision_maker: isDecisionMaker,
                    company_id: companyId || undefined,
                  })
                }
                disabled={!firstName || createMutation.isPending}
                className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-xs font-semibold shadow-md transition-all disabled:opacity-50"
              >
                {createMutation.isPending ? 'Saving...' : 'Save Contact'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Contacts;
