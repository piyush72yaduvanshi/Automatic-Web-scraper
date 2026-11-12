import { useQuery } from '@tanstack/react-query';
import { fetchEmails } from '../services/crmApi';
import { Mail, MailOpen, MousePointerClick, Reply, XCircle, Send } from 'lucide-react';
import type { EmailItem } from '../types';

interface EmailTimelineProps {
  companyId?: string;
  contactId?: string;
  dealId?: string;
}

const EmailTimeline: React.FC<EmailTimelineProps> = ({ companyId, contactId, dealId }) => {
  const { data: emails, isLoading } = useQuery<EmailItem[]>({
    queryKey: ['emails', companyId, contactId, dealId],
    queryFn: async () => {
      return await fetchEmails({
        company_id: companyId,
        contact_id: contactId,
        deal_id: dealId,
        limit: 50,
      });
    },
  });

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusInfo = (status: string) => {
    const statusMap = {
      draft: { 
        icon: Mail, 
        label: 'Draft',
        containerClass: 'bg-slate-500/10 border-slate-500/20',
        iconClass: 'text-slate-400',
        badgeClass: 'bg-slate-500/20 text-slate-400 border-slate-500/30'
      },
      sent: { 
        icon: Send, 
        label: 'Sent',
        containerClass: 'bg-blue-500/10 border-blue-500/20',
        iconClass: 'text-blue-400',
        badgeClass: 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      },
      delivered: { 
        icon: Mail, 
        label: 'Delivered',
        containerClass: 'bg-green-500/10 border-green-500/20',
        iconClass: 'text-green-400',
        badgeClass: 'bg-green-500/20 text-green-400 border-green-500/30'
      },
      opened: { 
        icon: MailOpen, 
        label: 'Opened',
        containerClass: 'bg-indigo-500/10 border-indigo-500/20',
        iconClass: 'text-indigo-400',
        badgeClass: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
      },
      clicked: { 
        icon: MousePointerClick, 
        label: 'Clicked',
        containerClass: 'bg-purple-500/10 border-purple-500/20',
        iconClass: 'text-purple-400',
        badgeClass: 'bg-purple-500/20 text-purple-400 border-purple-500/30'
      },
      replied: { 
        icon: Reply, 
        label: 'Replied',
        containerClass: 'bg-teal-500/10 border-teal-500/20',
        iconClass: 'text-teal-400',
        badgeClass: 'bg-teal-500/20 text-teal-400 border-teal-500/30'
      },
      bounced: { 
        icon: XCircle, 
        label: 'Bounced',
        containerClass: 'bg-red-500/10 border-red-500/20',
        iconClass: 'text-red-400',
        badgeClass: 'bg-red-500/20 text-red-400 border-red-500/30'
      },
    };
    return (
      statusMap[status as keyof typeof statusMap] || {
        icon: Mail,
        label: status,
        containerClass: 'bg-slate-500/10 border-slate-500/20',
        iconClass: 'text-slate-400',
        badgeClass: 'bg-slate-500/20 text-slate-400 border-slate-500/30'
      }
    );
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Mail className="w-5 h-5 text-blue-400" />
        <h3 className="text-lg font-bold text-white">Email Timeline</h3>
        <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-slate-800 text-slate-300">
          {emails?.length || 0}
        </span>
      </div>

      {/* Timeline */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="p-8 text-center text-sm text-slate-400">
            <div className="w-6 h-6 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin mx-auto mb-2" />
            Loading emails...
          </div>
        ) : emails?.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500 bg-slate-800/30 rounded-xl border border-slate-800">
            No email activity yet.
          </div>
        ) : (
          emails?.map((email) => {
            const statusInfo = getStatusInfo(email.status);
            const StatusIcon = statusInfo.icon;

            return (
              <div
                key={email.id}
                className="p-4 rounded-xl bg-slate-800/30 border border-slate-800 hover:border-slate-700 transition-all"
              >
                <div className="flex items-start gap-3">
                  {/* Status Icon */}
                  <div
                    className={`p-2 rounded-lg border ${statusInfo.containerClass}`}
                  >
                    <StatusIcon className={`w-4 h-4 ${statusInfo.iconClass}`} />
                  </div>

                  {/* Email Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-semibold text-white truncate">
                          {email.subject || '(No Subject)'}
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">
                          {email.direction === 'OUTBOUND' ? 'Sent to' : 'Received from'}{' '}
                          {email.contact_name || email.company_name || 'Unknown'}
                        </div>
                      </div>
                      <span
                        className={`px-2 py-0.5 text-xs font-semibold rounded-full border whitespace-nowrap ${statusInfo.badgeClass}`}
                      >
                        {statusInfo.label}
                      </span>
                    </div>

                    {/* Email Body Preview */}
                    {email.body_text && (
                      <div className="text-sm text-slate-300 line-clamp-2 mb-2">
                        {email.body_text}
                      </div>
                    )}

                    {/* Timestamps */}
                    <div className="flex flex-wrap gap-3 text-xs text-slate-500">
                      {email.sent_at && (
                        <div>
                          <span className="text-slate-600">Sent:</span> {formatDate(email.sent_at)}
                        </div>
                      )}
                      {email.opened_at && (
                        <div>
                          <span className="text-slate-600">Opened:</span>{' '}
                          {formatDate(email.opened_at)}
                        </div>
                      )}
                      {email.clicked_at && (
                        <div>
                          <span className="text-slate-600">Clicked:</span>{' '}
                          {formatDate(email.clicked_at)}
                        </div>
                      )}
                      {email.replied_at && (
                        <div>
                          <span className="text-slate-600">Replied:</span>{' '}
                          {formatDate(email.replied_at)}
                        </div>
                      )}
                    </div>

                    {/* Engagement Indicators */}
                    {(email.opened_at || email.clicked_at || email.replied_at) && (
                      <div className="flex gap-2 mt-3">
                        {email.opened_at && (
                          <div className="flex items-center gap-1 px-2 py-1 bg-indigo-500/10 rounded-lg">
                            <MailOpen className="w-3 h-3 text-indigo-400" />
                            <span className="text-xs text-indigo-400">Opened</span>
                          </div>
                        )}
                        {email.clicked_at && (
                          <div className="flex items-center gap-1 px-2 py-1 bg-purple-500/10 rounded-lg">
                            <MousePointerClick className="w-3 h-3 text-purple-400" />
                            <span className="text-xs text-purple-400">Clicked</span>
                          </div>
                        )}
                        {email.replied_at && (
                          <div className="flex items-center gap-1 px-2 py-1 bg-teal-500/10 rounded-lg">
                            <Reply className="w-3 h-3 text-teal-400" />
                            <span className="text-xs text-teal-400">Replied</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default EmailTimeline;
