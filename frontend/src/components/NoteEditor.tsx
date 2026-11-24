import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createNote, updateNote, NoteCreateData, NoteUpdateData } from '../services/crmApi';
import { StickyNote, X, Check, Pin } from 'lucide-react';
import type { NoteItem } from '../types';

interface NoteEditorProps {
  companyId?: string;
  contactId?: string;
  dealId?: string;
  leadId?: string;
  existingNote?: NoteItem;
  onClose: () => void;
}

const NoteEditor: React.FC<NoteEditorProps> = ({
  companyId,
  contactId,
  dealId,
  leadId,
  existingNote,
  onClose,
}) => {
  const queryClient = useQueryClient();
  const [content, setContent] = useState(existingNote?.content || '');
  const [isPinned, setIsPinned] = useState(existingNote?.is_pinned || false);

  const createMutation = useMutation({
    mutationFn: async (data: NoteCreateData) => {
      return await createNote(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: NoteUpdateData }) => {
      return await updateNote(id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!content.trim()) return;

    if (existingNote) {
      updateMutation.mutate({
        id: existingNote.id,
        data: { content, is_pinned: isPinned },
      });
    } else {
      createMutation.mutate({
        content,
        company_id: companyId,
        contact_id: contactId,
        deal_id: dealId,
        lead_id: leadId,
        is_pinned: isPinned,
      });
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;
  const isError = createMutation.isError || updateMutation.isError;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#0A0E1A] border border-slate-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
              <StickyNote className="w-5 h-5 text-yellow-400" />
            </div>
            <h2 className="text-lg font-bold text-white">
              {existingNote ? 'Edit Note' : 'Create Note'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Pin Toggle */}
          <div className="flex items-center justify-between p-3 bg-slate-800/30 rounded-xl border border-slate-800">
            <div className="flex items-center gap-2">
              <Pin className="w-4 h-4 text-slate-400" />
              <span className="text-sm text-slate-300">Pin this note to the top</span>
            </div>
            <button
              type="button"
              onClick={() => setIsPinned(!isPinned)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                isPinned ? 'bg-indigo-500' : 'bg-slate-700'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  isPinned ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Content */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">
              Note Content *
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={12}
              required
              placeholder="Enter your note here... 

You can add:
• Key discussion points
• Action items
• Follow-up reminders
• Important observations"
              className="w-full px-3.5 py-2.5 bg-[#0E1424] border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none font-mono"
            />
            <div className="mt-2 text-xs text-slate-500">
              {content.length} characters
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-semibold transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !content.trim()}
              className="flex-1 px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  {existingNote ? 'Update Note' : 'Create Note'}
                </>
              )}
            </button>
          </div>

          {isError && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-sm text-red-400">
              Error saving note. Please try again.
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default NoteEditor;
