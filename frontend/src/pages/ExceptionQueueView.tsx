import React, { useState, useEffect } from 'react';
import {
  AlertOctagon,
  RefreshCw,
  AlertTriangle,
  RotateCw,
  MessageSquare,
  Server,
  Trash2,
} from 'lucide-react';
import { ExceptionItem } from '../types';

export const ExceptionQueueView: React.FC = () => {
  const [exceptions, setExceptions] = useState<ExceptionItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [message, setMessage] = useState<string | null>(null);

  const fetchExceptions = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/exceptions');
      if (res.ok) {
        const data = await res.json();
        setExceptions(data.items || []);
        setTotal(data.total_exceptions || 0);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExceptions();
  }, []);

  const handleResolveAction = async (item: ExceptionItem) => {
    if (item.action_type === 'RETRY_WORKFLOW') {
      try {
        const res = await fetch(`/api/v1/workflows/executions/${item.entity_id}/retry`, { method: 'POST' });
        if (res.ok) {
          setMessage(`Retried workflow execution ${item.entity_id}!`);
          fetchExceptions();
        }
      } catch {
        setMessage('Retry failed.');
      }
    } else {
      setMessage(`Action ${item.action_type} acknowledged for ${item.title}.`);
    }
  };

  const filtered = filterSeverity === 'ALL'
    ? exceptions
    : exceptions.filter((e) => e.severity === filterSeverity);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center bg-gray-900 border border-gray-800 p-6 rounded-xl">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <AlertOctagon className="w-7 h-7 text-rose-400" />
              Centralized Exception &amp; Review Queue
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">
              {total} Operational Exceptions
            </span>
          </div>
          <p className="text-gray-400 text-sm mt-1">
            Aggregated system anomalies requiring human review: workflow failures, delivery bounces, compliance alerts, and sensitive replies.
          </p>
        </div>
        <button
          onClick={fetchExceptions}
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

      {/* Severity Filter Tabs */}
      <div className="flex gap-2">
        {['ALL', 'URGENT', 'HIGH', 'MEDIUM'].map((s) => (
          <button
            key={s}
            onClick={() => setFilterSeverity(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filterSeverity === s
                ? 'bg-rose-600 text-white'
                : 'bg-gray-900 hover:bg-gray-800 text-gray-400'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Exceptions List */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        {loading ? (
          <div className="text-center py-10 text-gray-400">Scanning exception queue...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-10 text-emerald-400 flex flex-col items-center justify-center">
            <span className="text-lg font-bold">All Systems Clear!</span>
            <span className="text-xs text-gray-500 mt-1">Zero pending workflow failures or compliance exceptions.</span>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((item) => (
              <div
                key={item.id}
                className={`p-4 rounded-xl border flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition ${
                  item.severity === 'URGENT' ? 'bg-rose-950/20 border-rose-500/50' :
                  item.severity === 'HIGH' ? 'bg-amber-950/20 border-amber-500/40' :
                  'bg-gray-800/40 border-gray-700/60'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-1">
                    {item.category === 'WORKFLOW_FAILURE' && <RotateCw className="w-5 h-5 text-amber-400" />}
                    {item.category === 'DELIVERABILITY_ALERT' && <AlertTriangle className="w-5 h-5 text-rose-400" />}
                    {item.category === 'COMPLIANCE_REQUEST' && <Trash2 className="w-5 h-5 text-rose-400" />}
                    {item.category === 'INBOUND_ATTENTION' && <MessageSquare className="w-5 h-5 text-blue-400" />}
                    {item.category === 'INTEGRATION_ANOMALY' && <Server className="w-5 h-5 text-amber-400" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        item.severity === 'URGENT' ? 'bg-rose-500/20 text-rose-400' :
                        item.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-700 text-gray-300'
                      }`}>
                        {item.severity}
                      </span>
                      <span className="text-xs text-gray-400">{item.category}</span>
                      <span className="text-xs text-gray-500">• {new Date(item.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <h3 className="font-semibold text-white text-sm mt-1">{item.title}</h3>
                    <p className="text-xs text-gray-300 mt-0.5 line-clamp-2">{item.details}</p>
                  </div>
                </div>

                <div className="self-end md:self-center">
                  <button
                    onClick={() => handleResolveAction(item)}
                    className="px-3.5 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
                  >
                    Resolve / Review
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
