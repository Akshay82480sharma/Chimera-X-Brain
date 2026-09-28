"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Settings, Save, Moon, Sun, Monitor, Bell, Shield, AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const API = process.env.NEXT_PUBLIC_API_URL;

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");
  const [settings, setSettings] = useState({
    theme: "dark",
    notifications: true,
    auto_route: true,
    data_collection: false,
    default_priority: 100
  });
  const [wipeConfirm, setWipeConfirm] = useState(false);
  const [isWiping, setIsWiping] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved">("idle");

  const handleSave = () => {
    setSaveStatus("saving");
    // Persist to localStorage (local-first, no backend needed)
    localStorage.setItem("chimera-x-settings", JSON.stringify(settings));
    setTimeout(() => {
      setSaveStatus("saved");
      setTimeout(() => setSaveStatus("idle"), 2000);
    }, 300);
  };

  async function handleWipe() {
    setIsWiping(true);
    try {
      const res = await fetch(`${API}/v1/admin/wipe`, { method: "DELETE" });
      if (res.ok) {
        setWipeConfirm(false);
        alert("All data has been wiped. Providers and API keys have been preserved.");
      }
    } catch (e) {
      alert("Failed to wipe database. Is the backend running?");
    } finally {
      setIsWiping(false);
    }
  };

  return (
    <div className="h-full overflow-y-auto p-10 max-w-5xl mx-auto flex gap-8">
      {/* Sidebar */}
      <div className="w-64 shrink-0">
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3 mb-8">
            <Settings size={28} className="text-zinc-400" /> Settings
          </h1>
          
          <nav className="flex flex-col gap-2">
            {[
              { id: "general", label: "General", icon: Monitor },
              { id: "routing", label: "Auto-Routing", icon: Settings },
              { id: "privacy", label: "Privacy & Security", icon: Shield },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  activeTab === tab.id 
                    ? "bg-white/10 text-white shadow-lg border border-white/10" 
                    : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
                }`}
              >
                <tab.icon size={18} />
                {tab.label}
              </button>
            ))}
          </nav>
        </motion.div>
      </div>

      {/* Content */}
      <div className="flex-1">
        <motion.div 
          key={activeTab}
          initial={{ opacity: 0, y: 10 }} 
          animate={{ opacity: 1, y: 0 }}
          className="bg-[#131316] border border-zinc-800/60 rounded-3xl p-8 shadow-2xl min-h-[500px]"
        >
          {activeTab === "general" && (
            <div className="space-y-8">
              <div>
                <h2 className="text-xl font-bold text-white mb-2">Appearance</h2>
                <p className="text-zinc-400 text-sm mb-6">Customize how Chimera-X looks on your device.</p>
                
                <div className="flex gap-4">
                  {[
                    { id: "light", icon: Sun, label: "Light" },
                    { id: "dark", icon: Moon, label: "Dark" },
                    { id: "system", icon: Monitor, label: "System" },
                  ].map(theme => (
                    <button
                      key={theme.id}
                      onClick={() => setSettings({...settings, theme: theme.id})}
                      className={`flex-1 flex flex-col items-center gap-3 p-4 rounded-2xl border-2 transition-all ${
                        settings.theme === theme.id 
                          ? "border-emerald-500 bg-emerald-500/10 text-emerald-400" 
                          : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700 hover:bg-zinc-800"
                      }`}
                    >
                      <theme.icon size={24} />
                      <span className="font-medium text-sm">{theme.label}</span>
                    </button>
                  ))}
                </div>
              </div>
              
              <hr className="border-zinc-800" />
              
              <div>
                <h2 className="text-xl font-bold text-white mb-2">Notifications</h2>
                <div className="flex items-center justify-between p-4 bg-zinc-900/50 border border-zinc-800 rounded-2xl">
                  <div>
                    <p className="font-medium text-white flex items-center gap-2"><Bell size={16}/> Push Notifications</p>
                    <p className="text-sm text-zinc-500">Receive alerts for rate-limits and fallbacks.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" checked={settings.notifications} onChange={() => setSettings({...settings, notifications: !settings.notifications})} />
                    <div className="w-11 h-6 bg-zinc-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                  </label>
                </div>
              </div>
            </div>
          )}

          {activeTab === "routing" && (
            <div className="space-y-8">
              <div>
                <h2 className="text-xl font-bold text-white mb-2">Auto-Routing</h2>
                <p className="text-zinc-400 text-sm mb-6">Configure how the brain selects providers.</p>
                
                <div className="flex items-center justify-between p-4 bg-zinc-900/50 border border-zinc-800 rounded-2xl mb-6">
                  <div>
                    <p className="font-medium text-white">Enable Fallback Router</p>
                    <p className="text-sm text-zinc-500">Automatically switch providers if one fails.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" checked={settings.auto_route} onChange={() => setSettings({...settings, auto_route: !settings.auto_route})} />
                    <div className="w-11 h-6 bg-zinc-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-500"></div>
                  </label>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-zinc-400">Default Priority for New Providers</label>
                  <input 
                    type="number" 
                    value={settings.default_priority}
                    onChange={(e) => setSettings({...settings, default_priority: parseInt(e.target.value)})}
                    className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none max-w-xs block" 
                  />
                  <p className="text-xs text-zinc-500">Lower numbers are preferred first.</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === "privacy" && (
            <div className="space-y-8">
              <div>
                <h2 className="text-xl font-bold text-white mb-2">Privacy & Security</h2>
                <p className="text-zinc-400 text-sm mb-6">Manage how your data is handled locally.</p>
                
                <div className="flex items-center justify-between p-4 bg-zinc-900/50 border border-zinc-800 rounded-2xl">
                  <div>
                    <p className="font-medium text-white">Telemetry</p>
                    <p className="text-sm text-zinc-500">Send anonymous error logs to improve the router.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" checked={settings.data_collection} onChange={() => setSettings({...settings, data_collection: !settings.data_collection})} />
                    <div className="w-11 h-6 bg-zinc-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-500"></div>
                  </label>
                </div>
                
                <div className="mt-8 p-5 border border-red-500/30 bg-red-500/5 rounded-2xl">
                  <h3 className="font-bold text-red-400 mb-2 flex items-center gap-2">
                    <AlertTriangle size={18} /> Danger Zone
                  </h3>
                  <p className="text-sm text-zinc-400 mb-4">
                    Erase all local memories, chat histories, prompts, and tools. 
                    <strong className="text-zinc-300"> Provider configurations and API keys will be preserved.</strong>
                  </p>
                  
                  <AnimatePresence mode="wait">
                    {!wipeConfirm ? (
                      <motion.div key="button" initial={{ opacity: 1 }} exit={{ opacity: 0 }}>
                        <Button 
                          onClick={() => setWipeConfirm(true)}
                          variant="destructive" 
                          className="bg-red-500/20 hover:bg-red-500/30 text-red-400 font-bold border border-red-500/30"
                        >
                          Wipe Database
                        </Button>
                      </motion.div>
                    ) : (
                      <motion.div 
                        key="confirm" 
                        initial={{ opacity: 0, y: 5 }} 
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center gap-4"
                      >
                        <p className="text-sm font-bold text-red-400">Are you sure? This cannot be undone.</p>
                        <Button 
                          onClick={handleWipe}
                          disabled={isWiping}
                          className="bg-red-500 hover:bg-red-600 text-white font-bold"
                        >
                          {isWiping ? <Loader2 size={16} className="animate-spin mr-2" /> : null}
                          {isWiping ? "Wiping..." : "Yes, Wipe Everything"}
                        </Button>
                        <Button 
                          onClick={() => setWipeConfirm(false)} 
                          variant="ghost" 
                          className="text-zinc-400"
                        >
                          Cancel
                        </Button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </div>
          )}
          
          <div className="mt-12 pt-6 border-t border-zinc-800 flex justify-end items-center gap-4">
            <AnimatePresence>
              {saveStatus === "saved" && (
                <motion.span 
                  initial={{ opacity: 0, x: 10 }} 
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0 }}
                  className="text-emerald-400 text-sm font-medium flex items-center gap-1.5"
                >
                  <CheckCircle2 size={16} /> Settings saved
                </motion.span>
              )}
            </AnimatePresence>
            <Button 
              onClick={handleSave} 
              disabled={saveStatus === "saving"}
              className="bg-zinc-100 hover:bg-white text-black font-bold px-8 py-5 rounded-xl shadow-xl shadow-white/10 flex items-center gap-2"
            >
              {saveStatus === "saving" ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
              Save Settings
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
