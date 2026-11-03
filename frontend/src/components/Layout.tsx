import { useState, useMemo } from 'react';
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
  HardDrive,
  Cpu,
  Layers,
} from 'lucide-react';

const Layout = () => {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [navSearch, setNavSearch] = useState('');

  const navGroups = [
    {
      label: 'Core Discovery',
      items: [
        { path: '/', label: 'Overview', icon: LayoutDashboard },
        { path: '/discovery', label: 'Lead Discovery', icon: Search, badge: 'Maps API' },
        { path: '/leads', label: 'Leads Directory', icon: Users },
        { path: '/jobs', label: 'Batch Jobs', icon: Briefcase },
      ],
    },
    {
      label: 'CRM & Pipeline',
      items: [
        { path: '/companies', label: 'Companies', icon: Building2 },
        { path: '/contacts', label: 'Contacts', icon: Contact2 },
        { path: '/pipeline', label: 'Deals & Pipeline', icon: Kanban, badge: 'Kanban' },
        { path: '/meetings', label: 'Meetings & Calls', icon: Calendar },
        { path: '/tasks', label: 'Tasks & Follow-ups', icon: CheckSquare },
      ],
    },
    {
      label: 'Automation & Outreach',
      items: [
        { path: '/workflows', label: 'Native Workflows', icon: Workflow, badge: 'Zero n8n' },
        { path: '/campaigns', label: 'Campaign Engine', icon: Target },
        { path: '/sequences', label: 'Follow-up Sequences', icon: ListOrdered },
        { path: '/outreach', label: 'Approval Queue', icon: Send },
        { path: '/conversations', label: 'Unified Inbox', icon: MessageSquare },
      ],
    },
    {
      label: 'Marketing & SEO',
      items: [
        { path: '/content', label: 'Content & Social', icon: Share2, badge: 'MinIO' },
        { path: '/seo', label: 'SEO & Inbound', icon: Globe },
        { path: '/research', label: 'Research & Intel', icon: BrainCircuit },
      ],
    },
    {
      label: 'Governance & Intelligence',
      items: [
        { path: '/deliverability', label: 'Deliverability & DNS', icon: Mail },
        { path: '/compliance', label: 'Consent & GDPR', icon: Shield },
        { path: '/exceptions', label: 'Exception Queue', icon: AlertOctagon },
        { path: '/reports', label: 'Scheduled Reports', icon: FileBarChart },
        { path: '/agents', label: 'AI Agents', icon: Bot, badge: '15 Active' },
        { path: '/knowledge', label: 'Knowledge Base', icon: BookOpen, badge: 'pgvector' },
        { path: '/analytics', label: 'Analytics KPIs', icon: BarChart3 },
        { path: '/integrations', label: 'Integrations & Health', icon: Sliders },
        { path: '/settings', label: 'Settings', icon: Settings },
      ],
    },
  ];

  // Filter navigation items by search query if user types in sidebar
  const filteredNavGroups = useMemo(() => {
    if (!navSearch.trim()) return navGroups;
    const q = navSearch.toLowerCase();
    return navGroups
      .map((g) => ({
        ...g,
        items: g.items.filter(
          (item) => item.label.toLowerCase().includes(q) || item.path.toLowerCase().includes(q)
        ),
      }))
      .filter((g) => g.items.length > 0);
  }, [navSearch]);

  // Determine current active section title
  const currentSection = useMemo(() => {
    for (const group of navGroups) {
      for (const item of group.items) {
        if (item.path === '/' && location.pathname === '/') return { group: group.label, item: item.label };
        if (item.path !== '/' && location.pathname.startsWith(item.path)) {
          return { group: group.label, item: item.label };
        }
      }
    }
    return { group: 'Platform', item: 'Command Center' };
  }, [location.pathname]);

  return (
    <div className="flex h-screen bg-[#0B0F19] text-slate-100 overflow-hidden font-sans antialiased selection:bg-indigo-500 selection:text-white">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Navigation Shell */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-[#0E1322] border-r border-slate-800/80 flex flex-col transition-all duration-300 ease-in-out lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0 shadow-2xl shadow-indigo-950/50' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 px-5 border-b border-slate-800/80 flex items-center justify-between bg-[#0E1322]/90 backdrop-blur-md">
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-blue-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition-transform">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-white tracking-tight text-sm flex items-center gap-1.5">
                <span>AI Sales &amp; CRM</span>
                <span className="px-1.5 py-0.2 text-[9px] font-extrabold uppercase rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                  v2.5
                </span>
              </div>
              <div className="text-[10px] text-slate-400 font-medium flex items-center gap-1 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block" />
                <span>Zero n8n • Native Engine</span>
              </div>
            </div>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Nav Search Input */}
        <div className="px-4 pt-3.5 pb-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={navSearch}
              onChange={(e) => setNavSearch(e.target.value)}
              placeholder="Search views, tools, RAG..."
              className="w-full bg-slate-900/90 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/80 transition"
            />
            {navSearch && (
              <button
                onClick={() => setNavSearch('')}
                className="absolute right-2.5 top-2 text-[10px] text-slate-500 hover:text-slate-300"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Scrollable Navigation Groups */}
        <div className="flex-1 overflow-y-auto px-3.5 py-2 space-y-5 scrollbar-thin scrollbar-thumb-slate-800">
          {filteredNavGroups.map((group) => (
            <div key={group.label} className="space-y-1">
              <div className="px-2.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center justify-between">
                <span>{group.label}</span>
                <span className="text-[9px] text-slate-600 font-normal">{group.items.length}</span>
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
                      className={`group flex items-center justify-between px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-md shadow-indigo-500/20 font-semibold'
                          : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                      }`}
                    >
                      <div className="flex items-center space-x-2.5 min-w-0">
                        <Icon
                          className={`w-4 h-4 shrink-0 transition-colors ${
                            isActive ? 'text-white' : 'text-slate-400 group-hover:text-indigo-400'
                          }`}
                        />
                        <span className="truncate">{item.label}</span>
                      </div>
                      {item.badge && (
                        <span
                          className={`ml-2 px-1.5 py-0.5 text-[9px] font-bold uppercase rounded tracking-wider ${
                            isActive
                              ? 'bg-white/20 text-white'
                              : 'bg-slate-800/80 text-slate-400 group-hover:text-indigo-300 border border-slate-700/60'
                          }`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Live Infrastructure System Footer */}
        <div className="p-3 border-t border-slate-800/80 bg-[#0B0F19]/90 space-y-2">
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-lg p-2.5 space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-400 flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-cyan-400" /> MinIO Storage
              </span>
              <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                ACTIVE
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-indigo-400" /> pgvector RAG
              </span>
              <span className="text-[10px] font-bold text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded border border-indigo-500/20">
                READY
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main App Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-[#0B0F19]">
        {/* Top Navbar */}
        <header className="h-16 border-b border-slate-800/80 bg-[#0E1322]/80 backdrop-blur-md flex items-center justify-between px-6 shrink-0 z-10">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-500 flex items-center gap-1">
                <Layers className="w-3.5 h-3.5" />
                {currentSection.group}
              </span>
              <span className="text-slate-600">/</span>
              <span className="font-semibold text-slate-200">{currentSection.item}</span>
            </div>
          </div>

          {/* Quick Header Actions */}
          <div className="flex items-center space-x-3">
            <Link
              to="/discovery"
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 rounded-lg shadow-sm shadow-indigo-500/25 transition-all"
            >
              <Search className="w-3.5 h-3.5" />
              <span>Launch Discovery</span>
            </Link>
            <Link
              to="/outreach"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 rounded-lg border border-indigo-500/30 transition-colors"
            >
              <Send className="w-3.5 h-3.5 text-indigo-400" />
              <span>Approval Queue</span>
            </Link>
            <Link
              to="/exceptions"
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 rounded-lg border border-amber-500/30 transition-colors"
            >
              <AlertOctagon className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden sm:inline">Exceptions</span>
            </Link>
          </div>
        </header>

        {/* Page Content Body */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-[#0B0F19] text-slate-100">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;
