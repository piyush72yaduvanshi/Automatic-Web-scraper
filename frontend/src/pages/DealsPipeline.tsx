import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { KanbanBoard, KanbanStage, DealItem } from '../types';
import {
  Kanban,
  Plus,
  ChevronRight,
  Building2,
  DollarSign,
  TrendingUp,
  Sparkles,
} from 'lucide-react';

const DealsPipeline: React.FC = () => {
  const queryClient = useQueryClient();
  const [showAddDealModal, setShowAddDealModal] = useState(false);
  const [newDealTitle, setNewDealTitle] = useState('');
  const [newDealAmount, setNewDealAmount] = useState('5000');
  const [newDealCompany, setNewDealCompany] = useState('');

  // 1. Fetch Kanban Board
  const { data: kanban, isLoading } = useQuery<KanbanBoard>({
    queryKey: ['crm_kanban'],
    queryFn: async () => {
      const res = await api.get('/crm/deals/kanban');
      return res.data;
    },
    refetchInterval: 12000,
  });

  // 2. Fetch Companies for Dropdown
  const { data: companies } = useQuery<any[]>({
    queryKey: ['crm_companies_list'],
    queryFn: async () => {
      const res = await api.get('/crm/companies');
      return res.data;
    },
  });

  // Stage Move Mutation
  const moveStageMutation = useMutation({
    mutationFn: async ({ dealId, stageId }: { dealId: string; stageId: string }) => {
      await api.patch(`/crm/deals/${dealId}/stage`, { stage_id: stageId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm_kanban'] });
    },
  });

  // Create Deal Mutation
  const createDealMutation = useMutation({
    mutationFn: async (payload: any) => {
      await api.post('/crm/deals', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm_kanban'] });
      setShowAddDealModal(false);
      setNewDealTitle('');
      setNewDealAmount('5000');
    },
  });

  const handleAdvanceDeal = (deal: DealItem, currentStageIndex: number, stages: KanbanStage[]) => {
    if (currentStageIndex < stages.length - 1) {
      const nextStage = stages[currentStageIndex + 1];
      moveStageMutation.mutate({ dealId: deal.id, stageId: nextStage.id });
    }
  };

  const totalPipelineVal = kanban?.stages.reduce((acc, s) => acc + s.total_value, 0) || 0;
  const totalDealsCount = kanban?.stages.reduce((acc, s) => acc + s.deals_count, 0) || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
              <span className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                <Kanban className="w-5 h-5" />
              </span>
              Deals & Sales Pipeline Kanban
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Live Real-Time
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1.5">
            Visual sales pipeline. Advance opportunities from Lead to Closed Won with automated revenue forecasting.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-[#0E1424] border border-slate-800 px-4 py-2 rounded-xl text-right hidden sm:block">
            <span className="text-[10px] text-slate-400 block font-semibold uppercase tracking-wider">
              Open Pipeline Value
            </span>
            <div className="flex items-center justify-end gap-1 text-emerald-400 font-bold text-base">
              <DollarSign className="w-4 h-4 text-emerald-400" />
              <span>{totalPipelineVal.toLocaleString()}</span>
              <span className="text-slate-500 text-xs font-normal">({totalDealsCount} deals)</span>
            </div>
          </div>

          <button
            onClick={() => setShowAddDealModal(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all"
          >
            <Plus className="w-4 h-4" /> Add Opportunity
          </button>
        </div>
      </div>

      {/* Kanban Board Columns */}
      {isLoading ? (
        <div className="p-16 text-center text-sm text-slate-400 bg-[#0E1424] rounded-2xl border border-slate-800 flex flex-col items-center justify-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
          <span>Synchronizing sales pipeline state...</span>
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4 pt-1">
          {kanban?.stages.map((stage, sIdx) => (
            <div
              key={stage.id}
              className="w-80 flex-shrink-0 bg-[#0E1424] rounded-2xl border border-slate-800 flex flex-col max-h-[760px] shadow-sm hover:border-slate-700 transition-colors"
            >
              {/* Column Header */}
              <div className="p-4 border-b border-slate-800/80 bg-[#131B2E]/60 rounded-t-2xl flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs font-bold text-white tracking-tight">{stage.name}</h3>
                    <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-slate-800 text-slate-300 rounded-md">
                      {stage.deals_count}
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-medium mt-0.5 block">
                    ${stage.total_value.toLocaleString()} expected
                  </span>
                </div>
                <span className="text-[10px] font-semibold text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                  <TrendingUp className="w-2.5 h-2.5" />
                  {(stage.probability * 100).toFixed(0)}%
                </span>
              </div>

              {/* Deal Cards Container */}
              <div className="p-3 flex-1 overflow-y-auto space-y-3 custom-scrollbar">
                {stage.deals.length === 0 ? (
                  <div className="py-12 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl my-2">
                    No active deals in stage
                  </div>
                ) : (
                  stage.deals.map((deal) => (
                    <div
                      key={deal.id}
                      className="bg-[#131B2E] p-4 rounded-xl border border-slate-800/90 shadow-sm hover:border-indigo-500/50 hover:shadow-indigo-500/10 hover:shadow-md transition-all space-y-2.5 group"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-xs font-bold text-slate-100 group-hover:text-white leading-snug transition-colors">
                          {deal.title}
                        </h4>
                        <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-md flex-shrink-0">
                          ${deal.amount.toLocaleString()}
                        </span>
                      </div>

                      <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-slate-500" />
                        <span className="truncate">{deal.company_name || 'Individual Prospect'}</span>
                      </div>

                      <div className="flex items-center justify-between pt-2.5 border-t border-slate-800/80 text-[10px]">
                        <span className="text-slate-500">
                          {new Date(deal.created_at).toLocaleDateString()}
                        </span>
                        {sIdx < (kanban?.stages.length || 0) - 1 && (
                          <button
                            onClick={() => handleAdvanceDeal(deal, sIdx, kanban!.stages)}
                            disabled={moveStageMutation.isPending}
                            className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-semibold bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 px-2.5 py-1 rounded-lg transition-all"
                          >
                            Advance <ChevronRight className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Deal Modal */}
      {showAddDealModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0E1424] border border-slate-800 rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-5 text-white">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Create New Opportunity
              </h3>
              <button
                onClick={() => setShowAddDealModal(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Deal Title *</label>
                <input
                  type="text"
                  placeholder="e.g. Enterprise Software License & Setup"
                  value={newDealTitle}
                  onChange={(e) => setNewDealTitle(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Estimated Value ($ USD)</label>
                <div className="relative">
                  <DollarSign className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="number"
                    value={newDealAmount}
                    onChange={(e) => setNewDealAmount(e.target.value)}
                    className="w-full pl-9 pr-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Associated Company</label>
                <select
                  value={newDealCompany}
                  onChange={(e) => setNewDealCompany(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-[#131B2E] border border-slate-700 rounded-xl text-xs text-slate-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">Select a company (Optional)...</option>
                  {companies?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                onClick={() => setShowAddDealModal(false)}
                className="px-4 py-2 border border-slate-700 rounded-xl text-xs text-slate-300 hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  newDealTitle &&
                  createDealMutation.mutate({
                    title: newDealTitle,
                    amount: parseFloat(newDealAmount) || 0,
                    company_id: newDealCompany || undefined,
                  })
                }
                disabled={!newDealTitle || createDealMutation.isPending}
                className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white rounded-xl text-xs font-semibold shadow-md transition-all disabled:opacity-50"
              >
                {createDealMutation.isPending ? 'Creating...' : 'Create Deal'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DealsPipeline;
