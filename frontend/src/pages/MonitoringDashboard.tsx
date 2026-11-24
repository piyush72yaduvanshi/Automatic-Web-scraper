import React, { useState, useEffect } from 'react';
import { Activity, Database, Server, HardDrive, CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react';
import api from '../services/api';

interface HealthStatus {
  overall: 'healthy' | 'degraded' | 'unhealthy';
  postgres: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  redis: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  minio: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
}

export const MonitoringDashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchHealth = async () => {
    try {
      setError(null);
      const response = await api.get('/health');
      setHealth(response.data);
      setLastUpdate(new Date());
    } catch (err: any) {
      console.error('Health check failed:', err);
      setError(err.message || 'Failed to fetch health status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    if (status === 'healthy') return <CheckCircle className="w-5 h-5 text-green-500" />;
    if (status === 'degraded') return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    if (status === 'unhealthy') return <XCircle className="w-5 h-5 text-red-500" />;
    return <AlertCircle className="w-5 h-5 text-gray-400" />;
  };

  const getStatusColor = (status: string) => {
    if (status === 'healthy') return 'bg-green-100 text-green-800';
    if (status === 'degraded') return 'bg-yellow-100 text-yellow-800';
    if (status === 'unhealthy') return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getStatusBadge = (status: string) => {
    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status)}`}>
        {getStatusIcon(status)}
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex flex-col items-center gap-3">
            <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
            <p className="text-sm font-medium text-slate-500">Loading system health...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-7 h-7 text-indigo-600" />
              System Monitoring
            </h1>
            <p className="text-slate-600 mt-1">Real-time health status of all system components</p>
          </div>
          <button
            onClick={fetchHealth}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
        {lastUpdate && (
          <p className="text-xs text-slate-500 mt-2">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        )}
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">Health Check Failed</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Overall Status Card */}
      {health && (
        <div className="mb-6 p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900 mb-1">Overall System Status</h2>
              <p className="text-sm text-slate-600">Aggregated health across all services</p>
            </div>
            <div className="text-right">
              {getStatusBadge(health.overall)}
            </div>
          </div>
        </div>
      )}

      {/* Component Status Grid */}
      {health && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* PostgreSQL */}
          <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Database className="w-6 h-6 text-blue-600" />
              </div>
              {getStatusIcon(health.postgres)}
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-1">PostgreSQL</h3>
            <p className="text-sm text-slate-600 mb-3">Primary database with pgvector</p>
            {getStatusBadge(health.postgres)}
          </div>

          {/* Redis */}
          <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 bg-red-100 rounded-lg">
                <Server className="w-6 h-6 text-red-600" />
              </div>
              {getStatusIcon(health.redis)}
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-1">Redis</h3>
            <p className="text-sm text-slate-600 mb-3">Cache and message broker</p>
            {getStatusBadge(health.redis)}
          </div>

          {/* MinIO */}
          <div className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <HardDrive className="w-6 h-6 text-purple-600" />
              </div>
              {getStatusIcon(health.minio)}
            </div>
            <h3 className="text-lg font-semibold text-slate-900 mb-1">MinIO</h3>
            <p className="text-sm text-slate-600 mb-3">S3-compatible object storage</p>
            {getStatusBadge(health.minio)}
          </div>
        </div>
      )}

      {/* Additional Info */}
      <div className="mt-6 p-4 bg-slate-50 border border-slate-200 rounded-lg">
        <h3 className="text-sm font-semibold text-slate-900 mb-2">About Monitoring</h3>
        <ul className="text-sm text-slate-600 space-y-1">
          <li>• Health checks run every 30 seconds automatically</li>
          <li>• Metrics are collected at <code className="px-1 py-0.5 bg-white rounded text-xs">/metrics</code> endpoint</li>
          <li>• Errors are tracked with Sentry (if configured)</li>
          <li>• All requests include X-Request-ID for tracing</li>
        </ul>
      </div>
    </div>
  );
};

export default MonitoringDashboard;
