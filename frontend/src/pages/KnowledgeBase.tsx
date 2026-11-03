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
} from 'lucide-react';

const KnowledgeBase: React.FC = () => {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('SERVICE_OFFERING');
  const [content, setContent] = useState('');

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-blue-600" />
            Knowledge Base & RAG Engine
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Store company playbooks, service definitions, case studies, and search them with hybrid vector embeddings.
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold shadow-sm"
        >
          <Plus className="w-4 h-4" /> Add Knowledge Doc
        </button>
      </div>

      {/* Semantic Search Console */}
      <div className="bg-white border rounded-lg p-5 shadow-sm space-y-3">
        <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
          <Sparkles className="w-4 h-4 text-blue-600" /> Semantic RAG Search Playground
        </h3>
        <p className="text-xs text-slate-500">
          Search stored company knowledge using vector embeddings and keyword fallback matching.
        </p>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Ask or query your knowledge base (e.g. 'What services do we offer for healthcare?')..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1 px-3 py-2 border rounded-md text-xs focus:ring-1 focus:ring-blue-500"
          />
          <button
            onClick={handleSearch}
            disabled={isSearching || !searchQuery}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50"
          >
            <Search className="w-3.5 h-3.5" /> {isSearching ? 'Searching...' : 'Search RAG'}
          </button>
        </div>

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="mt-4 space-y-2 pt-2 border-t">
            <div className="text-xs font-semibold text-slate-700">Top Semantic Matches:</div>
            {searchResults.map((r, i) => (
              <div key={i} className="p-3 bg-slate-50 rounded border text-xs space-y-1">
                <div className="flex items-center justify-between text-slate-500 text-[11px]">
                  <span className="font-semibold text-slate-800">{r.document_title} ({r.category})</span>
                  <span>Score: {r.relevance_score}</span>
                </div>
                <p className="text-slate-700 font-sans">{r.chunk_text}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stored Documents Grid */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-slate-800">Knowledge Documents ({documents?.length || 0})</h3>
        {isLoading ? (
          <div className="p-8 text-center text-xs text-slate-400 bg-white border rounded">Loading knowledge docs...</div>
        ) : documents?.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500 bg-white border rounded-lg">
            No knowledge documents uploaded. Add your company profile, offerings, or sales scripts.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents?.map((d) => (
              <div key={d.id} className="bg-white border rounded-lg p-4 shadow-sm space-y-2.5">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-500" />
                    <h4 className="text-xs font-bold text-slate-900 line-clamp-1">{d.title}</h4>
                  </div>
                  <span className="text-[10px] bg-slate-100 text-slate-600 font-medium px-2 py-0.5 rounded">
                    {d.category}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 flex justify-between pt-2 border-t">
                  <span>{d.chunks_count} chunks embedded</span>
                  <span>{new Date(d.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Document Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Add Knowledge Document</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Document Title</label>
                <input
                  type="text"
                  placeholder="e.g. Core Services & Pricing Playbook"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
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
                <label className="text-xs font-semibold text-slate-700 block mb-1">Document Content</label>
                <textarea
                  rows={8}
                  placeholder="Paste article, sales script, or services text here. It will be automatically chunked and embedded..."
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs font-sans"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <button onClick={() => setShowAddModal(false)} className="px-3 py-1.5 border rounded text-xs text-slate-700">
                Cancel
              </button>
              <button
                onClick={() => title && content && createMutation.mutate({ title, category, content })}
                disabled={!title || !content || createMutation.isPending}
                className="px-4 py-1.5 bg-blue-600 text-white rounded text-xs font-semibold hover:bg-blue-700"
              >
                Chunk & Embed Document
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBase;
