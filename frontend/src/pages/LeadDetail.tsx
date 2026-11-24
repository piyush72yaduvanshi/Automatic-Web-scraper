import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Mail,
  Phone,
  ExternalLink,
  Instagram,
  Linkedin,
  Facebook,
  Twitter,
  Zap,
  Loader2,
  Copy,
  Check,
  Sparkles,
  Layers,
  Globe,
  MapPin,
  Share2,
  Building2,
} from 'lucide-react';
import { useLead } from '../hooks/useLeads';
import api from '../services/api';

const LeadDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { data: lead, isLoading, isError, error, refetch } = useLead(id!);

  const [isScanning, setIsScanning] = useState(false);
  const [copiedText, setCopiedText] = useState<string | null>(null);
  const [scanMessage, setScanMessage] = useState<string | null>(null);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(text);
    setTimeout(() => setCopiedText(null), 2000);
  };

  const handleDeepScan = async () => {
    if (!id) return;
    setIsScanning(true);
    setScanMessage('⚡ Initiating multi-source deep extraction across Firecrawl, Google Search Radar, and AI...');

    try {
      await api.post(`/leads/${id}/scan`);
      await refetch();
      setScanMessage('✅ Multi-source scan completed and data updated!');
      setTimeout(() => setScanMessage(null), 3000);
    } catch (err: any) {
      setScanMessage(`❌ Scan failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsScanning(false);
    }
  };

  const getSocialIcon = (platform: string) => {
    switch (platform.toUpperCase()) {
      case 'INSTAGRAM':
        return Instagram;
      case 'LINKEDIN':
        return Linkedin;
      case 'FACEBOOK':
        return Facebook;
      case 'X':
      case 'TWITTER':
        return Twitter;
      default:
        return ExternalLink;
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 bg-[#0E1424] rounded-2xl border border-slate-800">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent" />
        <p className="text-xs text-slate-400 font-medium">Loading lead details...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8 bg-red-950/40 border border-red-500/30 rounded-2xl text-center space-y-4 max-w-lg mx-auto mt-12">
        <h3 className="text-lg font-bold text-red-200">Failed to load lead details</h3>
        <p className="text-xs text-red-300">{(error as any)?.message || 'Lead could not be loaded.'}</p>
        <div className="flex justify-center gap-3">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-red-600 text-white rounded-xl text-xs font-semibold hover:bg-red-700 shadow-md"
          >
            Retry
          </button>
          <Link
            to="/leads"
            className="px-4 py-2 bg-[#131B2E] text-slate-300 border border-slate-700 rounded-xl text-xs font-semibold hover:bg-slate-800"
          >
            &larr; Back to Leads
          </Link>
        </div>
      </div>
    );
  }

  if (!lead) {
    return (
      <div className="text-center py-16 bg-[#0E1424] rounded-2xl border border-slate-800">
        <h3 className="text-base font-bold text-white">Lead not found</h3>
        <Link to="/leads" className="text-indigo-400 hover:text-indigo-300 mt-2 inline-block font-semibold text-xs">
          &larr; Back to Leads
        </Link>
      </div>
    );
  }

  const emails = (lead.contacts || []).filter((c) => c.contact_type === 'EMAIL');
  const phones = (lead.contacts || []).filter((c) => c.contact_type === 'PHONE');
  const evidence = lead.source_evidence || [];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Navigation & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
        <Link
          to="/leads"
          className="inline-flex items-center text-xs font-semibold text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5 mr-1.5" />
          Back to Leads Directory
        </Link>

        {/* Deep Scan, Qualify & CRM Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={async () => {
              try {
                setScanMessage('Evaluating lead qualification against Ideal Customer Profile...');
                const res = await api.post(`/leads/${id}/qualify`);
                await refetch();
                setScanMessage(`🎯 Qualified with Score ${res.data.qualification_score}/100 (${res.data.qualification_status})`);
              } catch (e: any) {
                alert(`Qualification error: ${e.response?.data?.detail || e.message}`);
              }
            }}
            className="inline-flex items-center px-3.5 py-2 bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 font-semibold rounded-xl text-xs transition-colors"
          >
            <Sparkles className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
            AI Qualify Lead
          </button>

          <button
            onClick={async () => {
              try {
                const res = await api.post(`/crm/companies/convert-from-lead/${id}`);
                await refetch();
                alert(`Successfully converted to CRM Company '${res.data.company_name}' with initial deal!`);
              } catch (e: any) {
                alert(`Conversion error: ${e.response?.data?.detail || e.message}`);
              }
            }}
            className="inline-flex items-center px-3.5 py-2 bg-[#131B2E] hover:bg-slate-800 text-slate-200 border border-slate-700 font-semibold rounded-xl text-xs transition-colors"
          >
            <Building2 className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
            Convert to CRM
          </button>

          <button
            onClick={async () => {
              try {
                const res = await api.post(`/outreach/drafts/lead/${id}`);
                alert(`Personalized outreach draft created and enqueued to Human Approval Queue! Approval ID: ${res.data.approval_id}`);
              } catch (e: any) {
                alert(`Draft error: ${e.response?.data?.detail || e.message}`);
              }
            }}
            className="inline-flex items-center px-3.5 py-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold rounded-xl text-xs transition-colors"
          >
            <Mail className="w-3.5 h-3.5 mr-1.5 text-emerald-400" />
            Draft Outreach
          </button>

          <button
            onClick={handleDeepScan}
            disabled={isScanning}
            className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white font-semibold rounded-xl shadow-lg shadow-indigo-500/20 text-xs transition-all disabled:opacity-50"
          >
            {isScanning ? (
              <>
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                Scanning...
              </>
            ) : (
              <>
                <Zap className="w-3.5 h-3.5 mr-1.5 fill-white" />
                Deep AI Scan
              </>
            )}
          </button>
        </div>
      </div>

      {scanMessage && (
        <div className="p-3.5 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-xs font-semibold text-indigo-300 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400 flex-shrink-0" />
          <span>{scanMessage}</span>
        </div>
      )}

      {/* Business Hero Card */}
      <div className="bg-[#0E1424] rounded-2xl shadow-sm border border-slate-800 p-6 sm:p-8 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">{lead.business_name}</h1>
              <span className="px-2.5 py-0.5 bg-indigo-500/10 text-indigo-400 text-xs font-bold rounded-full border border-indigo-500/20">
                {lead.source_provider}
              </span>
            </div>
            {lead.category && <p className="text-xs font-semibold text-slate-400 mt-1">{lead.category}</p>}
          </div>
        </div>

        {lead.description && (
          <div className="p-4 bg-[#131B2E] rounded-xl border border-slate-700/80 text-xs text-slate-300 leading-relaxed">
            <span className="font-semibold text-white block mb-1">Business Overview / AI Insights:</span>
            {lead.description}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs pt-4 border-t border-slate-800">
          {lead.address && (
            <div className="flex items-start gap-2.5">
              <MapPin className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Address</p>
                <p className="text-slate-200 font-medium mt-0.5">{lead.address}</p>
              </div>
            </div>
          )}

          {(lead.city || lead.state || lead.country) && (
            <div className="flex items-start gap-2.5">
              <Globe className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Territory</p>
                <p className="text-slate-200 font-medium mt-0.5">
                  {[lead.city, lead.state, lead.country].filter(Boolean).join(', ')}
                </p>
              </div>
            </div>
          )}

          {lead.website && (
            <div className="flex items-start gap-2.5">
              <ExternalLink className="w-4 h-4 text-indigo-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Official Website</p>
                <a
                  href={lead.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-400 hover:text-indigo-300 font-semibold mt-0.5 block truncate max-w-xs transition-colors"
                >
                  {lead.website}
                </a>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Contacts Grid: Emails & Phones */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Email Addresses */}
        <div className="bg-[#0E1424] rounded-2xl shadow-sm border border-slate-800 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
                <Mail className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-bold text-white">Verified Email Addresses</h2>
            </div>
            <span className="px-2.5 py-0.5 bg-indigo-500/10 text-indigo-400 text-xs font-bold rounded-full border border-indigo-500/20">
              {emails.length} Found
            </span>
          </div>

          {emails.length > 0 ? (
            <div className="space-y-2.5">
              {emails.map((email) => {
                const val = email.normalized_value || email.original_value;
                return (
                  <div
                    key={email.id}
                    className="p-3.5 bg-[#131B2E] border border-slate-700/80 rounded-xl flex items-center justify-between gap-3 hover:border-indigo-500/50 transition-colors"
                  >
                    <div className="min-w-0">
                      <a href={`mailto:${val}`} className="text-xs font-bold text-indigo-400 hover:text-indigo-300 truncate block">
                        {val}
                      </a>
                      {email.source_url && (
                        <p className="text-[10px] text-slate-500 mt-0.5 truncate max-w-xs">
                          Source: {email.source_url}
                        </p>
                      )}
                    </div>

                    <button
                      onClick={() => handleCopy(val)}
                      title="Copy email"
                      className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors flex-shrink-0"
                    >
                      {copiedText === val ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500 text-xs space-y-2">
              <Mail className="w-7 h-7 mx-auto opacity-40" />
              <p>No email addresses discovered yet.</p>
              <button
                onClick={handleDeepScan}
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300"
              >
                Run Multi-Source Scan to search
              </button>
            </div>
          )}
        </div>

        {/* Phone Numbers */}
        <div className="bg-[#0E1424] rounded-2xl shadow-sm border border-slate-800 p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
                <Phone className="w-4 h-4" />
              </div>
              <h2 className="text-sm font-bold text-white">Verified Phone Numbers</h2>
            </div>
            <span className="px-2.5 py-0.5 bg-emerald-500/10 text-emerald-400 text-xs font-bold rounded-full border border-emerald-500/20">
              {phones.length} Found
            </span>
          </div>

          {phones.length > 0 ? (
            <div className="space-y-2.5">
              {phones.map((phone) => {
                const val = phone.normalized_value || phone.original_value;
                return (
                  <div
                    key={phone.id}
                    className="p-3.5 bg-[#131B2E] border border-slate-700/80 rounded-xl flex items-center justify-between gap-3 hover:border-emerald-500/50 transition-colors"
                  >
                    <div className="min-w-0">
                      <a href={`tel:${val}`} className="text-xs font-bold text-emerald-400 hover:text-emerald-300 truncate block">
                        {val}
                      </a>
                      {phone.source_url && (
                        <p className="text-[10px] text-slate-500 mt-0.5 truncate max-w-xs">
                          Source: {phone.source_url}
                        </p>
                      )}
                    </div>

                    <button
                      onClick={() => handleCopy(val)}
                      title="Copy phone"
                      className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors flex-shrink-0"
                    >
                      {copiedText === val ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500 text-xs space-y-2">
              <Phone className="w-7 h-7 mx-auto opacity-40" />
              <p>No phone numbers discovered yet.</p>
              <button
                onClick={handleDeepScan}
                className="text-xs font-semibold text-indigo-400 hover:text-indigo-300"
              >
                Run Multi-Source Scan to search
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Social Profiles */}
      <div className="bg-[#0E1424] rounded-2xl shadow-sm border border-slate-800 p-6 space-y-4">
        <h2 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
          <Share2 className="w-4 h-4 text-purple-400" />
          Social Footprint & Profiles
        </h2>

        {(lead.social_profiles || []).length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {(lead.social_profiles || []).map((profile) => {
              const Icon = getSocialIcon(profile.platform);
              return (
                <a
                  key={profile.id}
                  href={profile.profile_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center p-3.5 bg-[#131B2E] border border-slate-700/80 rounded-xl hover:border-purple-500/50 hover:bg-[#18223a] transition-all group"
                >
                  <Icon className="w-4 h-4 mr-3 text-purple-400 group-hover:scale-110 transition-transform flex-shrink-0" />
                  <div className="min-w-0">
                    <span className="text-xs font-bold text-white block">{profile.platform}</span>
                    <span className="text-[10px] text-slate-400 block truncate max-w-[120px]">{profile.profile_url}</span>
                  </div>
                  <ExternalLink className="w-3 h-3 ml-auto text-slate-500 group-hover:text-purple-400" />
                </a>
              );
            })}
          </div>
        ) : (
          <p className="text-slate-500 text-xs text-center py-6">
            No social media profiles discovered yet. Run a Deep Scan to extract social profiles via Google Search Radar.
          </p>
        )}
      </div>

      {/* Source Evidence Audit Trail */}
      {evidence.length > 0 && (
        <div className="bg-[#0E1424] rounded-2xl shadow-sm border border-slate-800 p-6 space-y-3">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              Multi-Source Evidence Audit Trail
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Full transparent attribution for every data point extracted across discovery sources.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-800/80 text-xs">
              <thead className="bg-[#131B2E]/70">
                <tr>
                  <th className="px-4 py-2.5 text-left font-bold text-slate-400 uppercase text-[10px]">Field</th>
                  <th className="px-4 py-2.5 text-left font-bold text-slate-400 uppercase text-[10px]">Extracted Value</th>
                  <th className="px-4 py-2.5 text-left font-bold text-slate-400 uppercase text-[10px]">Provider Source</th>
                  <th className="px-4 py-2.5 text-left font-bold text-slate-400 uppercase text-[10px]">Source URL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70 font-mono">
                {evidence.map((ev, i) => (
                  <tr key={i} className="hover:bg-[#131B2E]/60 transition-colors">
                    <td className="px-4 py-2.5 font-semibold text-slate-200 uppercase text-[10px]">{ev.field_name}</td>
                    <td className="px-4 py-2.5 text-indigo-400 font-medium">{ev.extracted_value}</td>
                    <td className="px-4 py-2.5 text-slate-400 font-sans text-xs">{ev.provider || 'Radar'}</td>
                    <td className="px-4 py-2.5 text-slate-400 truncate max-w-xs text-xs">
                      <a href={ev.source_url} target="_blank" rel="noopener noreferrer" className="hover:underline text-indigo-400">
                        {ev.source_url}
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default LeadDetail;
