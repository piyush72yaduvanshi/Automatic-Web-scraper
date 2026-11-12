import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createCallLog, CallLogCreateData } from '../services/crmApi';
import { Phone, X, Check } from 'lucide-react';

interface CallLogFormProps {
  companyId?: string;
  contactId?: string;
  dealId?: string;
  onClose: () => void;
}

const CallLogForm: React.FC<CallLogFormProps> = ({ companyId, contactId, dealId, onClose }) => {
  const queryClient = useQueryClient();
  const [direction, setDirection] = useState<'INBOUND' | 'OUTBOUND'>('OUTBOUND');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [durationSeconds, setDurationSeconds] = useState(0);
  const [outcome, setOutcome] = useState('CONNECTED');
  const [notes, setNotes] = useState('');
  const [callStartedAt, setCallStartedAt] = useState('');

  const createMutation = useMutation({
    mutationFn: async (data: CallLogCreateData) => {
      return await createCallLog(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['call_logs'] });
      onClose();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      company_id: companyId,
      contact_id: contactId,
      deal_id: dealId,
      direction,
      phone_number: phoneNumber,
      duration_seconds: durationSeconds,
      outcome,
      notes,
      call_started_at: callStartedAt ? new Date(callStartedAt).toISOString() : new Date().toISOString(),
    });
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#0A0E1A] border border-slate-800 rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-green-500/10 border border-green-500/20">
              <Phone className="w-5 h-5 text-green-400" />
            </div>
            <h2 className="text-lg font-bold text-white">Log Phone Call</h2>
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
          {/* Direction */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Direction</label>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setDirection('OUTBOUND')}
                className={`flex-1 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  direction === 'OUTBOUND'
                    ? 'bg-blue-500/20 text-blue-400 border-2 border-blue-500/40'
                    : 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:bg-slate-800'
                }`}
              >
                Outbound Call
              </button>
              <button
                type="button"
                onClick={() => setDirection('INBOUND')}
                className={`flex-1 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  direction === 'INBOUND'
                    ? 'bg-green-500/20 text-green-400 border-2 border-green-500/40'
                    : 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:bg-slate-800'
                }`}
              >
                Inbound Call
              </button>
            </div>
          </div>

          {/* Phone Number */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Phone Number</label>
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="+1 (555) 123-4567"
              className="w-full px-3.5 py-2.5 bg-[#0E1424] border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {/* Duration */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Duration (seconds)</label>
            <input
              type="number"
              value={durationSeconds}
              onChange={(e) => setDurationSeconds(parseInt(e.target.value) || 0)}
              min="0"
              placeholder="120"
              className="w-full px-3.5 py-2.5 bg-[#0E1424] border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {/* Outcome */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Outcome</label>
            <select
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#0E1424] border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            >
              <option value="CONNECTED">Connected</option>
              <option value="NO_ANSWER">No Answer</option>
              <option value="VOICEMAIL">Voicemail</option>
              <option value="BUSY">Busy</option>
            </select>
          </div>

          {/* Call Started At */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Call Date & Time</label>
            <input
              type="datetime-local"
              value={callStartedAt}
              onChange={(e) => setCallStartedAt(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#0E1424] border border-slate-800 rounded-xl text-sm text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={4}
              placeholder="Call summary, key points discussed, next steps..."
              className="w-full px-3.5 py-2.5 bg-[#0E1424] border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 resize-none"
            />
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
              disabled={createMutation.isPending}
              className="flex-1 px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {createMutation.isPending ? (
                <>
                  <div className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  Log Call
                </>
              )}
            </button>
          </div>

          {createMutation.isError && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-sm text-red-400">
              Error logging call. Please try again.
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default CallLogForm;
