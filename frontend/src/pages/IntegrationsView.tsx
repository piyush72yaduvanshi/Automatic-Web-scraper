import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { HealthSummary, IntegrationStatusItem } from '../types';
import {
  Sliders,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Power,
  ShieldCheck,
  Bot,
  Globe,
  Mail,
  Server,
  Key,
  Share2,
  Instagram,
  Facebook,
  Twitter,
  Linkedin,
} from 'lucide-react';

const IntegrationsView: React.FC = () => {
  const queryClient = useQueryClient();
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ provider: string; message: string; success: boolean } | null>(null);

  const { data: healthData, isLoading, refetch } = useQuery<HealthSummary>({
    queryKey: ['integrations_health'],
    queryFn: async () => {
      const res = await api.get('/integrations/health');
      return res.data;
    },
    refetchInterval: 15000,
  });

  const toggleMutation = useMutation({
    mutationFn: async ({ provider, enabled }: { provider: string; enabled: boolean }) => {
      await api.patch(`/integrations/${provider}/toggle`, { enabled });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations_health'] });
    },
  });

  const handleValidate = async (provider: string) => {
    setTestingProvider(provider);
    setTestResult(null);
    try {
      const res = await api.post(`/integrations/${provider}/validate`);
      setTestResult({
        provider,
        message: res.data.message || (res.data.success ? 'Validated successfully' : 'Validation failed'),
        success: res.data.success,
      });
      refetch();
    } catch (err: any) {
      setTestResult({
        provider,
        message: err.response?.data?.detail || err.message || 'Validation request failed',
        success: false,
      });
    } finally {
      setTestingProvider(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" /> Healthy & Ready
          </span>
        );
      case 'NOT_CONFIGURED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <AlertTriangle className="w-3.5 h-3.5" /> Not Configured
          </span>
        );
      case 'DISABLED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-500 border border-slate-700">
            <Power className="w-3.5 h-3.5" /> Disabled
          </span>
        );
      case 'DEGRADED':
      case 'TEMPORARILY_UNAVAILABLE':
      case 'RATE_LIMITED':
      case 'INVALID_CREDENTIALS':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3.5 h-3.5" /> {status}
          </span>
        );
    }
  };

  const getCategoryIcon = (category: string, name?: string) => {
    if (name === 'instagram') return <Instagram className="w-4 h-4 text-pink-400" />;
    if (name === 'facebook') return <Facebook className="w-4 h-4 text-blue-500" />;
    if (name === 'twitter') return <Twitter className="w-4 h-4 text-sky-400" />;
    if (name === 'linkedin') return <Linkedin className="w-4 h-4 text-blue-400" />;
    if (category.includes('Social')) return <Share2 className="w-4 h-4 text-pink-400" />;
    if (category.includes('AI')) return <Bot className="w-4 h-4 text-indigo-400" />;
    if (category.includes('Discovery')) return <Globe className="w-4 h-4 text-blue-400" />;
    if (category.includes('Enrichment')) return <Key className="w-4 h-4 text-cyan-400" />;
    if (category.includes('Outreach') || category.includes('Messaging')) return <Mail className="w-4 h-4 text-emerald-400" />;
    return <Server className="w-4 h-4 text-purple-400" />;
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
              <span className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Sliders className="w-5 h-5" />
              </span>
              Integrations & Provider Health
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Live .env Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1.5">
            Active credentials from .env, runtime inspection, and fault-tolerant fallback adapters.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-[#0E1424] hover:bg-[#131B2E] text-slate-300 border border-slate-800 rounded-xl text-xs font-semibold shadow-sm transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-400" /> Refresh Health
        </button>
      </div>

      {/* Critical Fault Tolerance Banner */}
      <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-200 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <p className="font-bold text-white">Active .env Configuration Engine & Zero-Crash Architecture</p>
          <p className="text-slate-300 leading-relaxed">
            API keys configured in <code className="text-indigo-300 bg-slate-900/60 px-1 py-0.5 rounded">.env</code> and <code className="text-indigo-300 bg-slate-900/60 px-1 py-0.5 rounded">backend/.env</code> are dynamically detected and verified.
            Missing keys safely fall back to offline algorithmic Heuristic NLP without crashing.
          </p>
        </div>
      </div>

      {/* Summary KPI Badges */}
      {healthData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-[#0E1424] p-4 rounded-2xl border border-slate-800 shadow-sm">
            <div className="text-xs font-semibold text-slate-400">Overall Status</div>
            <div className="mt-1 text-base font-bold text-white flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${healthData.overall_status === 'HEALTHY' ? 'bg-emerald-400 shadow-sm shadow-emerald-400' : 'bg-amber-400'}`} />
              {healthData.overall_status}
            </div>
          </div>
          <div className="bg-[#0E1424] p-4 rounded-2xl border border-slate-800 shadow-sm">
            <div className="text-xs font-semibold text-slate-400">Healthy Providers</div>
            <div className="mt-1 text-base font-bold text-emerald-400">
              {healthData.healthy_count} <span className="text-xs font-normal text-slate-500">/ {healthData.total_integrations}</span>
            </div>
          </div>
          <div className="bg-[#0E1424] p-4 rounded-2xl border border-slate-800 shadow-sm">
            <div className="text-xs font-semibold text-slate-400">Not Configured</div>
            <div className="mt-1 text-base font-bold text-slate-400">{healthData.not_configured_count}</div>
          </div>
          <div className="bg-[#0E1424] p-4 rounded-2xl border border-slate-800 shadow-sm">
            <div className="text-xs font-semibold text-slate-400">Degraded / Errors</div>
            <div className="mt-1 text-base font-bold text-amber-400">{healthData.degraded_count}</div>
          </div>
        </div>
      )}

      {/* Test Result Toast */}
      {testResult && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center justify-between ${
            testResult.success
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            {testResult.success ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <XCircle className="w-4 h-4 text-rose-400" />}
            <span>
              <strong className="text-white uppercase">{testResult.provider}:</strong> {testResult.message}
            </span>
          </div>
          <button onClick={() => setTestResult(null)} className="text-slate-400 hover:text-white font-bold ml-4">
            ×
          </button>
        </div>
      )}

      {/* Integrations Table/Cards */}
      <div className="bg-[#0E1424] rounded-2xl border border-slate-800 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 bg-[#131B2E]/60 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white">Connected Services & Providers</h3>
          <span className="text-xs text-slate-400">Showing {healthData?.integrations?.length || 0} external services</span>
        </div>

        {isLoading ? (
          <div className="p-16 text-center text-sm text-slate-400 flex flex-col items-center justify-center gap-3">
            <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
            <span>Inspecting integrations health...</span>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {healthData?.integrations?.map((item: IntegrationStatusItem) => (
              <div
                key={item.name}
                className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-[#131B2E]/60 transition-colors"
              >
                <div className="flex items-start gap-3.5">
                  <div className="p-2 rounded-xl bg-[#131B2E] border border-slate-700/60 mt-0.5">
                    {getCategoryIcon(item.category, item.name)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <h4 className="text-sm font-bold text-white">{item.display_name}</h4>
                      {getStatusBadge(item.status)}
                    </div>
                    <p className="text-xs text-slate-400 mt-1 max-w-xl">{item.description}</p>
                    <p className="text-xs font-medium text-slate-300 mt-1.5 flex items-center gap-1.5">
                      <span className="text-slate-500">Status:</span> {item.user_message}
                    </p>
                    {item.last_error && (
                      <div className="mt-2 text-xs text-rose-300 bg-rose-500/10 border border-rose-500/20 p-2.5 rounded-xl max-w-lg">
                        <strong>Last Error:</strong> {item.last_error}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2.5 self-end sm:self-center">
                  <button
                    onClick={() => handleValidate(item.name)}
                    disabled={testingProvider === item.name || !item.is_configured}
                    className="px-3.5 py-1.5 border border-slate-700 rounded-xl text-xs font-semibold text-slate-200 bg-[#131B2E] hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    {testingProvider === item.name ? 'Testing...' : 'Test Connection'}
                  </button>
                  <button
                    onClick={() => toggleMutation.mutate({ provider: item.name, enabled: !item.is_enabled })}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
                      item.is_enabled
                        ? 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        : 'bg-emerald-600 text-white hover:bg-emerald-500'
                    }`}
                  >
                    {item.is_enabled ? 'Disable' : 'Enable'}
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

export default IntegrationsView;
