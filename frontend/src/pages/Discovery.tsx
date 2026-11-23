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
    preferred_provider: 'local_maps',
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
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-indigo-900/90 via-[#18223a] to-[#0E1424] border border-indigo-500/20 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-indigo-500/10 to-transparent pointer-events-none" />
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-500/20 border border-indigo-500/30 backdrop-blur-md rounded-full text-xs font-semibold mb-3 text-indigo-300">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            Next-Gen Multi-Source Lead Discovery Engine
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Business Discovery & Real-Time Radar
          </h1>
          <p className="mt-2 text-slate-300 max-w-2xl text-xs sm:text-sm">
            Extract verified leads with phones, emails, executive names, and social footprints across Google Maps, SerpAPI, Firecrawl, and Gemini AI.
          </p>
        </div>
      </div>

      {/* Main Search Panel */}
      <div className="bg-[#0E1424] rounded-2xl shadow-sm border border-slate-800 overflow-hidden">
        <div className="p-6 sm:p-7 space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Category / Query */}
            <div className="lg:col-span-2">
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Target Business Category *
              </label>
              <div className="relative">
                <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  value={formData.query}
                  onChange={(e) => setFormData({ ...formData, query: e.target.value })}
                  placeholder="e.g. Dentists, Real Estate, Solar Companies"
                  className="w-full pl-10 pr-4 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-xs font-semibold text-white placeholder-slate-500 shadow-sm"
                />
              </div>
            </div>

            {/* Location */}
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Location / City *
              </label>
              <input
                type="text"
                required
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                placeholder="e.g. Lucknow, India"
                className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-xs font-semibold text-white placeholder-slate-500 shadow-sm"
              />
            </div>

            {/* Limit */}
            <div>
              <label className="block text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Target Results
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={formData.limit}
                onChange={(e) => setFormData({ ...formData, limit: Number(e.target.value) })}
                className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-xs font-semibold text-white shadow-sm"
              />
            </div>
          </div>

          {/* Advanced Multi-Source Settings Toggle */}
          <div className="pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="inline-flex items-center text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              {showAdvanced ? <ChevronUp className="w-3.5 h-3.5 mr-1" /> : <ChevronDown className="w-3.5 h-3.5 mr-1" />}
              {showAdvanced ? 'Hide Advanced Settings & AI Keys' : 'Configure Multi-Source Providers & Gemini/OpenRouter Keys'}
            </button>

            {showAdvanced && (
              <div className="mt-3.5 p-4 bg-[#131B2E] rounded-xl border border-slate-700/80 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1.5">Discovery Source Engine</label>
                  <select
                    value={formData.preferred_provider}
                    onChange={(e) => setFormData({ ...formData, preferred_provider: e.target.value })}
                    className="w-full px-3 py-2 bg-[#0E1424] border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="local_maps">🌟 Local Google Maps Scraper (100% Free & Unlimited, Port 8080)</option>
                    <option value="multi">Multi-Source Hybrid (Local Maps + Google Places + SerpAPI)</option>
                    <option value="google_places">Google Places API (Official Maps Platform)</option>
                    <option value="serpapi">SerpAPI Google Maps (Ultra-Fast 1-2s)</option>
                    <option value="apify">Apify Google Maps Scraper (Deep Run)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1.5">AI Extraction & Lead Scoring</label>
                  <label className="flex items-center gap-2 cursor-pointer mt-2">
                    <input
                      type="checkbox"
                      checked={aiEnabled}
                      onChange={(e) => setAiEnabled(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-700 bg-[#0E1424] text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-xs font-medium text-slate-300">Enable AI Lead Intelligence</span>
                  </label>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                    Gemini / OpenRouter Key (Optional override)
                  </label>
                  <input
                    type="password"
                    value={customAiKey}
                    onChange={(e) => setCustomAiKey(e.target.value)}
                    placeholder="AIzaSy... or sk-or-..."
                    className="w-full px-3 py-2 bg-[#0E1424] border border-slate-700 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                  <span className="text-[10px] text-slate-500 mt-1 block">Defaults to backend configuration if left empty.</span>
                </div>
              </div>
            )}
          </div>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-3 border-t border-slate-800">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Multi-source extraction: Google Maps + Website Crawl + Search Radar + AI Heuristics</span>
            </div>

            <div className="flex items-center gap-2.5 w-full sm:w-auto">
              {/* Button 1: Live Scan (Starts streaming immediately) */}
              <button
                type="button"
                onClick={() => handleLiveScan()}
                disabled={isScanning}
                className="flex-1 sm:flex-initial inline-flex items-center justify-center px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white font-semibold rounded-xl text-xs shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all disabled:opacity-50"
              >
                {isScanning ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                    Scanning & Streaming...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-1.5 text-yellow-300 fill-yellow-300" />
                    Quick Live Scan
                  </>
                )}
              </button>

              {/* Button 2: Background Job */}
              <button
                type="button"
                onClick={handleBackgroundJob}
                disabled={createJob.isPending || isScanning}
                className="inline-flex items-center justify-center px-4 py-2.5 bg-[#131B2E] hover:bg-slate-800 text-slate-200 font-medium rounded-xl border border-slate-700 transition-colors disabled:opacity-50 text-xs"
              >
                {createJob.isPending ? <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" /> : null}
                Background Job
              </button>

              {isScanning && (
                <button
                  type="button"
                  onClick={stopScan}
                  className="px-3.5 py-2.5 bg-red-500/20 hover:bg-red-500/30 text-red-300 text-xs font-semibold rounded-xl border border-red-500/40 transition-colors"
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
        <div className="space-y-5">
          {/* Stream Progress Header */}
          <div className="bg-[#0E1424] rounded-2xl shadow-sm border border-slate-800 p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className={`inline-block w-2.5 h-2.5 rounded-full ${isScanning ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
                <h2 className="text-base font-bold text-white">
                  {isScanning ? 'Live Multi-Source Scan in Progress...' : 'Live Scan Results'}
                </h2>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Found <span className="font-semibold text-indigo-400">{scannedLeads.length}</span> leads ready with verified contacts.
              </p>
            </div>

            <div className="flex items-center gap-2.5">
              <button
                onClick={() => setShowLogs(!showLogs)}
                className="inline-flex items-center px-3 py-1.5 bg-[#131B2E] hover:bg-slate-800 text-slate-300 text-xs font-semibold rounded-lg border border-slate-700 transition-colors"
              >
                <Terminal className="w-3.5 h-3.5 mr-1.5" />
                {showLogs ? 'Hide Live Terminal' : 'Show Live Terminal'}
              </button>

              {scannedLeads.length > 0 && (
                <button
                  onClick={handleExportScanned}
                  className="inline-flex items-center px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors"
                >
                  <Download className="w-3.5 h-3.5 mr-1.5" />
                  Export {scannedLeads.length} Leads (CSV)
                </button>
              )}
            </div>
          </div>

          {/* Live Terminal Log Drawer */}
          {showLogs && (
            <div className="bg-[#080C14] text-slate-200 rounded-xl p-4 font-mono text-xs shadow-inner max-h-48 overflow-y-auto space-y-1 border border-slate-800">
              <div className="flex items-center justify-between text-slate-500 pb-1 mb-2 border-b border-slate-800 text-[10px]">
                <span>[SCAN LOG STREAM]</span>
                <span className="uppercase text-indigo-400 font-semibold">{scanStep}</span>
              </div>
              {scanLogs.map((log, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <span className="text-indigo-400 select-none">&gt;</span>
                  <span className={log.includes('✅') ? 'text-emerald-300' : log.includes('⚡') ? 'text-cyan-300' : 'text-slate-300'}>
                    {log}
                  </span>
                </div>
              ))}
              {isScanning && (
                <div className="flex items-center gap-2 text-slate-500 italic pt-1">
                  <Loader2 className="w-3 h-3 animate-spin text-indigo-400" />
                  <span>Extracting from sources in real-time...</span>
                </div>
              )}
            </div>
          )}

          {/* Scanned Leads Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {scannedLeads.map((lead) => {
              const quality = lead.quality_score || 50;
              const qualityBadgeColor =
                quality >= 80 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                quality >= 60 ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' :
                'bg-amber-500/10 text-amber-400 border-amber-500/20';

              return (
                <div
                  key={lead.id}
                  className="bg-[#0E1424] rounded-2xl border border-slate-800 p-5 shadow-sm hover:border-slate-700 transition-all flex flex-col justify-between"
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-3 mb-2.5">
                      <div>
                        <h3 className="text-base font-bold text-white hover:text-indigo-400 transition-colors">
                          <Link to={`/leads/${lead.id}`}>{lead.business_name}</Link>
                        </h3>
                        <p className="text-[11px] font-medium text-slate-400 mt-0.5">
                          {lead.category || 'Business'} • {lead.city || 'India'}
                        </p>
                      </div>

                      <span className={`px-2 py-0.5 text-[10px] font-bold rounded-full border ${qualityBadgeColor}`}>
                        Score {quality}%
                      </span>
                    </div>

                    {/* Sources Consulted Pills */}
                    {lead.sources_consulted && lead.sources_consulted.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mb-2.5">
                        {lead.sources_consulted.map((src, i) => (
                          <span key={i} className="px-2 py-0.5 bg-[#131B2E] text-slate-400 text-[10px] font-semibold rounded-md border border-slate-700/60">
                            {src}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Description / Summary */}
                    {lead.description && (
                      <p className="text-xs text-slate-300 line-clamp-2 mb-3 bg-[#131B2E]/60 p-2.5 rounded-lg border border-slate-800">
                        {lead.description}
                      </p>
                    )}

                    {/* Key People */}
                    {lead.key_people && lead.key_people.length > 0 && (
                      <div className="mb-3 flex items-center gap-2 p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg">
                        <UserCheck className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                        <div className="text-xs">
                          <span className="font-semibold text-white">{lead.key_people[0].name}</span>
                          <span className="text-indigo-400 ml-1">({lead.key_people[0].role})</span>
                        </div>
                      </div>
                    )}

                    {/* Contacts Summary */}
                    <div className="space-y-1.5 mb-3">
                      {/* Phones */}
                      {lead.phones && lead.phones.length > 0 ? (
                        <div className="flex flex-wrap gap-2 items-center">
                          <Phone className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                          {lead.phones.slice(0, 2).map((ph, i) => {
                            const val = ph.normalized || ph.original || '';
                            return (
                              <button
                                key={i}
                                onClick={() => handleCopy(val)}
                                title="Click to copy"
                                className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-500/10 text-emerald-300 text-xs rounded-md border border-emerald-500/20 hover:bg-emerald-500/20"
                              >
                                <span>{val}</span>
                                {copiedText === val ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 opacity-60" />}
                              </button>
                            );
                          })}
                        </div>
                      ) : null}

                      {/* Emails */}
                      {lead.emails && lead.emails.length > 0 ? (
                        <div className="flex flex-wrap gap-2 items-center">
                          <Mail className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                          {lead.emails.slice(0, 2).map((em, i) => (
                            <button
                              key={i}
                              onClick={() => handleCopy(em.email)}
                              title="Click to copy"
                              className="inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-500/10 text-indigo-300 text-xs rounded-md border border-indigo-500/20 hover:bg-indigo-500/20"
                            >
                              <span>{em.email}</span>
                              {copiedText === em.email ? <Check className="w-3 h-3 text-indigo-400" /> : <Copy className="w-3 h-3 opacity-60" />}
                            </button>
                          ))}
                        </div>
                      ) : null}

                      {/* Socials */}
                      {lead.social_profiles && lead.social_profiles.length > 0 ? (
                        <div className="flex flex-wrap gap-2 items-center pt-0.5">
                          <Share2 className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                          {lead.social_profiles.slice(0, 3).map((soc, i) => (
                            <a
                              key={i}
                              href={soc.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-2 py-0.5 bg-purple-500/10 text-purple-300 hover:bg-purple-500/20 text-xs rounded-md border border-purple-500/20 inline-flex items-center gap-1"
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
                  <div className="pt-2.5 border-t border-slate-800 flex items-center justify-between text-xs">
                    {lead.website ? (
                      <a
                        href={lead.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-slate-400 hover:text-indigo-400 font-medium inline-flex items-center gap-1"
                      >
                        <Globe className="w-3.5 h-3.5" />
                        Visit Website
                      </a>
                    ) : (
                      <span className="text-slate-500">No Website</span>
                    )}

                    <Link
                      to={`/leads/${lead.id}`}
                      className="font-semibold text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-0.5"
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
      <div className="bg-[#0E1424] border border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="font-bold text-white text-base flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400 fill-amber-400" />
              One-Click Popular Discoveries
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Click any verified industry preset below to auto-fill search parameters and start extracting leads.
            </p>
          </div>

          <span className="text-[11px] font-bold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 rounded-full self-start sm:self-auto">
            {popularPresets.length} Verified Presets
          </span>
        </div>

        {/* Category Tabs */}
        <div className="flex flex-wrap gap-1.5 pt-1 border-t border-slate-800">
          {presetCategories.map((cat) => {
            const isActive = selectedCategoryTab === cat;
            return (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategoryTab(cat)}
                className={`px-3 py-1 text-xs font-bold rounded-lg transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-[#131B2E] text-slate-300 hover:bg-slate-800 border border-slate-700/80'
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
                className="group inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#131B2E] text-slate-200 text-xs font-semibold rounded-xl border border-slate-700/80 shadow-sm hover:border-indigo-500 hover:bg-indigo-600 hover:text-white transition-all transform hover:-translate-y-0.5"
              >
                <span>{item.q}</span>
                <span className="text-[10px] opacity-60 group-hover:opacity-100 font-normal">in</span>
                <span className="text-indigo-400 font-bold group-hover:text-amber-200">{item.loc}</span>
              </button>
            ))}
        </div>
      </div>

      {/* Discovered Leads Live Database Feed */}
      {(!isScanning && scannedLeads.length === 0) && (
        <div className="bg-[#0E1424] rounded-2xl border border-slate-800 shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Recently Discovered Businesses
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Latest leads saved in the database with verified contacts across previous discovery runs
              </p>
            </div>

            <Link
              to="/leads"
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-1"
            >
              <span>View All {recentDiscoveredLeads?.total || 0} Leads</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>

          {recentLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
            </div>
          ) : recentDiscoveredLeads?.items && recentDiscoveredLeads.items.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentDiscoveredLeads.items.map((lead) => (
                <div
                  key={lead.id}
                  className="bg-[#131B2E] rounded-xl p-4 border border-slate-800 hover:border-indigo-500/40 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="font-bold text-white text-sm hover:text-indigo-400 transition-colors">
                      <Link to={`/leads/${lead.id}`}>{lead.business_name}</Link>
                    </div>
                    <div className="text-xs text-slate-400 mt-0.5">
                      {lead.category || 'Business'} • {lead.city || 'India'}
                    </div>

                    <div className="flex items-center gap-3 mt-3 text-xs">
                      <span className="inline-flex items-center text-indigo-400 font-semibold">
                        <Mail className="w-3.5 h-3.5 mr-1" />
                        {lead.email_count || 0}
                      </span>
                      <span className="inline-flex items-center text-emerald-400 font-semibold">
                        <Phone className="w-3.5 h-3.5 mr-1" />
                        {lead.phone_count || 0}
                      </span>
                      <span className="inline-flex items-center text-purple-400 font-semibold">
                        <Share2 className="w-3.5 h-3.5 mr-1" />
                        {lead.social_count || 0}
                      </span>
                      <span className="text-[10px] uppercase font-bold text-slate-400 px-1.5 py-0.5 bg-slate-800 rounded">
                        {lead.source_provider}
                      </span>
                    </div>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-slate-800 flex items-center justify-between text-xs">
                    {lead.website ? (
                      <a
                        href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-slate-400 hover:text-indigo-400 inline-flex items-center gap-1 text-[11px]"
                      >
                        <Globe className="w-3 h-3" />
                        Website
                      </a>
                    ) : (
                      <span className="text-slate-500 text-[11px]">No Website</span>
                    )}

                    <Link
                      to={`/leads/${lead.id}`}
                      className="text-indigo-400 hover:text-indigo-300 font-semibold text-[11px]"
                    >
                      View &rarr;
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center py-6 text-xs text-slate-500">
              No discovered leads yet. Start by searching above!
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default Discovery;
