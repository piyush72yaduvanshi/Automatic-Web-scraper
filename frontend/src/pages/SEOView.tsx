import React, { useState, useEffect } from 'react';
import {
  Globe,
  Sparkles,
  FileText,
  RefreshCw,
} from 'lucide-react';
import { SEOProjectItem, SEOKeywordItem } from '../types';

export const SEOView: React.FC = () => {
  const [projects, setProjects] = useState<SEOProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [keywords, setKeywords] = useState<SEOKeywordItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [seedTopic, setSeedTopic] = useState<string>('');
  const [clustering, setClustering] = useState<boolean>(false);
  const [activeBrief, setActiveBrief] = useState<any | null>(null);
  const [briefKeyword, setBriefKeyword] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/seo/projects');
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
        if (data.length > 0 && !selectedProjectId) {
          setSelectedProjectId(data[0].id);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchKeywords = async (projectId: string) => {
    try {
      const res = await fetch(`/api/v1/seo/projects/${projectId}/keywords`);
      if (res.ok) setKeywords(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      fetchKeywords(selectedProjectId);
    }
  }, [selectedProjectId]);

  const handleClusterKeywords = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId || !seedTopic.trim()) return;
    setClustering(true);
    try {
      const res = await fetch(`/api/v1/seo/projects/${selectedProjectId}/clusters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ seed_topic: seedTopic }),
      });
      if (res.ok) {
        setMessage(`AI generated keywords & clusters for '${seedTopic}'!`);
        setSeedTopic('');
        fetchKeywords(selectedProjectId);
      }
    } catch {
      setMessage('Error clustering keywords.');
    } finally {
      setClustering(false);
    }
  };

  const handleCreateBrief = async (kw: SEOKeywordItem) => {
    try {
      const res = await fetch(`/api/v1/seo/keywords/${kw.id}/brief`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setActiveBrief(data.brief);
        setBriefKeyword(kw.keyword);
        fetchKeywords(selectedProjectId!);
      }
    } catch {
      setMessage('Error generating content brief.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center bg-gray-900 border border-gray-800 p-6 rounded-xl">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Globe className="w-7 h-7 text-indigo-400" />
            SEO &amp; Inbound Marketing Engine
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Keyword research, semantic clustering, search intent classification, content briefs, and meta drafting.
          </p>
        </div>
        <button
          onClick={() => selectedProjectId && fetchKeywords(selectedProjectId)}
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

      {/* Project Selector & Cluster Generator */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400 font-semibold uppercase">Project:</span>
            <select
              value={selectedProjectId || ''}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.target_domain})
                </option>
              ))}
            </select>
          </div>

          <form onSubmit={handleClusterKeywords} className="flex gap-2 w-full md:w-auto">
            <input
              type="text"
              required
              value={seedTopic}
              onChange={(e) => setSeedTopic(e.target.value)}
              placeholder="e.g. B2B Sales Automation"
              className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:outline-none"
            />
            <button
              type="submit"
              disabled={clustering}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              {clustering ? 'Clustering...' : 'Generate Clusters'}
            </button>
          </form>
        </div>
      </div>

      {/* Brief Drawer / Modal if active */}
      {activeBrief && (
        <div className="bg-gray-900 border border-indigo-500/40 rounded-xl p-5 space-y-3">
          <div className="flex justify-between items-center pb-2 border-b border-gray-800">
            <h3 className="font-bold text-white text-base flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-400" />
              Content Brief: {briefKeyword}
            </h3>
            <button onClick={() => setActiveBrief(null)} className="text-gray-400 hover:text-white text-sm">✕ Close</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-gray-300">
            <div>
              <div className="font-semibold text-gray-400 mb-1">Meta Title:</div>
              <div className="bg-gray-800/60 p-2 rounded text-white font-mono">{activeBrief.meta_title}</div>
            </div>
            <div>
              <div className="font-semibold text-gray-400 mb-1">Meta Description:</div>
              <div className="bg-gray-800/60 p-2 rounded text-white font-mono">{activeBrief.meta_description}</div>
            </div>
          </div>
          <div className="text-xs">
            <div className="font-semibold text-gray-400 mb-1">Suggested Headings (H1/H2):</div>
            <ul className="list-disc list-inside space-y-1 text-gray-300">
              {activeBrief.headings?.map((h: string, idx: number) => (
                <li key={idx}>{h}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Keywords Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-base font-semibold text-white mb-4">Target Keyword Clusters ({keywords.length})</h2>
        {loading ? (
          <div className="text-center py-8 text-gray-400">Loading keywords...</div>
        ) : keywords.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No keywords in this project yet. Use the cluster generator above!</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-gray-800/60 text-xs uppercase text-gray-400 border-b border-gray-700">
                <tr>
                  <th className="py-3 px-4">Keyword</th>
                  <th className="py-3 px-4">Cluster</th>
                  <th className="py-3 px-4">Search Intent</th>
                  <th className="py-3 px-4">Target Page</th>
                  <th className="py-3 px-4">Monthly Vol</th>
                  <th className="py-3 px-4">Brief &amp; Meta</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {keywords.map((kw) => (
                  <tr key={kw.id} className="hover:bg-gray-800/30">
                    <td className="py-3 px-4 font-medium text-white">{kw.keyword}</td>
                    <td className="py-3 px-4 text-xs text-gray-400">{kw.cluster_name}</td>
                    <td className="py-3 px-4 text-xs">
                      <span className={`px-2 py-0.5 rounded font-semibold ${
                        kw.search_intent === 'COMMERCIAL' ? 'bg-indigo-500/20 text-indigo-300' :
                        kw.search_intent === 'TRANSACTIONAL' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-gray-700 text-gray-300'
                      }`}>
                        {kw.search_intent}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs font-mono text-gray-400">{kw.target_page_type}</td>
                    <td className="py-3 px-4 text-xs font-semibold text-white">{kw.search_volume.toLocaleString()}</td>
                    <td className="py-3 px-4 text-xs">
                      {kw.status === 'BRIEF_CREATED' ? (
                        <span className="text-emerald-400 font-semibold">Brief Ready</span>
                      ) : (
                        <span className="text-gray-500">Pending</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleCreateBrief(kw)}
                        className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded text-xs font-medium inline-flex items-center gap-1"
                      >
                        <FileText className="w-3 h-3" /> Brief &amp; Meta
                      </button>
                    </td>
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
