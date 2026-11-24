import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { KnowledgeDocItem } from '../types';
import {
  BookOpen,
  Plus,
  Search,
  Sparkles,
  FileText,
  Cpu,
  Layers,
  Copy,
  Check,
} from 'lucide-react';

const KnowledgeBase: React.FC = () => {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('SERVICE_OFFERING');
  const [content, setContent] = useState('');
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  // Semantic search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // 1. Fetch Documents
  const { data: documents, isLoading } = useQuery<KnowledgeDocItem[]>({
    queryKey: ['knowledge_docs'],
    queryFn: async () => {
      const res = await api.get('/knowledge/documents');
      return res.data;
    },
  });

  // 2. Create Document Mutation
  const createMutation = useMutation({
    mutationFn: async (payload: any) => {
      await api.post('/knowledge/documents', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge_docs'] });
      setShowAddModal(false);
      setTitle('');
      setContent('');
    },
  });

  const handleSearch = async () => {
    if (!searchQuery) return;
    setIsSearching(true);
    try {
      const res = await api.post('/knowledge/search', { query: searchQuery, limit: 5 });
      setSearchResults(res.data.results || []);
    } catch (e: any) {
      alert(`Search failed: ${e.message}`);
    } finally {
      setIsSearching(false);
    }
  };

  const copyChunk = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#0E1424] border border-slate-800 p-6 rounded-2xl shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
              <BookOpen className="w-7 h-7 text-indigo-400" />
              Knowledge Base &amp; pgvector RAG
            </h1>
            <span className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1">
              <Cpu className="w-3 h-3 text-indigo-400" />
              pgvector 768-dim
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-400">
            Store company playbooks, offerings, ICP profiles, and query them with hybrid cosine similarity and lexical citations.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/20 transition-all shrink-0"
        >
          <Plus className="w-4 h-4" /> Add Knowledge Doc
        </button>
      </div>

      {/* Semantic Search Console */}
      <div className="rounded-2xl bg-[#0E1424] border border-slate-800 p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" /> Semantic RAG Search Playground
          </h3>
          <span className="text-[10px] text-slate-400 flex items-center gap-1">
            <Layers className="w-3.5 h-3.5 text-cyan-400" /> Native Cosine Distance (&lt;=&gt;)
          </span>
        </div>

        <p className="text-xs text-slate-400">
          Query stored internal knowledge. AI reasoning agents inject retrieved chunks into cold emails, objections, and ICP qualification.
        </p>

        <div className="flex flex-col sm:flex-row gap-2.5">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
            <input
              type="text"
              placeholder="Ask anything (e.g. 'How do we handle pricing resistance?' or 'What is our healthcare ICP?')..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={isSearching || !searchQuery}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 disabled:opacity-50 transition shadow-md shadow-indigo-600/20"
          >
            {isSearching ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Searching Vector Index...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Search RAG</span>
              </>
            )}
          </button>
        </div>

        {/* Search Results Display */}
        {searchResults.length > 0 && (
          <div className="mt-5 space-y-3 pt-4 border-t border-slate-800">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-200">Top Semantic Matches ({searchResults.length}):</span>
              <span className="text-[11px] text-slate-500">Sorted by Cosine Relevance</span>
            </div>

            <div className="grid grid-cols-1 gap-3">
              {searchResults.map((r, i) => (
                <div
                  key={i}
                  className="p-4 bg-slate-900/80 hover:bg-slate-900 rounded-xl border border-slate-800/90 text-xs space-y-2 transition"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-full bg-indigo-500/20 text-indigo-300 font-bold text-[10px] flex items-center justify-center border border-indigo-500/30">
                        {i + 1}
                      </span>
                      <span className="font-bold text-white">{r.document_title}</span>
                      <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                        {r.category}
                      </span>
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        Relevance: {r.relevance_score}
                      </span>
                      <button
                        onClick={() => copyChunk(r.chunk_text, i)}
                        className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition"
                        title="Copy chunk text"
                      >
                        {copiedIdx === i ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>
                  <p className="text-slate-300 font-sans leading-relaxed bg-black/20 p-2.5 rounded-lg border border-white/5">
                    {r.chunk_text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Stored Documents Grid */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white tracking-tight">
            Repository Documents ({documents?.length || 0})
          </h3>
          <span className="text-xs text-slate-500">Auto-chunked &amp; Vectorized</span>
        </div>

        {isLoading ? (
          <div className="p-12 text-center text-xs text-slate-400 bg-[#0E1424] border border-slate-800 rounded-xl">
            Loading repository knowledge docs...
          </div>
        ) : documents?.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400 bg-[#0E1424] border border-slate-800 rounded-xl space-y-2">
            <p>No knowledge documents uploaded yet.</p>
            <p className="text-slate-500">Add sales scripts, case studies, or service offerings to activate RAG.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents?.map((d) => (
              <div
                key={d.id}
                className="bg-[#0E1424] border border-slate-800 rounded-xl p-5 shadow-md space-y-3 hover:border-slate-700 transition"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="p-2 rounded-lg bg-indigo-500/15 text-indigo-400 shrink-0">
                      <FileText className="w-4 h-4" />
                    </div>
                    <h4 className="text-xs font-bold text-white truncate">{d.title}</h4>
                  </div>
                  <span className="text-[10px] bg-slate-800 text-slate-300 font-semibold px-2 py-0.5 rounded shrink-0 border border-slate-700/60">
                    {d.category}
                  </span>
                </div>

                <div className="text-[11px] text-slate-400 flex justify-between items-center pt-2.5 border-t border-slate-800/80">
                  <span className="flex items-center gap-1 text-cyan-400">
                    <Cpu className="w-3 h-3" />
                    {d.chunks_count} vector chunks
                  </span>
                  <span>{new Date(d.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Document Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0E1424] border border-slate-800 rounded-2xl shadow-2xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-indigo-400" />
                Add Knowledge Document
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3.5">
              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Document Title</label>
                <input
                  type="text"
                  placeholder="e.g. Core Services & Pricing Playbook 2026"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700/80 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="SERVICE_OFFERING">Service Offering</option>
                  <option value="COMPANY_PROFILE">Company Profile</option>
                  <option value="ICP">Ideal Customer Profile</option>
                  <option value="CASE_STUDY">Case Study</option>
                  <option value="EMAIL_TEMPLATE">Email Template</option>
                  <option value="OBJECTION_HANDLING">Objection Handling</option>
                  <option value="PLAYBOOK">Sales Playbook</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-300 block mb-1">Document Content</label>
                <textarea
                  rows={8}
                  placeholder="Paste article, sales script, or services text here. It will be automatically chunked and embedded with pgvector..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-sans"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2.5 pt-3 border-t border-slate-800">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 border border-slate-700 rounded-xl text-xs font-medium text-slate-300 hover:bg-slate-800 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => title && content && createMutation.mutate({ title, category, content })}
                disabled={!title || !content || createMutation.isPending}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/25 transition disabled:opacity-50"
              >
                {createMutation.isPending ? 'Vectorizing...' : 'Chunk & Embed Document'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBase;
