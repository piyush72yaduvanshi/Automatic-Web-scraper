import React, { useState, useEffect } from 'react';
import {
  Shield,
  Trash2,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Search,
} from 'lucide-react';
import { ConsentRecordItem } from '../types';

export const ComplianceView: React.FC = () => {
  const [consents, setConsents] = useState<ConsentRecordItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [testRecipient, setTestRecipient] = useState<string>('');
  const [testChannel, setTestChannel] = useState<string>('EMAIL');
  const [checkResult, setCheckResult] = useState<any | null>(null);
  const [checking, setChecking] = useState<boolean>(false);

  // Deletion Request
  const [deleteEmail, setDeleteEmail] = useState<string>('');
  const [deleteReason, setDeleteReason] = useState<string>('GDPR_RIGHT_TO_BE_FORGOTTEN');
  const [deleting, setDeleting] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchConsents = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/compliance/consents');
      if (res.ok) setConsents(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConsents();
  }, []);

  const handleTestEligibility = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testRecipient.trim()) return;
    setChecking(true);
    setCheckResult(null);
    try {
      const res = await fetch('/api/v1/compliance/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipient: testRecipient, channel: testChannel }),
      });
      if (res.ok) setCheckResult(await res.json());
    } catch {
      setMessage('Error running compliance check.');
    } finally {
      setChecking(false);
    }
  };

  const handleDeleteRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deleteEmail.trim()) return;
    setDeleting(true);
    try {
      const res = await fetch('/api/v1/compliance/deletion-request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipient: deleteEmail, reason: deleteReason }),
      });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Data deletion executed for ${deleteEmail}! Anonymized ${data.contacts_anonymized} contacts and added permanent suppression.`);
        setDeleteEmail('');
        fetchConsents();
      }
    } catch {
      setMessage('Error executing deletion request.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center bg-gray-900 border border-gray-800 p-6 rounded-xl">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="w-7 h-7 text-indigo-400" />
            Global Consent & GDPR / CAN-SPAM Compliance
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Centralized lawful basis records, channel-specific consent verification, and GDPR 'Right to be Forgotten' erasure.
          </p>
        </div>
        <button
          onClick={fetchConsents}
          className="p-2.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg transition"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {message && (
        <div className="p-4 bg-indigo-950/60 border border-indigo-500/40 rounded-lg text-indigo-200 text-sm flex justify-between items-center">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-indigo-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Grid: 2 Interactive Testing & Erasure Boxes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Pre-Flight Eligibility Simulator */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-base font-semibold text-white mb-2 flex items-center gap-2">
            <Search className="w-4 h-4 text-indigo-400" />
            Pre-Flight Compliance Simulator
          </h2>
          <p className="text-xs text-gray-400 mb-4">
            Simulate the mandatory compliance gatekeeper check for an email or phone number across channels.
          </p>
          <form onSubmit={handleTestEligibility} className="space-y-3">
            <div className="flex gap-2">
              <input
                type="text"
                required
                value={testRecipient}
                onChange={(e) => setTestRecipient(e.target.value)}
                placeholder="prospect@company.com or +12025550199"
                className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:outline-none"
              />
              <select
                value={testChannel}
                onChange={(e) => setTestChannel(e.target.value)}
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
              >
                <option value="EMAIL">Email</option>
                <option value="WHATSAPP">WhatsApp</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={checking}
              className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold transition"
            >
              {checking ? 'Evaluating...' : 'Run Pre-Flight Check'}
            </button>
          </form>

          {checkResult && (
            <div className={`mt-4 p-3 rounded-lg border text-xs ${
              checkResult.is_eligible
                ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300'
                : 'bg-rose-950/40 border-rose-500/40 text-rose-300'
            }`}>
              <div className="font-bold flex items-center gap-1.5">
                {checkResult.is_eligible ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                {checkResult.is_eligible ? 'PASSED: Eligible for Outreach' : 'BLOCKED: Outreach Prohibited'}
              </div>
              <div className="mt-1">Reason: {checkResult.reason}</div>
              <div className="text-[11px] opacity-80 mt-0.5">{checkResult.details}</div>
            </div>
          )}
        </div>

        {/* GDPR Right to be Forgotten Erasure */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="text-base font-semibold text-white mb-2 flex items-center gap-2">
            <Trash2 className="w-4 h-4 text-rose-400" />
            GDPR 'Right to be Forgotten' Erasure
          </h2>
          <p className="text-xs text-gray-400 mb-4">
            Anonymizes matching contact information and records permanent suppression to guarantee they are never contacted again.
          </p>
          <form onSubmit={handleDeleteRequest} className="space-y-3">
            <input
              type="email"
              required
              value={deleteEmail}
              onChange={(e) => setDeleteEmail(e.target.value)}
              placeholder="user@requested-erasure.com"
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:outline-none"
            />
            <select
              value={deleteReason}
              onChange={(e) => setDeleteReason(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
            >
              <option value="GDPR_RIGHT_TO_BE_FORGOTTEN">GDPR Right to be Forgotten (Article 17)</option>
              <option value="CCPA_OPT_OUT">CCPA Consumer Erasure Request</option>
              <option value="EXPLICIT_OPTOUT">Explicit Opt-out &amp; Anonymization</option>
            </select>
            <button
              type="submit"
              disabled={deleting}
              className="w-full py-2 bg-rose-700 hover:bg-rose-600 text-white rounded-lg text-xs font-semibold transition"
            >
              {deleting ? 'Executing Erasure...' : 'Execute Data Erasure &amp; Suppress'}
            </button>
          </form>
        </div>
      </div>

      {/* Table: Consent Records */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-base font-semibold text-white mb-4">Centralized Consent &amp; Lawful Basis Registry ({consents.length})</h2>
        {loading ? (
          <div className="text-center py-8 text-gray-400">Loading consents...</div>
        ) : consents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No consent records logged yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-gray-800/60 text-xs uppercase text-gray-400 border-b border-gray-700">
                <tr>
                  <th className="py-3 px-4">Recipient</th>
                  <th className="py-3 px-4">Lawful Basis</th>
                  <th className="py-3 px-4">Email Consent</th>
                  <th className="py-3 px-4">WhatsApp Consent</th>
                  <th className="py-3 px-4">Marketing Eligible</th>
                  <th className="py-3 px-4">Collected At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {consents.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-800/30">
                    <td className="py-3 px-4 font-medium text-white">{c.recipient}</td>
                    <td className="py-3 px-4 text-xs">
                      <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {c.lawful_basis}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs">
                      {c.channel_email_consent ? (
                        <span className="text-emerald-400 flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> Yes</span>
                      ) : (
                        <span className="text-rose-400 flex items-center gap-1"><XCircle className="w-3.5 h-3.5" /> No</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-xs">
                      {c.channel_whatsapp_consent ? (
                        <span className="text-emerald-400 flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> Opted-in</span>
                      ) : (
                        <span className="text-gray-500">No Opt-in</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-xs">
                      <span className={`px-2 py-0.5 rounded font-semibold ${
                        c.marketing_eligible ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                      }`}>
                        {c.marketing_eligible ? 'Eligible' : 'Ineligible'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-gray-400">{c.collected_at ? new Date(c.collected_at).toLocaleDateString() : 'N/A'}</td>
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

