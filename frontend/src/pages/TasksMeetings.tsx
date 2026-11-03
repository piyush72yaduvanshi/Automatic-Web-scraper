import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { TaskItem, MeetingItem } from '../types';
import {
  CheckSquare,
  Calendar,
  Plus,
  CheckCircle2,
  Clock,
  Sparkles,
  Building2,
} from 'lucide-react';

const TasksMeetings: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'tasks' | 'meetings'>('tasks');

  // Task creation state
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [taskTitle, setTaskTitle] = useState('');
  const [taskPriority, setTaskPriority] = useState('medium');
  const [taskDueDate, setTaskDueDate] = useState('');

  // Meeting creation state
  const [showMeetingModal, setShowMeetingModal] = useState(false);
  const [meetingTitle, setMeetingTitle] = useState('Product Demo & Architecture Discussion');
  const [meetingStart, setMeetingStart] = useState('2026-11-10T10:00');
  const [meetingEnd, setMeetingEnd] = useState('2026-11-10T10:45');
  const [meetingAgenda, setMeetingAgenda] = useState('Review CRM requirements and present tailored software solution');

  // 1. Fetch Tasks
  const { data: tasks, isLoading: loadingTasks } = useQuery<TaskItem[]>({
    queryKey: ['crm_tasks'],
    queryFn: async () => {
      const res = await api.get('/crm/tasks');
      return res.data;
    },
    refetchInterval: 10000,
  });

  // 2. Fetch Meetings
  const { data: meetings, isLoading: loadingMeetings } = useQuery<MeetingItem[]>({
    queryKey: ['crm_meetings'],
    queryFn: async () => {
      const res = await api.get('/crm/meetings');
      return res.data;
    },
    refetchInterval: 10000,
  });

  // Complete Task Mutation
  const completeTaskMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.patch(`/crm/tasks/${id}/complete`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm_tasks'] });
    },
  });

  // Create Task Mutation
  const createTaskMutation = useMutation({
    mutationFn: async (payload: any) => {
      await api.post('/crm/tasks', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm_tasks'] });
      setShowTaskModal(false);
      setTaskTitle('');
    },
  });

  // Create Meeting Mutation
  const createMeetingMutation = useMutation({
    mutationFn: async (payload: any) => {
      await api.post('/crm/meetings', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm_meetings'] });
      setShowMeetingModal(false);
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <CheckSquare className="w-6 h-6 text-blue-600" />
            Tasks, Follow-ups & Calendar Meetings
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Stay on top of sales action items, scheduled calls, and automated meeting prep dossiers.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="bg-slate-100 p-1 rounded-lg flex gap-1">
            <button
              onClick={() => setActiveTab('tasks')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === 'tasks' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'
              }`}
            >
              Action Tasks
            </button>
            <button
              onClick={() => setActiveTab('meetings')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === 'meetings' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'
              }`}
            >
              Meetings
            </button>
          </div>

          <button
            onClick={() => (activeTab === 'tasks' ? setShowTaskModal(true) : setShowMeetingModal(true))}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold shadow-sm"
          >
            <Plus className="w-4 h-4" /> {activeTab === 'tasks' ? 'Add Task' : 'Schedule Call'}
          </button>
        </div>
      </div>

      {/* Tab: Tasks */}
      {activeTab === 'tasks' && (
        <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
          <div className="p-4 border-b bg-slate-50 text-xs font-semibold text-slate-700 flex justify-between">
            <span>Pending & Completed Tasks</span>
            <span>{tasks?.length || 0} tasks recorded</span>
          </div>

          <div className="divide-y divide-slate-100 text-xs">
            {loadingTasks ? (
              <div className="p-8 text-center text-slate-400">Loading tasks...</div>
            ) : tasks?.length === 0 ? (
              <div className="p-12 text-center text-slate-500">
                No active tasks. Create a follow-up reminder above.
              </div>
            ) : (
              tasks?.map((t) => (
                <div key={t.id} className="p-4 flex items-center justify-between hover:bg-slate-50/50">
                  <div className="flex items-start gap-3">
                    <button
                      onClick={() => t.status !== 'completed' && completeTaskMutation.mutate(t.id)}
                      className={`mt-0.5 rounded-full p-0.5 ${
                        t.status === 'completed' ? 'text-emerald-500 cursor-default' : 'text-slate-300 hover:text-emerald-500'
                      }`}
                    >
                      <CheckCircle2 className="w-5 h-5" />
                    </button>
                    <div>
                      <h4 className={`text-xs font-semibold ${t.status === 'completed' ? 'line-through text-slate-400' : 'text-slate-900'}`}>
                        {t.title}
                      </h4>
                      {t.description && <p className="text-[11px] text-slate-500 mt-0.5">{t.description}</p>}
                      {t.company_name && (
                        <div className="text-[11px] text-slate-600 flex items-center gap-1 mt-1">
                          <Building2 className="w-3 h-3 text-slate-400" /> {t.company_name}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded uppercase ${
                        t.priority === 'urgent' || t.priority === 'high'
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {t.priority}
                    </span>
                    {t.due_date && (
                      <span className="text-[11px] text-slate-500 flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" /> {new Date(t.due_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Tab: Meetings */}
      {activeTab === 'meetings' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {loadingMeetings ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading scheduled meetings...</div>
            ) : meetings?.length === 0 ? (
              <div className="col-span-2 p-12 text-center text-xs text-slate-500 bg-white border rounded-lg">
                No meetings scheduled yet. Click "Schedule Call" to book an introductory meeting with AI briefing.
              </div>
            ) : (
              meetings?.map((m) => (
                <div key={m.id} className="bg-white border rounded-lg p-5 shadow-sm space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">{m.title}</h4>
                      {m.company_name && (
                        <div className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                          <Building2 className="w-3.5 h-3.5 text-slate-400" /> {m.company_name}
                        </div>
                      )}
                    </div>
                    <span className="text-[10px] bg-blue-50 text-blue-700 font-semibold px-2 py-0.5 rounded-full">
                      {m.status}
                    </span>
                  </div>

                  <div className="text-xs text-slate-600 flex items-center gap-2 bg-slate-50 p-2.5 rounded">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    <span>
                      {new Date(m.start_time).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                    </span>
                  </div>

                  {m.prep_notes && (
                    <div className="p-3 bg-indigo-50/70 border border-indigo-100 rounded text-xs text-indigo-950 space-y-1">
                      <div className="font-semibold text-indigo-900 flex items-center gap-1 text-[11px]">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-600" /> AI Executive Briefing:
                      </div>
                      <p className="text-[11px] text-indigo-900 whitespace-pre-wrap leading-relaxed">{m.prep_notes}</p>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Task Modal */}
      {showTaskModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Add CRM Action Task</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Task Title</label>
                <input
                  type="text"
                  placeholder="e.g. Follow up on proposal via LinkedIn"
                  value={taskTitle}
                  onChange={(e) => setTaskTitle(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Priority</label>
                  <select
                    value={taskPriority}
                    onChange={(e) => setTaskPriority(e.target.value)}
                    className="w-full px-3 py-2 border rounded text-xs"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Due Date</label>
                  <input
                    type="date"
                    value={taskDueDate}
                    onChange={(e) => setTaskDueDate(e.target.value)}
                    className="w-full px-3 py-2 border rounded text-xs"
                  />
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <button onClick={() => setShowTaskModal(false)} className="px-3 py-1.5 border rounded text-xs text-slate-700">
                Cancel
              </button>
              <button
                onClick={() => taskTitle && createTaskMutation.mutate({ title: taskTitle, priority: taskPriority, due_date: taskDueDate || undefined })}
                className="px-4 py-1.5 bg-blue-600 text-white rounded text-xs font-semibold hover:bg-blue-700"
              >
                Create Task
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Meeting Modal */}
      {showMeetingModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Schedule Meeting with AI Briefing</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Meeting Title</label>
                <input
                  type="text"
                  value={meetingTitle}
                  onChange={(e) => setMeetingTitle(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">Start Time</label>
                  <input
                    type="datetime-local"
                    value={meetingStart}
                    onChange={(e) => setMeetingStart(e.target.value)}
                    className="w-full px-3 py-2 border rounded text-xs"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1">End Time</label>
                  <input
                    type="datetime-local"
                    value={meetingEnd}
                    onChange={(e) => setMeetingEnd(e.target.value)}
                    className="w-full px-3 py-2 border rounded text-xs"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Agenda</label>
                <textarea
                  rows={3}
                  value={meetingAgenda}
                  onChange={(e) => setMeetingAgenda(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <button onClick={() => setShowMeetingModal(false)} className="px-3 py-1.5 border rounded text-xs text-slate-700">
                Cancel
              </button>
              <button
                onClick={() =>
                  createMeetingMutation.mutate({
                    title: meetingTitle,
                    start_time: meetingStart,
                    end_time: meetingEnd,
                    agenda: meetingAgenda,
                  })
                }
                className="px-4 py-1.5 bg-blue-600 text-white rounded text-xs font-semibold hover:bg-blue-700"
              >
                Schedule & Prep
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TasksMeetings;
