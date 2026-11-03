import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { KanbanBoard, KanbanStage, DealItem } from '../types';
import {
  Kanban,
  Plus,
  ChevronRight,
  Building2,
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Kanban className="w-6 h-6 text-blue-600" />
            Deals & Sales Pipeline Kanban
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Visual sales pipeline. Advance opportunities from Lead to Won with revenue tracking.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <span className="text-[11px] text-slate-400 block font-semibold uppercase">Open Pipeline Value</span>
            <span className="text-base font-bold text-slate-900">${totalPipelineVal.toLocaleString()}</span>
          </div>
          <button
            onClick={() => setShowAddDealModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold shadow-sm transition-colors"
          >
            <Plus className="w-4 h-4" /> Add Opportunity
          </button>
        </div>
      </div>

      {/* Kanban Board Columns */}
      {isLoading ? (
        <div className="p-12 text-center text-sm text-slate-500 bg-white rounded-lg border">Loading Sales Pipeline...</div>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {kanban?.stages.map((stage, sIdx) => (
            <div
              key={stage.id}
              className="w-72 flex-shrink-0 bg-slate-100/90 rounded-lg border border-slate-200 flex flex-col max-h-[750px]"
            >
              {/* Column Header */}
              <div className="p-3.5 border-b border-slate-200/80 bg-white/70 rounded-t-lg flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold text-slate-800 tracking-tight">{stage.name}</h3>
                  <span className="text-[10px] text-slate-500 font-medium">
                    ${stage.total_value.toLocaleString()} ({stage.deals_count})
                  </span>
                </div>
                <span className="text-[10px] font-semibold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                  {(stage.probability * 100).toFixed(0)}%
                </span>
              </div>

              {/* Deal Cards Container */}
              <div className="p-2.5 flex-1 overflow-y-auto space-y-2.5">
                {stage.deals.length === 0 ? (
                  <div className="py-8 text-center text-xs text-slate-400">No deals in this stage</div>
                ) : (
                  stage.deals.map((deal) => (
                    <div
                      key={deal.id}
                      className="bg-white p-3.5 rounded-md border border-slate-200/90 shadow-xs hover:shadow-sm hover:border-slate-300 transition-all space-y-2"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-xs font-bold text-slate-900 leading-snug">{deal.title}</h4>
                        <span className="text-xs font-bold text-emerald-600 flex-shrink-0">
                          ${deal.amount.toLocaleString()}
                        </span>
                      </div>

                      <div className="text-[11px] text-slate-600 flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-slate-400" />
                        <span>{deal.company_name}</span>
                      </div>

                      <div className="flex items-center justify-between pt-1.5 border-t border-slate-100 text-[10px]">
                        <span className="text-slate-400">
                          {new Date(deal.created_at).toLocaleDateString()}
                        </span>
                        {sIdx < (kanban?.stages.length || 0) - 1 && (
                          <button
                            onClick={() => handleAdvanceDeal(deal, sIdx, kanban!.stages)}
                            className="inline-flex items-center gap-0.5 text-blue-600 hover:text-blue-800 font-semibold"
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
        <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Create New Opportunity</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Deal Title</label>
                <input
                  type="text"
                  placeholder="e.g. Enterprise Software License & Setup"
                  value={newDealTitle}
                  onChange={(e) => setNewDealTitle(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Estimated Value ($ USD)</label>
                <input
                  type="number"
                  value={newDealAmount}
                  onChange={(e) => setNewDealAmount(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Associated Company</label>
                <select
                  value={newDealCompany}
                  onChange={(e) => setNewDealCompany(e.target.value)}
                  className="w-full px-3 py-2 border rounded text-xs"
                >
                  <option value="">Select a company...</option>
                  {companies?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t">
              <button
                onClick={() => setShowAddDealModal(false)}
                className="px-3 py-1.5 border rounded text-xs text-slate-700 hover:bg-slate-50"
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
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold shadow-sm"
              >
                Create Deal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DealsPipeline;
