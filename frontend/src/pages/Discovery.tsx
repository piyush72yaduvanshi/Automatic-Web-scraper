import { useState, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Search,
  Zap,
  Loader2,
  ExternalLink,
  Mail,
  Phone,
  Share2,
  Sparkles,
  Download,
  Terminal,
  ShieldCheck,
  UserCheck,
  Globe,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useCreateJob } from '../hooks/useJobs';
import { useLeads } from '../hooks/useLeads';
import { DiscoveryJobCreate, LiveScannedLead } from '../types';

const Discovery = () => {
  const navigate = useNavigate();
  const createJob = useCreateJob();
  const { data: recentDiscoveredLeads, isLoading: recentLoading } = useLeads({ page: 1, page_size: 6 });

  // Form State
  const [formData, setFormData] = useState<DiscoveryJobCreate>({
    query: 'dentist',
    location: 'Lucknow',
    radius_km: 10,
    limit: 10,
    sources: ['maps', 'web', 'social'],
    enrich_emails: true,
    enrich_phones: true,
    enrich_socials: true,
    preferred_provider: 'multi',
  });

  const [aiEnabled, setAiEnabled] = useState(true);
  const [customAiKey, setCustomAiKey] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedCategoryTab, setSelectedCategoryTab] = useState<string>('All');

  const popularPresets = [
    // 🏥 Healthcare & Wellness
    { q: 'Dentists', loc: 'Lucknow', category: 'Healthcare' },
    { q: 'Hospitals & Medical Centers', loc: 'Delhi NCR', category: 'Healthcare' },
    { q: 'Diagnostic Labs & Pathology', loc: 'Hyderabad', category: 'Healthcare' },
    { q: 'Dermatologists & Skin Clinics', loc: 'Mumbai', category: 'Healthcare' },
    { q: 'Ayurveda & Wellness Retreats', loc: 'Kerala', category: 'Healthcare' },
    { q: 'Pharmacies & Chemists', loc: 'Pune', category: 'Healthcare' },
    { q: 'Veterinary Clinics & Pet Care', loc: 'Bangalore', category: 'Healthcare' },
    { q: 'Eye Care & Optical Centers', loc: 'Ahmedabad', category: 'Healthcare' },

    // 💻 Tech, SaaS & Agencies
    { q: 'Software Companies', loc: 'Noida', category: 'Tech & Agency' },
    { q: 'AI & SaaS Startups', loc: 'Bangalore', category: 'Tech & Agency' },
    { q: 'Digital Marketing Agencies', loc: 'Mumbai', category: 'Tech & Agency' },
    { q: 'Web & Mobile App Developers', loc: 'Gurgaon', category: 'Tech & Agency' },
    { q: 'Cybersecurity Firms', loc: 'Hyderabad', category: 'Tech & Agency' },
    { q: 'Cloud & DevOps Consultancies', loc: 'Pune', category: 'Tech & Agency' },
    { q: 'IT Hardware & Networking', loc: 'Chennai', category: 'Tech & Agency' },
    { q: 'SEO & Content Agencies', loc: 'Kolkata', category: 'Tech & Agency' },

    // 🏢 Real Estate & Infrastructure
    { q: 'Real Estate Developers', loc: 'Bangalore', category: 'Real Estate' },
    { q: 'Interior Designers & Decorators', loc: 'Delhi', category: 'Real Estate' },
    { q: 'Architects & Civil Engineers', loc: 'Ahmedabad', category: 'Real Estate' },
    { q: 'Commercial Property Brokers', loc: 'Gurgaon', category: 'Real Estate' },
    { q: 'Solar Panel & Clean Energy Installers', loc: 'Jaipur', category: 'Real Estate' },
    { q: 'Building Material Suppliers', loc: 'Surat', category: 'Real Estate' },
    { q: 'Co-working Spaces', loc: 'Mumbai', category: 'Real Estate' },

    // 🏨 Hospitality, Travel & Dining
    { q: 'Hotels & Resorts', loc: 'Goa', category: 'Hospitality' },
    { q: 'Fine Dining Restaurants', loc: 'Mumbai', category: 'Hospitality' },
    { q: 'Artisan Cafes & Bakeries', loc: 'Chandigarh', category: 'Hospitality' },
    { q: 'Banquets & Wedding Venues', loc: 'Jaipur', category: 'Hospitality' },
    { q: 'Tour Operators & Travel Agencies', loc: 'Shimla', category: 'Hospitality' },
    { q: 'Heritage Homestays & Villas', loc: 'Udaipur', category: 'Hospitality' },
    { q: 'Catering Services', loc: 'Lucknow', category: 'Hospitality' },

    // ⚖️ Finance, Legal & Professional
    { q: 'Chartered Accountants (CAs)', loc: 'Mumbai', category: 'Finance & Legal' },
    { q: 'Corporate Law Firms', loc: 'Delhi', category: 'Finance & Legal' },
    { q: 'Executive Recruitment & HR', loc: 'Bangalore', category: 'Finance & Legal' },
    { q: 'Wealth Managers & Financial Advisors', loc: 'Ahmedabad', category: 'Finance & Legal' },
    { q: 'Patent & IP Law Firms', loc: 'Hyderabad', category: 'Finance & Legal' },
    { q: 'Insurance Brokers', loc: 'Kolkata', category: 'Finance & Legal' },

    // 🏭 Manufacturing, Wholesale & Logistics
    { q: 'Textile Manufacturers & Exporters', loc: 'Surat', category: 'Manufacturing' },
    { q: 'Automobile Component Suppliers', loc: 'Chennai', category: 'Manufacturing' },
    { q: 'Packaging & Printing Solutions', loc: 'Indore', category: 'Manufacturing' },
    { q: 'Chemical & Polymer Manufacturers', loc: 'Vadodara', category: 'Manufacturing' },
    { q: 'Freight Forwarders & Logistics', loc: 'Mumbai', category: 'Manufacturing' },
    { q: 'Electronics & Hardware Wholesalers', loc: 'Delhi', category: 'Manufacturing' },
  ];

  const presetCategories = [
    'All',
    'Healthcare',
    'Tech & Agency',
    'Real Estate',
    'Hospitality',
    'Finance & Legal',
    'Manufacturing',
  ];

  // Live Scan Streaming State
  const [isScanning, setIsScanning] = useState(false);
  const [scanStep, setScanStep] = useState<string>('idle');
  const [scanLogs, setScanLogs] = useState<string[]>([]);
  const [scannedLeads, setScannedLeads] = useState<LiveScannedLead[]>([]);
  const [copiedText, setCopiedText] = useState<string | null>(null);
  const [showLogs, setShowLogs] = useState(true);

  const eventSourceRef = useRef<EventSource | null>(null);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(text);
    setTimeout(() => setCopiedText(null), 2000);
  };

  // Start Live Scan Stream
  const handleLiveScan = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!formData.query || !formData.location) return;

    // Reset scan state
    setIsScanning(true);
    setScanStep('starting');
    setScanLogs(['⚡ Initializing multi-source scanner engine...']);
    setScannedLeads([]);

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    const params = new URLSearchParams({
      query: formData.query,
      location: formData.location,
      limit: String(formData.limit || 10),
      provider: formData.preferred_provider || 'multi',
    });

    if (customAiKey.trim()) {
      params.append('ai_key', customAiKey.trim());
    }

    const es = new EventSource(`${apiUrl}/discovery/scan/stream?${params.toString()}`);
    eventSourceRef.current = es;

    es.addEventListener('status', (event) => {
      try {
        const data = JSON.parse(event.data);
        setScanStep(data.step || 'processing');
        if (data.message) {
          setScanLogs((prev) => [...prev, data.message]);
        }
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    });

    es.addEventListener('discovered', (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.message) {
          setScanLogs((prev) => [...prev, data.message]);
        }
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    });

    es.addEventListener('lead_ready', (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.lead) {
          setScannedLeads((prev) => {
            const exists = prev.some((l) => l.id === data.lead.id);
            if (exists) return prev;
            return [data.lead, ...prev];
          });
        }
        if (data.message) {
          setScanLogs((prev) => [...prev, data.message]);
        }
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    });

    es.addEventListener('complete', (event) => {
      try {
        const data = JSON.parse(event.data);
        setScanStep('complete');
        if (data.message) {
          setScanLogs((prev) => [...prev, data.message]);
        }
        setIsScanning(false);
        es.close();
      } catch (err) {
        console.error('SSE parse error:', err);
      }
    });

    es.addEventListener('error', (event) => {
      console.warn('SSE stream notice/error:', event);
      setScanLogs((prev) => [...prev, '⚠️ Live scan stream closed or completed.']);
      setIsScanning(false);
      es.close();
    });
  };

  const stopScan = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setIsScanning(false);
    setScanLogs((prev) => [...prev, '🛑 Scan stopped by user.']);
  };

  // Launch Background Job
  const handleBackgroundJob = async () => {
    try {
      await createJob.mutateAsync(formData);
      navigate('/jobs');
    } catch (error) {
      console.error('Failed to create background job:', error);
    }
  };

  // Export Scanned Leads to CSV
  const handleExportScanned = () => {
    if (scannedLeads.length === 0) return;
    const headers = [
      'Business Name',
      'Category',
      'Quality Score',
      'City',
      'Address',
      'Website',
      'Emails',
      'Phones',
      'Socials',
      'Key People',
      'Sources Consulted',
    ];

    const rows = scannedLeads.map((l) => [
      `"${l.business_name || ''}"`,
      `"${l.category || ''}"`,
      l.quality_score || 0,
      `"${l.city || ''}"`,
      `"${(l.address || '').replace(/"/g, '""')}"`,
      `"${l.website || ''}"`,
      `"${l.emails.map((e) => e.email).join(', ')}"`,
      `"${l.phones.map((p) => p.normalized || p.original).join(', ')}"`,
      `"${l.social_profiles.map((s) => s.url).join(', ')}"`,
      `"${(l.key_people || []).map((k) => `${k.name} (${k.role})`).join(', ')}"`,
      `"${(l.sources_consulted || []).join(', ')}"`,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `leads_${formData.query}_${formData.location}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="px-4 sm:px-0 max-w-7xl mx-auto space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-800 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
            Next-Gen Multi-Source Lead Discovery Engine
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
            Business Discovery & Real-Time Radar
          </h1>
          <p className="mt-2 text-blue-100 max-w-2xl text-base">
            Extract verified leads with phones, emails, executive names, and social footprints across Google Maps, SerpAPI, Firecrawl, and Gemini AI.
          </p>
        </div>
      </div>

      {/* Main Search Panel */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6 sm:p-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Category / Query */}
            <div className="lg:col-span-2">
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Target Business Category *
              </label>
              <div className="relative">
                <Search className="w-5 h-5 text-gray-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  value={formData.query}
                  onChange={(e) => setFormData({ ...formData, query: e.target.value })}
                  placeholder="e.g. Dentists, Real Estate, Solar Companies"
                  className="w-full pl-11 pr-4 py-2.5 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-semibold text-gray-900 placeholder-gray-400 shadow-sm"
                />
              </div>
            </div>

            {/* Location */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Location / City *
              </label>
              <input
                type="text"
                required
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                placeholder="e.g. Lucknow, India"
                className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-semibold text-gray-900 placeholder-gray-400 shadow-sm"
              />
            </div>

            {/* Limit */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-1.5">
                Target Results
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={formData.limit}
                onChange={(e) => setFormData({ ...formData, limit: Number(e.target.value) })}
                className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-semibold text-gray-900 shadow-sm"
              />
            </div>
          </div>

          {/* Advanced Multi-Source Settings Toggle */}
          <div className="pt-2 border-t border-gray-100">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="inline-flex items-center text-sm font-semibold text-blue-600 hover:text-blue-800"
            >
              {showAdvanced ? <ChevronUp className="w-4 h-4 mr-1" /> : <ChevronDown className="w-4 h-4 mr-1" />}
              {showAdvanced ? 'Hide Advanced Settings & AI Keys' : 'Configure Multi-Source Providers & Gemini/OpenRouter Keys'}
            </button>

            {showAdvanced && (
              <div className="mt-4 p-5 bg-gray-50 rounded-xl border border-gray-200 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-2">Discovery Source Engine</label>
                  <select
                    value={formData.preferred_provider}
                    onChange={(e) => setFormData({ ...formData, preferred_provider: e.target.value })}
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium"
                  >
                    <option value="multi">🌟 Multi-Source Hybrid (SerpAPI + Google Maps + Web)</option>
                    <option value="serpapi">⚡ SerpAPI Google Maps (Ultra-Fast 1-2s)</option>
                    <option value="apify">🗺️ Apify Google Maps Scraper (Deep Run)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-2">AI Extraction & Lead Scoring</label>
                  <label className="flex items-center gap-2 cursor-pointer mt-1.5">
                    <input
                      type="checkbox"
                      checked={aiEnabled}
                      onChange={(e) => setAiEnabled(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                    <span className="text-sm font-medium text-gray-700">Enable AI Lead Intelligence</span>
                  </label>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 mb-1">
                    Gemini / OpenRouter Key (Optional override)
                  </label>
                  <input
                    type="password"
                    value={customAiKey}
                    onChange={(e) => setCustomAiKey(e.target.value)}
                    placeholder="AIzaSy... or sk-or-..."
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-xs"
                  />
                  <span className="text-[11px] text-gray-500">Defaults to backend .env configuration if left empty.</span>
                </div>
              </div>
            )}
          </div>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-gray-100">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Multi-source extraction: Google Maps + Website Crawl + Search Radar + AI Heuristics</span>
            </div>

            <div className="flex items-center gap-3 w-full sm:w-auto">
              {/* Button 1: Live Scan (Starts streaming immediately!) */}
              <button
                type="button"
                onClick={() => handleLiveScan()}
                disabled={isScanning}
                className="flex-1 sm:flex-initial inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold rounded-xl shadow-md hover:shadow-lg transition-all disabled:opacity-50"
              >
                {isScanning ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Scanning & Streaming...
                  </>
                ) : (
                  <>
                    <Zap className="w-5 h-5 mr-2 text-yellow-300 fill-yellow-300" />
                    ⚡ Quick Live Scan
                  </>
                )}
              </button>

              {/* Button 2: Background Job */}
              <button
                type="button"
                onClick={handleBackgroundJob}
                disabled={createJob.isPending || isScanning}
                className="inline-flex items-center justify-center px-5 py-3 bg-gray-100 hover:bg-gray-200 text-gray-800 font-medium rounded-xl border border-gray-200 transition-colors disabled:opacity-50 text-sm"
              >
                {createJob.isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                🚀 Background Job
              </button>

              {isScanning && (
                <button
                  type="button"
                  onClick={stopScan}
                  className="px-4 py-3 bg-red-100 hover:bg-red-200 text-red-700 text-sm font-semibold rounded-xl"
                >
                  Stop
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Live Scan Results & Terminal Stream Section */}
      {(isScanning || scannedLeads.length > 0 || scanLogs.length > 0) && (
        <div className="space-y-6">
          {/* Stream Progress Header */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className={`inline-block w-3 h-3 rounded-full ${isScanning ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'}`}></span>
                <h2 className="text-xl font-bold text-gray-900">
                  {isScanning ? 'Live Multi-Source Scan in Progress...' : 'Live Scan Results'}
                </h2>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Found <span className="font-semibold text-blue-600">{scannedLeads.length}</span> leads ready with verified contacts.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowLogs(!showLogs)}
                className="inline-flex items-center px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-semibold rounded-lg border border-gray-200"
              >
                <Terminal className="w-3.5 h-3.5 mr-1.5" />
                {showLogs ? 'Hide Live Terminal' : 'Show Live Terminal'}
              </button>

              {scannedLeads.length > 0 && (
                <button
                  onClick={handleExportScanned}
                  className="inline-flex items-center px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold rounded-xl shadow-sm"
                >
                  <Download className="w-4 h-4 mr-1.5" />
                  Export {scannedLeads.length} Leads (CSV)
                </button>
              )}
            </div>
          </div>

          {/* Live Terminal Log Drawer */}
          {showLogs && (
            <div className="bg-slate-900 text-slate-100 rounded-xl p-4 font-mono text-xs shadow-inner max-h-48 overflow-y-auto space-y-1 border border-slate-800">
              <div className="flex items-center justify-between text-slate-400 pb-1 mb-2 border-b border-slate-800">
                <span>[SCAN LOG STREAM]</span>
                <span className="text-[10px] uppercase">{scanStep}</span>
              </div>
              {scanLogs.map((log, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-blue-400 select-none">&gt;</span>
                  <span className={log.includes('✅') ? 'text-emerald-300' : log.includes('⚡') ? 'text-cyan-300' : 'text-slate-200'}>
                    {log}
                  </span>
                </div>
              ))}
              {isScanning && (
                <div className="flex items-center gap-2 text-slate-400 italic pt-1">
                  <Loader2 className="w-3 h-3 animate-spin text-blue-400" />
                  <span>Extracting from sources in real-time...</span>
                </div>
              )}
            </div>
          )}

          {/* Scanned Leads Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {scannedLeads.map((lead) => {
              const quality = lead.quality_score || 50;
              const qualityBadgeColor =
                quality >= 80 ? 'bg-emerald-100 text-emerald-800 border-emerald-200' :
                quality >= 60 ? 'bg-blue-100 text-blue-800 border-blue-200' :
                'bg-amber-100 text-amber-800 border-amber-200';

              return (
                <div
                  key={lead.id}
                  className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 hover:text-blue-600 transition-colors">
                          <Link to={`/leads/${lead.id}`}>{lead.business_name}</Link>
                        </h3>
                        <p className="text-xs font-medium text-gray-500 mt-0.5">
                          {lead.category || 'Business'} • {lead.city || 'India'}
                        </p>
                      </div>

                      <span className={`px-2.5 py-1 text-xs font-bold rounded-full border ${qualityBadgeColor}`}>
                        ★ Score {quality}%
                      </span>
                    </div>

                    {/* Sources Consulted Pills */}
                    {lead.sources_consulted && lead.sources_consulted.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-3">
                        {lead.sources_consulted.map((src, i) => (
                          <span key={i} className="px-2 py-0.5 bg-slate-100 text-slate-700 text-[10px] font-semibold rounded-md border border-slate-200">
                            {src}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Description / Summary */}
                    {lead.description && (
                      <p className="text-xs text-gray-600 line-clamp-2 mb-4 bg-gray-50 p-2.5 rounded-lg border border-gray-100">
                        {lead.description}
                      </p>
                    )}

                    {/* Key People */}
                    {lead.key_people && lead.key_people.length > 0 && (
                      <div className="mb-4 flex items-center gap-2 p-2 bg-indigo-50/70 border border-indigo-100 rounded-lg">
                        <UserCheck className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                        <div className="text-xs">
                          <span className="font-semibold text-indigo-900">{lead.key_people[0].name}</span>
                          <span className="text-indigo-600 ml-1">({lead.key_people[0].role})</span>
                        </div>
                      </div>
                    )}

                    {/* Contacts Summary */}
                    <div className="space-y-2 mb-4">
                      {/* Phones */}
                      {lead.phones && lead.phones.length > 0 ? (
                        <div className="flex flex-wrap gap-2 items-center">
                          <Phone className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                          {lead.phones.slice(0, 2).map((ph, i) => {
                            const val = ph.normalized || ph.original || '';
                            return (
                              <button
                                key={i}
                                onClick={() => handleCopy(val)}
                                title="Click to copy"
                                className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-50 text-emerald-800 text-xs rounded-md border border-emerald-200 hover:bg-emerald-100"
                              >
                                <span>{val}</span>
                                {copiedText === val ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3 opacity-60" />}
                              </button>
                            );
                          })}
                        </div>
                      ) : null}

                      {/* Emails */}
                      {lead.emails && lead.emails.length > 0 ? (
                        <div className="flex flex-wrap gap-2 items-center">
                          <Mail className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" />
                          {lead.emails.slice(0, 2).map((em, i) => (
                            <button
                              key={i}
                              onClick={() => handleCopy(em.email)}
                              title="Click to copy"
                              className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-800 text-xs rounded-md border border-blue-200 hover:bg-blue-100"
                            >
                              <span>{em.email}</span>
                              {copiedText === em.email ? <Check className="w-3 h-3 text-blue-600" /> : <Copy className="w-3 h-3 opacity-60" />}
                            </button>
                          ))}
                        </div>
                      ) : null}

                      {/* Socials */}
                      {lead.social_profiles && lead.social_profiles.length > 0 ? (
                        <div className="flex flex-wrap gap-2 items-center pt-1">
                          <Share2 className="w-3.5 h-3.5 text-purple-600 flex-shrink-0" />
                          {lead.social_profiles.slice(0, 3).map((soc, i) => (
                            <a
                              key={i}
                              href={soc.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-2 py-0.5 bg-purple-50 text-purple-800 hover:bg-purple-100 text-xs rounded-md border border-purple-200 inline-flex items-center gap-1"
                            >
                              <span>{soc.platform}</span>
                              <ExternalLink className="w-2.5 h-2.5" />
                            </a>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  </div>

                  {/* Card Footer */}
                  <div className="pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
                    {lead.website ? (
                      <a
                        href={lead.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-600 hover:text-blue-600 font-medium inline-flex items-center gap-1"
                      >
                        <Globe className="w-3.5 h-3.5" />
                        Visit Website
                      </a>
                    ) : (
                      <span className="text-gray-400">No Website</span>
                    )}

                    <Link
                      to={`/leads/${lead.id}`}
                      className="font-semibold text-blue-600 hover:text-blue-800 inline-flex items-center gap-0.5"
                    >
                      View Details &rarr;
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Suggested Search Prompts & Industry Presets */}
      <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 border border-blue-200/80 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="font-bold text-blue-950 text-base flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500 fill-amber-500" />
              ⚡ One-Click Popular Discoveries
            </h3>
            <p className="text-xs text-blue-700/80 mt-0.5">
              Click any verified industry preset below to auto-fill search parameters and start extracting leads
            </p>
          </div>

          <span className="text-[11px] font-bold text-indigo-700 bg-indigo-100/80 px-2.5 py-1 rounded-full self-start sm:self-auto">
            {popularPresets.length} Verified Presets
          </span>
        </div>

        {/* Category Tabs */}
        <div className="flex flex-wrap gap-1.5 pt-1 border-t border-blue-200/50">
          {presetCategories.map((cat) => {
            const isActive = selectedCategoryTab === cat;
            return (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategoryTab(cat)}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-white/80 text-blue-900 hover:bg-white hover:text-blue-700 border border-blue-200/60'
                }`}
              >
                {cat}
              </button>
            );
          })}
        </div>

        {/* Presets Cloud */}
        <div className="flex flex-wrap gap-2 pt-1">
          {popularPresets
            .filter((p) => selectedCategoryTab === 'All' || p.category === selectedCategoryTab)
            .map((item, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setFormData({ ...formData, query: item.q, location: item.loc });
                  window.scrollTo({ top: 180, behavior: 'smooth' });
                }}
                className="group inline-flex items-center gap-1.5 px-3 py-1.5 bg-white text-gray-800 text-xs font-semibold rounded-xl border border-blue-200/80 shadow-sm hover:border-blue-500 hover:bg-blue-600 hover:text-white transition-all transform hover:-translate-y-0.5"
              >
                <span>{item.q}</span>
                <span className="text-[10px] opacity-60 group-hover:opacity-100 font-normal">in</span>
                <span className="text-blue-600 font-bold group-hover:text-amber-200">{item.loc}</span>
              </button>
            ))}
        </div>
      </div>

      {/* Discovered Leads Live Database Feed */}
      {(!isScanning && scannedLeads.length === 0) && (
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100">
            <div>
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-600" />
                Recently Discovered Businesses
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Latest leads saved in the database with verified contacts across previous discovery runs
              </p>
            </div>
            <Link
              to="/leads"
              className="text-xs font-semibold text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
            >
              <span>View All {recentDiscoveredLeads?.total || 0} Leads</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>

          {recentLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            </div>
          ) : recentDiscoveredLeads?.items && recentDiscoveredLeads.items.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentDiscoveredLeads.items.map((lead) => (
                <div
                  key={lead.id}
                  className="bg-gray-50/60 rounded-xl p-4 border border-gray-200/80 hover:border-blue-300 hover:bg-blue-50/20 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="font-bold text-gray-900 text-sm hover:text-blue-600">
                      <Link to={`/leads/${lead.id}`}>{lead.business_name}</Link>
                    </div>
                    <div className="text-xs text-gray-500 mt-0.5">
                      {lead.category || 'Business'} • {lead.city || 'India'}
                    </div>

                    <div className="flex items-center gap-3 mt-3 text-xs">
                      <span className="inline-flex items-center text-blue-700 font-semibold">
                        <Mail className="w-3.5 h-3.5 mr-1" />
                        {lead.email_count || 0}
                      </span>
                      <span className="inline-flex items-center text-emerald-700 font-semibold">
                        <Phone className="w-3.5 h-3.5 mr-1" />
                        {lead.phone_count || 0}
                      </span>
                      <span className="inline-flex items-center text-purple-700 font-semibold">
                        <Share2 className="w-3.5 h-3.5 mr-1" />
                        {lead.social_count || 0}
                      </span>
                      <span className="text-[10px] uppercase font-bold text-slate-500 px-1.5 py-0.5 bg-slate-200 rounded">
                        {lead.source_provider}
                      </span>
                    </div>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-gray-200/60 flex items-center justify-between text-xs">
                    {lead.website ? (
                      <a
                        href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-gray-500 hover:text-blue-600 inline-flex items-center gap-1 text-[11px]"
                      >
                        <Globe className="w-3 h-3" />
                        Website
                      </a>
                    ) : (
                      <span className="text-gray-400 text-[11px]">No Website</span>
                    )}

                    <Link
                      to={`/leads/${lead.id}`}
                      className="text-blue-600 hover:text-blue-800 font-semibold text-[11px]"
                    >
                      View &rarr;
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center py-6 text-sm text-gray-500">
              No discovered leads yet. Start by searching above!
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default Discovery;
