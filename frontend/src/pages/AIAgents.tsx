import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../services/api';
import { AgentDefinition, AgentRunItem } from '../types';
import {
  Bot,
  Play,
  History,
  CheckCircle2,
  XCircle,
  Workflow,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

const AIAgents: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState<AgentDefinition | null>(null);
  const [inputPayload, setInputPayload] = useState('{\n  "query": "Dentist",\n  "location": "Lucknow"\n}');
  const [executionResult, setExecutionResult] = useState<any>(null);

  // Autonomous workflow state
  const [workflowGoal, setWorkflowGoal] = useState('Find 25 software consultancies in Bangalore and prepare personalized outreach drafts');
  const [workflowResult, setWorkflowResult] = useState<any>(null);

  // 1. Fetch Agents
  const { data: agents } = useQuery<AgentDefinition[]>({
    queryKey: ['agents_list'],
    queryFn: async () => {
      const res = await api.get('/agents');
      return res.data;
    },
  });

  // 2. Fetch Agent Runs
  const { data: runs, refetch: refetchRuns } = useQuery<AgentRunItem[]>({
    queryKey: ['agents_runs'],
    queryFn: async () => {
      const res = await api.get('/agents/runs?limit=25');
      return res.data;
    },
    refetchInterval: 10000,
  });

  // Execute Agent Mutation
  const executeMutation = useMutation({
    mutationFn: async ({ agentName, payload }: { agentName: string; payload: any }) => {
      const res = await api.post(`/agents/${agentName}/execute`, payload);
      return res.data;
    },
    onSuccess: (data) => {
      setExecutionResult(data);
      refetchRuns();
    },
    onError: (err: any) => {
      setExecutionResult({ error: err.response?.data?.detail || err.message });
    },
  });

  // Run Workflow Mutation
  const workflowMutation = useMutation({
    mutationFn: async (goal: string) => {
      const res = await api.post('/agents/workflow', { goal });
      return res.data;
    },
    onSuccess: (data) => {
      setWorkflowResult(data);
      refetchRuns();
    },
  });

  const handleSelectAgent = (agent: AgentDefinition) => {
    setSelectedAgent(agent);
    setExecutionResult(null);
    if (agent.name === 'company_research_agent') {
      setInputPayload('{\n  "company_name": "Apex Dental Hospital",\n  "website": "https://apexdental.com",\n  "category": "Dentistry"\n}');
    } else if (agent.name === 'email_personalization_agent') {
      setInputPayload('{\n  "company_name": "Tech Corp",\n  "contact_name": "Alex",\n  "pain_points": ["Manual outreach", "Lead qualification"]\n}');
    } else if (agent.name === 'reply_classification_agent') {
      setInputPayload('{\n  "reply_text": "Thanks for reaching out. What is your pricing and can we set up a quick 15-minute call Tuesday?"\n}');
    } else {
      setInputPayload('{\n  "query": "Enterprise Software",\n  "location": "Lucknow"\n}');
    }
  };

  const handleRunAgent = () => {
    if (!selectedAgent) return;
    try {
      const parsed = JSON.parse(inputPayload);
      executeMutation.mutate({ agentName: selectedAgent.name, payload: parsed });
    } catch (e) {
      alert('Invalid JSON input format');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
              <span className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Bot className="w-5 h-5" />
              </span>
              Specialized AI Agents & Autonomous Orchestrator
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              15 Scoped Agents
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1.5">
            Purpose-built AI agents with scoped tool permissions, execution limits, and multi-step workflow planning.
          </p>
        </div>
      </div>

      {/* Autonomous Workflow Runner Section */}
      <div className="bg-gradient-to-r from-indigo-950/80 via-[#131B2E] to-[#0E1424] border border-indigo-500/30 rounded-2xl p-6 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-2">
            <span className="p-1.5 rounded-lg bg-indigo-500/20 border border-indigo-500/30 text-indigo-300">
              <Workflow className="w-4 h-4" />
            </span>
            <h2 className="text-base font-bold text-white">Master Autonomous Workflow Planner</h2>
          </div>
          <p className="text-xs text-slate-300 mb-4 max-w-2xl leading-relaxed">
            Input an overarching sales or research objective. The orchestrator plans sub-steps, dispatches
            specialized agents, and enqueues external actions into the human approval queue.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={workflowGoal}
              onChange={(e) => setWorkflowGoal(e.target.value)}
              className="flex-1 px-4 py-2.5 bg-[#080C14] border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              placeholder="Describe your sales objective..."
            />
            <button
              onClick={() => workflowGoal && workflowMutation.mutate(workflowGoal)}
              disabled={workflowMutation.isPending}
              className="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2 disabled:opacity-50 transition-all"
            >
              {workflowMutation.isPending ? 'Planning & Coordinating...' : 'Execute Workflow'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {workflowResult && (
            <div className="mt-4 p-4 rounded-xl bg-[#080C14] border border-slate-700/80 text-xs space-y-2">
              <div className="font-semibold text-indigo-400">
                Workflow: {workflowResult.workflow_name} ({workflowResult.total_steps} steps planned)
              </div>
              <div className="space-y-1.5 pt-1.5">
                {workflowResult.execution_log?.map((st: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-[#0E1424] border border-slate-800">
                    <span className="text-slate-300">
                      Step {st.step}: <strong className="text-white">{st.agent}</strong> - {st.action || 'Internal Step'}
                    </span>
                    <span
                      className={`text-[11px] font-semibold px-2 py-0.5 rounded-md ${
                        st.status.includes('QUEUED')
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      }`}
                    >
                      {st.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Agents Grid and Interactive Runner */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: 15 Agents Directory */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Specialized Agents Directory ({agents?.length || 0})
            </h3>
            <span className="text-xs text-slate-400">Click an agent to configure & run</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-[620px] overflow-y-auto pr-1 custom-scrollbar">
            {agents?.map((agent) => {
              const isSelected = selectedAgent?.name === agent.name;
              return (
                <div
                  key={agent.name}
                  onClick={() => handleSelectAgent(agent)}
                  className={`p-4 rounded-xl border text-left cursor-pointer transition-all ${
                    isSelected
                      ? 'border-indigo-500 bg-[#131B2E] ring-1 ring-indigo-500/50 shadow-md'
                      : 'border-slate-800 bg-[#0E1424] hover:border-slate-700 hover:bg-[#131B2E]/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-white">{agent.role}</span>
                    <span className="text-[10px] font-mono text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-1.5 py-0.5 rounded">
                      {agent.name}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 line-clamp-2 mb-3 leading-relaxed">{agent.description}</p>
                  <div className="flex items-center gap-2 text-[10px] text-slate-500 pt-2 border-t border-slate-800">
                    <span>Tools: {agent.allowed_tools?.length || 0}</span>
                    <span>•</span>
                    <span>Max steps: {agent.max_execution_steps}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Interactive Agent Execution Console */}
        <div className="bg-[#0E1424] border border-slate-800 rounded-2xl p-5 shadow-sm space-y-4 text-white">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Play className="w-4 h-4 text-indigo-400" />
              Interactive Execution Console
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              {selectedAgent ? `Selected: ${selectedAgent.role}` : 'Select an agent from the left to run tests.'}
            </p>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">Input Parameters (JSON)</label>
            <textarea
              rows={6}
              value={inputPayload}
              onChange={(e) => setInputPayload(e.target.value)}
              className="w-full px-3 py-2 bg-[#131B2E] border border-slate-700 rounded-xl font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
          </div>

          <button
            onClick={handleRunAgent}
            disabled={!selectedAgent || executeMutation.isPending}
            className="w-full py-2.5 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-xs font-semibold shadow-md flex items-center justify-center gap-1.5 disabled:opacity-50 transition-all"
          >
            {executeMutation.isPending ? 'Executing Agent...' : `Run ${selectedAgent?.role || 'Agent'}`}
          </button>

          {/* Result Output */}
          {executionResult && (
            <div className="space-y-1.5 pt-2 border-t border-slate-800">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
                <span>Output Result:</span>
                {executionResult.duration_ms && (
                  <span className="text-slate-500 font-normal">{executionResult.duration_ms}ms</span>
                )}
              </div>
              <pre className="p-3 bg-[#080C14] text-emerald-400 rounded-xl text-[11px] font-mono overflow-x-auto max-h-64 overflow-y-auto border border-slate-800">
                {JSON.stringify(executionResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* Execution Telemetry History */}
      <div className="bg-[#0E1424] border border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 bg-[#131B2E]/60 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <History className="w-4 h-4 text-indigo-400" />
            Agent Execution Telemetry Log
          </h3>
          <span className="text-xs text-slate-400">Live runs recorded in PostgreSQL / SQLite</span>
        </div>
        <div className="divide-y divide-slate-800/80 text-xs">
          {runs?.length === 0 ? (
            <div className="p-8 text-center text-slate-500 text-xs">No agent runs recorded yet. Execute an agent above.</div>
          ) : (
            runs?.map((r) => (
              <div key={r.id} className="p-4 flex items-center justify-between hover:bg-[#131B2E]/40 transition-colors">
                <div className="flex items-center gap-3">
                  {r.status === 'COMPLETED' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400" />
                  )}
                  <div>
                    <span className="font-semibold text-white">{r.agent_name}</span>
                    <span className="text-slate-600 mx-1.5">•</span>
                    <span className="text-slate-400">{r.task_type}</span>
                    {r.error_message && <div className="text-[11px] text-rose-400 mt-0.5">{r.error_message}</div>}
                  </div>
                </div>
                <div className="flex items-center gap-4 text-slate-400 text-[11px]">
                  <span>{r.duration_ms}ms</span>
                  <span>{new Date(r.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default AIAgents;
