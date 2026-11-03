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
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Contact2 className="w-6 h-6 text-blue-600" />
            Decision Makers & Contacts
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            People directory with reachability scores, decision-maker status, and company affiliations.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold shadow-sm"
        >
          <Plus className="w-4 h-4" /> Add Contact
        </button>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
        <input
          type="text"
          placeholder="Search by name, email, or role..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-md text-xs focus:ring-1 focus:ring-blue-500"
        />
      </div>

      {/* Contacts List */}
      <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading contacts...</div>
        ) : contacts?.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            No contacts recorded yet. Add one above or convert qualified leads into contacts.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {contacts?.map((c) => (
              <div key={c.id} className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/60">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-slate-900">
                      {c.first_name} {c.last_name}
                    </h3>
                    {c.is_decision_maker && (
                      <span className="text-[10px] bg-amber-100 text-amber-800 font-semibold px-2 py-0.5 rounded-full flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3" /> Decision Maker
                      </span>
                    )}
                    <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                      {c.reachability_status}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
                    {c.job_title && <span className="font-medium text-slate-700">{c.job_title}</span>}
                    {c.company_name && (
                      <span className="flex items-center gap-1 text-slate-500">
                        <Building2 className="w-3.5 h-3.5 text-slate-400" /> {c.company_name}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-4 text-xs">
                  {c.email && (
                    <a
                      href={`mailto:${c.email}`}
                      className="flex items-center gap-1 text-blue-600 hover:text-blue-800"
                    >
                      <Mail className="w-3.5 h-3.5" /> {c.email}
                    </a>
                  )}
                  {c.phone && (
                    <span className="flex items-center gap-1 text-slate-600">
                      <Phone className="w-3.5 h-3.5 text-slate-400" /> {c.phone}
                    </span>
                  )}
                  {c.linkedin_url && (
                    <a
                      href={c.linkedin_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-slate-400 hover:text-blue-600"
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
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Add New Contact</h3>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">First Name</label>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full px-3 py-2 border rounded text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Last Name</label>
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full px-3 py-2 border rounded text-xs"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Phone</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Job Title</label>
                <input
                  type="text"
                  placeholder="e.g. Chief Executive Officer, CTO, Partner"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Company</label>
                <select
                  value={companyId}
                  onChange={(e) => setCompanyId(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                >
                  <option value="">Select company (optional)...</option>
                  {companies?.map((cmp) => (
                    <option key={cmp.id} value={cmp.id}>
                      {cmp.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="dm-check"
                  checked={isDecisionMaker}
                  onChange={(e) => setIsDecisionMaker(e.target.checked)}
                  className="rounded text-blue-600"
                />
                <label htmlFor="dm-check" className="text-xs text-slate-700 font-medium">
                  Verified Decision Maker (has budget authority)
                </label>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <button onClick={() => setShowAddModal(false)} className="px-3 py-1.5 border rounded text-xs text-slate-700">
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
                className="px-4 py-1.5 bg-blue-600 text-white rounded text-xs font-semibold hover:bg-blue-700"
              >
                Save Contact
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Contacts;
