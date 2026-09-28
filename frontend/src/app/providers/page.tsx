"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Network, Plus, Trash2, Edit2, Server, Cloud, ShieldAlert, Key, CheckCircle2, Settings2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const PROVIDER_TEMPLATES = [
  { slug: "openai", name: "OpenAI", type: "cloud", base_url: "https://api.openai.com/v1", priority: 10 },
  { slug: "gemini", name: "Google Gemini", type: "cloud", base_url: "", priority: 15 },
  { slug: "openrouter", name: "OpenRouter", type: "cloud", base_url: "https://openrouter.ai/api/v1", priority: 18 },
  { slug: "anthropic", name: "Anthropic", type: "cloud", base_url: "", priority: 20 },
  { slug: "perplexity", name: "Perplexity", type: "cloud", base_url: "https://api.perplexity.ai", priority: 25 },
  { slug: "huggingface", name: "Hugging Face", type: "cloud", base_url: "", priority: 30 },
  { slug: "alibaba", name: "Alibaba DashScope", type: "cloud", base_url: "", priority: 35 },
  { slug: "nvidia", name: "NVIDIA NIM", type: "cloud", base_url: "https://integrate.api.nvidia.com/v1", priority: 40 },
  { slug: "cerebras", name: "Cerebras", type: "cloud", base_url: "https://api.cerebras.ai/v1", priority: 42 },
  { slug: "groq", name: "Groq", type: "cloud", base_url: "https://api.groq.com/openai/v1", priority: 45 },
  { slug: "lm-studio", name: "LM Studio", type: "local", base_url: "http://127.0.0.1:1234/v1", priority: 50 },
  { slug: "ollama", name: "Ollama", type: "local", base_url: "http://127.0.0.1:11434/v1", priority: 60 }
];

