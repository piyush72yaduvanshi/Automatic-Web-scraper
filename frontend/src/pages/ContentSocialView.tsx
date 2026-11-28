import React, { useState, useEffect } from 'react';
import {
  Share2,
  Calendar,
  Sparkles,
  RefreshCw,
  Instagram,
  Facebook,
  Twitter,
  Linkedin,
  CheckCircle2,
  Clock,
  Send,
  Eye,
  Edit3,
  BarChart2,
  Settings,
  Layers,
  Search,
  Image as ImageIcon,
  ExternalLink,
  Radio,
  Zap,
  Filter,
  Mail,
  ShieldCheck,
} from 'lucide-react';
import {
  SocialAccountItem,
  SocialPostItem,
  SocialAutomationRuleItem,
  SocialAnalyticsData,
  SocialResearchResult,
} from '../types';

export const ContentSocialView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'ACCOUNTS' | 'STUDIO' | 'PREVIEWS' | 'CALENDAR' | 'RULES' | 'ANALYTICS' | 'LISTENING'>('STUDIO');
  
  // Social Media Listening State
  const [listeningStatus, setListeningStatus] = useState<any>(null);
  const [listeningRunning, setListeningRunning] = useState<boolean>(false);
  const [listeningPlatforms, setListeningPlatforms] = useState<string[]>(['LINKEDIN', 'X', 'FACEBOOK', 'INSTAGRAM']);
  const [listeningKeywords, setListeningKeywords] = useState<string>('looking for, need recommendations, recommend a crm, hiring an agency, budget approved');
  const [listeningScanResult, setListeningScanResult] = useState<any>(null);

  const fetchListeningStatus = async () => {
    try {
      const res = await fetch('/api/v1/social/listening/status');
      if (res.ok) {
        setListeningStatus(await res.json());
      }
    } catch (e) {
      console.error('Failed to fetch listening status:', e);
    }
  };

  const handleRunListeningScan = async () => {
    setListeningRunning(true);
    try {
      const kwList = listeningKeywords.split(',').map((s) => s.trim()).filter(Boolean);
      const res = await fetch('/api/v1/social/listening/run-now', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platforms: listeningPlatforms,
          keywords: kwList.length > 0 ? kwList : undefined,
          limit_per_platform: 3,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setListeningScanResult(data);
        setMessage(`Intent scan complete! Extracted ${data.total_leads_extracted} buyer intent leads across platforms.`);
        fetchListeningStatus();
      } else {
        setMessage('Social listening scan failed.');
      }
    } catch {
      setMessage('Error running social listening scan.');
    } finally {
      setListeningRunning(false);
    }
  };
  
  // Data States
  const [accounts, setAccounts] = useState<SocialAccountItem[]>([]);
  const [posts, setPosts] = useState<SocialPostItem[]>([]);
  const [rules, setRules] = useState<SocialAutomationRuleItem[]>([]);
  const [analytics, setAnalytics] = useState<SocialAnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [message, setMessage] = useState<string | null>(null);

  // AI Studio Generation Form
  const [topic, setTopic] = useState<string>('Why 80% of Cold Outbound Fails Without Pre-Flight Evidence');
  const [pillar, setPillar] = useState<string>('TECHNICAL_EXPERTISE');
  const [targetAudience, setTargetAudience] = useState<string>('B2B Founders & VP Sales');
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([
    'INSTAGRAM',
    'FACEBOOK',
    'TWITTER',
    'LINKEDIN_PERSONAL',
    'LINKEDIN_ORG',
  ]);
  const [automationMode, setAutomationMode] = useState<'MANUAL' | 'APPROVAL_BASED' | 'FULLY_AUTOMATED'>('APPROVAL_BASED');
  const [customInstructions, setCustomInstructions] = useState<string>('');
  const [generating, setGenerating] = useState<boolean>(false);

  // Research State
  const [researching, setResearching] = useState<boolean>(false);
  const [researchResult, setResearchResult] = useState<SocialResearchResult | null>(null);

  // Post Editing & Preview State
  const [editingPostId, setEditingPostId] = useState<string | null>(null);
  const [editCaption, setEditCaption] = useState<string>('');
  const [editHashtags, setEditHashtags] = useState<string>('');
  const [editMediaUrl, setEditMediaUrl] = useState<string>('');
  const [previewPlatform, setPreviewPlatform] = useState<string>('LINKEDIN_PERSONAL');
  const [publishingId, setPublishingId] = useState<string | null>(null);

  // Filter States for Calendar / Posts
  const [calendarPlatformFilter, setCalendarPlatformFilter] = useState<string>('ALL');
  const [calendarStatusFilter, setCalendarStatusFilter] = useState<string>('ALL');

  // Fetch all data
  const fetchData = async () => {
    setLoading(true);
    try {
      const [accRes, postRes, ruleRes, anaRes] = await Promise.all([
        fetch('/api/v1/social/accounts'),
        fetch('/api/v1/social/posts'),
        fetch('/api/v1/social/rules'),
        fetch('/api/v1/social/analytics'),
      ]);

      if (accRes.ok) setAccounts(await accRes.json());
      if (postRes.ok) {
        const postsData: SocialPostItem[] = await postRes.json();
        setPosts(postsData);
        if (postsData.length > 0 && !editingPostId) {
          const first = postsData[0];
          setEditingPostId(first.id);
          setEditCaption(first.caption);
          setEditHashtags(first.hashtags.join(' '));
          setEditMediaUrl(first.media_urls[0] || '');
          setPreviewPlatform(first.platform);
        }
      }
      if (ruleRes.ok) setRules(await ruleRes.json());
      if (anaRes.ok) setAnalytics(await anaRes.json());
    } catch (err) {
      console.error('Error fetching social media data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    fetchListeningStatus();
  }, []);

  // 1. Run AI Topic Research
  const handleResearchTopic = async () => {
    if (!topic.trim()) return;
    setResearching(true);
    try {
      const res = await fetch('/api/v1/social/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, target_audience: targetAudience }),
      });
      if (res.ok) {
        const data: SocialResearchResult = await res.json();
        setResearchResult(data);
        setMessage('AI Research Complete: Trending angles and audience resonances extracted!');
      }
    } catch {
      setMessage('Failed to execute AI topic research.');
    } finally {
      setResearching(false);
    }
  };

  // 2. Generate Platform-Specific Posts & Creative Briefs
  const handleGeneratePosts = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim() || selectedPlatforms.length === 0) return;
    setGenerating(true);
    try {
      const res = await fetch('/api/v1/social/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic,
          pillar,
          target_audience: targetAudience,
          platforms: selectedPlatforms,
          automation_mode: automationMode,
          custom_instructions: customInstructions,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Success! Generated ${data.posts_created} platform-native posts with creative briefs.`);
        await fetchData();
        setActiveTab('PREVIEWS');
      }
    } catch {
      setMessage('Failed to generate social media posts.');
    } finally {
      setGenerating(false);
    }
  };

  // 3. Test Connection on a Social Account
  const handleTestConnection = async (accountId: string) => {
    try {
      const res = await fetch(`/api/v1/social/accounts/${accountId}/test`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setMessage(`Account verification result: ${data.test_result.status} - ${data.test_result.message || 'Verified!'}`);
        fetchData();
      }
    } catch {
      setMessage('Account connection test failed.');
    }
  };

  // 4. Select a post for editing and preview
  const handleSelectPostForEdit = (p: SocialPostItem) => {
    setEditingPostId(p.id);
    setEditCaption(p.caption);
    setEditHashtags(p.hashtags.join(' '));
    setEditMediaUrl(p.media_urls[0] || '');
    setPreviewPlatform(p.platform);
  };

  // 5. Save edited post
  const handleSavePostChanges = async () => {
    if (!editingPostId) return;
    try {
      const hashtagsArray = editHashtags
        .split(' ')
        .map((h) => h.trim())
        .filter((h) => h.length > 0)
        .map((h) => (h.startsWith('#') ? h : `#${h}`));

      const res = await fetch(`/api/v1/social/posts/${editingPostId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          caption: editCaption,
          hashtags: hashtagsArray,
          media_urls: editMediaUrl ? [editMediaUrl] : [],
        }),
      });

      if (res.ok) {
        setMessage('Post changes saved successfully!');
        fetchData();
      }
    } catch {
      setMessage('Failed to save post changes.');
    }
  };

  // 6. Approve Post
  const handleApprovePost = async (postId: string) => {
    try {
      const res = await fetch(`/api/v1/social/posts/${postId}/approve`, {
        method: 'POST',
      });
      if (res.ok) {
        setMessage('Post approved for scheduling / publishing!');
        fetchData();
      }
    } catch {
      setMessage('Failed to approve post.');
    }
  };

  // 7. Publish Post Immediately
  const handlePublishPostNow = async (postId: string) => {
    setPublishingId(postId);
    try {
      const res = await fetch(`/api/v1/social/posts/${postId}/publish`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        if (data.success) {
          setMessage(`Post published successfully via official API! URL: ${data.external_post_url || 'Verified'}`);
        } else if (data.provider_status === 'NOT_CONFIGURED') {
          setMessage(`API status: NOT_CONFIGURED. Retained draft for manual copy-paste.`);
        } else {
          setMessage(`Publishing failed: ${data.error || 'Unknown error'}`);
        }
        fetchData();
      }
    } catch {
      setMessage('Network error during post publishing.');
    } finally {
      setPublishingId(null);
    }
  };

  // 8. Run an Automation Rule
  const handleRunRule = async (ruleId: string) => {
    try {
      const res = await fetch(`/api/v1/social/rules/${ruleId}/run`, {
        method: 'POST',
      });
      if (res.ok) {
        setMessage('Automation rule executed: Posts researched, generated, and staged!');
        fetchData();
      }
    } catch {
      setMessage('Failed to execute automation rule.');
    }
  };

  // 9. Sync Platform Metrics
  const handleSyncMetrics = async () => {
    try {
      const res = await fetch('/api/v1/social/analytics/sync', { method: 'POST' });
      if (res.ok) {
        setMessage('Synchronized live post metrics from official platform APIs!');
        fetchData();
      }
    } catch {
      setMessage('Failed to sync social metrics.');
    }
  };

  // Helper: platform icon
  const getPlatformIcon = (plat: string) => {
    switch (plat) {
      case 'INSTAGRAM':
        return <Instagram className="w-4 h-4 text-pink-400" />;
      case 'FACEBOOK':
        return <Facebook className="w-4 h-4 text-blue-400" />;
      case 'TWITTER':
        return <Twitter className="w-4 h-4 text-sky-400" />;
      case 'LINKEDIN_PERSONAL':
      case 'LINKEDIN_ORG':
        return <Linkedin className="w-4 h-4 text-indigo-400" />;
      default:
        return <Share2 className="w-4 h-4 text-gray-400" />;
    }
  };

  // Helper: status badge
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PUBLISHED':
        return <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">PUBLISHED</span>;
      case 'SCHEDULED':
        return <span className="px-2 py-0.5 text-xs rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30">SCHEDULED</span>;
      case 'APPROVED':
        return <span className="px-2 py-0.5 text-xs rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">APPROVED</span>;
      case 'PENDING_APPROVAL':
        return <span className="px-2 py-0.5 text-xs rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">PENDING APPROVAL</span>;
      case 'FAILED':
        return <span className="px-2 py-0.5 text-xs rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">FAILED</span>;
      case 'ACTIVE':
        return <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">ACTIVE</span>;
      case 'NOT_CONFIGURED':
        return <span className="px-2 py-0.5 text-xs rounded-full bg-gray-500/20 text-gray-400 border border-gray-500/30">NOT_CONFIGURED</span>;
      case 'EXPIRED':
        return <span className="px-2 py-0.5 text-xs rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">EXPIRED</span>;
      default:
        return <span className="px-2 py-0.5 text-xs rounded-full bg-gray-700 text-gray-300">{status}</span>;
    }
  };

  const selectedPostForPreview = posts.find((p) => p.id === editingPostId);

  const filteredCalendarPosts = posts.filter((p) => {
    if (calendarPlatformFilter !== 'ALL' && p.platform !== calendarPlatformFilter) return false;
    if (calendarStatusFilter !== 'ALL' && p.status !== calendarStatusFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-gray-900 border border-gray-800 p-6 rounded-xl gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Share2 className="w-7 h-7 text-indigo-400" />
              Multi-Platform Social Media Automation
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              4 Official Platforms
            </span>
          </div>
          <p className="text-gray-400 text-sm mt-1">
            End-to-end AI research, platform-tailored copy, creative briefs, live preview editing, calendar scheduling, and official API publishing across Instagram, Facebook, X, and LinkedIn.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg text-sm transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {message && (
        <div className="p-4 bg-indigo-950/70 border border-indigo-500/40 rounded-lg text-indigo-200 text-sm flex justify-between items-center">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-indigo-400 hover:text-white font-bold">✕</button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex overflow-x-auto border-b border-gray-800 bg-gray-900/60 p-1.5 rounded-lg gap-2">
        <button
          onClick={() => setActiveTab('STUDIO')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
            activeTab === 'STUDIO' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          AI Studio &amp; Research
        </button>
        <button
          onClick={() => setActiveTab('PREVIEWS')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
            activeTab === 'PREVIEWS' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
          }`}
        >
          <Eye className="w-4 h-4" />
          Post Editor &amp; Live Previews
          {posts.filter((p) => p.status === 'PENDING_APPROVAL').length > 0 && (
            <span className="px-1.5 py-0.5 text-xs bg-amber-500 text-black font-bold rounded-full">
              {posts.filter((p) => p.status === 'PENDING_APPROVAL').length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('CALENDAR')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
            activeTab === 'CALENDAR' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
          }`}
        >
          <Calendar className="w-4 h-4" />
          Content Calendar ({posts.length})
        </button>
        <button
          onClick={() => setActiveTab('ACCOUNTS')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
            activeTab === 'ACCOUNTS' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
          }`}
        >
          <Settings className="w-4 h-4" />
          Connected Accounts ({accounts.length})
        </button>
        <button
          onClick={() => setActiveTab('RULES')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
            activeTab === 'RULES' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
          }`}
        >
          <Layers className="w-4 h-4" />
          Automation Modes &amp; Rules
        </button>
        <button
          onClick={() => setActiveTab('ANALYTICS')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
            activeTab === 'ANALYTICS' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
          }`}
        >
          <BarChart2 className="w-4 h-4" />
          Analytics &amp; Performance
        </button>
        <button
          onClick={() => { setActiveTab('LISTENING'); fetchListeningStatus(); }}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition ${
            activeTab === 'LISTENING' ? 'bg-indigo-600 text-white shadow' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
          }`}
        >
          <Radio className="w-4 h-4 text-emerald-400" />
          Intent Listening &amp; Lead Extractor
          {listeningStatus?.total_social_leads_captured > 0 && (
            <span className="px-1.5 py-0.5 text-xs bg-emerald-500/20 text-emerald-400 font-bold rounded-full border border-emerald-500/30">
              {listeningStatus.total_social_leads_captured}
            </span>
          )}
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: AI STUDIO & RESEARCH */}
      {/* ========================================================================= */}
      {activeTab === 'STUDIO' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                AI Multi-Platform Content Generator &amp; Strategist
              </h2>
              <span className="text-xs text-gray-400">Step 1: Research &rarr; Step 2: Generate</span>
            </div>

            <form onSubmit={handleGeneratePosts} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-gray-300 block mb-1">Topic or Core Idea</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="e.g. Why Mass Cold Outreach Fails and How Verified Evidence Wins"
                    className="flex-1 px-3.5 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
                    required
                  />
                  <button
                    type="button"
                    onClick={handleResearchTopic}
                    disabled={researching || !topic.trim()}
                    className="px-4 py-2.5 bg-indigo-950 hover:bg-indigo-900 text-indigo-200 border border-indigo-500/40 rounded-lg text-sm flex items-center gap-2 transition"
                  >
                    <Search className={`w-4 h-4 ${researching ? 'animate-spin' : ''}`} />
                    {researching ? 'Researching...' : 'Research Trends'}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-gray-300 block mb-1">Content Pillar</label>
                  <select
                    value={pillar}
                    onChange={(e) => setPillar(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                  >
                    <option value="TECHNICAL_EXPERTISE">Technical Expertise (Architecture &amp; Code)</option>
                    <option value="PROOF_OF_WORK">Proof of Work (Case Studies &amp; Benchmarks)</option>
                    <option value="PROBLEM_AWARENESS">Problem Awareness (Root Cause Analysis)</option>
                    <option value="COMPANY_UPDATES">Company Updates (Product &amp; Releases)</option>
                    <option value="OFFERS_AND_SERVICES">Offers &amp; Services (Direct Value Call)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-gray-300 block mb-1">Target Audience</label>
                  <input
                    type="text"
                    value={targetAudience}
                    onChange={(e) => setTargetAudience(e.target.value)}
                    placeholder="e.g. B2B Founders, Sales Leaders, CTOs"
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                  />
                </div>
              </div>

              {/* Target Platforms Selection */}
              <div>
                <label className="text-xs font-semibold text-gray-300 block mb-2">Target Platforms for Cross-Posting</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                  {[
                    { id: 'INSTAGRAM', label: 'Instagram (Visual + Bio)', icon: <Instagram className="w-4 h-4 text-pink-400" /> },
                    { id: 'FACEBOOK', label: 'Facebook Page Feed', icon: <Facebook className="w-4 h-4 text-blue-400" /> },
                    { id: 'TWITTER', label: 'X (Twitter Thread)', icon: <Twitter className="w-4 h-4 text-sky-400" /> },
                    { id: 'LINKEDIN_PERSONAL', label: 'LinkedIn (Personal)', icon: <Linkedin className="w-4 h-4 text-indigo-400" /> },
                    { id: 'LINKEDIN_ORG', label: 'LinkedIn (Company Page)', icon: <Linkedin className="w-4 h-4 text-indigo-300" /> },
                  ].map((p) => {
                    const isChecked = selectedPlatforms.includes(p.id);
                    return (
                      <button
                        type="button"
                        key={p.id}
                        onClick={() => {
                          if (isChecked) {
                            setSelectedPlatforms(selectedPlatforms.filter((x) => x !== p.id));
                          } else {
                            setSelectedPlatforms([...selectedPlatforms, p.id]);
                          }
                        }}
                        className={`flex items-center gap-2 p-2.5 rounded-lg border text-xs font-medium transition text-left ${
                          isChecked
                            ? 'bg-indigo-950/60 border-indigo-500/60 text-white'
                            : 'bg-gray-800/60 border-gray-700 text-gray-400 hover:bg-gray-800'
                        }`}
                      >
                        {p.icon}
                        <span className="truncate">{p.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Automation Mode Selection */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-semibold text-gray-300 block mb-1">Automation Workflow Mode</label>
                  <select
                    value={automationMode}
                    onChange={(e) => setAutomationMode(e.target.value as any)}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                  >
                    <option value="APPROVAL_BASED">Approval-based (AI drafts, human reviews &amp; approves)</option>
                    <option value="MANUAL">Manual (Create draft for manual staging &amp; editing)</option>
                    <option value="FULLY_AUTOMATED">Fully Automated (AI generates and auto-schedules to calendar)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-gray-300 block mb-1">Custom Tone or Constraints (Optional)</label>
                  <input
                    type="text"
                    value={customInstructions}
                    onChange={(e) => setCustomInstructions(e.target.value)}
                    placeholder="e.g. Include specific metrics, avoid promotional fluff"
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={generating || selectedPlatforms.length === 0}
                  className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium rounded-lg text-sm flex items-center gap-2 shadow-lg transition"
                >
                  <Sparkles className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
                  {generating ? 'Generating Cross-Platform Posts...' : 'Generate Platform Posts & Creative Briefs'}
                </button>
              </div>
            </form>
          </div>

          {/* AI Research & Trend Sidebar */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Search className="w-4 h-4 text-indigo-400" />
              AI Trend &amp; Audience Research
            </h3>

            {researchResult ? (
              <div className="space-y-4 text-xs">
                <div>
                  <span className="text-gray-400 font-semibold block mb-1">Viral &amp; High-Curiosity Angles:</span>
                  <ul className="space-y-1.5 text-gray-200">
                    {researchResult.trending_angles.map((a, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-indigo-400">•</span>
                        <span>{a}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <span className="text-gray-400 font-semibold block mb-1">Audience Resonance Pain Points:</span>
                  <ul className="space-y-1.5 text-gray-200">
                    {researchResult.audience_resonances.map((r, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-emerald-400">✓</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <span className="text-gray-400 font-semibold block mb-1">Recommended Discovery Hashtags:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {researchResult.recommended_keywords.map((k, i) => (
                      <span key={i} className="px-2 py-0.5 bg-gray-800 text-indigo-300 rounded border border-gray-700">
                        {k.startsWith('#') ? k : `#${k}`}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <span className="text-gray-400 font-semibold block mb-1">Visual Creative Aesthetic:</span>
                  <p className="text-gray-300 bg-gray-800/80 p-2.5 rounded border border-gray-700">
                    {researchResult.visual_theme}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center py-10 text-gray-500 space-y-2">
                <Search className="w-8 h-8 mx-auto text-gray-600" />
                <p className="text-xs">Click "Research Trends" above to uncover viral angles, high-resonance hooks, and visual directions.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: POST EDITOR & LIVE PREVIEWS */}
      {/* ========================================================================= */}
      {activeTab === 'PREVIEWS' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Post Selection List */}
          <div className="lg:col-span-4 bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
            <h3 className="text-sm font-bold text-white flex items-center justify-between">
              <span>Generated &amp; Staged Posts</span>
              <span className="text-xs text-gray-400">{posts.length} total</span>
            </h3>

            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {posts.map((p) => {
                const isSelected = p.id === editingPostId;
                return (
                  <div
                    key={p.id}
                    onClick={() => handleSelectPostForEdit(p)}
                    className={`p-3 rounded-lg border cursor-pointer transition ${
                      isSelected
                        ? 'bg-indigo-950/60 border-indigo-500/80'
                        : 'bg-gray-800/50 border-gray-700 hover:bg-gray-800'
                    }`}
                  >
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="flex items-center gap-1.5 text-xs font-bold text-white">
                        {getPlatformIcon(p.platform)}
                        {p.platform.replace('_', ' ')}
                      </span>
                      {getStatusBadge(p.status)}
                    </div>
                    <p className="text-xs text-gray-300 line-clamp-2">{p.caption}</p>
                    <div className="mt-2 flex justify-between items-center text-[10px] text-gray-400">
                      <span>{p.hashtags.length} hashtags</span>
                      <span>{p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Live Preview Card & Editor */}
          <div className="lg:col-span-8 space-y-6">
            {selectedPostForPreview ? (
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {/* Authentic Platform Mockup Frame */}
                <div className="bg-gray-950 border border-gray-800 rounded-2xl p-5 shadow-2xl flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between pb-3 border-b border-gray-800 mb-4">
                      <div className="flex items-center gap-2">
                        {getPlatformIcon(previewPlatform)}
                        <span className="text-xs font-bold text-gray-200">
                          {previewPlatform.replace('_', ' ')} Live Preview
                        </span>
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-gray-800 text-gray-400">
                        {selectedPostForPreview.creative_brief?.aspect_ratio || '16:9'}
                      </span>
                    </div>

                    {/* Platform Specific Header Mockup */}
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center text-white font-bold text-sm">
                        AC
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white flex items-center gap-1">
                          Acme Technologies
                          {previewPlatform.includes('LINKEDIN') && <span className="text-[10px] text-gray-400">• 1st</span>}
                        </div>
                        <div className="text-[10px] text-gray-400">
                          {previewPlatform === 'INSTAGRAM' && '@acme_official'}
                          {previewPlatform === 'TWITTER' && '@acmeworks • Just now'}
                          {previewPlatform === 'FACEBOOK' && 'Sponsored • Public'}
                          {previewPlatform.includes('LINKEDIN') && 'AI Sales & CRM Operating System • 2h'}
                        </div>
                      </div>
                    </div>

                    {/* Post Caption Body */}
                    <div className="text-xs text-gray-200 whitespace-pre-line mb-3 font-sans leading-relaxed">
                      {editCaption}
                    </div>

                    {/* Hashtags display */}
                    {editHashtags && (
                      <div className="text-xs text-indigo-400 font-medium mb-3">
                        {editHashtags}
                      </div>
                    )}

                    {/* Attached Image Preview */}
                    {editMediaUrl && (
                      <div className="relative rounded-lg overflow-hidden border border-gray-800 mb-3 bg-gray-900 aspect-video flex items-center justify-center">
                        <img
                          src={editMediaUrl}
                          alt="Creative preview"
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = 'none';
                          }}
                        />
                        <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/70 backdrop-blur rounded text-[10px] text-gray-200 flex items-center gap-1.5">
                          <ImageIcon className="w-3 h-3 text-indigo-400" />
                          <span>{selectedPostForPreview.creative_brief?.text_overlay || 'Headline Overlay'}</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Platform Engagement Action Bar */}
                  <div className="pt-3 border-t border-gray-800/80 flex items-center justify-between text-gray-400 text-xs">
                    <span className="flex items-center gap-1 hover:text-red-400 cursor-pointer">❤️ Like</span>
                    <span className="flex items-center gap-1 hover:text-blue-400 cursor-pointer">💬 Comment</span>
                    <span className="flex items-center gap-1 hover:text-emerald-400 cursor-pointer">🔁 Repost / Share</span>
                    <span className="flex items-center gap-1 hover:text-indigo-400 cursor-pointer">🔖 Save</span>
                  </div>
                </div>

                {/* Editor & Metadata Panel */}
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
                  <h4 className="text-sm font-bold text-white flex items-center gap-2">
                    <Edit3 className="w-4 h-4 text-indigo-400" />
                    Customize &amp; Refine Post Copy
                  </h4>

                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Post Caption</label>
                    <textarea
                      rows={6}
                      value={editCaption}
                      onChange={(e) => setEditCaption(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500 font-sans"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Hashtags</label>
                    <input
                      type="text"
                      value={editHashtags}
                      onChange={(e) => setEditHashtags(e.target.value)}
                      placeholder="#SalesAI #B2B #Automation"
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-xs text-white"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-gray-400 block mb-1">Creative Media Image URL</label>
                    <input
                      type="text"
                      value={editMediaUrl}
                      onChange={(e) => setEditMediaUrl(e.target.value)}
                      placeholder="https://images.unsplash.com/..."
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-xs text-white"
                    />
                  </div>

                  {/* Creative Brief Details */}
                  {selectedPostForPreview.creative_brief && (
                    <div className="p-3 bg-gray-800/60 rounded-lg border border-gray-700/60 space-y-1.5 text-[11px]">
                      <span className="font-semibold text-gray-300 block">AI Creative Brief Guidelines:</span>
                      <p className="text-gray-400">Concept: {selectedPostForPreview.creative_brief.visual_concept}</p>
                      <div className="flex gap-4 text-gray-400">
                        <span>Dimensions: {selectedPostForPreview.creative_brief.dimensions}</span>
                        <span>Ratio: {selectedPostForPreview.creative_brief.aspect_ratio}</span>
                      </div>
                    </div>
                  )}

                  {/* Actions Bar */}
                  <div className="pt-2 flex flex-wrap gap-2 justify-between items-center">
                    <button
                      onClick={handleSavePostChanges}
                      className="px-3.5 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-semibold rounded-lg transition"
                    >
                      Save Changes
                    </button>

                    <div className="flex gap-2">
                      {selectedPostForPreview.status === 'PENDING_APPROVAL' && (
                        <button
                          onClick={() => handleApprovePost(selectedPostForPreview.id)}
                          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          Approve Post
                        </button>
                      )}

                      <button
                        onClick={() => handlePublishPostNow(selectedPostForPreview.id)}
                        disabled={publishingId === selectedPostForPreview.id}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow"
                      >
                        <Send className={`w-3.5 h-3.5 ${publishingId === selectedPostForPreview.id ? 'animate-spin' : ''}`} />
                        {publishingId === selectedPostForPreview.id ? 'Publishing...' : 'Publish Now'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-20 bg-gray-900 border border-gray-800 rounded-xl text-gray-500">
                <Eye className="w-10 h-10 mx-auto text-gray-600 mb-2" />
                <p className="text-sm">Select a post from the left list to review its live mockup, edit copy, or publish.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: CONTENT CALENDAR */}
      {/* ========================================================================= */}
      {activeTab === 'CALENDAR' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Calendar className="w-5 h-5 text-indigo-400" />
                Centralized Cross-Platform Content Calendar
              </h2>
              <p className="text-xs text-gray-400">
                Manage upcoming schedule, immediate dispatches, and confirmed publishing timestamps across all 4 platforms.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <select
                value={calendarPlatformFilter}
                onChange={(e) => setCalendarPlatformFilter(e.target.value)}
                className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-xs text-white"
              >
                <option value="ALL">All Platforms</option>
                <option value="INSTAGRAM">Instagram</option>
                <option value="FACEBOOK">Facebook</option>
                <option value="TWITTER">X (Twitter)</option>
                <option value="LINKEDIN_PERSONAL">LinkedIn Personal</option>
                <option value="LINKEDIN_ORG">LinkedIn Org</option>
              </select>

              <select
                value={calendarStatusFilter}
                onChange={(e) => setCalendarStatusFilter(e.target.value)}
                className="px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-xs text-white"
              >
                <option value="ALL">All Statuses</option>
                <option value="SCHEDULED">Scheduled</option>
                <option value="PUBLISHED">Published</option>
                <option value="PENDING_APPROVAL">Pending Approval</option>
                <option value="DRAFT">Draft</option>
                <option value="FAILED">Failed</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-800 text-gray-400 uppercase font-semibold">
                <tr>
                  <th className="p-3">Platform</th>
                  <th className="p-3">Post Caption &amp; Hashtags</th>
                  <th className="p-3">Mode</th>
                  <th className="p-3">Scheduled / Published</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Official API Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800 text-gray-300">
                {filteredCalendarPosts.length > 0 ? (
                  filteredCalendarPosts.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-800/40">
                      <td className="p-3 whitespace-nowrap">
                        <span className="flex items-center gap-1.5 font-bold text-white">
                          {getPlatformIcon(p.platform)}
                          {p.platform.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="p-3 max-w-xs">
                        <p className="line-clamp-2 text-gray-200">{p.caption}</p>
                        <span className="text-[10px] text-indigo-400">{p.hashtags.join(' ')}</span>
                      </td>
                      <td className="p-3 whitespace-nowrap text-gray-400">
                        {p.automation_mode}
                      </td>
                      <td className="p-3 whitespace-nowrap">
                        <div className="flex items-center gap-1.5 text-gray-300">
                          <Clock className="w-3.5 h-3.5 text-gray-400" />
                          <span>
                            {p.published_at
                              ? new Date(p.published_at).toLocaleString()
                              : (p.scheduled_for ? new Date(p.scheduled_for).toLocaleString() : 'Immediate')}
                          </span>
                        </div>
                      </td>
                      <td className="p-3 whitespace-nowrap">
                        {getStatusBadge(p.status)}
                      </td>
                      <td className="p-3 whitespace-nowrap">
                        {p.external_post_url ? (
                          <a
                            href={p.external_post_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                          >
                            <span>Confirmed ID</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : (
                          <span className="text-gray-500">{p.publishing_provider_status}</span>
                        )}
                      </td>
                      <td className="p-3 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => {
                              handleSelectPostForEdit(p);
                              setActiveTab('PREVIEWS');
                            }}
                            className="p-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded"
                            title="Edit & Preview"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          {p.status !== 'PUBLISHED' && (
                            <button
                              onClick={() => handlePublishPostNow(p.id)}
                              disabled={publishingId === p.id}
                              className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-[11px] font-semibold"
                            >
                              Publish
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-gray-500">
                      No posts found matching the filter criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: CONNECTED ACCOUNTS DASHBOARD */}
      {/* ========================================================================= */}
      {activeTab === 'ACCOUNTS' && (
        <div className="space-y-6">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
              <Settings className="w-5 h-5 text-indigo-400" />
              Connected Official Social Accounts
            </h2>
            <p className="text-xs text-gray-400 mb-6">
              Manage API authorization status, verify token health, and review connected handles for Instagram, Facebook Pages, X, and LinkedIn.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {accounts.map((acc) => (
                <div key={acc.id} className="bg-gray-800/60 border border-gray-700/80 rounded-xl p-5 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center gap-2">
                        {getPlatformIcon(acc.platform)}
                        <span className="text-sm font-bold text-white">{acc.platform.replace('_', ' ')}</span>
                      </div>
                      {getStatusBadge(acc.status)}
                    </div>

                    <div className="space-y-1 mb-4">
                      <h4 className="text-sm font-semibold text-gray-100">{acc.account_name}</h4>
                      <p className="text-xs text-indigo-300 font-mono">{acc.account_handle}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-2 p-2.5 bg-gray-900/60 rounded-lg text-xs mb-4">
                      <div>
                        <span className="text-gray-400 text-[10px] block">Followers / Audience</span>
                        <span className="font-bold text-white">{acc.followers_count.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-gray-400 text-[10px] block">Last Synced</span>
                        <span className="text-gray-300 text-[11px]">
                          {acc.last_sync_at ? new Date(acc.last_sync_at).toLocaleDateString() : 'Never'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-gray-700/60 flex items-center justify-between">
                    <span className="text-[10px] text-gray-400">
                      {acc.status === 'NOT_CONFIGURED' ? 'Add API keys in .env' : 'Official API Linked'}
                    </span>
                    <button
                      onClick={() => handleTestConnection(acc.id)}
                      className="px-3 py-1.5 bg-indigo-600/80 hover:bg-indigo-600 text-white rounded text-xs font-semibold transition"
                    >
                      Verify Connection
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Official API Permissions Guidance */}
          <div className="bg-gray-900/60 border border-gray-800 p-5 rounded-xl space-y-2 text-xs text-gray-400">
            <span className="font-bold text-gray-200 block">Official API Setup &amp; Permission Scopes:</span>
            <ul className="list-disc pl-5 space-y-1">
              <li><strong className="text-gray-300">Instagram:</strong> Requires Meta Graph API with <code className="text-indigo-300">instagram_basic</code>, <code className="text-indigo-300">instagram_content_publish</code>, and <code className="text-indigo-300">pages_read_engagement</code>.</li>
              <li><strong className="text-gray-300">Facebook Pages:</strong> Requires Page Access Token with <code className="text-indigo-300">pages_manage_posts</code> and <code className="text-indigo-300">pages_read_engagement</code>.</li>
              <li><strong className="text-gray-300">X (Twitter):</strong> Requires X API v2 Project with <code className="text-indigo-300">tweet.read</code> and <code className="text-indigo-300">tweet.write</code> OAuth 2.0 scopes or OAuth 1.0a User Context.</li>
              <li><strong className="text-gray-300">LinkedIn:</strong> Requires Community Management API with <code className="text-indigo-300">w_member_social</code> (Personal) and <code className="text-indigo-300">w_organization_social</code> (Company Page).</li>
            </ul>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 5: AUTOMATION RULES & MODES */}
      {/* ========================================================================= */}
      {activeTab === 'RULES' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-indigo-400" />
                Autonomous Social Publishing Rules &amp; Cadence
              </h2>
              <p className="text-xs text-gray-400">
                Configure autonomous scheduling rules with frequency caps, pillar rotation, and automation modes.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {rules.map((r) => (
              <div key={r.id} className="bg-gray-800/60 border border-gray-700/80 rounded-xl p-5 space-y-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-sm font-bold text-white">{r.name}</h3>
                    <span className="text-xs text-indigo-400 font-semibold">{r.mode}</span>
                  </div>
                  <span className={`px-2 py-0.5 text-xs rounded-full ${r.is_active ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-gray-700 text-gray-400'}`}>
                    {r.is_active ? 'ACTIVE' : 'PAUSED'}
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-gray-400 block mb-1">Target Cross-Posting Platforms:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {r.platforms.map((p, i) => (
                        <span key={i} className="px-2 py-0.5 bg-gray-900 text-gray-200 rounded border border-gray-700 flex items-center gap-1">
                          {getPlatformIcon(p)}
                          {p.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <span className="text-gray-400 block mb-1">Daily Frequency Cap &amp; Times:</span>
                    <p className="text-gray-300">Max {r.max_posts_per_day} posts/day at {r.posting_times.join(', ')} UTC</p>
                  </div>
                </div>

                <div className="pt-3 border-t border-gray-700/60 flex items-center justify-between">
                  <span className="text-[10px] text-gray-400">
                    Last Run: {r.last_run_at ? new Date(r.last_run_at).toLocaleString() : 'Never'}
                  </span>
                  <button
                    onClick={() => handleRunRule(r.id)}
                    className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold flex items-center gap-1.5 shadow"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Trigger Rule Now
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 6: ANALYTICS & PERFORMANCE REPORTS */}
      {/* ========================================================================= */}
      {activeTab === 'ANALYTICS' && analytics && (
        <div className="space-y-6">
          {/* Executive Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-900 border border-gray-800 p-5 rounded-xl">
              <span className="text-xs text-gray-400 font-medium block mb-1">Total Impressions</span>
              <span className="text-2xl font-bold text-white">{analytics.summary.total_impressions.toLocaleString()}</span>
              <span className="text-[10px] text-emerald-400 block mt-1">Cross-platform reach</span>
            </div>

            <div className="bg-gray-900 border border-gray-800 p-5 rounded-xl">
              <span className="text-xs text-gray-400 font-medium block mb-1">Total Engagements</span>
              <span className="text-2xl font-bold text-indigo-400">{analytics.summary.total_engagements.toLocaleString()}</span>
              <span className="text-[10px] text-gray-400 block mt-1">{analytics.summary.total_likes} likes • {analytics.summary.total_comments} comments</span>
            </div>

            <div className="bg-gray-900 border border-gray-800 p-5 rounded-xl">
              <span className="text-xs text-gray-400 font-medium block mb-1">Avg Engagement Rate</span>
              <span className="text-2xl font-bold text-emerald-400">{analytics.summary.average_engagement_rate}%</span>
              <span className="text-[10px] text-emerald-400 block mt-1">Industry benchmark: 1.8%</span>
            </div>

            <div className="bg-gray-900 border border-gray-800 p-5 rounded-xl">
              <span className="text-xs text-gray-400 font-medium block mb-1">Published Content</span>
              <span className="text-2xl font-bold text-white">{analytics.summary.published_posts}</span>
              <span className="text-[10px] text-gray-400 block mt-1">{analytics.summary.scheduled_posts} scheduled in calendar</span>
            </div>
          </div>

          {/* AI Executive Performance Report */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-3">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                AI Executive Social Media Performance Report
              </h3>
              <button
                onClick={handleSyncMetrics}
                className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded text-xs flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Sync Live Platform Metrics
              </button>
            </div>
            <p className="text-sm text-gray-300 leading-relaxed bg-gray-800/40 p-4 rounded-lg border border-gray-700/50">
              {analytics.ai_executive_report}
            </p>
          </div>

          {/* Platform Performance Breakdown */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <h3 className="text-sm font-bold text-white mb-4">Platform Performance Breakdown</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {Object.entries(analytics.platform_breakdown).map(([platform, data]) => (
                <div key={platform} className="bg-gray-800/50 border border-gray-700/60 p-4 rounded-xl space-y-2">
                  <div className="flex items-center gap-1.5 font-bold text-white text-xs">
                    {getPlatformIcon(platform)}
                    <span className="truncate">{platform.replace('_', ' ')}</span>
                  </div>
                  <div className="text-xs space-y-1">
                    <div className="flex justify-between text-gray-400">
                      <span>Posts:</span>
                      <span className="text-white font-semibold">{data.post_count}</span>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Impressions:</span>
                      <span className="text-white font-semibold">{data.impressions.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-gray-400">
                      <span>Engagements:</span>
                      <span className="text-white font-semibold">{data.engagements.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 7: SOCIAL MEDIA LISTENING & LEAD EXTRACTION AGENT */}
      {/* ========================================================================= */}
      {activeTab === 'LISTENING' && (
        <div className="space-y-6">
          {/* Top Banner & Status */}
          <div className="bg-gradient-to-r from-gray-900 via-indigo-950/40 to-gray-900 border border-indigo-500/30 rounded-2xl p-6 shadow-xl">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
              <div>
                <div className="flex items-center gap-2.5">
                  <span className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                    <Radio className="w-6 h-6 animate-pulse" />
                  </span>
                  <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      Autonomous Social Intent Listening Agent
                      <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                        Live Agent Engine
                      </span>
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">
                      Scans Facebook, Instagram, X (Twitter), and LinkedIn for buyer intent signals, extracts prospect contacts, and automatically enrolls them into the CRM &amp; SMTP outreach pipeline.
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3">
                <a
                  href="http://localhost:8025"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-gray-800/80 hover:bg-gray-700 text-slate-200 border border-gray-700 rounded-xl text-xs font-semibold shadow-sm transition"
                >
                  <Mail className="w-4 h-4 text-emerald-400" />
                  Open Mailpit Inbox (Port 8025)
                  <ExternalLink className="w-3.5 h-3.5 text-gray-400" />
                </a>
                <button
                  onClick={handleRunListeningScan}
                  disabled={listeningRunning}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-md transition"
                >
                  {listeningRunning ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Scanning Social Channels...
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 text-amber-300" />
                      Run Instant Intent Scan Now
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Metrics Row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
              <div className="bg-gray-900/80 border border-gray-800 p-4 rounded-xl">
                <span className="text-xs text-gray-400 block mb-1">Total Social Leads Captured</span>
                <span className="text-2xl font-bold text-white">
                  {listeningStatus?.total_social_leads_captured || 0}
                </span>
                <span className="text-[10px] text-emerald-400 block mt-1">✓ Converted to CRM Business Leads</span>
              </div>
              <div className="bg-gray-900/80 border border-gray-800 p-4 rounded-xl">
                <span className="text-xs text-gray-400 block mb-1">Monitored Channels</span>
                <div className="flex items-center gap-2 mt-1.5">
                  <Linkedin className="w-4 h-4 text-blue-400" />
                  <Twitter className="w-4 h-4 text-sky-400" />
                  <Facebook className="w-4 h-4 text-blue-500" />
                  <Instagram className="w-4 h-4 text-pink-400" />
                  <span className="text-xs text-slate-300 font-semibold ml-1">4 Active Channels</span>
                </div>
                <span className="text-[10px] text-gray-400 block mt-1">LinkedIn, X, Facebook, Instagram</span>
              </div>
              <div className="bg-gray-900/80 border border-gray-800 p-4 rounded-xl">
                <span className="text-xs text-gray-400 block mb-1">Autonomous Schedule</span>
                <span className="text-sm font-semibold text-indigo-300 block">
                  Every 4 Hours + Daily Scan
                </span>
                <span className="text-[10px] text-gray-400 block mt-1">Background cron &amp; periodic polling</span>
              </div>
              <div className="bg-gray-900/80 border border-gray-800 p-4 rounded-xl">
                <span className="text-xs text-gray-400 block mb-1">Auto-Outreach Integration</span>
                <span className="text-sm font-semibold text-emerald-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" /> Auto-Enrolled &amp; Sent
                </span>
                <span className="text-[10px] text-gray-400 block mt-1">Mailpit SMTP + Pixel Tracking</span>
              </div>
            </div>
          </div>

          {/* Configuration & Intent Filter Bar */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Filter className="w-4 h-4 text-indigo-400" />
              Target Social Platforms &amp; Buyer Intent Keywords
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-2">Target Platforms</label>
                <div className="flex flex-wrap gap-2">
                  {['LINKEDIN', 'X', 'FACEBOOK', 'INSTAGRAM'].map((plat) => {
                    const isSelected = listeningPlatforms.includes(plat);
                    return (
                      <button
                        key={plat}
                        type="button"
                        onClick={() => {
                          if (isSelected) {
                            if (listeningPlatforms.length > 1) {
                              setListeningPlatforms(listeningPlatforms.filter((p) => p !== plat));
                            }
                          } else {
                            setListeningPlatforms([...listeningPlatforms, plat]);
                          }
                        }}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition border ${
                          isSelected
                            ? 'bg-indigo-600/30 text-indigo-300 border-indigo-500/50'
                            : 'bg-gray-800/60 text-gray-400 border-gray-700/60 hover:text-gray-200'
                        }`}
                      >
                        {plat === 'LINKEDIN' && <Linkedin className="w-3.5 h-3.5 text-blue-400" />}
                        {plat === 'X' && <Twitter className="w-3.5 h-3.5 text-sky-400" />}
                        {plat === 'FACEBOOK' && <Facebook className="w-3.5 h-3.5 text-blue-500" />}
                        {plat === 'INSTAGRAM' && <Instagram className="w-3.5 h-3.5 text-pink-400" />}
                        {plat}
                        {isSelected && <span className="text-emerald-400">✓</span>}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 mb-2">
                  Buyer Intent Trigger Phrases (Comma separated)
                </label>
                <input
                  type="text"
                  value={listeningKeywords}
                  onChange={(e) => setListeningKeywords(e.target.value)}
                  placeholder="looking for, need recommendations, recommend a crm, budget approved..."
                  className="w-full px-3 py-2 bg-gray-950 border border-gray-800 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Scan Results Display */}
          {listeningScanResult && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Latest Scan Results ({listeningScanResult.total_leads_extracted} Leads Extracted &amp; Enrolled)
                </h3>
                <span className="text-xs text-gray-400">
                  Scanned: {new Date(listeningScanResult.executed_at).toLocaleTimeString()}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(listeningScanResult.results_by_platform || {}).map(([plat, leads]: [string, any]) =>
                  (leads || []).map((l: any, idx: number) => (
                    <div
                      key={`${plat}-${idx}`}
                      className="bg-gray-950/80 border border-gray-800/90 rounded-xl p-4 space-y-3 hover:border-indigo-500/40 transition"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {plat === 'LINKEDIN' && <Linkedin className="w-4 h-4 text-blue-400" />}
                          {plat === 'X' && <Twitter className="w-4 h-4 text-sky-400" />}
                          {plat === 'FACEBOOK' && <Facebook className="w-4 h-4 text-blue-500" />}
                          {plat === 'INSTAGRAM' && <Instagram className="w-4 h-4 text-pink-400" />}
                          <span className="font-semibold text-white text-xs">{l.author}</span>
                          <span className="px-2 py-0.5 text-[10px] bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 rounded-md">
                            {plat}
                          </span>
                        </div>
                        <span className="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full">
                          {l.intent_score}% Intent Score
                        </span>
                      </div>

                      <p className="text-xs text-gray-300 bg-gray-900/60 p-2.5 rounded-lg border border-gray-800/80 italic">
                        "{l.content}"
                      </p>

                      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-gray-800/80 text-[11px]">
                        <div className="flex items-center gap-3 text-gray-400">
                          {l.email && (
                            <span className="text-indigo-300 font-medium flex items-center gap-1">
                              <Mail className="w-3 h-3" /> {l.email}
                            </span>
                          )}
                          {l.phone && (
                            <span className="text-emerald-300 font-medium">
                              📞 {l.phone}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-emerald-400 font-semibold flex items-center gap-1">
                            ✓ {l.outreach_status || 'Auto-Enrolled'}
                          </span>
                          <a
                            href="/leads"
                            className="px-2 py-1 bg-indigo-600/30 hover:bg-indigo-600 text-indigo-200 hover:text-white rounded text-[10px] font-semibold transition"
                          >
                            View in CRM
                          </a>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
