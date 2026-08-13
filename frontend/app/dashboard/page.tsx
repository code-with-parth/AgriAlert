"use client";

import { useEffect, useState } from "react";
import { Activity, PhoneIncoming, CheckCircle, XCircle } from "lucide-react";

type Metrics = {
  total: number;
  successful: number;
  failed: number;
};

export default function Dashboard() {
  const [metrics, setMetrics] = useState<Metrics>({
    total: 0,
    successful: 0,
    failed: 0,
  });
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    try {
      const res = await fetch("/api/metrics");
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (error) {
      console.error("Failed to fetch metrics:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    // Auto-refresh every 5 seconds
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const successRate =
    metrics.total > 0
      ? Math.round((metrics.successful / metrics.total) * 100)
      : 0;

  return (
    <div className="min-h-screen bg-green-50/30 p-8 text-neutral-900 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Project Title */}
        <div className="text-center w-full">
          <h1 className="text-4xl font-bold text-white mb-2 tracking-wide">AgriAlert (कृषीअलर्ट)</h1>
        </div>

        {/* Header Section */}
        <header className="flex flex-col md:flex-row items-center justify-between border-b border-green-200 pb-6">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-green-600 text-white rounded-xl shadow-lg">
              <Activity size={32} />
            </div>
            <div>
              <h1 className="text-3xl font-extrabold text-white tracking-tight">AgriAlert Analytics</h1>
              <p className="text-white mt-1 font-medium">Real-time monitoring for the Farm & Field Agent</p>
            </div>
          </div>
          <div className="mt-4 md:mt-0 flex items-center space-x-2 text-sm text-green-600 bg-green-100 px-4 py-2 rounded-full shadow-inner">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            <span className="font-semibold">Live Updating</span>
          </div>
        </header>

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
          </div>
        )}

        {/* Metrics Grid */}
        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            
            {/* Total Calls Card */}
            <div className="bg-white rounded-2xl p-6 shadow-xl shadow-green-900/5 border border-green-100 flex flex-col justify-between transform transition duration-300 hover:scale-105">
              <div className="flex justify-between items-start">
                <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider">Total Calls</p>
                <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                  <PhoneIncoming size={24} />
                </div>
              </div>
              <div className="mt-4">
                <h3 className="text-5xl font-black text-neutral-800">{metrics.total}</h3>
              </div>
            </div>

            {/* Successful Calls Card */}
            <div className="bg-white rounded-2xl p-6 shadow-xl shadow-green-900/5 border border-green-100 flex flex-col justify-between transform transition duration-300 hover:scale-105">
              <div className="flex justify-between items-start">
                <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider">Successful</p>
                <div className="p-2 bg-green-50 text-green-600 rounded-lg">
                  <CheckCircle size={24} />
                </div>
              </div>
              <div className="mt-4">
                <h3 className="text-5xl font-black text-green-600">{metrics.successful}</h3>
                <p className="text-sm text-green-600 mt-2 font-medium">Data delivered</p>
              </div>
            </div>

            {/* Failed Calls Card */}
            <div className="bg-white rounded-2xl p-6 shadow-xl shadow-green-900/5 border border-green-100 flex flex-col justify-between transform transition duration-300 hover:scale-105">
              <div className="flex justify-between items-start">
                <p className="text-sm font-semibold text-neutral-500 uppercase tracking-wider">Failed / Drops</p>
                <div className="p-2 bg-red-50 text-red-600 rounded-lg">
                  <XCircle size={24} />
                </div>
              </div>
              <div className="mt-4">
                <h3 className="text-5xl font-black text-red-600">{metrics.failed}</h3>
                <p className="text-sm text-red-600 mt-2 font-medium">Hangups or unfulfilled</p>
              </div>
            </div>

            {/* Success Rate Card */}
            <div className="bg-gradient-to-br from-green-600 to-emerald-800 rounded-2xl p-6 shadow-xl shadow-green-900/20 text-white flex flex-col justify-between transform transition duration-300 hover:scale-105">
              <div className="flex justify-between items-start">
                <p className="text-sm font-semibold text-green-100 uppercase tracking-wider">Success Rate</p>
              </div>
              <div className="mt-4">
                <div className="flex items-baseline space-x-1">
                  <h3 className="text-5xl font-black">{successRate}</h3>
                  <span className="text-2xl font-bold text-green-200">%</span>
                </div>
                
                {/* Mini progress bar */}
                <div className="w-full bg-green-900/50 rounded-full h-2 mt-4 overflow-hidden">
                  <div 
                    className="bg-green-300 h-2 rounded-full transition-all duration-1000 ease-out"
                    style={{ width: `${successRate}%` }}
                  ></div>
                </div>
              </div>
            </div>
            
          </div>
        )}

      </div>
    </div>
  );
}
