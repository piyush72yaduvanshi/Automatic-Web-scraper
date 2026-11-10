import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';

// Fast initial load: Eagerly load core dashboard
import Dashboard from './pages/Dashboard';

// Lazy load route pages for code-splitting and bundle performance
const Discovery = lazy(() => import('./pages/Discovery'));
const Jobs = lazy(() => import('./pages/Jobs'));
const Leads = lazy(() => import('./pages/Leads'));
const LeadDetail = lazy(() => import('./pages/LeadDetail'));
const Companies = lazy(() => import('./pages/Companies'));
const Contacts = lazy(() => import('./pages/Contacts'));
const DealsPipeline = lazy(() => import('./pages/DealsPipeline'));
const ResearchIntel = lazy(() => import('./pages/ResearchIntel'));
const OutreachApprovals = lazy(() => import('./pages/OutreachApprovals'));
const Conversations = lazy(() => import('./pages/Conversations'));
const TasksMeetings = lazy(() => import('./pages/TasksMeetings'));
const AIAgents = lazy(() => import('./pages/AIAgents'));
const KnowledgeBase = lazy(() => import('./pages/KnowledgeBase'));
const AnalyticsView = lazy(() => import('./pages/AnalyticsView'));
const IntegrationsView = lazy(() => import('./pages/IntegrationsView'));
const SettingsView = lazy(() => import('./pages/SettingsView'));

// Phase 2 Enterprise Views
const WorkflowEngineView = lazy(() =>
  import('./pages/WorkflowEngineView').then((m) => ({ default: m.WorkflowEngineView }))
);
const DeliverabilityView = lazy(() =>
  import('./pages/DeliverabilityView').then((m) => ({ default: m.DeliverabilityView }))
);
const CampaignsView = lazy(() =>
  import('./pages/CampaignsView').then((m) => ({ default: m.CampaignsView }))
);
const SequencesView = lazy(() =>
  import('./pages/SequencesView').then((m) => ({ default: m.SequencesView }))
);
const ComplianceView = lazy(() =>
  import('./pages/ComplianceView').then((m) => ({ default: m.ComplianceView }))
);
const ContentSocialView = lazy(() =>
  import('./pages/ContentSocialView').then((m) => ({ default: m.ContentSocialView }))
);
const SEOView = lazy(() =>
  import('./pages/SEOView').then((m) => ({ default: m.SEOView }))
);
const MeetingsView = lazy(() =>
  import('./pages/MeetingsView').then((m) => ({ default: m.MeetingsView }))
);
const ReportsView = lazy(() =>
  import('./pages/ReportsView').then((m) => ({ default: m.ReportsView }))
);
const ExceptionQueueView = lazy(() =>
  import('./pages/ExceptionQueueView').then((m) => ({ default: m.ExceptionQueueView }))
);
const MonitoringDashboard = lazy(() => import('./pages/MonitoringDashboard'));

const PageLoader: React.FC = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <div className="flex flex-col items-center gap-3">
      <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
      <p className="text-sm font-medium text-slate-500">Loading module...</p>
    </div>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="discovery" element={<Discovery />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="leads" element={<Leads />} />
            <Route path="leads/:id" element={<LeadDetail />} />

            {/* CRM & Deals */}
            <Route path="companies" element={<Companies />} />
            <Route path="contacts" element={<Contacts />} />
            <Route path="pipeline" element={<DealsPipeline />} />
            <Route path="meetings" element={<MeetingsView />} />
            <Route path="tasks" element={<TasksMeetings />} />

            {/* Automation & Sequences */}
            <Route path="workflows" element={<WorkflowEngineView />} />
            <Route path="campaigns" element={<CampaignsView />} />
            <Route path="sequences" element={<SequencesView />} />
            <Route path="outreach" element={<OutreachApprovals />} />
            <Route path="conversations" element={<Conversations />} />

            {/* Marketing & SEO */}
            <Route path="content" element={<ContentSocialView />} />
            <Route path="social" element={<ContentSocialView />} />
            <Route path="seo" element={<SEOView />} />
            <Route path="research" element={<ResearchIntel />} />

            {/* Governance & Health */}
            <Route path="deliverability" element={<DeliverabilityView />} />
            <Route path="compliance" element={<ComplianceView />} />
            <Route path="exceptions" element={<ExceptionQueueView />} />
            <Route path="monitoring" element={<MonitoringDashboard />} />
            <Route path="reports" element={<ReportsView />} />
            <Route path="agents" element={<AIAgents />} />
            <Route path="knowledge" element={<KnowledgeBase />} />
            <Route path="analytics" element={<AnalyticsView />} />
            <Route path="integrations" element={<IntegrationsView />} />
            <Route path="settings" element={<SettingsView />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