export default function ProvidersPage() {
  const [providers, setProviders] = useState<any[]>([]);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isBulkAdding, setIsBulkAdding] = useState(false);
  const [bulkData, setBulkData] = useState({ templateSlug: "", apiKeys: "" });
  const [formData, setFormData] = useState<any /* eslint-disable-line @typescript-eslint/no-explicit-any */>({
    slug: "", name: "", type: "cloud", base_url: "", api_key: "", priority: 100, is_active: true, daily_quota_limit: 1000
  });

  async function fetchSuggestions() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/stats/router-tune`);
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.suggestions);
      }
    } catch (e) {
      console.warn(e);
    }
  };

  async function fetchProviders() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/providers`);
      if (res.ok) setProviders(await res.json());
    } catch (e) {
      console.warn(e);
    }
  };

  async function handleSave() {
    try {
      const url = `${process.env.NEXT_PUBLIC_API_URL}/v1/providers${isEditing && providers.some(p => p.slug === formData.slug) ? `/${formData.slug}` : ''}`;
      const method = "POST";
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setIsEditing(false);
        fetchProviders();
      }
    } catch (e) {
      console.warn(e);
    }
  };

  async function handleBulkAddProviders() {
    if (!bulkData.templateSlug || !bulkData.apiKeys.trim()) return;
    
    const template = PROVIDER_TEMPLATES.find(t => t.slug === bulkData.templateSlug);
    if (!template) return;

    try {
      const keysToCreate = bulkData.apiKeys.split(/[,\n]/).map(k => k.trim()).filter(k => k.length > 0);
      let successCount = 0;
      
      const baseSlug = template.slug;
      
      for (const key of keysToCreate) {
        // Generate a strictly unique slug to avoid HTTP 409 conflicts
        let newSlug = baseSlug;
        let count = 1;
        // Check both local state and newly created ones within this loop to be safe
        // (the API handles checking DB state)
        let uniqueFound = false;
        while (!uniqueFound) {
          // If we want to be perfectly safe, we can just fetch all providers, but using a timestamp or random works too
          // Using count works as long as the UI state `providers` is reasonably up to date.
          const existsInUi = providers.some(p => p.slug === newSlug);
          if (existsInUi) {
            count++;
            newSlug = `${baseSlug}-${count}`;
          } else {
            uniqueFound = true;
          }
        }
        
        // Optimistically add it to our local providers list for the NEXT loop iteration's uniqueness check
        providers.push({ slug: newSlug }); 
        
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/providers`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...template,
            slug: newSlug,
            api_key: key
          })
        });
        successCount++;
      }
      
      setIsBulkAdding(false);
      setBulkData({ templateSlug: "", apiKeys: "" });
      alert(`Successfully added ${successCount} API keys!`);
      fetchProviders();
    } catch (e) {
      console.warn(e);
      alert("Error adding bulk providers");
    }
  }

  async function handleDelete(slug: string) {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/providers/${slug}`, { method: "DELETE" });
      if (res.ok) fetchProviders();
    } catch (e) {
      console.warn(e);
    }
  };

  const maskApiKey = (key: string) => {
    if (!key) return "Not set";
    if (key.length <= 8) return "••••••••";
    return `${key.slice(0, 4)}••••••••${key.slice(-4)}`;
  };


  
  useEffect(() => {
    fetchProviders();
    fetchSuggestions();
  }, []);

  return (
    <div className="h-full overflow-y-auto p-10 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-10">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-300 flex items-center gap-3">
            <Network size={36} className="text-blue-400" /> Providers & Routing
          </h1>
          <p className="text-zinc-400 mt-2 font-medium">Manage LLM APIs and local inference engines for the auto-router.</p>
        </motion.div>
        
        {!isEditing && !isBulkAdding && (
          <div className="flex gap-2">
            <Button 
              onClick={() => {
                setFormData({ slug: "", name: "", type: "cloud", base_url: "", api_key: "", priority: 100, is_active: true, daily_quota_limit: 1000 });
                setIsEditing(true);
              }}
              className="bg-blue-500 hover:bg-blue-600 text-white font-bold rounded-xl px-6 py-5 shadow-lg shadow-blue-500/20"
            >
              <Plus className="mr-2" /> Add Single
            </Button>
            <Button 
              onClick={() => setIsBulkAdding(true)}
              className="bg-indigo-500 hover:bg-indigo-600 text-white font-bold rounded-xl px-6 py-5 shadow-lg shadow-indigo-500/20"
            >
              <Plus className="mr-2" /> Bulk Add Keys
            </Button>
          </div>
        )}
      </div>

      {!isEditing && !isBulkAdding && suggestions.length > 0 && (
        <div className="mb-10 bg-indigo-500/10 border border-indigo-500/30 rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500" />
          <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
            <Settings2 className="text-indigo-400" /> Auto-Tune Suggestions
          </h2>
          <p className="text-sm text-zinc-400 mb-4">Based on recent latency and success rates, the router suggests these priority changes:</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {suggestions.map((s, idx) => {
              const successVal = parseFloat(s.success_rate);
              const latencyVal = parseFloat(s.avg_latency_ms);
              
              const successColor = successVal > 80 ? "text-emerald-400" : successVal > 40 ? "text-amber-400" : "text-red-400";
              const latencyColor = latencyVal < 2000 ? "text-emerald-400" : latencyVal < 10000 ? "text-amber-400" : "text-red-400";
              
              return (
                <div key={idx} className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 flex flex-col gap-1 transition-all hover:bg-zinc-800/50">
                  <span className="font-bold text-white text-base">{s.provider_name}</span>
                  <span className="text-sm text-zinc-400">Suggested Priority: <span className="text-indigo-400 font-bold">{s.suggested_priority}</span></span>
                  <div className="flex items-center gap-4 mt-2 pt-2 border-t border-zinc-800/80 text-xs">
                    <span className={`${successColor} font-semibold flex items-center gap-1`}>
                      {s.success_rate} Success
                    </span>
                    <span className={`${latencyColor} font-semibold flex items-center gap-1`}>
                      {s.avg_latency_ms}ms Avg
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <AnimatePresence mode="wait">
        {isEditing ? (
          <motion.div 
            key="edit"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-[#131316] border border-zinc-800/60 rounded-2xl p-8 shadow-2xl"
          >
            <h2 className="text-xl font-bold text-white mb-6">Configure Provider</h2>
            
            {/* Quick Templates */}
            {!providers.some(p => p.slug === formData.slug) && formData.name === "" && (
              <div className="mb-6">
                <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500 block mb-3">Quick Templates</span>
                <div className="flex flex-wrap gap-2">
                  {PROVIDER_TEMPLATES.map(t => (
                    <button 
                      key={t.slug} 
                      onClick={() => {
                        let newSlug = t.slug;
                        let count = 1;
                        while (providers.some(p => p.slug === newSlug)) {
                          count++;
                          newSlug = `${t.slug}-${count}`;
                        }
                        setFormData({ ...formData, ...t, slug: newSlug });
                      }} 
                      className="px-3 py-1.5 rounded-lg bg-zinc-800 border border-zinc-700 hover:bg-zinc-700 hover:border-zinc-600 text-xs font-medium text-zinc-300 transition-colors"
                    >
                      {t.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Slug (Unique ID)</label>
                <input 
                  type="text" 
                  value={formData.slug} 
                  onChange={e => setFormData({...formData, slug: e.target.value})} 
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none" 
                  placeholder="e.g., openai"
                  disabled={providers.some(p => p.slug === formData.slug) && formData.name !== ""}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Display Name</label>
                <input 
                  type="text" 
                  value={formData.name} 
                  onChange={e => setFormData({...formData, name: e.target.value})} 
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none"
                  placeholder="e.g., OpenAI" 
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Type</label>
                <select 
                  value={formData.type} 
                  onChange={e => setFormData({...formData, type: e.target.value})}
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none"
                >
                  <option value="cloud">Cloud API</option>
                  <option value="local">Local Engine</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Priority (Lower is preferred)</label>
                <input 
                  type="number" 
                  value={formData.priority} 
                  onChange={e => setFormData({...formData, priority: parseInt(e.target.value)})} 
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none" 
                />
              </div>
              <div className="space-y-2 col-span-2">
                <label className="text-sm font-medium text-zinc-400">API Key</label>
                <input 
                  type="password" 
                  value={formData.api_key} 
                  onChange={e => setFormData({...formData, api_key: e.target.value})} 
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none"
                  placeholder="sk-..." 
                />
              </div>
              <div className="space-y-2 col-span-2">
                <label className="text-sm font-medium text-zinc-400">Base URL (Optional)</label>
                <input 
                  type="text" 
                  value={formData.base_url || ""} 
                  onChange={e => setFormData({...formData, base_url: e.target.value})} 
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none"
                  placeholder="https://api.openai.com/v1" 
                />
              </div>
              <div className="space-y-2 col-span-2">
                <label className="text-sm font-medium text-zinc-400">Daily Quota Limit</label>
                <input 
                  type="number" 
                  value={formData.daily_quota_limit || ""} 
                  onChange={e => setFormData({...formData, daily_quota_limit: parseInt(e.target.value) || null})} 
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500/50 outline-none"
                  placeholder="Leave empty for unlimited" 
                />
              </div>
            </div>
            <div className="mt-8 flex gap-4 justify-end">
              <Button variant="ghost" onClick={() => setIsEditing(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={handleSave} className="bg-blue-500 hover:bg-blue-600 text-white font-bold rounded-lg px-6">Save Provider</Button>
            </div>
          </motion.div>
        ) : isBulkAdding ? (
          <motion.div 
            key="bulk"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-[#131316] border border-zinc-800/60 rounded-2xl p-8 shadow-2xl"
          >
            <h2 className="text-xl font-bold text-white mb-6">Bulk Add API Keys</h2>
            
            <div className="grid grid-cols-1 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Select Provider Template</label>
                <select 
                  value={bulkData.templateSlug} 
                  onChange={e => setBulkData({...bulkData, templateSlug: e.target.value})}
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-indigo-500/50 outline-none"
                >
                  <option value="" disabled>Select a template</option>
                  {PROVIDER_TEMPLATES.map(t => (
                    <option key={t.slug} value={t.slug}>{t.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Paste API Keys (comma or newline separated)</label>
                <textarea 
                  value={bulkData.apiKeys} 
                  onChange={e => setBulkData({...bulkData, apiKeys: e.target.value})} 
                  placeholder="sk-key1&#10;sk-key2&#10;sk-key3"
                  className="w-full h-48 bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white font-mono focus:ring-2 focus:ring-indigo-500/50 outline-none resize-none" 
                />
              </div>
            </div>
            <div className="mt-8 flex gap-4 justify-end">
              <Button variant="ghost" onClick={() => setIsBulkAdding(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={handleBulkAddProviders} className="bg-indigo-500 hover:bg-indigo-600 text-white font-bold rounded-lg px-6">Bulk Add {bulkData.apiKeys.split(/[,\n]/).filter(k=>k.trim().length>0).length || 0} Keys</Button>
            </div>
          </motion.div>
        ) : (
          <motion.div key="list" className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {providers.map((provider) => (
              <div key={provider.id} className="bg-[#131316] border border-zinc-800/60 rounded-2xl p-6 shadow-xl relative group">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-3 rounded-xl ${provider.type === 'local' ? 'bg-purple-500/10 text-purple-400' : 'bg-blue-500/10 text-blue-400'}`}>
                      {provider.type === 'local' ? <Server size={20} /> : <Cloud size={20} />}
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        {provider.name}
                      </h3>
                      <div className="flex gap-2 mt-1">
                        <span className="text-[10px] bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded uppercase font-semibold">Priority: {provider.priority}</span>
                        {provider.is_rate_limited ? (
                          <span className="text-[10px] bg-red-500/20 text-red-400 px-2 py-0.5 rounded uppercase font-semibold border border-red-500/30">Rate Limited</span>
                        ) : (provider.daily_quota_limit && provider.daily_quota_used >= provider.daily_quota_limit * 0.9) ? (
                          <span className="text-[10px] bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded uppercase font-semibold border border-amber-500/30">Near Limit</span>
                        ) : (
                          <span className="text-[10px] bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded uppercase font-semibold border border-emerald-500/30">Healthy</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      onClick={() => {
                        setFormData(provider);
                        setIsEditing(true);
                      }} 
                      className="p-2 bg-zinc-800/50 hover:bg-zinc-700 rounded-lg text-zinc-400 transition-colors"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button 
                      onClick={() => handleDelete(provider.slug)} 
                      className="p-2 bg-red-500/10 hover:bg-red-500/20 rounded-lg text-red-400 transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                
                <div className="space-y-3 bg-zinc-900/30 rounded-xl p-4 border border-zinc-800/40">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-zinc-500 flex items-center gap-2"><Key size={14}/> API Key</span>
                    <span className="font-mono text-zinc-300 bg-zinc-800/50 px-2 py-0.5 rounded">{maskApiKey(provider.api_key)}</span>
                  </div>
                  {provider.base_url && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-zinc-500">Base URL</span>
                      <span className="text-zinc-400 truncate max-w-[180px]">{provider.base_url}</span>
                    </div>
                  )}
                  {provider.daily_quota_limit && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-zinc-500">Daily Quota</span>
                      <span className="text-zinc-400">{provider.daily_quota_used || 0} / {provider.daily_quota_limit}</span>
                    </div>
                  )}
                  {provider.is_rate_limited && (
                    <div className="mt-3 p-2 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-400/90 flex items-center justify-between">
                      <span>Currently Rate Limited</span>
                      <span>Resets soon</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {providers.length === 0 && (
              <div className="col-span-full py-20 text-center border-2 border-dashed border-zinc-800/50 rounded-3xl">
                <Network className="mx-auto h-12 w-12 text-zinc-700 mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">No Providers Configured</h3>
                <p className="text-zinc-500">Add a provider to enable AI routing.</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
