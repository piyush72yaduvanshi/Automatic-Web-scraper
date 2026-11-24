import React, { useState, useEffect } from 'react';
import {
  Send,
  Plus,
  Play,
  Pause,
  RefreshCw,
  Users,
  Target,
  CornerUpLeft,
} from 'lucide-react';
import { CampaignDetailedItem } from '../types';

export const CampaignsView: React.FC = () => {
  const [campaigns, setCampaigns] = useState<CampaignDetailedItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [showEnrollModal, setShowEnrollModal] = useState<string | null>(null);
  const [enrollEmails, setEnrollEmails] = useState<string>('');
  const [message, setMessage] = useState<string | null>(null);

  // New Campaign Form
  const [newName, setNewName] = useState<string>('');
  const [newType, setNewType] = useState<string>('B2B_PROSPECTING');
  const [newDesc, setNewDesc] = useState<string>('');

  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/campaigns');
      if (res.ok) setCampaigns(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      const res = await fetch('/api/v1/campaigns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newName,
          campaign_type: newType,
          description: newDesc,
          channel: 'EMAIL',
        }),
      });
      if (res.ok) {
        setMessage('Campaign created successfully!');
        setShowCreateModal(false);
        setNewName('');
        setNewDesc('');
        fetchCampaigns();
      }
    } catch {
      setMessage('Failed to create campaign.');
    }
  };

  const handleToggleStatus = async (campId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'ACTIVE' ? 'PAUSED' : 'ACTIVE';
    try {
      const res = await fetch(`/api/v1/campaigns/${campId}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (res.ok) {
        setMessage(`Campaign status updated to ${nextStatus}.`);
        fetchCampaigns();
      }
    } catch {
      setMessage('Failed to update status.');
    }
  };

  const handleEnrollMembers = async (campId: string) => {
    const emailList = enrollEmails.split(/[\n,]+/).map((e) => e.trim()).filter((e) => e.includes('@'));
    if (emailList.length === 0) return;
    try {
      const res = await fetch(`/api/v1/campaigns/${campId}/enroll`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emails: emailList }),
      });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Enrolled ${data.enrolled} prospects! (Skipped: ${data.skipped})`);
        setShowEnrollModal(null);
        setEnrollEmails('');
        fetchCampaigns();
      }
    } catch {
      setMessage('Enrollment failed.');
    }
  };

  const filtered = selectedType === 'ALL'
    ? campaigns
    : campaigns.filter((c) => c.campaign_type === selectedType);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center bg-gray-900 border border-gray-800 p-6 rounded-xl">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Target className="w-7 h-7 text-indigo-400" />
            Campaign Management Engine
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Segment, orchestrate, and track 5 distinct campaign types with centralized compliance checks.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition"
          >
            <Plus className="w-4 h-4" />
            New Campaign
          </button>
          <button
            onClick={fetchCampaigns}
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

      {/* Filter Tabs across 5 campaign types */}
      <div className="flex gap-2 overflow-x-auto pb-2 border-b border-gray-800">
        {['ALL', 'B2B_PROSPECTING', 'NEWSLETTER', 'NURTURE', 'RE_ENGAGEMENT', 'INBOUND_FOLLOWUP'].map((t) => (
          <button
            key={t}
            onClick={() => setSelectedType(t)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap ${
              selectedType === t
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-900 hover:bg-gray-800 text-gray-400'
            }`}
          >
            {t.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Campaigns Grid */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading campaigns...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-gray-500 bg-gray-900 border border-gray-800 rounded-xl p-8">
          No campaigns found for this category. Create one above!
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filtered.map((c) => (
            <div key={c.id} className="bg-gray-900 border border-gray-800 rounded-xl p-6 flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-2">
                  <span className="px-2.5 py-0.5 text-xs font-semibold rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {c.campaign_type}
                  </span>
                  <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                    c.status === 'ACTIVE' ? 'bg-emerald-500/20 text-emerald-400' :
                    c.status === 'PAUSED' ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-700 text-gray-300'
                  }`}>
                    {c.status}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white">{c.name}</h3>
                <p className="text-xs text-gray-400 mt-1 line-clamp-2">{c.description || 'No description provided.'}</p>

                {/* Progress & Metrics */}
                <div className="grid grid-cols-4 gap-2 mt-4 pt-4 border-t border-gray-800/80 text-center">
                  <div className="bg-gray-800/40 rounded p-2">
                    <div className="text-xs text-gray-400 flex items-center justify-center gap-1">
                      <Users className="w-3 h-3" /> Enrolled
                    </div>
                    <div className="text-sm font-bold text-white mt-1">{c.total_members}</div>
                  </div>
                  <div className="bg-gray-800/40 rounded p-2">
                    <div className="text-xs text-gray-400 flex items-center justify-center gap-1">
                      <Send className="w-3 h-3" /> Sent
                    </div>
                    <div className="text-sm font-bold text-white mt-1">{c.sent_count}</div>
                  </div>
                  <div className="bg-gray-800/40 rounded p-2">
                    <div className="text-xs text-gray-400 flex items-center justify-center gap-1">
                      <CornerUpLeft className="w-3 h-3 text-emerald-400" /> Replied
                    </div>
                    <div className="text-sm font-bold text-emerald-400 mt-1">{c.replied_count}</div>
                  </div>
                  <div className="bg-gray-800/40 rounded p-2">
                    <div className="text-xs text-gray-400 flex items-center justify-center gap-1">
                      Bounced
                    </div>
                    <div className="text-sm font-bold text-rose-400 mt-1">{c.bounced_count}</div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-5 pt-3 border-t border-gray-800/80 flex justify-between items-center">
                <button
                  onClick={() => setShowEnrollModal(c.id)}
                  className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded text-xs font-medium flex items-center gap-1.5"
                >
                  <Users className="w-3.5 h-3.5" /> Enroll Leads
                </button>
                <button
                  onClick={() => handleToggleStatus(c.id, c.status)}
                  className={`px-3 py-1.5 rounded text-xs font-medium flex items-center gap-1.5 ${
                    c.status === 'ACTIVE'
                      ? 'bg-amber-900/40 hover:bg-amber-900/60 text-amber-300'
                      : 'bg-emerald-900/40 hover:bg-emerald-900/60 text-emerald-300'
                  }`}
                >
                  {c.status === 'ACTIVE' ? <><Pause className="w-3.5 h-3.5" /> Pause</> : <><Play className="w-3.5 h-3.5" /> Activate</>}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal: Create Campaign */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-md w-full">
            <h2 className="text-lg font-bold text-white mb-4">Create New Campaign</h2>
            <form onSubmit={handleCreateCampaign} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Campaign Name</label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="e.g. Q4 Solar Contractors Outreach"
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Campaign Type</label>
                <select
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                >
                  <option value="B2B_PROSPECTING">B2B Prospecting (Cold Outbound)</option>
                  <option value="NEWSLETTER">Newsletter (Permission-Based)</option>
                  <option value="NURTURE">Nurture (Opted-in Leads)</option>
                  <option value="RE_ENGAGEMENT">Re-engagement</option>
                  <option value="INBOUND_FOLLOWUP">Inbound Follow-up</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Description</label>
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Enroll Members */}
      {showEnrollModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-md w-full">
            <h2 className="text-lg font-bold text-white mb-2">Enroll Prospects</h2>
            <p className="text-xs text-gray-400 mb-4">
              Enter email addresses (one per line). All emails will automatically pass pre-flight compliance & suppression checks.
            </p>
            <textarea
              rows={6}
              value={enrollEmails}
              onChange={(e) => setEnrollEmails(e.target.value)}
              placeholder="alex@targetcorp.com&#10;sarah@innovatesoftware.io"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white font-mono"
            />
            <div className="flex justify-end gap-3 mt-4">
              <button
                type="button"
                onClick={() => setShowEnrollModal(null)}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleEnrollMembers(showEnrollModal)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold"
              >
                Validate & Enroll
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

