import React, { useState, useEffect } from 'react';
import {
  Share2,
  Calendar,
  Sparkles,
  RefreshCw,
} from 'lucide-react';
import { ContentItemData, CalendarEntryItem } from '../types';

export const ContentSocialView: React.FC = () => {
  const [items, setItems] = useState<ContentItemData[]>([]);
  const [calendarEntries, setCalendarEntries] = useState<CalendarEntryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedPillar, setSelectedPillar] = useState<string>('ALL');

  // New Content Form
  const [title, setTitle] = useState<string>('');
  const [pillar, setPillar] = useState<string>('TECHNICAL_EXPERTISE');
  const [coreIdea, setCoreIdea] = useState<string>('');
  const [targetAudience, setTargetAudience] = useState<string>('B2B Founders & Tech Leaders');
  const [platforms, setPlatforms] = useState<string[]>(['LINKEDIN', 'X']);
  const [generating, setGenerating] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchContentData = async () => {
    setLoading(true);
    try {
      const [itemsRes, calRes] = await Promise.all([
        fetch('/api/v1/content/items'),
        fetch('/api/v1/content/calendar'),
      ]);
      if (itemsRes.ok) setItems(await itemsRes.json());
      if (calRes.ok) setCalendarEntries(await calRes.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContentData();
  }, []);

  const handleGenerateContent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!coreIdea.trim()) return;
    setGenerating(true);
    try {
      const res = await fetch('/api/v1/content/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title || 'Strategic Insight',
          pillar,
          core_idea: coreIdea,
          target_audience: targetAudience,
          platforms,
        }),
      });
      if (res.ok) {
        setMessage('AI successfully drafted and repurposed content across platforms!');
        setTitle('');
        setCoreIdea('');
        fetchContentData();
      }
    } catch {
      setMessage('Error generating content drafts.');
    } finally {
      setGenerating(false);
    }
  };

  const handleScheduleEntry = async (itemId: string, channel: string) => {
    try {
      const scheduledDate = new Date();
      scheduledDate.setDate(scheduledDate.getDate() + 1);
      const res = await fetch('/api/v1/content/calendar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content_item_id: itemId,
          channel,
          scheduled_for: scheduledDate.toISOString(),
        }),
      });
      if (res.ok) {
        setMessage(`Scheduled ${channel} post for tomorrow!`);
        fetchContentData();
      }
    } catch {
      setMessage('Scheduling failed.');
    }
  };

  const filteredItems = selectedPillar === 'ALL'
    ? items
    : items.filter((i) => i.pillar === selectedPillar);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center bg-gray-900 border border-gray-800 p-6 rounded-xl">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <Share2 className="w-7 h-7 text-indigo-400" />
              Social Media &amp; Content Marketing
            </h1>
            <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              5 Content Pillars
            </span>
          </div>
          <p className="text-gray-400 text-sm mt-1">
            Plan, AI-generate, and repurpose content across LinkedIn, X, and Reddit with calendar scheduling and publishing governance.
          </p>
        </div>
        <button
          onClick={fetchContentData}
          className="p-2.5 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg transition"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {message && (
        <div className="p-4 bg-indigo-950/60 border border-indigo-500/40 rounded-lg text-indigo-200 text-sm flex justify-between items-center">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="text-indigo-400 hover:text-white">✕</button>
        </div>
      )}

      {/* AI Content Repurposer Box */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-400" />
          AI Multi-Platform Content Generator &amp; Repurposer
        </h2>
        <p className="text-xs text-gray-400 mb-4">
          Formulate a core idea once. The AI generates native, platform-specific copy tailored for LinkedIn, X (Twitter), and Reddit.
        </p>

        <form onSubmit={handleGenerateContent} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Content Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Scaling Sales Operations with AI"
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Content Pillar</label>
              <select
                value={pillar}
                onChange={(e) => setPillar(e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
              >
                <option value="TECHNICAL_EXPERTISE">Technical Expertise</option>
                <option value="PROOF_OF_WORK">Proof of Work / Case Studies</option>
                <option value="PROBLEM_AWARENESS">Problem Awareness</option>
                <option value="COMPANY_UPDATES">Company Updates</option>
                <option value="OFFERS_AND_SERVICES">Offers &amp; Services</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Target Audience</label>
              <input
                type="text"
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white"
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-400 block mb-1">Core Idea &amp; Key Takeaways</label>
            <textarea
              required
              rows={3}
              value={coreIdea}
              onChange={(e) => setCoreIdea(e.target.value)}
              placeholder="State the core hypothesis, lesson learned, or technical breakthrough..."
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white font-sans"
            />
          </div>

          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-4 text-xs text-gray-300">
              <span className="font-semibold text-gray-400">Target Channels:</span>
              {['LINKEDIN', 'X', 'REDDIT'].map((p) => (
                <label key={p} className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={platforms.includes(p)}
                    onChange={(e) => {
                      if (e.target.checked) setPlatforms([...platforms, p]);
                      else setPlatforms(platforms.filter((x) => x !== p));
                    }}
                    className="rounded bg-gray-800 border-gray-700 text-indigo-600"
                  />
                  {p}
                </label>
              ))}
            </div>

            <button
              type="submit"
              disabled={generating}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold flex items-center gap-2 transition disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              {generating ? 'Drafting across platforms...' : 'Generate &amp; Repurpose'}
            </button>
          </div>
        </form>
      </div>

      {/* Content Pillars Filter */}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {['ALL', 'TECHNICAL_EXPERTISE', 'PROOF_OF_WORK', 'PROBLEM_AWARENESS', 'COMPANY_UPDATES', 'OFFERS_AND_SERVICES'].map((p) => (
          <button
            key={p}
            onClick={() => setSelectedPillar(p)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition ${
              selectedPillar === p
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-900 hover:bg-gray-800 text-gray-400'
            }`}
          >
            {p.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Grid: Content Items with Platform Variations */}
      {loading ? (
        <div className="text-center py-10 text-gray-400">Loading content pieces...</div>
      ) : (
        <div className="space-y-5">
          {filteredItems.map((item) => (
            <div key={item.id} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <span className="px-2.5 py-0.5 text-xs font-semibold rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {item.pillar}
                  </span>
                  <h3 className="text-lg font-bold text-white mt-1">{item.title}</h3>
                  <p className="text-xs text-gray-400">Audience: {item.target_audience || 'General'}</p>
                </div>
                <span className="px-2.5 py-1 text-xs font-semibold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  {item.status}
                </span>
              </div>

              {/* Platform Draft Tabs */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {Object.entries(item.platform_drafts || {}).map(([plat, text]) => (
                  <div key={plat} className="bg-gray-800/40 border border-gray-700/60 rounded-lg p-3 flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-center mb-1.5">
                        <span className="font-bold text-xs text-indigo-400">{plat} Draft</span>
                        <button
                          onClick={() => handleScheduleEntry(item.id, plat)}
                          className="text-[10px] text-gray-300 hover:text-white flex items-center gap-1 bg-gray-700/60 px-2 py-0.5 rounded"
                        >
                          <Calendar className="w-3 h-3" /> Schedule
                        </button>
                      </div>
                      <p className="text-xs text-gray-300 whitespace-pre-line font-mono line-clamp-6">{text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upcoming Content Calendar */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-indigo-400" />
          Scheduled Content Calendar ({calendarEntries.length})
        </h2>
        {calendarEntries.length === 0 ? (
          <div className="text-center py-6 text-gray-500 text-sm">No scheduled posts yet. Click 'Schedule' on any draft above!</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-300">
              <thead className="bg-gray-800/60 text-xs uppercase text-gray-400 border-b border-gray-700">
                <tr>
                  <th className="py-2.5 px-4">Content Title</th>
                  <th className="py-2.5 px-4">Channel</th>
                  <th className="py-2.5 px-4">Scheduled For</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4">Publishing API</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {calendarEntries.map((e) => (
                  <tr key={e.id}>
                    <td className="py-3 px-4 font-medium text-white">{e.content_title}</td>
                    <td className="py-3 px-4 text-xs font-semibold text-indigo-400">{e.channel}</td>
                    <td className="py-3 px-4 text-xs text-gray-400">{new Date(e.scheduled_for).toLocaleString()}</td>
                    <td className="py-3 px-4 text-xs">
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 font-semibold">{e.status}</span>
                    </td>
                    <td className="py-3 px-4 text-xs">
                      <span className="px-2 py-0.5 rounded bg-gray-800 text-gray-400 font-mono text-[11px]">{e.publishing_provider_status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
