import React, { useState, useEffect } from 'react';
import {
  ListOrdered,
  Play,
  Clock,
  ShieldCheck,
  RefreshCw,
  Mail,
} from 'lucide-react';
import { FollowupSequenceItem } from '../types';

export const SequencesView: React.FC = () => {
  const [sequences, setSequences] = useState<FollowupSequenceItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [executionResult, setExecutionResult] = useState<any | null>(null);

  const fetchSequences = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/sequences');
      if (res.ok) setSequences(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSequences();
  }, []);

  const handleExecuteDue = async (seqId: string) => {
    setExecutingId(seqId);
    setExecutionResult(null);
    try {
      const res = await fetch(`/api/v1/sequences/${seqId}/execute-due`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setExecutionResult(data);
        setMessage(`Evaluated due steps for ${data.sequence_name}!`);
      } else {
        setMessage('Execution evaluation failed.');
      }
    } catch {
      setMessage('Error executing sequence check.');
    } finally {
      setExecutingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center bg-gray-900 border border-gray-800 p-6 rounded-xl">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <ListOrdered className="w-7 h-7 text-indigo-400" />
              Follow-Up & Cadence Sequences
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> 7 Pre-Execution Checks Enforced
            </span>
          </div>
          <p className="text-gray-400 text-sm mt-1">
            Multi-touch sequence blueprints with configurable delay intervals (Day 0, 3, 7, 14) and automated stop conditions.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={fetchSequences}
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

      {/* 7 Checks Banner */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-3">
          7 Mandatory Safety Checks Passed Before Every Outreach Touchpoint:
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 text-center text-xs">
          <div className="bg-gray-800/40 rounded p-2 text-gray-300">1. Eligibility</div>
          <div className="bg-gray-800/40 rounded p-2 text-gray-300">2. Suppression</div>
          <div className="bg-gray-800/40 rounded p-2 text-gray-300">3. Reply Pauses</div>
          <div className="bg-gray-800/40 rounded p-2 text-gray-300">4. Campaign Active</div>
          <div className="bg-gray-800/40 rounded p-2 text-gray-300">5. Human Approval</div>
          <div className="bg-gray-800/40 rounded p-2 text-gray-300">6. Kill Switch Off</div>
          <div className="bg-gray-800/40 rounded p-2 text-gray-300">7. Anti-Duplicate</div>
        </div>
      </div>

      {/* Execution Result Box */}
      {executionResult && (
        <div className="bg-gray-900 border border-indigo-500/40 rounded-xl p-5 space-y-2">
          <h3 className="font-semibold text-white text-sm">Execution Outcome: {executionResult.sequence_name}</h3>
          <div className="text-xs text-gray-300 flex gap-4">
            <span className="text-emerald-400 font-bold">Staged for Approval: {executionResult.staged_for_approval}</span>
            <span className="text-amber-400 font-bold">Blocked by Checks: {executionResult.blocked_count}</span>
          </div>
          {executionResult.blocked_reasons?.length > 0 && (
            <div className="mt-2 text-[11px] text-gray-400 bg-gray-950 p-3 rounded font-mono">
              <div className="font-semibold text-gray-300 mb-1">Check Block Details:</div>
              {executionResult.blocked_reasons.map((r: string, idx: number) => (
                <div key={idx}>• {r}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Sequences List */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading sequences...</div>
      ) : (
        <div className="space-y-6">
          {sequences.map((seq) => (
            <div key={seq.id} className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4 pb-4 border-b border-gray-800">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 text-xs font-semibold rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                      {seq.campaign_type}
                    </span>
                    <span className={`w-2 h-2 rounded-full ${seq.is_active ? 'bg-emerald-400' : 'bg-gray-500'}`} />
                  </div>
                  <h2 className="text-lg font-bold text-white mt-1">{seq.name}</h2>
                  <p className="text-xs text-gray-400">{seq.description}</p>
                </div>

                <button
                  onClick={() => handleExecuteDue(seq.id)}
                  disabled={executingId === seq.id}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50"
                >
                  <Play className="w-3.5 h-3.5" />
                  {executingId === seq.id ? 'Evaluating...' : 'Evaluate Due Steps (Run 7 Checks)'}
                </button>
              </div>

              {/* Timeline Steps Display */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {seq.steps.map((st) => (
                  <div key={st.step_number} className="bg-gray-800/40 border border-gray-700/60 rounded-xl p-4 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-xs text-indigo-400">Step {st.step_number}</span>
                        <span className="text-[11px] text-gray-400 flex items-center gap-1">
                          <Clock className="w-3 h-3" /> Day +{st.delay_days}
                        </span>
                      </div>
                      <div className="text-xs font-semibold text-white mb-2 flex items-center gap-1.5">
                        <Mail className="w-3.5 h-3.5 text-gray-400" />
                        {st.subject_template || 'Follow-up'}
                      </div>
                      <p className="text-xs text-gray-400 line-clamp-3 bg-gray-900/60 p-2.5 rounded border border-gray-800 font-mono">
                        {st.body_template}
                      </p>
                    </div>
                    <div className="mt-3 text-[10px] text-emerald-400 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3" /> Staged to Approval Queue
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
