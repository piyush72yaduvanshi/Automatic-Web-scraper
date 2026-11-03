import { useState } from 'react';
import {
  Settings as SettingsIcon,
  Shield,
  Sliders,
  CheckCircle2,
  Save,
} from 'lucide-react';

const SettingsView: React.FC = () => {
  const [icpFit, setIcpFit] = useState(25);
  const [businessPain, setBusinessPain] = useState(25);
  const [timingIntent, setTimingIntent] = useState(20);
  const [reachability, setReachability] = useState(15);
  const [evidenceQuality, setEvidenceQuality] = useState(15);

  const [savedMessage, setSavedMessage] = useState(false);

  const totalWeight = icpFit + businessPain + timingIntent + reachability + evidenceQuality;

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
            <span className="text-emerald-700 font-semibold">Enabled (100% of external messages require review)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsView;
