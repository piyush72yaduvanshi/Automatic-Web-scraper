import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Discovery from './pages/Discovery';
import Jobs from './pages/Jobs';
import Leads from './pages/Leads';
import LeadDetail from './pages/LeadDetail';
import Companies from './pages/Companies';
import Contacts from './pages/Contacts';
import DealsPipeline from './pages/DealsPipeline';
import ResearchIntel from './pages/ResearchIntel';
import OutreachApprovals from './pages/OutreachApprovals';
import Conversations from './pages/Conversations';
import TasksMeetings from './pages/TasksMeetings';
import AIAgents from './pages/AIAgents';
import KnowledgeBase from './pages/KnowledgeBase';
import AnalyticsView from './pages/AnalyticsView';
import IntegrationsView from './pages/IntegrationsView';
import SettingsView from './pages/SettingsView';

// Phase 2 Views
import { WorkflowEngineView } from './pages/WorkflowEngineView';
import { DeliverabilityView } from './pages/DeliverabilityView';
import { CampaignsView } from './pages/CampaignsView';
import { SequencesView } from './pages/SequencesView';
import { ComplianceView } from './pages/ComplianceView';
import { ContentSocialView } from './pages/ContentSocialView';
import { SEOView } from './pages/SEOView';
import { MeetingsView } from './pages/MeetingsView';
import { ReportsView } from './pages/ReportsView';
import { ExceptionQueueView } from './pages/ExceptionQueueView';

function App() {
  return (
    <BrowserRouter>
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
          <Route path="seo" element={<SEOView />} />
          <Route path="research" element={<ResearchIntel />} />
          
          {/* Governance & Health */}
          <Route path="deliverability" element={<DeliverabilityView />} />
          <Route path="compliance" element={<ComplianceView />} />
          <Route path="exceptions" element={<ExceptionQueueView />} />
          <Route path="reports" element={<ReportsView />} />
          <Route path="agents" element={<AIAgents />} />
          <Route path="knowledge" element={<KnowledgeBase />} />
          <Route path="analytics" element={<AnalyticsView />} />
          <Route path="integrations" element={<IntegrationsView />} />
          <Route path="settings" element={<SettingsView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
