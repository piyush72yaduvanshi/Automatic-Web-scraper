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
  Database,
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
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            <CheckCircle2 className="w-3.5 h-3.5" /> Healthy
          </span>
        );
      case 'NOT_CONFIGURED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
            <AlertTriangle className="w-3.5 h-3.5" /> Not Configured
          </span>
        );
      case 'DISABLED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-600">
            <Power className="w-3.5 h-3.5" /> Disabled
          </span>
        );
      case 'DEGRADED':
      case 'TEMPORARILY_UNAVAILABLE':
      case 'RATE_LIMITED':
      case 'INVALID_CREDENTIALS':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
            <AlertTriangle className="w-3.5 h-3.5" /> {status}
          </span>
        );
    }
  };

  const getCategoryIcon = (category: string) => {
    if (category.includes('AI')) return <Bot className="w-5 h-5 text-indigo-500" />;
    if (category.includes('Discovery')) return <Globe className="w-5 h-5 text-blue-500" />;
    if (category.includes('Outreach')) return <Mail className="w-5 h-5 text-emerald-500" />;
    return <Database className="w-5 h-5 text-slate-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Sliders className="w-6 h-6 text-blue-600" />
            Integrations & Provider Health
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time credential inspection, status tracking, and fault-tolerant fallback adapters.
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 border border-slate-300 rounded-md shadow-sm text-xs font-medium text-slate-700 bg-white hover:bg-slate-50"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-500" /> Refresh Health
        </button>
      </div>

      {/* Critical Fault Tolerance Banner */}
      <div className="p-4 rounded-lg bg-blue-50 border border-blue-200 text-blue-900 flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <p className="font-semibold text-blue-950">Zero-Crash Fault-Tolerant Architecture Active</p>
          <p className="text-blue-800 leading-relaxed">
            Missing, expired, or rate-limited API keys will never crash the system. When AI keys are absent,
            the offline Heuristic NLP provider guarantees full CRM and search functionality. Optional services
            remain safely disabled until configured.
          </p>
        </div>
      </div>

      {/* Summary KPI Badges */}
      {healthData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
            <div className="text-xs font-medium text-slate-500">Overall Status</div>
            <div className="mt-1 text-lg font-bold text-slate-900 flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${healthData.overall_status === 'HEALTHY' ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
              {healthData.overall_status}
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
            <div className="text-xs font-medium text-slate-500">Healthy Providers</div>
            <div className="mt-1 text-lg font-bold text-emerald-600">
              {healthData.healthy_count} <span className="text-xs font-normal text-slate-400">/ {healthData.total_integrations}</span>
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
            <div className="text-xs font-medium text-slate-500">Not Configured (Demo/Offline)</div>
            <div className="mt-1 text-lg font-bold text-slate-600">{healthData.not_configured_count}</div>
          </div>
          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
            <div className="text-xs font-medium text-slate-500">Degraded / Errors</div>
            <div className="mt-1 text-lg font-bold text-amber-600">{healthData.degraded_count}</div>
          </div>
        </div>
      )}

      {/* Test Result Toast */}
      {testResult && (
        <div
          className={`p-3.5 rounded-md border text-xs flex items-center justify-between ${
            testResult.success ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-rose-50 border-rose-200 text-rose-900'
          }`}
        >
          <div className="flex items-center gap-2">
            {testResult.success ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <XCircle className="w-4 h-4 text-rose-600" />}
            <span>
              <strong>{testResult.provider.toUpperCase()}:</strong> {testResult.message}
            </span>
          </div>
          <button onClick={() => setTestResult(null)} className="text-slate-400 hover:text-slate-600 font-bold ml-4">
            ×
          </button>
        </div>
      )}

      {/* Integrations Table/Cards */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-800">Connected Services & Providers</h3>
          <span className="text-xs text-slate-500">Showing {healthData?.integrations?.length || 0} external services</span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-sm text-slate-500">Inspecting integrations health...</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {healthData?.integrations?.map((item: IntegrationStatusItem) => (
              <div key={item.name} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/60 transition-colors">
                <div className="flex items-start gap-3.5">
                  <div className="p-2 rounded-lg bg-slate-100 mt-0.5">
                    {getCategoryIcon(item.category)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-semibold text-slate-900">{item.display_name}</h4>
                      {getStatusBadge(item.status)}
                    </div>
                    <p className="text-xs text-slate-500 mt-1 max-w-xl">{item.description}</p>
                    <p className="text-xs font-medium text-slate-600 mt-1.5 flex items-center gap-1.5">
                      <span className="text-slate-400">Current behavior:</span> {item.user_message}
                    </p>
                    {item.last_error && (
                      <div className="mt-2 text-xs text-rose-700 bg-rose-50 border border-rose-200 p-2 rounded max-w-lg">
                        <strong>Last Error:</strong> {item.last_error}
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2.5 self-end sm:self-center">
                  <button
                    onClick={() => handleValidate(item.name)}
                    disabled={testingProvider === item.name || !item.is_configured}
                    className="px-3 py-1.5 border border-slate-300 rounded text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    {testingProvider === item.name ? 'Testing...' : 'Test Connection'}
                  </button>
                  <button
                    onClick={() => toggleMutation.mutate({ provider: item.name, enabled: !item.is_enabled })}
                    className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                      item.is_enabled
                        ? 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                        : 'bg-emerald-600 text-white hover:bg-emerald-700'
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
