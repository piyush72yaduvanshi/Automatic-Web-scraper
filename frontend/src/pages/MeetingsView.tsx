import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  Plus,
  RefreshCw,
  Sparkles,
  Video,
} from 'lucide-react';

interface MeetingItem {
  id: string;
  title: string;
  company_name: string;
  contact_name: string;
  start_time: string;
  end_time: string;
  agenda?: string;
  meeting_url?: string;
  status: string;
  prep_notes?: string;
}

export const MeetingsView: React.FC = () => {
  const [meetings, setMeetings] = useState<MeetingItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showScheduleModal, setShowScheduleModal] = useState<boolean>(false);
  const [activeDossier, setActiveDossier] = useState<MeetingItem | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // Form State
  const [title, setTitle] = useState<string>('Sales Discovery Call');
  const [companyName, setCompanyName] = useState<string>('');
  const [startTime, setStartTime] = useState<string>('');
  const [agenda, setAgenda] = useState<string>('Initial capability review and workflow bottleneck analysis.');
  const [scheduling, setScheduling] = useState<boolean>(false);

  const fetchMeetings = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/meetings');
      if (res.ok) setMeetings(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMeetings();
  }, []);

  const handleScheduleMeeting = async (e: React.FormEvent) => {
    e.preventDefault();
    setScheduling(true);
    try {
      const res = await fetch('/api/v1/meetings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          company_name: companyName,
          start_time: startTime || new Date(Date.now() + 86400000).toISOString(),
          agenda,
        }),
      });
      if (res.ok) {
        setMessage('Meeting scheduled and AI briefing dossier synthesized!');
        setShowScheduleModal(false);
        setTitle('Sales Discovery Call');
        setCompanyName('');
        fetchMeetings();
      }
    } catch {
      setMessage('Error scheduling meeting.');
    } finally {
      setScheduling(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center bg-gray-900 border border-gray-800 p-6 rounded-xl">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Calendar className="w-7 h-7 text-indigo-400" />
              Meeting Scheduling &amp; Sales Handoff
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              AI Executive Briefings
            </span>
          </div>
          <p className="text-gray-400 text-sm mt-1">
            Book sales calls, coordinate Google Calendar availability, and automatically prepare executive cheat-sheets.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowScheduleModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold transition"
          >
            <Plus className="w-4 h-4" />
            Book Call
          </button>
          <button
            onClick={fetchMeetings}
            className="p-2.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg transition"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {message && (
        <div className="p-4 bg-indigo-950/60 border border-indigo-500/40 rounded-lg text-indigo-200 text-sm flex justify-between items-center">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-indigo-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Active AI Dossier Modal / Drawer */}
      {activeDossier && (
        <div className="bg-gray-900 border border-indigo-500/40 rounded-xl p-6 space-y-3">
          <div className="flex justify-between items-center pb-3 border-b border-gray-800">
            <h3 className="font-bold text-white text-base flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              AI Pre-Meeting Briefing: {activeDossier.title} ({activeDossier.company_name})
            </h3>
            <button onClick={() => setActiveDossier(null)} className="text-gray-400 hover:text-white text-sm">✕ Close</button>
          </div>
          <div className="text-xs text-gray-300 bg-gray-950 p-4 rounded-lg font-mono whitespace-pre-wrap max-h-72 overflow-y-auto">
            {activeDossier.prep_notes || 'No dossier generated.'}
          </div>
        </div>
      )}

      {/* Meetings Grid */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-base font-semibold text-white mb-4">Scheduled Appointments ({meetings.length})</h2>
        {loading ? (
          <div className="text-center py-10 text-gray-400">Loading scheduled meetings...</div>
        ) : meetings.length === 0 ? (
          <div className="text-center py-10 text-gray-500">No scheduled meetings yet. Click 'Book Call' to schedule!</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {meetings.map((m) => (
              <div key={m.id} className="bg-gray-800/40 border border-gray-700/60 rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-bold text-white text-base">{m.title}</span>
                    <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-400 uppercase">
                      {m.status}
                    </span>
                  </div>
                  <div className="text-xs text-indigo-400 font-semibold mb-2">{m.company_name} • {m.contact_name}</div>
                  <div className="text-xs text-gray-400 flex items-center gap-2 mb-3">
                    <Clock className="w-3.5 h-3.5" />
                    {new Date(m.start_time).toLocaleString()}
                  </div>
                  <p className="text-xs text-gray-300 bg-gray-900/60 p-2.5 rounded line-clamp-2">{m.agenda}</p>
                </div>

                <div className="mt-4 pt-3 border-t border-gray-700/60 flex justify-between items-center">
                  <a
                    href={m.meeting_url || '#'}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5"
                  >
                    <Video className="w-3.5 h-3.5" /> Launch Meet Link
                  </a>
                  <button
                    onClick={() => setActiveDossier(m)}
                    className="px-3 py-1.5 bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/40 rounded text-xs font-semibold flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3 h-3 text-indigo-400" /> View AI Briefing
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal: Schedule Meeting */}
      {showScheduleModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-md w-full">
            <h2 className="text-lg font-bold text-white mb-4">Book Sales Call</h2>
            <form onSubmit={handleScheduleMeeting} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Meeting Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Company / Account Name</label>
                <input
                  type="text"
                  required
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g. Acme Solar Solutions"
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Date &amp; Time (UTC)</label>
                <input
                  type="datetime-local"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Call Agenda</label>
                <textarea
                  rows={2}
                  value={agenda}
                  onChange={(e) => setAgenda(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowScheduleModal(false)}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={scheduling}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold"
                >
                  {scheduling ? 'Scheduling & Briefing...' : 'Schedule & Generate Dossier'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

