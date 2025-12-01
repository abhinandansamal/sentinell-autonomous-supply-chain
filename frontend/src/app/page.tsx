"use client";

import { useState } from "react";
import { api, ScanResponse } from "@/lib/api";
import { ShieldAlert, RefreshCw, ShoppingCart, Truck, Activity, AlertTriangle } from "lucide-react";

export default function Dashboard() {
  const [region, setRegion] = useState("Taiwan");
  const [loading, setLoading] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [orderStatus, setOrderStatus] = useState<string | null>(null);

  const handleScan = async () => {
    setLoading(true);
    setScanResult(null);
    setOrderStatus(null);
    try {
      const data = await api.scanRegion(region);
      setScanResult(data);
    } catch (err) {
      alert("Failed to connect to Sentinell Backend. Please check your .env.local file.");
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async () => {
    if (!confirm("Confirm purchase of 50 CPUs from backup supplier?")) return;
    setLoading(true);
    try {
      const res = await api.purchaseParts("Logic-Core-CPU", 50);
      setOrderStatus(res.summary);
    } catch (err) {
      alert("Purchase failed. Check console for details.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-4 md:p-8 font-sans">
      {/* Header */}
      <header className="mb-8 flex flex-col md:flex-row items-start md:items-center justify-between border-b border-slate-800 pb-4 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="text-blue-500" /> Sentinell.ai
          </h1>
          <p className="text-slate-400 text-sm">Autonomous Supply Chain Resilience System</p>
        </div>
        <div className="bg-slate-900 px-4 py-2 rounded-lg border border-slate-800 flex items-center gap-2">
          <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-green-400 text-sm font-medium">System Online</span>
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* LEFT COLUMN: Controls (4 cols) */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Scan Card */}
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg">
            <h2 className="text-lg font-semibold mb-4 text-white flex items-center gap-2">
              <Activity size={20} className="text-blue-400"/> Risk Monitor
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-xs uppercase tracking-wider text-slate-500 mb-1">Target Region</label>
                <select 
                  value={region} 
                  onChange={(e) => setRegion(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                >
                  <option value="Taiwan">Taiwan (High Risk Sim)</option>
                  <option value="USA">USA (Medium Risk Sim)</option>
                  <option value="Vietnam">Vietnam (Low Risk Sim)</option>
                </select>
              </div>
              
              <button
                onClick={handleScan}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition-all shadow-md active:scale-95"
              >
                {loading ? <RefreshCw className="animate-spin" /> : <ShieldAlert size={20} />}
                {loading ? "Analyzing..." : "Run Risk Analysis"}
              </button>
            </div>
          </div>

          {/* Action Card */}
          <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-lg opacity-90">
            <h2 className="text-lg font-semibold mb-2 text-white flex items-center gap-2">
              <ShoppingCart size={20} className="text-green-400"/> Response Actions
            </h2>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Detected a critical shortage? Authorize the Procurement Agent to negotiate with backup suppliers immediately.
            </p>
            <button 
              onClick={handlePurchase}
              disabled={loading || !scanResult}
              className={`w-full border-2 font-bold py-3 rounded-lg flex items-center justify-center gap-2 transition-all ${
                !scanResult 
                  ? "border-slate-700 text-slate-600 cursor-not-allowed"
                  : "border-green-600 text-green-500 hover:bg-green-900/20 active:scale-95"
              }`}
            >
              <Truck size={20} />
              Replenish Inventory
            </button>
          </div>
        </div>

        {/* RIGHT COLUMN: Feed (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-slate-900 min-h-[600px] p-6 rounded-xl border border-slate-800 relative shadow-xl flex flex-col">
            
            {/* Header Line */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
              <h2 className="text-xl font-semibold text-white">Agent Intelligence Feed</h2>
              <span className="text-xs text-slate-500 font-mono">LIVE CONNECTED</span>
            </div>

            {/* Empty State */}
            {!scanResult && !orderStatus && (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-600 space-y-4">
                <div className="p-4 bg-slate-800/50 rounded-full">
                  <ShieldAlert size={48} />
                </div>
                <p>Ready to analyze. Select a region to begin.</p>
              </div>
            )}

            <div className="space-y-6">
              {/* Scan Result */}
              {scanResult && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="flex items-center gap-3 mb-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold border flex items-center gap-2 ${
                      scanResult.risk_level === 'CRITICAL' ? 'bg-red-950/50 border-red-500 text-red-400' :
                      scanResult.risk_level === 'MEDIUM' ? 'bg-yellow-950/50 border-yellow-500 text-yellow-400' :
                      'bg-green-950/50 border-green-500 text-green-400'
                    }`}>
                      {scanResult.risk_level === 'CRITICAL' && <AlertTriangle size={12} />}
                      {scanResult.risk_level} RISK DETECTED
                    </span>
                    <span className="text-xs text-slate-500">{new Date(scanResult.timestamp).toLocaleTimeString()}</span>
                  </div>
                  
                  <div className="bg-slate-950 p-6 rounded-lg border border-slate-700/50 shadow-inner">
                    <pre className="whitespace-pre-wrap font-sans text-sm leading-7 text-slate-300">
                      {scanResult.summary}
                    </pre>
                  </div>
                </div>
              )}

              {/* Order Status */}
              {orderStatus && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-4">
                  <div className="bg-green-950/30 border border-green-900 p-4 rounded-lg flex gap-4">
                    <div className="p-2 bg-green-900/50 rounded h-fit">
                      <Truck size={24} className="text-green-400" />
                    </div>
                    <div>
                      <h3 className="text-green-400 font-bold mb-1">Procurement Agent Update</h3>
                      <p className="text-green-100/80 text-sm leading-relaxed">{orderStatus}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}