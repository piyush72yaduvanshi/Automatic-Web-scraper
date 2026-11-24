import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchCallLogs } from '../services/crmApi';
import { Phone, PhoneIncoming, PhoneOutgoing, Clock, Plus } from 'lucide-react';
import type { CallLogItem } from '../types';
import CallLogForm from './CallLogForm';

interface CallLogsListProps {
  companyId?: string;
  contactId?: string;
  dealId?: string;
}

const CallLogsList: React.FC<CallLogsListProps> = ({ companyId, contactId, dealId }) => {
  const [showForm, setShowForm] = useState(false);
  const [outcomeFilter, setOutcomeFilter] = useState<string>('');

  const { data: callLogs, isLoading } = useQuery<CallLogItem[]>({
    queryKey: ['call_logs', companyId, contactId, dealId, outcomeFilter],
    queryFn: async () => {
      return await fetchCallLogs({
        company_id: companyId,
        contact_id: contactId,
        deal_id: dealId,
        outcome: outcomeFilter || undefined,
        limit: 50,
      });
    },
  });

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

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

  const getOutcomeBadge = (outcome?: string) => {
    const styles = {
      CONNECTED: 'bg-green-500/20 text-green-400 border-green-500/30',
      NO_ANSWER: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      VOICEMAIL: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      BUSY: 'bg-red-500/20 text-red-400 border-red-500/30',
    };
    return styles[outcome as keyof typeof styles] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Phone className="w-5 h-5 text-green-400" />
          <h3 className="text-lg font-bold text-white">Call Logs</h3>
          <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-slate-800 text-slate-300">
            {callLogs?.length || 0}
          </span>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg text-xs font-semibold transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Log Call
        </button>
      </div>

      {/* Outcome Filter */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <button
          onClick={() => setOutcomeFilter('')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
            outcomeFilter === ''
              ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
              : 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:bg-slate-800'
          }`}
        >
          All Calls
        </button>
        {['CONNECTED', 'NO_ANSWER', 'VOICEMAIL', 'BUSY'].map((outcome) => (
          <button
            key={outcome}
            onClick={() => setOutcomeFilter(outcome)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${
              outcomeFilter === outcome
                ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                : 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:bg-slate-800'
            }`}
          >
            {outcome.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Call Logs List */}
      <div className="space-y-2">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-slate-400">
            <div className="w-6 h-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mx-auto mb-2" />
            Loading call logs...
          </div>
        ) : callLogs?.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500 bg-slate-800/30 rounded-xl border border-slate-800">
            No call logs yet. Click "Log Call" to create one.
          </div>
        ) : (
          callLogs?.map((log) => (
            <div
              key={log.id}
              className="p-4 rounded-xl bg-slate-800/30 border border-slate-800 hover:border-slate-700 transition-all"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  {/* Direction Icon */}
                  <div
                    className={`p-2 rounded-lg ${
                      log.direction === 'INBOUND'
                        ? 'bg-green-500/10 border border-green-500/20'
                        : 'bg-blue-500/10 border border-blue-500/20'
                    }`}
                  >
                    {log.direction === 'INBOUND' ? (
                      <PhoneIncoming className="w-4 h-4 text-green-400" />
                    ) : (
                      <PhoneOutgoing className="w-4 h-4 text-blue-400" />
                    )}
                  </div>

                  {/* Call Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-white">
                        {log.phone_number || 'Unknown Number'}
                      </span>
                      {log.outcome && (
                        <span
                          className={`px-2 py-0.5 text-xs font-semibold rounded-full border ${getOutcomeBadge(
                            log.outcome
                          )}`}
                        >
                          {log.outcome.replace('_', ' ')}
                        </span>
                      )}
                    </div>

                    <div className="text-xs text-slate-400 mb-2">
                      {log.contact_name && <span>{log.contact_name} • </span>}
                      {log.company_name && <span>{log.company_name} • </span>}
                      {log.call_started_at ? formatDate(log.call_started_at) : formatDate(log.created_at)}
                    </div>

                    {log.notes && (
                      <div className="text-sm text-slate-300 whitespace-pre-wrap break-words mt-2">
                        {log.notes}
                      </div>
                    )}
                  </div>
                </div>

                {/* Duration */}
                <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-700/50 rounded-lg">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-xs font-semibold text-slate-300">
                    {formatDuration(log.duration_seconds)}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Form Modal */}
      {showForm && (
        <CallLogForm
          companyId={companyId}
          contactId={contactId}
          dealId={dealId}
          onClose={() => setShowForm(false)}
        />
      )}
    </div>
  );
};

export default CallLogsList;
