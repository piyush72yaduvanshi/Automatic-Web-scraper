import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { ConversationItem, MessageItem } from '../types';
import {
  MessageSquare,
  Mail,
  MessageCircle,
  Sparkles,
} from 'lucide-react';

const Conversations: React.FC = () => {
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);

  const { data: conversations, isLoading } = useQuery<ConversationItem[]>({
    queryKey: ['conversations_list'],
    queryFn: async () => {
      const res = await api.get('/outreach/conversations');
      return res.data;
    },
    refetchInterval: 10000,
  });

  const activeId = selectedConvId || (conversations && conversations.length > 0 ? conversations[0].id : null);

  const { data: activeConv } = useQuery<any>({
    queryKey: ['conversation_detail', activeId],
    queryFn: async () => {
      if (!activeId) return null;
      const res = await api.get(`/outreach/conversations/${activeId}`);
      return res.data;
    },
    enabled: Boolean(activeId),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <MessageSquare className="w-6 h-6 text-blue-600" />
          Multi-Channel Conversations
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Unified inbox for synchronized Gmail threads and WhatsApp Business messaging.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-[700px]">
        {/* Left: Threads List */}
        <div className="bg-white border rounded-lg overflow-hidden flex flex-col">
          <div className="p-3.5 border-b bg-slate-50 text-xs font-semibold text-slate-700 flex justify-between items-center">
            <span>Conversations Inbox</span>
            <span className="text-[11px] text-slate-400">{conversations?.length || 0} threads</span>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {isLoading ? (
              <div className="p-6 text-center text-xs text-slate-400">Loading inbox...</div>
            ) : conversations?.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-400">
                No active conversations yet. Once approved emails or WhatsApp messages are sent, threads will appear here.
              </div>
            ) : (
              conversations?.map((c) => {
                const isSelected = c.id === activeId;
                return (
                  <div
                    key={c.id}
                    onClick={() => setSelectedConvId(c.id)}
                    className={`p-3.5 cursor-pointer text-left transition-colors ${
                      isSelected ? 'bg-blue-50/70 border-l-4 border-blue-600' : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1.5">
                        {c.channel === 'EMAIL' ? (
                          <Mail className="w-3.5 h-3.5 text-blue-500" />
                        ) : (
                          <MessageCircle className="w-3.5 h-3.5 text-emerald-500" />
                        )}
                        <span className="text-xs font-semibold text-slate-900 line-clamp-1">{c.subject || 'No Subject'}</span>
                      </div>
                      <span className="text-[10px] text-slate-400">{new Date(c.last_message_at).toLocaleDateString()}</span>
                    </div>
                    <div className="text-[11px] text-slate-500 flex justify-between">
                      <span>{c.channel}</span>
                      <span>{c.messages_count} messages</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Messages Thread View */}
        <div className="md:col-span-2 bg-white border rounded-lg flex flex-col overflow-hidden">
          {activeConv ? (
            <>
              {/* Thread Header */}
              <div className="p-4 border-b bg-slate-50 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{activeConv.subject}</h3>
                  <span className="text-xs text-slate-500">Channel: {activeConv.channel}</span>
                </div>
                <span className="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded-full">
                  {activeConv.status}
                </span>
              </div>

              {/* Messages Body */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/40">
                {activeConv.messages?.map((msg: MessageItem) => {
                  const isOutbound = msg.direction === 'OUTBOUND';
                  return (
                    <div key={msg.id} className={`flex flex-col ${isOutbound ? 'items-end' : 'items-start'}`}>
                      <div
                        className={`max-w-lg p-4 rounded-lg text-xs leading-relaxed shadow-xs ${
                          isOutbound
                            ? 'bg-blue-600 text-white rounded-br-none'
                            : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-4 mb-1 text-[10px] opacity-75">
                          <span>{isOutbound ? 'You' : msg.sender}</span>
                          <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                        <div className="whitespace-pre-wrap">{msg.body}</div>

                        {/* AI Classification badge on inbound */}
                        {!isOutbound && msg.ai_classification && (
                          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center gap-1.5 text-[11px] font-semibold text-indigo-700">
                            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                            <span>Intent: {msg.ai_classification}</span>
                          </div>
                        )}
                      </div>

                      {/* AI Suggested Reply */}
                      {!isOutbound && msg.suggested_reply && (
                        <div className="mt-2 max-w-lg p-3 bg-indigo-50 border border-indigo-200 rounded-lg text-xs text-indigo-950 space-y-1.5">
                          <div className="flex items-center gap-1.5 font-semibold text-[11px] text-indigo-800">
                            <Sparkles className="w-3.5 h-3.5" /> AI Suggested Response:
                          </div>
                          <p className="italic text-indigo-900 bg-white/70 p-2 rounded">{msg.suggested_reply}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center p-8 text-slate-400 text-xs">
              Select a conversation to view the message transcript.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Conversations;
