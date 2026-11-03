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
      label: 'CRM Engine',
      items: [
        { path: '/companies', label: 'Companies', icon: Building2 },
        { path: '/contacts', label: 'Contacts', icon: Contact2 },
        { path: '/pipeline', label: 'Deals & Pipeline', icon: Kanban },
        { path: '/tasks', label: 'Tasks & Follow-ups', icon: CheckSquare },
      ],
    },
    {
      label: 'Outreach & Comms',
      items: [
        { path: '/research', label: 'Research & Intel', icon: BrainCircuit },
        { path: '/outreach', label: 'Outreach & Approvals', icon: Send },
        { path: '/conversations', label: 'Conversations', icon: MessageSquare },
      ],
    },
    {
      label: 'AI & Operations',
      items: [
        { path: '/agents', label: 'AI Agents', icon: Bot },
        { path: '/knowledge', label: 'Knowledge Base', icon: BookOpen },
        { path: '/analytics', label: 'Analytics', icon: BarChart3 },
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
                AI Sales & CRM OS
              </span>
              <span className="text-[10px] text-blue-400 font-medium flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> Autonomous Platform
              </span>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-slate-400 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation list */}
        <div className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
          {navGroups.map((group) => (
            <div key={group.label}>
              <div className="px-3 mb-1.5 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
                {group.label}
              </div>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;

                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center px-3 py-2 text-xs font-medium rounded-md transition-colors ${
                        isActive
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                      }`}
                    >
                      <Icon className={`w-4 h-4 mr-2.5 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Bottom environment badge */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/30 text-[11px] text-slate-400 flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
            Operational
          </span>
          <span className="text-slate-500">v2.0-OS</span>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 sm:px-6 z-10 flex-shrink-0">
          <div className="flex items-center">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-md text-slate-500 hover:text-slate-700 hover:bg-slate-100"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h2 className="text-base font-semibold text-slate-800 ml-2 lg:ml-0">
              AI Sales & CRM Operating System
            </h2>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              to="/outreach"
              className="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-1 rounded-md font-medium hover:bg-amber-100 transition-colors flex items-center gap-1.5"
            >
              <span className="w-2 h-2 rounded-full bg-amber-500"></span>
              Human Approval Queue
            </Link>
            <Link
              to="/integrations"
              className="text-xs bg-slate-100 text-slate-700 hover:bg-slate-200 px-2.5 py-1 rounded-md font-medium transition-colors"
            >
              Provider Health
            </Link>
          </div>
        </header>

        {/* Main Route Content */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
