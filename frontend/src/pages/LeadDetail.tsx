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
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
        <p className="text-sm text-gray-500 font-medium">Loading lead details...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-8 bg-red-50 border border-red-200 rounded-2xl text-center space-y-4 max-w-lg mx-auto mt-12">
        <h3 className="text-lg font-bold text-red-900">Failed to load lead details</h3>
        <p className="text-sm text-red-700">{(error as any)?.message || 'Lead could not be loaded.'}</p>
        <div className="flex justify-center gap-3">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-semibold hover:bg-red-700"
          >
            Retry
          </button>
          <Link
            to="/leads"
            className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-xl text-sm font-semibold hover:bg-gray-50"
          >
            &larr; Back to Leads
          </Link>
        </div>
      </div>
    );
  }

  if (!lead) {
    return (
      <div className="text-center py-16">
        <h3 className="text-lg font-bold text-gray-900">Lead not found</h3>
        <Link to="/leads" className="text-blue-600 hover:text-blue-800 mt-2 inline-block font-semibold">
          &larr; Back to Leads
        </Link>
      </div>
    );
  }

  const emails = (lead.contacts || []).filter((c) => c.contact_type === 'EMAIL');
  const phones = (lead.contacts || []).filter((c) => c.contact_type === 'PHONE');
  const evidence = lead.source_evidence || [];

  return (
    <div className="px-4 sm:px-0 max-w-6xl mx-auto space-y-6">
      {/* Top Navigation & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <Link
          to="/leads"
          className="inline-flex items-center text-sm font-semibold text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4 mr-1.5" />
          Back to Leads
        </Link>

        {/* Deep Scan Button */}
        <button
          onClick={handleDeepScan}
          disabled={isScanning}
          className="inline-flex items-center px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-xl shadow-md text-sm transition-all disabled:opacity-50"
        >
          {isScanning ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Running Deep Multi-Source Scan...
            </>
          ) : (
            <>
              <Zap className="w-4 h-4 mr-1.5 fill-white" />
              ⚡ Deep AI Scan & Enrich
            </>
          )}
        </button>
      </div>

      {scanMessage && (
        <div className="p-3.5 bg-blue-50 border border-blue-200 rounded-xl text-sm font-semibold text-blue-900 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-blue-600 flex-shrink-0" />
          <span>{scanMessage}</span>
        </div>
      )}

      {/* Business Hero Card */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900">{lead.business_name}</h1>
              <span className="px-3 py-1 bg-blue-50 text-blue-700 text-xs font-bold rounded-full border border-blue-200">
                {lead.source_provider}
              </span>
            </div>
            {lead.category && <p className="text-sm font-semibold text-gray-500 mt-1">{lead.category}</p>}
          </div>
        </div>

        {lead.description && (
          <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-100 text-sm text-gray-700 leading-relaxed">
            <span className="font-semibold text-gray-900 block mb-1">Business Overview / AI Insights:</span>
            {lead.description}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs pt-4 border-t border-gray-100">
          {lead.address && (
            <div className="flex items-start gap-2.5">
              <MapPin className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-gray-500 font-semibold uppercase tracking-wider text-[10px]">Address</p>
                <p className="text-gray-900 font-medium mt-0.5">{lead.address}</p>
              </div>
            </div>
          )}

          {(lead.city || lead.state || lead.country) && (
            <div className="flex items-start gap-2.5">
              <Globe className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-gray-500 font-semibold uppercase tracking-wider text-[10px]">Territory</p>
                <p className="text-gray-900 font-medium mt-0.5">
                  {[lead.city, lead.state, lead.country].filter(Boolean).join(', ')}
                </p>
              </div>
            </div>
          )}

          {lead.website && (
            <div className="flex items-start gap-2.5">
              <ExternalLink className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-gray-500 font-semibold uppercase tracking-wider text-[10px]">Official Website</p>
                <a
                  href={lead.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 font-semibold mt-0.5 block truncate max-w-xs"
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
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-blue-100 text-blue-700 rounded-xl">
                <Mail className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold text-gray-900">Verified Email Addresses</h2>
            </div>
            <span className="px-2.5 py-0.5 bg-blue-50 text-blue-700 text-xs font-bold rounded-full">
              {emails.length} Found
            </span>
          </div>

          {emails.length > 0 ? (
            <div className="space-y-3">
              {emails.map((email) => {
                const val = email.normalized_value || email.original_value;
                return (
                  <div
                    key={email.id}
                    className="p-3.5 bg-gray-50 border border-gray-200 rounded-xl flex items-center justify-between gap-3 hover:bg-blue-50/40 transition-colors"
                  >
                    <div className="min-w-0">
                      <a href={`mailto:${val}`} className="text-sm font-bold text-blue-600 hover:text-blue-800 truncate block">
                        {val}
                      </a>
                      {email.source_url && (
                        <p className="text-[11px] text-gray-500 mt-0.5 truncate max-w-xs">
                          Source: {email.source_url}
                        </p>
                      )}
                    </div>

                    <button
                      onClick={() => handleCopy(val)}
                      title="Copy email"
                      className="p-2 text-gray-500 hover:text-blue-600 hover:bg-white rounded-lg border border-transparent hover:border-gray-200 transition-all flex-shrink-0"
                    >
                      {copiedText === val ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400 text-sm">
              <Mail className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No email addresses found yet.</p>
              <button
                onClick={handleDeepScan}
                className="mt-2 text-xs font-semibold text-blue-600 hover:text-blue-800"
              >
                Run Multi-Source Scan to search
              </button>
            </div>
          )}
        </div>

        {/* Phone Numbers */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-emerald-100 text-emerald-700 rounded-xl">
                <Phone className="w-5 h-5" />
              </div>
              <h2 className="text-lg font-bold text-gray-900">Verified Phone Numbers</h2>
            </div>
            <span className="px-2.5 py-0.5 bg-emerald-50 text-emerald-700 text-xs font-bold rounded-full">
              {phones.length} Found
            </span>
          </div>

          {phones.length > 0 ? (
            <div className="space-y-3">
              {phones.map((phone) => {
                const val = phone.normalized_value || phone.original_value;
                return (
                  <div
                    key={phone.id}
                    className="p-3.5 bg-gray-50 border border-gray-200 rounded-xl flex items-center justify-between gap-3 hover:bg-emerald-50/40 transition-colors"
                  >
                    <div className="min-w-0">
                      <a href={`tel:${val}`} className="text-sm font-bold text-emerald-700 hover:text-emerald-900 truncate block">
                        {val}
                      </a>
                      {phone.source_url && (
                        <p className="text-[11px] text-gray-500 mt-0.5 truncate max-w-xs">
                          Source: {phone.source_url}
                        </p>
                      )}
                    </div>

                    <button
                      onClick={() => handleCopy(val)}
                      title="Copy phone"
                      className="p-2 text-gray-500 hover:text-emerald-600 hover:bg-white rounded-lg border border-transparent hover:border-gray-200 transition-all flex-shrink-0"
                    >
                      {copiedText === val ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400 text-sm">
              <Phone className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No phone numbers found yet.</p>
              <button
                onClick={handleDeepScan}
                className="mt-2 text-xs font-semibold text-blue-600 hover:text-blue-800"
              >
                Run Multi-Source Scan to search
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Social Profiles */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
          <Share2 className="w-5 h-5 text-purple-600" />
          Social Footprint & Profiles
        </h2>

        {(lead.social_profiles || []).length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {(lead.social_profiles || []).map((profile) => {
              const Icon = getSocialIcon(profile.platform);
              return (
                <a
                  key={profile.id}
                  href={profile.profile_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center p-3.5 bg-gray-50 border border-gray-200 rounded-xl hover:border-purple-300 hover:bg-purple-50/50 transition-all group"
                >
                  <Icon className="w-5 h-5 mr-3 text-purple-600 group-hover:scale-110 transition-transform" />
                  <div className="min-w-0">
                    <span className="text-xs font-bold text-gray-900 block">{profile.platform}</span>
                    <span className="text-[10px] text-gray-500 block truncate max-w-[120px]">{profile.profile_url}</span>
                  </div>
                  <ExternalLink className="w-3.5 h-3.5 ml-auto text-gray-400 group-hover:text-purple-600" />
                </a>
              );
            })}
          </div>
        ) : (
          <p className="text-gray-400 text-sm text-center py-6">
            No social media profiles discovered yet. Run a Deep Scan to extract social profiles via Google Search Radar.
          </p>
        )}
      </div>

      {/* Source Evidence Audit Trail */}
      {evidence.length > 0 && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-600" />
            Multi-Source Evidence Audit Trail
          </h2>
          <p className="text-xs text-gray-500 mb-4">
            Full transparent attribution for every data point extracted across discovery sources.
          </p>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-xs">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left font-bold text-gray-600">Field</th>
                  <th className="px-4 py-2 text-left font-bold text-gray-600">Extracted Value</th>
                  <th className="px-4 py-2 text-left font-bold text-gray-600">Provider Source</th>
                  <th className="px-4 py-2 text-left font-bold text-gray-600">Source URL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 font-mono">
                {evidence.map((ev, i) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-semibold text-gray-900 uppercase text-[11px]">{ev.field_name}</td>
                    <td className="px-4 py-2.5 text-blue-700 font-medium">{ev.extracted_value}</td>
                    <td className="px-4 py-2.5 text-gray-600 font-sans">{ev.provider || 'Radar'}</td>
                    <td className="px-4 py-2.5 text-gray-400 truncate max-w-xs">
                      <a href={ev.source_url} target="_blank" rel="noopener noreferrer" className="hover:underline text-blue-600">
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
