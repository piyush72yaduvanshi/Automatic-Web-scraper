import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import {
  BrainCircuit,
  Sparkles,
  ShieldCheck,
  HelpCircle,
  AlertCircle,
  ArrowRight,
} from 'lucide-react';

const ResearchIntel: React.FC = () => {
  const [companyName, setCompanyName] = useState('Apex Dental Hospital');
  const [website, setWebsite] = useState('https://apexdental.com');
  const [category, setCategory] = useState('Dentistry & Oral Surgery');
  const [location, setLocation] = useState('Lucknow, Uttar Pradesh');
  const [rawText, setRawText] = useState('Apex Dental was founded by Dr. Rajesh Sharma. We offer dental implants, smile design, and Invisalign.');
  const [report, setReport] = useState<any>(null);

  // Fetch recent leads for quick load
  const { data: leads } = useQuery<any>({
    queryKey: ['quick_leads_select'],
    queryFn: async () => {
      const res = await api.get('/leads?page=1&page_size=10');
      return res.data;
    },
  });

  const researchMutation = useMutation({
    mutationFn: async (payload: any) => {
      const res = await api.post('/agents/company_research_agent/execute', payload);
      return res.data;
    },
    onSuccess: (data) => {
      setReport(data.result);
    },
    onError: (err: any) => {
      alert(`Research failed: ${err.response?.data?.detail || err.message}`);
    },
  });

  const handleSelectExistingLead = (lead: any) => {
    setCompanyName(lead.business_name);
    setWebsite(lead.website || '');
    setCategory(lead.category || '');
    setLocation(`${lead.city || ''}, ${lead.state || ''}`.trim());
    setRawText(lead.description || '');
  };

  const handleRunResearch = () => {
    researchMutation.mutate({
      company_name: companyName,
      website,
      category,
      location,
      raw_text: rawText,
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <BrainCircuit className="w-6 h-6 text-blue-600" />
          Company Research & Intelligence Engine
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Deep B2B dossier generator strictly distinguishing verified evidence from AI inferences and unknowns.
        </p>
      </div>

      {/* Input Form and Presets */}
      <div className="bg-white border rounded-lg p-5 shadow-sm space-y-4">
        {leads?.items?.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-500 font-medium">Quick load from discovered leads:</span>
            {leads.items.slice(0, 4).map((l: any) => (
              <button
                key={l.id}
                onClick={() => handleSelectExistingLead(l)}
                className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-2.5 py-1 rounded-md transition-colors"
              >
                {l.business_name}
              </button>
            ))}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">Company Name</label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="w-full px-3 py-2 border rounded text-xs"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">Website URL</label>
            <input
              type="text"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              className="w-full px-3 py-2 border rounded text-xs"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">Industry / Category</label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 border rounded text-xs"
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1">Location</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3 py-2 border rounded text-xs"
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1">Context / Scraped Content Snippets</label>
          <textarea
            rows={2}
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            className="w-full px-3 py-2 border rounded text-xs font-mono"
            placeholder="Paste raw website text or snippet context..."
          />
        </div>

        <button
          onClick={handleRunResearch}
          disabled={researchMutation.isPending || !companyName}
          className="w-full sm:w-auto px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold shadow-sm flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {researchMutation.isPending ? 'Synthesizing Dossier...' : 'Generate Intelligence Report'}
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Structured Intelligence Dossier */}
      {report && (
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-6 shadow-sm space-y-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-bold text-slate-900">{companyName} — Sales Dossier</h2>
                <span className="text-xs font-semibold bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full">
                  Confidence Score: {report.confidence_score || 80}/100
                </span>
              </div>
              <p className="text-xs text-slate-700 bg-slate-50 p-3.5 rounded border border-slate-100 leading-relaxed">
                {report.company_overview || report.summary}
              </p>
            </div>

            {/* Pain Points & Suggested Offering */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg bg-amber-50/70 border border-amber-200/80 space-y-2">
                <h3 className="text-xs font-bold text-amber-900 flex items-center gap-1.5 uppercase tracking-wider">
                  <AlertCircle className="w-4 h-4 text-amber-600" /> Identified Pain Points
                </h3>
                <ul className="list-disc list-inside text-xs text-amber-900 space-y-1">
                  {report.pain_points?.map((p: string, i: number) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>

              <div className="p-4 rounded-lg bg-blue-50/70 border border-blue-200/80 space-y-2">
                <h3 className="text-xs font-bold text-blue-900 flex items-center gap-1.5 uppercase tracking-wider">
                  <Sparkles className="w-4 h-4 text-blue-600" /> Suggested Service & Angle
                </h3>
                <p className="text-xs text-blue-950 font-semibold">{report.suggested_offering}</p>
                <p className="text-xs text-blue-800 leading-relaxed">{report.recommended_approach}</p>
              </div>
            </div>

            {/* Strict Truth Separation Columns */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 border-t border-slate-100 pt-5">
              {/* Column 1: Verified Facts */}
              <div className="p-4 rounded-lg bg-emerald-50/70 border border-emerald-200/80 space-y-2">
                <h4 className="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" /> Verified Facts (Evidence)
                </h4>
                <ul className="space-y-1 text-xs text-emerald-950">
                  {report.verified_facts?.map((f: string, i: number) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Column 2: Inferred Insights */}
              <div className="p-4 rounded-lg bg-indigo-50/70 border border-indigo-200/80 space-y-2">
                <h4 className="text-xs font-bold text-indigo-900 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-indigo-600" /> Inferred Insights (Unverified)
                </h4>
                <ul className="space-y-1 text-xs text-indigo-950">
                  {report.inferred_insights?.map((ins: string, i: number) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-indigo-400 font-bold">•</span>
                      <span>{ins}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Column 3: Unknowns */}
              <div className="p-4 rounded-lg bg-slate-100 border border-slate-200 space-y-2">
                <h4 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <HelpCircle className="w-4 h-4 text-slate-500" /> Unknowns (Needs Discovery)
                </h4>
                <ul className="space-y-1 text-xs text-slate-700">
                  {report.unknowns?.map((u: string, i: number) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-slate-400 font-bold">•</span>
                      <span>{u}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResearchIntel;
