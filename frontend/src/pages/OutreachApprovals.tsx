import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { OutreachApprovalItem, CampaignItem } from '../types';
import {
  Send,
  CheckCircle2,
  XCircle,
  Edit3,
  ShieldAlert,
  Mail,
  MessageCircle,
  Ban,
  Sparkles,
} from 'lucide-react';

const OutreachApprovals: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'approvals' | 'campaigns' | 'suppression'>('approvals');
  const [statusFilter, setStatusFilter] = useState<string>('PENDING');

  // Edit modal state
  const [editingItem, setEditingItem] = useState<OutreachApprovalItem | null>(null);
  const [editSubject, setEditSubject] = useState('');
  const [editBody, setEditBody] = useState('');

  // Rejection modal
  const [rejectingItem, setRejectingItem] = useState<OutreachApprovalItem | null>(null);
  const [rejectReason, setRejectReason] = useState('Prospect not an immediate fit');

  // New Suppression
  const [suppressInput, setSuppressInput] = useState('');

  // 1. Fetch Approvals
  const { data: approvals, isLoading: loadingApprovals } = useQuery<OutreachApprovalItem[]>({
    queryKey: ['outreach_approvals', statusFilter],
    queryFn: async () => {
      const res = await api.get(`/outreach/approvals${statusFilter ? `?status=${statusFilter}` : ''}`);
      return res.data;
    },
    refetchInterval: 8000,
  });

  // 2. Fetch Campaigns
  const { data: campaigns } = useQuery<CampaignItem[]>({
    queryKey: ['outreach_campaigns'],
    queryFn: async () => {
      const res = await api.get('/outreach/campaigns');
      return res.data;
    },
    enabled: activeTab === 'campaigns',
  });

  // 3. Fetch Suppression
  const { data: suppressionList, refetch: refetchSuppression } = useQuery<any[]>({
    queryKey: ['outreach_suppression'],
    queryFn: async () => {
      const res = await api.get('/outreach/suppression');
      return res.data;
    },
    enabled: activeTab === 'suppression',
  });

  // Mutations
  const approveMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post(`/outreach/approvals/${id}/approve`);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['outreach_approvals'] });
      alert(data.message || 'Approved and sent successfully!');
    },
    onError: (err: any) => {
      alert(`Approval execution failed: ${err.response?.data?.detail || err.message}`);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      await api.post(`/outreach/approvals/${id}/reject`, { reason });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['outreach_approvals'] });
      setRejectingItem(null);
    },
  });

  const editMutation = useMutation({
    mutationFn: async ({ id, subject, body }: { id: string; subject: string; body: string }) => {
      await api.patch(`/outreach/approvals/${id}`, { subject, body_content: body });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['outreach_approvals'] });
      setEditingItem(null);
    },
  });

  const addSuppressionMutation = useMutation({
    mutationFn: async (recipient: string) => {
      await api.post('/outreach/suppression', { recipient, channel: 'ALL', reason: 'MANUAL_USER_ADD' });
    },
    onSuccess: () => {
      setSuppressInput('');
      refetchSuppression();
    },
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Send className="w-6 h-6 text-blue-600" />
            Outreach Campaigns & Human Approval Queue
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Strict human-in-the-loop safeguards. AI generates drafts; real external sending requires your review.
          </p>
        </div>

        {/* Tab selection */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('approvals')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              activeTab === 'approvals' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Approval Queue
          </button>
          <button
            onClick={() => setActiveTab('campaigns')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              activeTab === 'campaigns' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Campaigns
          </button>
          <button
            onClick={() => setActiveTab('suppression')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              activeTab === 'suppression' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Suppression List
          </button>
        </div>
      </div>

      {/* Tab: Approval Queue */}
      {activeTab === 'approvals' && (
        <div className="space-y-4">
          {/* Status Filter Tabs */}
          <div className="flex items-center gap-2">
            {['PENDING', 'SENT', 'REJECTED', 'FAILED', ''].map((st) => (
              <button
                key={st || 'ALL'}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                  statusFilter === st
                    ? 'bg-blue-600 border-blue-600 text-white font-semibold'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                {st || 'ALL'}
              </button>
            ))}
          </div>

          {loadingApprovals ? (
            <div className="p-8 text-center text-sm text-slate-500 bg-white rounded-lg border">Loading approval items...</div>
          ) : approvals?.length === 0 ? (
            <div className="p-12 text-center bg-white rounded-lg border border-slate-200">
              <ShieldAlert className="w-10 h-10 text-slate-400 mx-auto mb-2" />
              <h3 className="text-sm font-semibold text-slate-800">No items in queue with status '{statusFilter || 'ALL'}'</h3>
              <p className="text-xs text-slate-500 mt-1">
                When you click "Draft Outreach" on a lead or run a workflow, generated drafts appear here for review.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {approvals?.map((item) => (
                <div key={item.id} className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:border-slate-300 transition-all">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3 mb-3">
                    <div className="flex items-center gap-2">
                      <span className="p-1.5 rounded bg-blue-50 text-blue-600">
                        {item.action_type.includes('EMAIL') ? <Mail className="w-4 h-4" /> : <MessageCircle className="w-4 h-4" />}
                      </span>
                      <span className="text-xs font-semibold text-slate-900">{item.action_type}</span>
                      <span className="text-xs text-slate-400">•</span>
                      <span className="text-xs text-slate-600 font-medium">To: {item.recipient_name} ({item.recipient_destination})</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                          item.status === 'PENDING'
                            ? 'bg-amber-100 text-amber-800'
                            : item.status === 'SENT'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {item.status}
                      </span>
                      <span className="text-[11px] text-slate-400">Created: {new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {item.subject && (
                    <div className="mb-2 text-xs">
                      <strong className="text-slate-700">Subject:</strong> <span className="text-slate-900 font-medium">{item.subject}</span>
                    </div>
                  )}

                  <div className="bg-slate-50 p-3.5 rounded-md text-xs text-slate-800 whitespace-pre-wrap font-sans border border-slate-100 mb-3">
                    {item.body_content}
                  </div>

                  {item.evidence_context && (
                    <div className="text-[11px] text-slate-500 bg-blue-50/60 border border-blue-100 p-2 rounded mb-3 flex items-start gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-blue-500 flex-shrink-0 mt-0.5" />
                      <span>{item.evidence_context}</span>
                    </div>
                  )}

                  {/* Actions Bar */}
                  {item.status === 'PENDING' && (
                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                      <button
                        onClick={() => {
                          setEditingItem(item);
                          setEditSubject(item.subject || '');
                          setEditBody(item.body_content);
                        }}
                        className="inline-flex items-center gap-1 px-3 py-1.5 border border-slate-300 rounded text-xs font-medium text-slate-700 hover:bg-slate-50"
                      >
                        <Edit3 className="w-3.5 h-3.5" /> Edit Draft
                      </button>
                      <button
                        onClick={() => setRejectingItem(item)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 border border-rose-200 text-rose-700 hover:bg-rose-50 rounded text-xs font-medium"
                      >
                        <XCircle className="w-3.5 h-3.5" /> Reject
                      </button>
                      <button
                        onClick={() => approveMutation.mutate(item.id)}
                        disabled={approveMutation.isPending}
                        className="inline-flex items-center gap-1 px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold shadow-sm"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" /> Approve & Send
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab: Campaigns */}
      {activeTab === 'campaigns' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-semibold text-slate-800">Multi-Touch Outreach Campaigns</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {campaigns?.map((c) => (
              <div key={c.id} className="bg-white border rounded-lg p-5 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-slate-900">{c.name}</h4>
                  <span className="text-[11px] bg-blue-50 text-blue-700 font-semibold px-2 py-0.5 rounded-full">{c.channel}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs py-2 bg-slate-50 rounded">
                  <div>
                    <span className="text-slate-400 block text-[10px]">PROSPECTS</span>
                    <span className="font-bold text-slate-800">{c.total_prospects}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">SENT</span>
                    <span className="font-bold text-slate-800">{c.sent_count}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">REPLIES</span>
                    <span className="font-bold text-emerald-600">{c.replied_count}</span>
                  </div>
                </div>
                <div className="text-xs text-slate-500 flex justify-between">
                  <span>{c.steps_count} sequence step(s)</span>
                  <span>Created: {new Date(c.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Suppression List */}
      {activeTab === 'suppression' && (
        <div className="space-y-4">
          <div className="bg-white p-4 border rounded-lg shadow-sm space-y-3">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
              <Ban className="w-4 h-4 text-rose-600" /> Add to Global Suppression
            </h3>
            <p className="text-xs text-slate-500">
              Suppressed emails and numbers are strictly blocked from all automated and manual outreach.
            </p>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Email address or E.164 phone to suppress..."
                value={suppressInput}
                onChange={(e) => setSuppressInput(e.target.value)}
                className="flex-1 px-3 py-2 border rounded-md text-xs focus:ring-1 focus:ring-blue-500"
              />
              <button
                onClick={() => suppressInput && addSuppressionMutation.mutate(suppressInput)}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-md text-xs font-semibold"
              >
                Suppress Recipient
              </button>
            </div>
          </div>

          <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
            <div className="p-4 border-b bg-slate-50 text-xs font-semibold text-slate-700">Suppression Registry ({suppressionList?.length || 0})</div>
            <div className="divide-y divide-slate-100 text-xs">
              {suppressionList?.map((s) => (
                <div key={s.id} className="p-3.5 flex justify-between items-center">
                  <span className="font-mono text-slate-900">{s.recipient}</span>
                  <div className="flex items-center gap-3 text-slate-500 text-[11px]">
                    <span className="bg-slate-100 px-2 py-0.5 rounded">{s.reason}</span>
                    <span>{new Date(s.opted_out_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Edit Draft Modal */}
      {editingItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-xl w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Edit Outreach Draft</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Subject</label>
                <input
                  type="text"
                  value={editSubject}
                  onChange={(e) => setEditSubject(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Email / Message Body</label>
                <textarea
                  rows={8}
                  value={editBody}
                  onChange={(e) => setEditBody(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs font-mono"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <button onClick={() => setEditingItem(null)} className="px-3 py-1.5 border rounded text-xs text-slate-700">
                Cancel
              </button>
              <button
                onClick={() => editMutation.mutate({ id: editingItem.id, subject: editSubject, body: editBody })}
                className="px-4 py-1.5 bg-blue-600 text-white rounded text-xs font-semibold hover:bg-blue-700"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Reason Modal */}
      {rejectingItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Reject Outreach Item</h3>
            <p className="text-xs text-slate-500">Provide an audit reason for rejecting this outbound communication draft:</p>
            <input
              type="text"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              className="w-full px-3 py-2 border rounded text-xs"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setRejectingItem(null)} className="px-3 py-1.5 border rounded text-xs text-slate-700">
                Cancel
              </button>
              <button
                onClick={() => rejectMutation.mutate({ id: rejectingItem.id, reason: rejectReason })}
                className="px-4 py-1.5 bg-rose-600 text-white rounded text-xs font-semibold hover:bg-rose-700"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OutreachApprovals;
