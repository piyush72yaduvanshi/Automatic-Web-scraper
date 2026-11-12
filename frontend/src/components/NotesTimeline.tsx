import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchNotes, deleteNote } from '../services/crmApi';
import { StickyNote, Pin, Edit2, Trash2, Plus } from 'lucide-react';
import type { NoteItem } from '../types';
import NoteEditor from './NoteEditor';

interface NotesTimelineProps {
  companyId?: string;
  contactId?: string;
  dealId?: string;
  leadId?: string;
}

const NotesTimeline: React.FC<NotesTimelineProps> = ({ companyId, contactId, dealId, leadId }) => {
  const queryClient = useQueryClient();
  const [showEditor, setShowEditor] = useState(false);
  const [editingNote, setEditingNote] = useState<NoteItem | undefined>();

  const { data: notes, isLoading } = useQuery<NoteItem[]>({
    queryKey: ['notes', companyId, contactId, dealId, leadId],
    queryFn: async () => {
      return await fetchNotes({
        company_id: companyId,
        contact_id: contactId,
        deal_id: dealId,
        lead_id: leadId,
        limit: 100,
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return await deleteNote(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notes'] });
    },
  });

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleEdit = (note: NoteItem) => {
    setEditingNote(note);
    setShowEditor(true);
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this note?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleCloseEditor = () => {
    setShowEditor(false);
    setEditingNote(undefined);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <StickyNote className="w-5 h-5 text-yellow-400" />
          <h3 className="text-lg font-bold text-white">Notes</h3>
          <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-slate-800 text-slate-300">
            {notes?.length || 0}
          </span>
        </div>
        <button
          onClick={() => setShowEditor(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-400 rounded-lg text-xs font-semibold transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Note
        </button>
      </div>

      {/* Timeline */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-slate-400">
            <div className="w-6 h-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mx-auto mb-2" />
            Loading notes...
          </div>
        ) : notes?.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500 bg-slate-800/30 rounded-xl border border-slate-800">
            No notes yet. Click "Add Note" to create one.
          </div>
        ) : (
          notes?.map((note) => (
            <div
              key={note.id}
              className={`p-4 rounded-xl border transition-all ${
                note.is_pinned
                  ? 'bg-yellow-500/5 border-yellow-500/20'
                  : 'bg-slate-800/30 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  {note.is_pinned && (
                    <Pin className="w-4 h-4 text-yellow-400 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-slate-400">
                      {formatDate(note.created_at)}
                      {note.created_by && ` • by ${note.created_by}`}
                    </div>
                    {(note.company_name || note.contact_name || note.deal_title) && (
                      <div className="text-xs text-slate-500 mt-0.5">
                        {[note.company_name, note.contact_name, note.deal_title]
                          .filter(Boolean)
                          .join(' • ')}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleEdit(note)}
                    className="p-1.5 hover:bg-slate-700 rounded-lg transition-colors group"
                    title="Edit note"
                  >
                    <Edit2 className="w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-400" />
                  </button>
                  <button
                    onClick={() => handleDelete(note.id)}
                    disabled={deleteMutation.isPending}
                    className="p-1.5 hover:bg-red-500/10 rounded-lg transition-colors group"
                    title="Delete note"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-slate-400 group-hover:text-red-400" />
                  </button>
                </div>
              </div>
              
              <div className="text-sm text-slate-300 whitespace-pre-wrap break-words">
                {note.content}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Editor Modal */}
      {showEditor && (
        <NoteEditor
          companyId={companyId}
          contactId={contactId}
          dealId={dealId}
          leadId={leadId}
          existingNote={editingNote}
          onClose={handleCloseEditor}
        />
      )}
    </div>
  );
};

export default NotesTimeline;
