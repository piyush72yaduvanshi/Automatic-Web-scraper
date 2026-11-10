import React, { useState, useEffect } from 'react';
import {
  Plus,
  Calendar,
  Clock,
  MapPin,
  Building,
  Play,
  Edit2,
  Trash2,
  Target,
  ChevronRight,
  ToggleLeft,
  ToggleRight,
  Save,
  X,
  GripVertical,
} from 'lucide-react';
import DiscoveryRunHistory from '../components/DiscoveryRunHistory';

interface DiscoveryTarget {
  id: string;
  type: 'city' | 'country' | 'industry' | 'keyword';
  value: string;
  priority: number;
}

interface DiscoverySchedule {
  id: string;
  name: string;
  description: string;
  scheduleType: 'hourly' | 'daily' | 'weekly' | 'custom';
  cronExpression?: string;
  intervalHours?: number;
  maxLeadsPerRun: number;
  active: boolean;
  lastRunAt?: string;
  nextRunAt?: string;
  leadsDiscovered: number;
  targets: DiscoveryTarget[];
}

const DiscoveryScheduler: React.FC = () => {
  const [schedules, setSchedules] = useState<DiscoverySchedule[]>([]);
  const [selectedSchedule, setSelectedSchedule] = useState<DiscoverySchedule | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [editingSchedule, setEditingSchedule] = useState<Partial<DiscoverySchedule> | null>(null);
  const [newTarget, setNewTarget] = useState({ type: 'city', value: '' });

  // Fetch schedules from backend
  useEffect(() => {
    fetchSchedules();
  }, []);

  const fetchSchedules = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/discovery/schedules');
      if (response.ok) {
        const data = await response.json();
        setSchedules(data);
      }
    } catch (error) {
      console.error('Failed to fetch schedules:', error);
      showToast('Failed to load schedules', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    // Simple toast implementation - can be replaced with a proper toast library
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white text-sm font-medium transition-all ${
      type === 'success' ? 'bg-emerald-600' : type === 'error' ? 'bg-red-600' : 'bg-indigo-600'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  };

  const handleCreateSchedule = () => {
    setEditingSchedule({
      name: '',
      description: '',
      scheduleType: 'daily',
      maxLeadsPerRun: 100,
      active: true,
      targets: [],
      leadsDiscovered: 0,
    });
    setShowCreateModal(true);
  };

  const handleSaveSchedule = async () => {
    if (!editingSchedule || !editingSchedule.name) {
      showToast('Please enter a schedule name', 'error');
      return;
    }

    try {
      const method = editingSchedule.id ? 'PUT' : 'POST';
      const url = editingSchedule.id
        ? `/api/discovery/schedules/${editingSchedule.id}`
        : '/api/discovery/schedules';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editingSchedule),
      });

      if (response.ok) {
        const saved = await response.json();
        if (editingSchedule.id) {
          setSchedules(schedules.map((s) => (s.id === saved.id ? saved : s)));
          showToast('Schedule updated successfully', 'success');
        } else {
          setSchedules([...schedules, saved]);
          showToast('Schedule created successfully', 'success');
        }
        setShowCreateModal(false);
        setEditingSchedule(null);
      } else {
        showToast('Failed to save schedule', 'error');
      }
    } catch (error) {
      console.error('Failed to save schedule:', error);
      showToast('Failed to save schedule', 'error');
    }
  };

  const handleToggleActive = async (schedule: DiscoverySchedule) => {
    try {
      const response = await fetch(`/api/discovery/schedules/${schedule.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...schedule, active: !schedule.active }),
      });

      if (response.ok) {
        const updated = await response.json();
        setSchedules(schedules.map((s) => (s.id === updated.id ? updated : s)));
        showToast(
          `Schedule ${updated.active ? 'activated' : 'deactivated'}`,
          'success'
        );
      }
    } catch (error) {
      console.error('Failed to toggle schedule:', error);
      showToast('Failed to update schedule', 'error');
    }
  };

  const handleDeleteSchedule = async (scheduleId: string) => {
    if (!confirm('Are you sure you want to delete this schedule?')) return;

    try {
      const response = await fetch(`/api/discovery/schedules/${scheduleId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setSchedules(schedules.filter((s) => s.id !== scheduleId));
        if (selectedSchedule?.id === scheduleId) {
          setSelectedSchedule(null);
        }
        showToast('Schedule deleted successfully', 'success');
      }
    } catch (error) {
      console.error('Failed to delete schedule:', error);
      showToast('Failed to delete schedule', 'error');
    }
  };

  const handleRunNow = async (scheduleId: string) => {
    try {
      const response = await fetch(`/api/discovery/schedules/${scheduleId}/run`, {
        method: 'POST',
      });

      if (response.ok) {
        showToast('Discovery run triggered successfully', 'success');
        fetchSchedules();
      } else {
        showToast('Failed to trigger discovery run', 'error');
      }
    } catch (error) {
      console.error('Failed to run schedule:', error);
      showToast('Failed to trigger discovery run', 'error');
    }
  };

  const handleAddTarget = () => {
    if (!editingSchedule || !newTarget.value.trim()) return;

    const target: DiscoveryTarget = {
      id: Date.now().toString(),
      type: newTarget.type as DiscoveryTarget['type'],
      value: newTarget.value.trim(),
      priority: (editingSchedule.targets?.length || 0) + 1,
    };

    setEditingSchedule({
      ...editingSchedule,
      targets: [...(editingSchedule.targets || []), target],
    });
    setNewTarget({ type: 'city', value: '' });
  };

  const handleRemoveTarget = (targetId: string) => {
    if (!editingSchedule) return;
    setEditingSchedule({
      ...editingSchedule,
      targets: editingSchedule.targets?.filter((t) => t.id !== targetId),
    });
  };

  const formatNextRun = (nextRunAt?: string) => {
    if (!nextRunAt) return 'Not scheduled';
    const date = new Date(nextRunAt);
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    if (hours > 24) return `In ${Math.floor(hours / 24)}d ${hours % 24}h`;
    if (hours > 0) return `In ${hours}h ${minutes}m`;
    if (minutes > 0) return `In ${minutes}m`;
    return 'Soon';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Target className="w-7 h-7 text-indigo-400" />
            Automated Lead Discovery
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Schedule and manage automated lead discovery from multiple sources
          </p>
        </div>
        <button
          onClick={handleCreateSchedule}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-indigo-500/25 transition-all"
        >
          <Plus className="w-4 h-4" />
          Create New Schedule
        </button>
      </div>

      {/* Schedules List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full flex items-center justify-center py-12">
            <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : schedules.length === 0 ? (
          <div className="col-span-full bg-slate-900/50 border border-slate-800 rounded-xl p-12 text-center">
            <Target className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No discovery schedules yet</p>
            <button
              onClick={handleCreateSchedule}
              className="mt-4 text-indigo-400 text-sm font-medium hover:text-indigo-300"
            >
              Create your first schedule
            </button>
          </div>
        ) : (
          schedules.map((schedule) => (
            <div
              key={schedule.id}
              className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 hover:border-indigo-500/50 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-base font-semibold text-white mb-1">
                    {schedule.name}
                  </h3>
                  <p className="text-xs text-slate-400">{schedule.description}</p>
                </div>
                <button
                  onClick={() => handleToggleActive(schedule)}
                  className="ml-2 transition-colors"
                >
                  {schedule.active ? (
                    <ToggleRight className="w-8 h-8 text-emerald-500" />
                  ) : (
                    <ToggleLeft className="w-8 h-8 text-slate-600" />
                  )}
                </button>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex items-center text-xs text-slate-400">
                  <Calendar className="w-3.5 h-3.5 mr-1.5" />
                  <span className="capitalize">{schedule.scheduleType}</span>
                  {schedule.intervalHours && (
                    <span className="ml-1">({schedule.intervalHours}h)</span>
                  )}
                </div>
                <div className="flex items-center text-xs text-slate-400">
                  <Clock className="w-3.5 h-3.5 mr-1.5" />
                  Next run: {formatNextRun(schedule.nextRunAt)}
                </div>
                <div className="flex items-center text-xs text-emerald-400">
                  <Target className="w-3.5 h-3.5 mr-1.5" />
                  {schedule.leadsDiscovered} leads discovered
                </div>
              </div>

              <div className="flex items-center gap-2 pt-3 border-t border-slate-800">
                <button
                  onClick={() => {
                    setEditingSchedule(schedule);
                    setShowCreateModal(true);
                  }}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition-colors"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                  Edit
                </button>
                <button
                  onClick={() => handleRunNow(schedule.id)}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition-colors"
                >
                  <Play className="w-3.5 h-3.5" />
                  Run Now
                </button>
                <button
                  onClick={() => handleDeleteSchedule(schedule.id)}
                  className="px-3 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 text-xs font-medium rounded-lg transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              {schedule.targets && schedule.targets.length > 0 && (
                <button
                  onClick={() => setSelectedSchedule(schedule)}
                  className="w-full mt-3 flex items-center justify-center gap-1 px-3 py-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  View {schedule.targets.length} targets
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* Target Management Section */}
      {selectedSchedule && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">
              Targets for "{selectedSchedule.name}"
            </h2>
            <button
              onClick={() => setSelectedSchedule(null)}
              className="p-1 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-2">
            {selectedSchedule.targets && selectedSchedule.targets.length > 0 ? (
              selectedSchedule.targets.map((target) => (
                <div
                  key={target.id}
                  className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg"
                >
                  <GripVertical className="w-4 h-4 text-slate-600" />
                  <div className="flex items-center gap-2 flex-1">
                    {target.type === 'city' && <MapPin className="w-4 h-4 text-blue-400" />}
                    {target.type === 'industry' && <Building className="w-4 h-4 text-purple-400" />}
                    <div className="flex-1">
                      <div className="text-sm font-medium text-white">{target.value}</div>
                      <div className="text-xs text-slate-400 capitalize">{target.type}</div>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500">Priority {target.priority}</div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-slate-400 text-sm">
                No targets configured
              </div>
            )}
          </div>
        </div>
      )}

      {/* Discovery Run History */}
      <DiscoveryRunHistory />

      {/* Create/Edit Schedule Modal */}
      {showCreateModal && editingSchedule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
            <div className="sticky top-0 bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">
                {editingSchedule.id ? 'Edit Schedule' : 'Create New Schedule'}
              </h2>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingSchedule(null);
                }}
                className="p-1 text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Schedule Name <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={editingSchedule.name || ''}
                  onChange={(e) =>
                    setEditingSchedule({ ...editingSchedule, name: e.target.value })
                  }
                  placeholder="e.g., Daily City Discovery"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Description
                </label>
                <textarea
                  value={editingSchedule.description || ''}
                  onChange={(e) =>
                    setEditingSchedule({ ...editingSchedule, description: e.target.value })
                  }
                  placeholder="Describe the purpose of this schedule"
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              {/* Schedule Type */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Schedule Type
                </label>
                <select
                  value={editingSchedule.scheduleType || 'daily'}
                  onChange={(e) =>
                    setEditingSchedule({
                      ...editingSchedule,
                      scheduleType: e.target.value as DiscoverySchedule['scheduleType'],
                    })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="custom">Custom (Cron)</option>
                </select>
              </div>

              {/* Hourly Interval */}
              {editingSchedule.scheduleType === 'hourly' && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Interval (hours)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="24"
                    value={editingSchedule.intervalHours || 1}
                    onChange={(e) =>
                      setEditingSchedule({
                        ...editingSchedule,
                        intervalHours: parseInt(e.target.value),
                      })
                    }
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              )}

              {/* Cron Expression */}
              {editingSchedule.scheduleType === 'custom' && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Cron Expression
                  </label>
                  <input
                    type="text"
                    value={editingSchedule.cronExpression || ''}
                    onChange={(e) =>
                      setEditingSchedule({
                        ...editingSchedule,
                        cronExpression: e.target.value,
                      })
                    }
                    placeholder="0 9 * * *"
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    Example: "0 9 * * *" runs daily at 9 AM
                  </p>
                </div>
              )}

              {/* Max Leads Per Run */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                  Max Leads Per Run
                </label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={editingSchedule.maxLeadsPerRun || 100}
                  onChange={(e) =>
                    setEditingSchedule({
                      ...editingSchedule,
                      maxLeadsPerRun: parseInt(e.target.value),
                    })
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              {/* Active Toggle */}
              <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
                <div>
                  <div className="text-sm font-medium text-white">Active</div>
                  <div className="text-xs text-slate-400">
                    Enable this schedule to run automatically
                  </div>
                </div>
                <button
                  onClick={() =>
                    setEditingSchedule({
                      ...editingSchedule,
                      active: !editingSchedule.active,
                    })
                  }
                >
                  {editingSchedule.active ? (
                    <ToggleRight className="w-10 h-10 text-emerald-500" />
                  ) : (
                    <ToggleLeft className="w-10 h-10 text-slate-600" />
                  )}
                </button>
              </div>

              {/* Target Management */}
              <div className="border-t border-slate-800 pt-4">
                <h3 className="text-sm font-semibold text-white mb-3">Discovery Targets</h3>

                {/* Add Target Form */}
                <div className="flex gap-2 mb-3">
                  <select
                    value={newTarget.type}
                    onChange={(e) => setNewTarget({ ...newTarget, type: e.target.value })}
                    className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option value="city">City</option>
                    <option value="country">Country</option>
                    <option value="industry">Industry</option>
                    <option value="keyword">Keyword</option>
                  </select>
                  <input
                    type="text"
                    value={newTarget.value}
                    onChange={(e) => setNewTarget({ ...newTarget, value: e.target.value })}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddTarget()}
                    placeholder="Enter target value"
                    className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    onClick={handleAddTarget}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>

                {/* Target List */}
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {editingSchedule.targets && editingSchedule.targets.length > 0 ? (
                    editingSchedule.targets.map((target) => (
                      <div
                        key={target.id}
                        className="flex items-center gap-3 p-2.5 bg-slate-800/50 rounded-lg"
                      >
                        <GripVertical className="w-4 h-4 text-slate-600" />
                        {target.type === 'city' && <MapPin className="w-4 h-4 text-blue-400" />}
                        {target.type === 'industry' && (
                          <Building className="w-4 h-4 text-purple-400" />
                        )}
                        <div className="flex-1">
                          <div className="text-sm text-white">{target.value}</div>
                          <div className="text-xs text-slate-500 capitalize">{target.type}</div>
                        </div>
                        <button
                          onClick={() => handleRemoveTarget(target.id)}
                          className="p-1 text-red-400 hover:text-red-300 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-6 text-slate-500 text-sm">
                      No targets added yet
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="sticky bottom-0 bg-slate-900 border-t border-slate-800 px-6 py-4 flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingSchedule(null);
                }}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveSchedule}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white text-sm font-semibold rounded-lg transition-all"
              >
                <Save className="w-4 h-4" />
                {editingSchedule.id ? 'Update Schedule' : 'Create Schedule'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiscoveryScheduler;
