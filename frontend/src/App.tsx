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
          <Route path="companies" element={<Companies />} />
          <Route path="contacts" element={<Contacts />} />
          <Route path="pipeline" element={<DealsPipeline />} />
          <Route path="research" element={<ResearchIntel />} />
          <Route path="outreach" element={<OutreachApprovals />} />
          <Route path="conversations" element={<Conversations />} />
          <Route path="tasks" element={<TasksMeetings />} />
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
