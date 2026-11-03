import { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Search,
  Users,
  Building2,
  Contact2,
  BrainCircuit,
  Kanban,
  Send,
  MessageSquare,
  CheckSquare,
  Bot,
  BookOpen,
  BarChart3,
  Sliders,
  Settings,
  Briefcase,
  Menu,
  X,
  ShieldCheck,
  Workflow,
  Mail,
  Target,
  ListOrdered,
  Calendar,
  Share2,
  Globe,
  FileBarChart,
  AlertOctagon,
  Shield,
} from 'lucide-react';

const Layout = () => {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navGroups = [
    {
      label: 'Core Discovery',
      items: [
        { path: '/', label: 'Overview', icon: LayoutDashboard },
        { path: '/discovery', label: 'Lead Discovery', icon: Search },
        { path: '/leads', label: 'Leads Directory', icon: Users },
        { path: '/jobs', label: 'Batch Jobs', icon: Briefcase },
      ],
    },
    {
      label: 'CRM & Pipeline',
      items: [
        { path: '/companies', label: 'Companies', icon: Building2 },
        { path: '/contacts', label: 'Contacts', icon: Contact2 },
        { path: '/pipeline', label: 'Deals & Pipeline', icon: Kanban },
        { path: '/meetings', label: 'Meetings & Calls', icon: Calendar },
        { path: '/tasks', label: 'Tasks & Follow-ups', icon: CheckSquare },
      ],
    },
    {
      label: 'Automation & Sequences',
      items: [
        { path: '/workflows', label: 'Native Workflows', icon: Workflow },
        { path: '/campaigns', label: 'Campaign Engine', icon: Target },
        { path: '/sequences', label: 'Follow-up Sequences', icon: ListOrdered },
        { path: '/outreach', label: 'Approval Queue', icon: Send },
        { path: '/conversations', label: 'Unified Inbox', icon: MessageSquare },
      ],
    },
    {
      label: 'Marketing & SEO',
      items: [
        { path: '/content', label: 'Content & Social', icon: Share2 },
        { path: '/seo', label: 'SEO & Inbound', icon: Globe },
        { path: '/research', label: 'Research & Intel', icon: BrainCircuit },
      ],
    },
    {
      label: 'Governance & Health',
      items: [
        { path: '/deliverability', label: 'Deliverability & DNS', icon: Mail },
        { path: '/compliance', label: 'Consent & GDPR', icon: Shield },
        { path: '/exceptions', label: 'Exception Queue', icon: AlertOctagon },
        { path: '/reports', label: 'Scheduled Reports', icon: FileBarChart },
        { path: '/agents', label: 'AI Agents', icon: Bot },
        { path: '/knowledge', label: 'Knowledge Base', icon: BookOpen },
        { path: '/analytics', label: 'Analytics KPIs', icon: BarChart3 },
        { path: '/integrations', label: 'Integrations & Health', icon: Sliders },
        { path: '/settings', label: 'Settings', icon: Settings },
      ],
    },
  ];

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 text-slate-200 flex flex-col transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand header */}
        <div className="flex items-center justify-between h-16 px-5 border-b border-slate-800 bg-slate-950/40">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold shadow-md shadow-blue-500/20">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <span className="font-semibold text-white tracking-tight text-sm block">
                AI Sales &amp; CRM OS
              </span>
              <span className="text-[10px] text-blue-400 font-medium flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> Native Python Engine
              </span>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1.5 text-slate-400 hover:text-white rounded-md hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Navigation Groups */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5 scrollbar-thin scrollbar-thumb-slate-700">
          {navGroups.map((group) => (
            <div key={group.label} className="space-y-1">
              <div className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                {group.label}
              </div>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive =
                    item.path === '/'
                      ? location.pathname === '/'
                      : location.pathname.startsWith(item.path);

                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center space-x-2.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        isActive
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <Icon
                        className={`w-4 h-4 shrink-0 ${
                          isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'
                        }`}
                      />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* User / Status Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/40">
          <div className="flex items-center space-x-2.5 px-2 py-1.5">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <div className="text-xs">
              <div className="font-medium text-white">System Active</div>
              <div className="text-[10px] text-slate-400">0% Downtime • Zero n8n</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-6 shrink-0 shadow-sm">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Workspace &bull; Production Mode
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              to="/exceptions"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 rounded-lg border border-amber-200"
            >
              <AlertOctagon className="w-3.5 h-3.5" />
              <span>Exceptions</span>
            </Link>
            <Link
              to="/outreach"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Approval Queue</span>
            </Link>
          </div>
        </header>

        {/* Page Content Body */}
        <main className="flex-1 overflow-y-auto p-6 bg-slate-950 text-slate-100">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
