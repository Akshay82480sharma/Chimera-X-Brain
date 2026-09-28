"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { MemoryStick, HardDrive, Zap, Network, Bot, Activity, MessageSquarePlus, TrendingUp, BarChart3 } from "lucide-react";
import Link from "next/link";

const API = process.env.NEXT_PUBLIC_API_URL;

export default function Dashboard() {
  const [stats, setStats] = useState<any /* eslint-disable-line @typescript-eslint/no-explicit-any */>({
    metrics: { total_providers: 0, active_models: 0, total_chats: 0 },
    recent_memories: []
  });
  const [activity, setActivity] = useState<any[]>([]);

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await fetch(`${API}/v1/stats`);
        if (res.ok) setStats(await res.json());
      } catch (e) {
        console.warn("Failed to fetch stats", e);
      }
    };
    async function fetchActivity() {
      try {
        const res = await fetch(`${API}/v1/admin/activity`);
        if (res.ok) {
          const data = await res.json();
          setActivity(data.activity || []);
        }
      } catch (e) {
        console.warn("Failed to fetch activity", e);
      }
    };
    fetchStats();
    fetchActivity();
  }, []);

  const maxTotal = Math.max(...activity.map(a => a.total), 1);

  return (
    <div className="h-full overflow-y-auto p-8 max-w-7xl mx-auto flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">System Dashboard</h1>
        <p className="text-zinc-400 mt-1">Chimera-X Brain is online and ready.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Total Chats" value={stats.metrics.total_chats} icon={Activity} color="indigo" />
        <StatCard title="Memories" value={`${stats.recent_memories.length} facts`} icon={MemoryStick} color="emerald" />
        <StatCard title="Active Models" value={stats.metrics.active_models} icon={Bot} color="purple" />
        <StatCard title="Providers" value={stats.metrics.total_providers} icon={Network} color="blue" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Routing Activity Chart */}
        <div className="lg:col-span-2 bg-[#131316] border border-zinc-800/60 rounded-xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-zinc-100 flex items-center gap-2">
              <BarChart3 size={20} className="text-zinc-400" />
              Routing Activity (24h)
            </h2>
            <div className="flex items-center gap-4 text-xs font-medium">
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> Success</span>
              <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-red-500"></span> Failure</span>
            </div>
          </div>
          
          {activity.length > 0 ? (
            <div className="h-[240px] flex items-end gap-1 px-2">
              {activity.map((a, i) => {
                const successHeight = (a.success / maxTotal) * 200;
                const failureHeight = (a.failure / maxTotal) * 200;
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-0.5 group relative" title={`${a.hour}\n✅ ${a.success} success\n❌ ${a.failure} failures\n⚡ ${a.avg_latency}ms avg`}>
                    <div className="w-full flex flex-col gap-0.5">
                      {a.failure > 0 && (
                        <div 
                          className="w-full bg-red-500/60 rounded-t-sm transition-all group-hover:bg-red-500" 
                          style={{ height: `${failureHeight}px` }} 
                        />
                      )}
                      <div 
                        className="w-full bg-emerald-500/60 rounded-t-sm transition-all group-hover:bg-emerald-500" 
                        style={{ height: `${Math.max(successHeight, 2)}px` }} 
                      />
                    </div>
                    <span className="text-[8px] text-zinc-600 mt-1 rotate-45 origin-left whitespace-nowrap hidden group-hover:block absolute -bottom-4">
                      {a.hour.split(" ")[1]}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-[240px] flex flex-col items-center justify-center border border-zinc-800/40 rounded-lg bg-zinc-900/30">
              <TrendingUp size={32} className="text-zinc-700 mb-3" />
              <p className="text-zinc-500 text-sm font-medium">No routing activity yet</p>
              <p className="text-zinc-600 text-xs mt-1">Chat with the Brain to generate routing data.</p>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="flex flex-col gap-4">
          <div className="bg-[#131316] border border-zinc-800/60 rounded-xl p-6 flex-1">
            <h2 className="text-lg font-semibold text-zinc-100 mb-4">Quick Actions</h2>
            <div className="flex flex-col gap-3">
              <Link href="/chat" className="flex items-center gap-3 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 transition-colors">
                <MessageSquarePlus className="w-5 h-5" />
                <span className="font-medium text-sm">New Chat</span>
              </Link>
              <Link href="/knowledge" className="flex items-center gap-3 p-3 rounded-lg bg-zinc-800/40 border border-zinc-800 hover:bg-zinc-800 transition-colors text-zinc-300">
                <HardDrive className="w-5 h-5" />
                <span className="font-medium text-sm">Upload Knowledge</span>
              </Link>
              <Link href="/providers" className="flex items-center gap-3 p-3 rounded-lg bg-zinc-800/40 border border-zinc-800 hover:bg-zinc-800 transition-colors text-zinc-300">
                <Zap className="w-5 h-5" />
                <span className="font-medium text-sm">Add Provider</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
      
      {/* Recent Memory Stream */}
      <div>
        <h2 className="text-lg font-semibold text-zinc-100 mb-4">Recent Memory Stream</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {stats.recent_memories.length === 0 ? (
            <p className="text-zinc-500 text-sm col-span-full">No memories recorded yet. Start a chat to begin learning.</p>
          ) : (
            stats.recent_memories.map((mem: any /* eslint-disable-line @typescript-eslint/no-explicit-any */) => (
              <MemoryCard 
                key={mem.id}
                title={mem.title} 
                type={mem.type} 
                date={new Date(mem.date).toLocaleString()} 
                provider={mem.provider} 
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, trend, trendUp, color }: any /* eslint-disable-line @typescript-eslint/no-explicit-any */) {
  const colorMap: Record<string, string> = {
    indigo: "text-indigo-400 bg-indigo-500/10",
    emerald: "text-emerald-400 bg-emerald-500/10",
    purple: "text-purple-400 bg-purple-500/10",
    blue: "text-blue-400 bg-blue-500/10",
  };
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-[#131316] border border-zinc-800/60 rounded-xl p-5 flex flex-col gap-4 relative overflow-hidden group"
    >
      <div className="flex items-center justify-between">
        <span className="text-zinc-400 text-sm font-medium">{title}</span>
        <div className={`p-2 rounded-lg ${colorMap[color]}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="flex items-end gap-2">
        <span className="text-2xl font-bold text-zinc-100 tracking-tight">{value}</span>
        {trend && (
          <span className={`text-xs font-medium mb-1 ${trendUp ? "text-emerald-400" : "text-red-400"}`}>
            {trend}
          </span>
        )}
      </div>
      <div className="absolute inset-0 bg-gradient-to-tr from-white/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
    </motion.div>
  );
}

function MemoryCard({ title, type, date, provider }: any /* eslint-disable-line @typescript-eslint/no-explicit-any */) {
  return (
    <div className="bg-[#131316] border border-zinc-800/60 rounded-xl p-4 hover:border-zinc-700 cursor-pointer transition-colors group">
      <div className="flex justify-between items-start mb-2">
        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-zinc-800 text-zinc-300 uppercase tracking-wider">{type}</span>
        <span className="text-xs text-zinc-500">{date}</span>
      </div>
      <h3 className="text-sm font-medium text-zinc-200 group-hover:text-emerald-400 transition-colors line-clamp-1">{title}</h3>
      <div className="mt-3 flex items-center gap-1.5">
        <Activity className="w-3.5 h-3.5 text-zinc-500" />
        <span className="text-xs text-zinc-500">{provider}</span>
      </div>
    </div>
  );
}
