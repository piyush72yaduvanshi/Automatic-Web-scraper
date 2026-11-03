import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Mail,
  Globe,
  Power,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Send,
  CornerUpLeft,
} from 'lucide-react';
import { EmailAccountItem, EmailDomainItem, DeliverabilityStats } from '../types';

export const DeliverabilityView: React.FC = () => {
  const [stats, setStats] = useState<DeliverabilityStats | null>(null);
  const [mailboxes, setMailboxes] = useState<EmailAccountItem[]>([]);
  const [domains, setDomains] = useState<EmailDomainItem[]>([]);
  const [verifyDomainInput, setVerifyDomainInput] = useState<string>('');
  const [verifying, setVerifying] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [message, setMessage] = useState<string | null>(null);

  const fetchDeliverabilityData = async () => {
    setLoading(true);
    try {
      const [statsRes, mbRes, domRes] = await Promise.all([
        fetch('/api/v1/deliverability/stats'),
        fetch('/api/v1/deliverability/mailboxes'),
        fetch('/api/v1/deliverability/domains'),
      ]);
      if (statsRes.ok) setStats(await statsRes.json());
      if (mbRes.ok) setMailboxes(await mbRes.json());
      if (domRes.ok) setDomains(await domRes.json());
    } catch (err) {
      console.error('Failed to load deliverability data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeliverabilityData();
  }, []);

  const handleToggleKillSwitch = async () => {
    if (!stats) return;
    const newState = !stats.kill_switch_active;
    const reason = newState ? 'Manual operator safety halt' : 'Manual operator resume';
    try {
      const res = await fetch('/api/v1/deliverability/kill-switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: newState, reason }),
      });
      if (res.ok) {
        setMessage(`Global Outbound Kill Switch ${newState ? 'ENGAGED' : 'DISENGAGED'}.`);
        fetchDeliverabilityData();
      }
    } catch {
      setMessage('Failed to toggle kill switch.');
    }
  };

  const handleVerifyDomain = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!verifyDomainInput.trim()) return;
    setVerifying(true);
    try {
      const res = await fetch('/api/v1/deliverability/domains/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain_name: verifyDomainInput }),
      });
      if (res.ok) {
        setMessage(`DNS verified for ${verifyDomainInput}!`);
        setVerifyDomainInput('');
        fetchDeliverabilityData();
      } else {
        setMessage('Domain verification query failed.');
      }
    } catch {
      setMessage('Error running DNS verification.');
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Kill Switch */}
      <div className={`p-6 rounded-xl border flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition-colors ${
        stats?.kill_switch_active
          ? 'bg-rose-950/40 border-rose-500/50'
          : 'bg-gray-900 border-gray-800'
      }`}>
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Mail className="w-7 h-7 text-indigo-400" />
              Email Deliverability & Mailbox Health
            </h1>
            {stats?.kill_switch_active ? (
              <span className="px-3 py-1 text-xs font-bold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40 flex items-center gap-1.5 animate-pulse">
                <ShieldAlert className="w-3.5 h-3.5" /> KILL SWITCH ACTIVE (OUTBOUND BLOCKED)
              </span>
            ) : (
              <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" /> Outbound Active
              </span>
            )}
          </div>
          <p className="text-gray-400 text-sm mt-1">
            Real-time DNS SPF/DKIM/DMARC authentication, connected mailbox quotas, and domain reputation protection.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleToggleKillSwitch}
            className={`px-4 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition ${
              stats?.kill_switch_active
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                : 'bg-rose-600 hover:bg-rose-500 text-white'
            }`}
          >
            <Power className="w-4 h-4" />
            {stats?.kill_switch_active ? 'Disengage Kill Switch' : 'HALT ALL OUTBOUND (Kill Switch)'}
          </button>
          <button
            onClick={fetchDeliverabilityData}
            className="p-2.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg transition"
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

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="text-gray-400 text-xs font-medium uppercase flex items-center justify-between">
            <span>Sent Messages</span>
            <Send className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{stats?.total_sent || 0}</div>
          <div className="text-xs text-gray-500 mt-1">Delivered: {stats?.total_delivered || 0}</div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="text-gray-400 text-xs font-medium uppercase flex items-center justify-between">
            <span>Bounce Rate</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className={`text-2xl font-bold mt-2 ${
            (stats?.bounce_rate_percent || 0) > 5 ? 'text-rose-400' : 'text-emerald-400'
          }`}>
            {stats?.bounce_rate_percent || 0}%
          </div>
          <div className="text-xs text-gray-500 mt-1">Threshold: &lt; 5.0% (auto-pause)</div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="text-gray-400 text-xs font-medium uppercase flex items-center justify-between">
            <span>Reply Rate</span>
            <CornerUpLeft className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{stats?.reply_rate_percent || 0}%</div>
          <div className="text-xs text-gray-500 mt-1">Replies: {stats?.total_replied || 0}</div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="text-gray-400 text-xs font-medium uppercase flex items-center justify-between">
            <span>Complaints</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">{stats?.total_complaints || 0}</div>
          <div className="text-xs text-gray-500 mt-1">Unsubscribes: {stats?.total_unsubscribed || 0}</div>
        </div>
      </div>

      {/* Connected Mailboxes */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Mail className="w-5 h-5 text-indigo-400" />
          Connected Mailboxes & Daily Quotas ({mailboxes.length})
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {mailboxes.map((mb) => (
            <div key={mb.id} className="bg-gray-800/40 border border-gray-700/60 rounded-lg p-4 flex justify-between items-center">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white text-sm">{mb.email_address}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    mb.health_status === 'HEALTHY' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                  }`}>
                    {mb.health_status}
                  </span>
                </div>
                <div className="text-xs text-gray-400 mt-1 flex gap-3">
                  <span>Provider: {mb.provider}</span>
                  <span>•</span>
                  <span>OAuth: {mb.oauth_status}</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-bold text-white">{mb.sent_today} / {mb.daily_quota}</div>
                <div className="text-[10px] text-gray-400">Daily quota used</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Domain DNS Authentication (SPF, DKIM, DMARC, MX) */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Globe className="w-5 h-5 text-indigo-400" />
            Sender Domain Authentication (SPF / DKIM / DMARC / MX)
          </h2>
          <form onSubmit={handleVerifyDomain} className="flex gap-2 w-full md:w-auto">
            <input
              type="text"
              placeholder="e.g. acme-corp.com"
              value={verifyDomainInput}
              onChange={(e) => setVerifyDomainInput(e.target.value)}
              className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={verifying}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-medium transition disabled:opacity-50"
            >
              {verifying ? 'Querying DNS...' : 'Verify Domain'}
            </button>
          </form>
        </div>

        {loading ? (
          <div className="text-center py-6 text-gray-400">Querying domain records...</div>
        ) : domains.length === 0 ? (
          <div className="text-center py-6 text-gray-500">No domains verified yet. Enter a domain above to query live DNS.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-gray-800/60 text-xs uppercase text-gray-400 border-b border-gray-700">
                <tr>
                  <th className="py-3 px-4">Domain Name</th>
                  <th className="py-3 px-4">SPF</th>
                  <th className="py-3 px-4">DKIM</th>
                  <th className="py-3 px-4">DMARC</th>
                  <th className="py-3 px-4">MX Status</th>
                  <th className="py-3 px-4">Last Checked</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {domains.map((d) => (
                  <tr key={d.id} className="hover:bg-gray-800/30">
                    <td className="py-3 px-4 font-medium text-white">{d.domain_name}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        d.spf_status === 'VERIFIED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                      }`}>
                        {d.spf_status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        d.dkim_status === 'VERIFIED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700 text-gray-300'
                      }`}>
                        {d.dkim_status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        d.dmarc_status === 'VERIFIED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                      }`}>
                        {d.dmarc_status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                        d.mx_status === 'VERIFIED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                      }`}>
                        {d.mx_status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-gray-400">{d.last_checked_at ? new Date(d.last_checked_at).toLocaleDateString() : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

