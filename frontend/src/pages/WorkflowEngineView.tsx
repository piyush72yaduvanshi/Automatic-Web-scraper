import React, { useState, useEffect } from 'react';
import {
  Workflow,
  Play,
  RotateCw,
  XCircle,
  CheckCircle2,
  AlertCircle,
  Clock,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react';
import { WorkflowDefinitionItem, WorkflowExecutionItem } from '../types';

export const WorkflowEngineView: React.FC = () => {
  const [definitions, setDefinitions] = useState<WorkflowDefinitionItem[]>([]);
  const [executions, setExecutions] = useState<WorkflowExecutionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [triggeringId, setTriggeringId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const fetchWorkflowData = async () => {
    setLoading(true);
    try {
      const [defRes, execRes] = await Promise.all([
        fetch('/api/v1/workflows'),
        fetch('/api/v1/workflows/executions'),
      ]);
      if (defRes.ok) setDefinitions(await defRes.json());
      if (execRes.ok) setExecutions(await execRes.json());
    } catch (err) {
      console.error('Failed to load workflow engine data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflowData();
  }, []);

  const handleManualTrigger = async (workflowId: string) => {
    setTriggeringId(workflowId);
    try {
      const res = await fetch(`/api/v1/workflows/${workflowId}/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ triggered_by: 'ui_operator', timestamp: new Date().toISOString() }),
      });
      if (res.ok) {
        setMessage('Workflow execution started successfully!');
        fetchWorkflowData();
      } else {
        setMessage('Failed to trigger workflow.');
      }
    } catch {
      setMessage('Error triggering workflow.');
    } finally {
      setTriggeringId(null);
    }
  };

  const handleRetryExecution = async (execId: string) => {
    try {
      const res = await fetch(`/api/v1/workflows/executions/${execId}/retry`, { method: 'POST' });
      if (res.ok) {
        setMessage('Execution retried successfully!');
        fetchWorkflowData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleCancelExecution = async (execId: string) => {
    try {
      const res = await fetch(`/api/v1/workflows/executions/${execId}/cancel`, { method: 'POST' });
      if (res.ok) {
        setMessage('Execution cancelled.');
        fetchWorkflowData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center bg-gray-900 border border-gray-800 p-6 rounded-xl">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Workflow className="w-7 h-7 text-indigo-400" />
              Native Python Workflow Automation Engine
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              Zero n8n Dependency
            </span>
          </div>
          <p className="text-gray-400 text-sm mt-1">
            Event-driven and scheduled stateful sales workflows executed natively in Python with PostgreSQL persistence.
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={fetchWorkflowData}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg text-sm font-medium transition"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {message && (
        <div className="p-4 bg-indigo-950/60 border border-indigo-500/40 rounded-lg text-indigo-200 text-sm flex justify-between items-center">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-indigo-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Grid: Workflow Definitions */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <Play className="w-5 h-5 text-indigo-400" />
          Active Workflow Blueprints ({definitions.length})
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {definitions.map((wf) => (
            <div key={wf.id} className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-start mb-2">
                  <span className="px-2 py-0.5 text-xs font-semibold rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {wf.trigger_type}
                  </span>
                  <span className={`w-2 h-2 rounded-full ${wf.is_active ? 'bg-emerald-400' : 'bg-gray-500'}`} />
                </div>
                <h3 className="font-semibold text-white text-base">{wf.name}</h3>
                <p className="text-xs text-gray-400 mt-1 line-clamp-2">{wf.description || 'No description provided.'}</p>
                <div className="mt-3 text-xs text-gray-400 flex items-center gap-2">
                  <span>Steps: {wf.steps?.length || 0}</span>
                  <span>•</span>
                  <span>Timeout: {wf.timeout_seconds}s</span>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-gray-800/80 flex justify-between items-center">
                <span className="text-xs text-gray-500">v{wf.version}.0</span>
                <button
                  onClick={() => handleManualTrigger(wf.id)}
                  disabled={triggeringId === wf.id}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-50"
                >
                  <Play className="w-3.5 h-3.5" />
                  {triggeringId === wf.id ? 'Running...' : 'Run Now'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Table: Executions History */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-indigo-400" />
          Execution History & State Machine
        </h2>

        {loading ? (
          <div className="text-center py-8 text-gray-400">Loading workflow executions...</div>
        ) : executions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No workflow runs recorded yet. Trigger one above!</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-gray-800/60 text-xs uppercase text-gray-400 border-b border-gray-700">
                <tr>
                  <th className="py-3 px-4">Workflow Name</th>
                  <th className="py-3 px-4">Trigger</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Current Step</th>
                  <th className="py-3 px-4">Retries</th>
                  <th className="py-3 px-4">Started At</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {executions.map((ex) => (
                  <tr key={ex.id} className="hover:bg-gray-800/30">
                    <td className="py-3 px-4 font-medium text-white">{ex.workflow_name}</td>
                    <td className="py-3 px-4 text-xs text-gray-400">{ex.trigger_event}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${
                        ex.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400' :
                        ex.status === 'RUNNING' ? 'bg-blue-500/20 text-blue-400' :
                        ex.status === 'WAITING_FOR_APPROVAL' ? 'bg-amber-500/20 text-amber-400' :
                        ex.status === 'FAILED' ? 'bg-rose-500/20 text-rose-400' : 'bg-gray-700 text-gray-300'
                      }`}>
                        {ex.status === 'COMPLETED' && <CheckCircle2 className="w-3 h-3" />}
                        {ex.status === 'FAILED' && <AlertCircle className="w-3 h-3" />}
                        {ex.status === 'WAITING_FOR_APPROVAL' && <ShieldAlert className="w-3 h-3" />}
                        {ex.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-xs text-gray-400">{ex.current_step_id || 'Finished'}</td>
                    <td className="py-3 px-4 text-xs text-gray-400">{ex.retry_count}</td>
                    <td className="py-3 px-4 text-xs text-gray-400">{ex.created_at ? new Date(ex.created_at).toLocaleTimeString() : 'N/A'}</td>
                    <td className="py-3 px-4 text-right space-x-2">
                      {ex.status === 'FAILED' && (
                        <button
                          onClick={() => handleRetryExecution(ex.id)}
                          className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded text-xs inline-flex items-center gap-1"
                        >
                          <RotateCw className="w-3 h-3" /> Retry
                        </button>
                      )}
                      {(ex.status === 'RUNNING' || ex.status === 'WAITING_FOR_APPROVAL') && (
                        <button
                          onClick={() => handleCancelExecution(ex.id)}
                          className="px-2.5 py-1 bg-rose-900/40 hover:bg-rose-900/60 text-rose-300 rounded text-xs inline-flex items-center gap-1"
                        >
                          <XCircle className="w-3 h-3" /> Cancel
                        </button>
                      )}
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
