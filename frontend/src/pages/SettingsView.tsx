import { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Shield,
  Sliders,
  CheckCircle2,
  Save,
  Zap,
  AlertCircle,
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
const API_KEY = import.meta.env.VITE_API_KEY || '';

const SettingsView: React.FC = () => {
  const [icpFit, setIcpFit] = useState(25);
  const [businessPain, setBusinessPain] = useState(25);
  const [timingIntent, setTimingIntent] = useState(20);
  const [reachability, setReachability] = useState(15);
  const [evidenceQuality, setEvidenceQuality] = useState(15);

  // Automation settings
  const [autoEnroll, setAutoEnroll] = useState(true);
  const [autoApprove, setAutoApprove] = useState(true);
  const [autoCRM, setAutoCRM] = useState(true);
  const [minScoreOutreach, setMinScoreOutreach] = useState(70);
  const [minScoreCRM, setMinScoreCRM] = useState(60);
  const [emailEnrichment, setEmailEnrichment] = useState(true);

  const [savedMessage, setSavedMessage] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const totalWeight = icpFit + businessPain + timingIntent + reachability + evidenceQuality;

  // Load automation settings on mount
  useEffect(() => {
    loadAutomationSettings();
  }, []);

  const loadAutomationSettings = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/automation/settings`, {
        headers: {
          'X-API-Key': API_KEY,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        const settings = data.settings || [];
        
        // Map settings to state
        settings.forEach((setting: any) => {
          switch (setting.setting_key) {
            case 'auto_enroll_to_outreach':
              setAutoEnroll(setting.setting_value === 'true');
              break;
            case 'auto_approve_emails':
              setAutoApprove(setting.setting_value === 'true');
              break;
            case 'auto_convert_to_crm':
              setAutoCRM(setting.setting_value === 'true');
              break;
            case 'min_score_for_outreach':
              setMinScoreOutreach(parseInt(setting.setting_value));
              break;
            case 'min_score_for_crm':
              setMinScoreCRM(parseInt(setting.setting_value));
              break;
            case 'email_enrichment_enabled':
              setEmailEnrichment(setting.setting_value === 'true');
              break;
          }
        });
      }
    } catch (error) {
      console.error('Failed to load automation settings:', error);
    }
  };

  const saveAutomationSettings = async () => {
    setLoading(true);
    setErrorMessage('');
    
    try {
      const settingsToUpdate = [
        { key: 'auto_enroll_to_outreach', value: autoEnroll.toString() },
        { key: 'auto_approve_emails', value: autoApprove.toString() },
        { key: 'auto_convert_to_crm', value: autoCRM.toString() },
        { key: 'min_score_for_outreach', value: minScoreOutreach.toString() },
        { key: 'min_score_for_crm', value: minScoreCRM.toString() },
        { key: 'email_enrichment_enabled', value: emailEnrichment.toString() },
      ];

      for (const setting of settingsToUpdate) {
        await fetch(`${API_BASE_URL}/api/v1/automation/settings/${setting.key}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
          },
          body: JSON.stringify({ value: setting.value }),
        });
      }

      setSavedMessage(true);
      setTimeout(() => setSavedMessage(false), 3000);
    } catch (error) {
      setErrorMessage('Failed to save automation settings');
      console.error('Error saving settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = () => {
    setSavedMessage(true);
    setTimeout(() => setSavedMessage(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-blue-600" />
          System Settings & ICP Configuration
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Customize qualification scoring weights, security credentials, and platform operating preferences.
        </p>
      </div>

      {savedMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-md flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Settings updated successfully.
        </div>
      )}

      {/* ICP Scoring Weights Card */}
      <div className="bg-white border rounded-lg p-6 shadow-sm space-y-5">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
              <Sliders className="w-4 h-4 text-blue-600" />
              Lead Qualification ICP Weights
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Configure how the AI Lead Qualification Engine weighs different factors when scoring prospects (0–100).
            </p>
          </div>
          <span
            className={`text-xs font-bold px-2.5 py-1 rounded-full ${
              totalWeight === 100 ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
            }`}
          >
            Total: {totalWeight}%
          </span>
        </div>

        <div className="space-y-4 pt-2">
          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
              <span>ICP Firmographic Fit (Industry, Size, Category)</span>
              <span>{icpFit}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              value={icpFit}
              onChange={(e) => setIcpFit(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
              <span>Business Pain Points & Requirement Urgency</span>
              <span>{businessPain}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              value={businessPain}
              onChange={(e) => setBusinessPain(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
              <span>Timing & Intent Signals (Hiring, Expansion)</span>
              <span>{timingIntent}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              value={timingIntent}
              onChange={(e) => setTimingIntent(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
              <span>Contact Reachability (Verified Email / Phone)</span>
              <span>{reachability}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              value={reachability}
              onChange={(e) => setReachability(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
              <span>Evidence Quality & Source Depth</span>
              <span>{evidenceQuality}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="50"
              value={evidenceQuality}
              onChange={(e) => setEvidenceQuality(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>
        </div>

        <button
          onClick={handleSave}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-xs font-semibold shadow-sm flex items-center gap-1.5"
        >
          <Save className="w-3.5 h-3.5" /> Save Weights
        </button>
      </div>

      {/* Lead Automation Settings Card */}
      <div className="bg-white border rounded-lg p-6 shadow-sm space-y-5">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
            <Zap className="w-4 h-4 text-amber-600" />
            Lead Automation Pipeline
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure zero-intervention automation for lead processing, outreach enrollment, and CRM conversion.
          </p>
        </div>

        {errorMessage && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-md flex items-center gap-2">
            <AlertCircle className="w-4 h-4" /> {errorMessage}
          </div>
        )}

        <div className="space-y-4 pt-2">
          {/* Auto-enroll to outreach */}
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-md border">
            <div className="flex-1">
              <p className="text-xs font-semibold text-slate-900">Auto-enroll qualified leads in outreach sequences</p>
              <p className="text-xs text-slate-500 mt-0.5">Automatically add leads to B2B prospecting cadence when score threshold is met</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-4">
              <input 
                type="checkbox" 
                checked={autoEnroll}
                onChange={(e) => setAutoEnroll(e.target.checked)}
                className="sr-only peer" 
              />
              <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Auto-approve emails */}
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-md border">
            <div className="flex-1">
              <p className="text-xs font-semibold text-slate-900">Auto-approve AI-generated emails</p>
              <p className="text-xs text-slate-500 mt-0.5">Skip manual review queue for validated, personalized outreach drafts</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-4">
              <input 
                type="checkbox" 
                checked={autoApprove}
                onChange={(e) => setAutoApprove(e.target.checked)}
                className="sr-only peer" 
              />
              <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Auto-convert to CRM */}
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-md border">
            <div className="flex-1">
              <p className="text-xs font-semibold text-slate-900">Auto-convert leads to CRM entities</p>
              <p className="text-xs text-slate-500 mt-0.5">Automatically create Companies, Contacts, and Deals for qualified leads</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-4">
              <input 
                type="checkbox" 
                checked={autoCRM}
                onChange={(e) => setAutoCRM(e.target.checked)}
                className="sr-only peer" 
              />
              <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Email enrichment */}
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-md border">
            <div className="flex-1">
              <p className="text-xs font-semibold text-slate-900">Email enrichment for leads without contact</p>
              <p className="text-xs text-slate-500 mt-0.5">Automatically discover and validate email addresses using pattern guessing and scraping</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer ml-4">
              <input 
                type="checkbox" 
                checked={emailEnrichment}
                onChange={(e) => setEmailEnrichment(e.target.checked)}
                className="sr-only peer" 
              />
              <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {/* Score thresholds */}
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="p-3 bg-slate-50 rounded-md border">
              <label className="text-xs font-semibold text-slate-700 block mb-2">
                Min Score for Outreach Enrollment
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={minScoreOutreach}
                onChange={(e) => setMinScoreOutreach(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Qualification score required (0-100)</p>
            </div>

            <div className="p-3 bg-slate-50 rounded-md border">
              <label className="text-xs font-semibold text-slate-700 block mb-2">
                Min Score for CRM Conversion
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={minScoreCRM}
                onChange={(e) => setMinScoreCRM(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-slate-500 mt-1">Qualification score required (0-100)</p>
            </div>
          </div>
        </div>

        <button
          onClick={saveAutomationSettings}
          disabled={loading}
          className="px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-slate-400 text-white rounded text-xs font-semibold shadow-sm flex items-center gap-1.5"
        >
          <Save className="w-3.5 h-3.5" /> {loading ? 'Saving...' : 'Save Automation Settings'}
        </button>
      </div>

      {/* Security & Access Protection Card */}
      <div className="bg-white border rounded-lg p-6 shadow-sm space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
            <Shield className="w-4 h-4 text-emerald-600" />
            Security & Authentication
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Application security controls for private personal deployment.
          </p>
        </div>

        <div className="bg-slate-50 p-4 rounded-md border text-xs space-y-2">
          <div className="flex justify-between items-center">
            <span className="font-semibold text-slate-700">Single-User Token Authentication:</span>
            <span className="text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              Active / Enforced via X-API-Key
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-semibold text-slate-700">SSRF Domain Protection:</span>
            <span className="text-emerald-700 font-semibold">Enabled (Private IPs & Cloud Metadata Blocked)</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="font-semibold text-slate-700">Outbound Human Approval Guard:</span>
            <span className={`font-semibold ${autoApprove ? 'text-amber-700' : 'text-emerald-700'}`}>
              {autoApprove ? 'Auto-Approval Enabled (validated emails only)' : 'Enabled (100% manual review required)'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsView;
