"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Server, RefreshCw, Cpu, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const getProviderTheme = (slug: string, type: string) => {
  if (!slug) return { color: "text-zinc-400", bg: "bg-zinc-500/10", border: "border-zinc-500/20" };
  const s = slug.toLowerCase();
  if (s.includes("lmstudio") || s.includes("lm-studio")) return { color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" };
  if (s.includes("ollama")) return { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" };
  if (s.includes("openai")) return { color: "text-purple-400", bg: "bg-purple-500/10", border: "border-purple-500/20" };
  if (s.includes("anthropic") || s.includes("claude")) return { color: "text-orange-400", bg: "bg-orange-500/10", border: "border-orange-500/20" };
  if (type === "local") return { color: "text-cyan-400", bg: "bg-cyan-500/10", border: "border-cyan-500/20" };
  return { color: "text-zinc-400", bg: "bg-zinc-500/10", border: "border-zinc-500/20" };
};

export default function ModelsPage() {
  const [models, setModels] = useState<any[]>([]);
  const [providers, setProviders] = useState<any[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [isBulkAdding, setIsBulkAdding] = useState(false);
  const [newModel, setNewModel] = useState({ provider_id: "", model_name: "", display_name: "", size_gb: 0 });
  const [bulkModels, setBulkModels] = useState({ provider_id: "", model_names: "" });

  async function fetchProviders() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/providers`);
      if (res.ok) setProviders(await res.json());
    } catch (e) {
      console.warn(e);
    }
  }

  async function handleAddModel() {
    if (!newModel.provider_id || !newModel.model_name || !newModel.display_name) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/models`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider_id: parseInt(newModel.provider_id),
          model_name: newModel.model_name,
          display_name: newModel.display_name,
          size_gb: newModel.size_gb
        })
      });
      if (res.ok) {
        setIsAdding(false);
        setNewModel({ provider_id: "", model_name: "", display_name: "", size_gb: 0 });
        fetchModels();
      }
    } catch (e) {
      console.warn(e);
    }
  }

  async function handleBulkAddModel() {
    if (!bulkModels.provider_id || !bulkModels.model_names.trim()) return;
    try {
      const modelsToCreate = bulkModels.model_names.split(",").map(m => m.trim()).filter(m => m.length > 0);
      let successCount = 0;
      
      for (const modelId of modelsToCreate) {
        // Auto-generate a readable display name based on the model ID
        const displayName = modelId.split("/").pop()?.replace(/-/g, " ") || modelId;
        
        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/models`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider_id: parseInt(bulkModels.provider_id),
            model_name: modelId,
            display_name: displayName.toUpperCase()
          })
        });
        successCount++;
      }
      
      setIsBulkAdding(false);
      setBulkModels({ provider_id: "", model_names: "" });
      alert(`Successfully added ${successCount} models!`);
      fetchModels();
    } catch (e) {
      console.warn(e);
      alert("Error adding bulk models");
    }
  }

  async function fetchModels() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/models`);
      if (res.ok) {
        const data = await res.json();
        setModels(Array.isArray(data) ? data : data.data || []);
      }
    } catch (e) {
      console.warn(e);
    }
  };

  async function handleDeleteModel(modelId: number) {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/models/${modelId}`, { method: "DELETE" });
      if (res.ok) fetchModels();
    } catch (e) {
      console.warn(e);
    }
  }

  async function syncModels() {
    setIsSyncing(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/models/sync`, { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        if (data.errors && data.errors.length > 0) {
          alert("Sync finished with errors:\n" + data.errors.join("\n"));
        } else if (data.synced > 0) {
          alert(`Successfully synced ${data.synced} new models!`);
        } else {
          alert("Sync finished. No new models found (or all are already synced).");
        }
        fetchModels();
      }
    } catch (e: any) {
      console.warn(e);
      alert("Failed to reach sync endpoint: " + e.message);
    } finally {
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    fetchModels();
    fetchProviders();
  }, []);

  return (
    <div className="h-full overflow-y-auto p-10 max-w-7xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10 flex items-end justify-between"
      >
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
            Model Manager
          </h1>
          <p className="text-zinc-400 mt-2 font-medium">Dynamically synced from your active local providers.</p>
        </div>
        <div className="flex items-center gap-2">
          {!isAdding && !isBulkAdding && (
            <>
              <Button 
                onClick={() => setIsAdding(true)} 
                className="bg-blue-500 hover:bg-blue-600 text-white gap-2 h-10 px-4 rounded-xl"
              >
                + Add Single
              </Button>
              <Button 
                onClick={() => setIsBulkAdding(true)} 
                className="bg-indigo-500 hover:bg-indigo-600 text-white gap-2 h-10 px-4 rounded-xl"
              >
                + Bulk Add
              </Button>
            </>
          )}
          <Button 
            onClick={syncModels} 
            disabled={isSyncing}
            className="bg-white/5 border border-white/10 hover:bg-white/10 text-white gap-2 h-10 px-4 rounded-xl"
          >
            <RefreshCw size={16} className={isSyncing ? "animate-spin" : ""} />
            {isSyncing ? "Syncing..." : "Sync Local Models"}
          </Button>
        </div>
      </motion.div>

      <AnimatePresence>
        {isAdding && (
          <motion.div 
            initial={{ opacity: 0, height: 0, marginBottom: 0 }}
            animate={{ opacity: 1, height: "auto", marginBottom: 24 }}
            exit={{ opacity: 0, height: 0, marginBottom: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-[#131316] border border-zinc-800/60 rounded-2xl p-6 shadow-xl flex items-end gap-4">
              <div className="flex-1 space-y-2">
                <label className="text-sm font-medium text-zinc-400">Provider</label>
                <select 
                  value={newModel.provider_id} 
                  onChange={e => setNewModel({...newModel, provider_id: e.target.value})}
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 outline-none"
                >
                  <option value="" disabled>Select a provider</option>
                  {providers.map(p => (
                    <option key={p.id} value={p.id}>{p.name} ({p.slug})</option>
                  ))}
                </select>
              </div>
              <div className="flex-1 space-y-2">
                <label className="text-sm font-medium text-zinc-400">Model ID (e.g. gpt-4o)</label>
                <input 
                  type="text" 
                  value={newModel.model_name} 
                  onChange={e => setNewModel({...newModel, model_name: e.target.value})} 
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 outline-none" 
                />
              </div>
              <div className="flex-1 space-y-2">
                <label className="text-sm font-medium text-zinc-400">Display Name</label>
                <input 
                  type="text" 
                  value={newModel.display_name} 
                  onChange={e => setNewModel({...newModel, display_name: e.target.value})} 
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 outline-none" 
                />
              </div>
              <div className="w-24 space-y-2">
                <label className="text-sm font-medium text-zinc-400">Size (GB)</label>
                <input 
                  type="number" 
                  step="0.1"
                  value={newModel.size_gb || ""} 
                  onChange={e => setNewModel({...newModel, size_gb: parseFloat(e.target.value) || 0})} 
                  placeholder="Optional"
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 outline-none" 
                />
              </div>
              <Button onClick={handleAddModel} className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold h-[42px] px-6">
                Save
              </Button>
              <Button onClick={() => setIsAdding(false)} variant="ghost" className="text-zinc-400 h-[42px]">
                Cancel
              </Button>
            </div>
          </motion.div>
        )}
        
        {isBulkAdding && (
          <motion.div 
            initial={{ opacity: 0, height: 0, marginBottom: 0 }}
            animate={{ opacity: 1, height: "auto", marginBottom: 24 }}
            exit={{ opacity: 0, height: 0, marginBottom: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-[#131316] border border-zinc-800/60 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
              <div className="flex gap-4">
                <div className="w-1/3 space-y-2">
                  <label className="text-sm font-medium text-zinc-400">Provider</label>
                  <select 
                    value={bulkModels.provider_id} 
                    onChange={e => setBulkModels({...bulkModels, provider_id: e.target.value})}
                    className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 outline-none"
                  >
                    <option value="" disabled>Select a provider</option>
                    {providers.map(p => (
                      <option key={p.id} value={p.id}>{p.name} ({p.slug})</option>
                    ))}
                  </select>
                </div>
                <div className="flex-1 space-y-2">
                  <label className="text-sm font-medium text-zinc-400">Paste Comma-Separated Models</label>
                  <textarea 
                    value={bulkModels.model_names} 
                    onChange={e => setBulkModels({...bulkModels, model_names: e.target.value})} 
                    placeholder="e.g. google/gemma-4-31b-it, openai/gpt-4o, anthropic/claude-3.5-sonnet"
                    className="w-full h-24 bg-zinc-900/50 border border-zinc-800 rounded-lg p-2.5 text-white focus:ring-2 focus:ring-blue-500/50 outline-none resize-none" 
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button onClick={() => setIsBulkAdding(false)} variant="ghost" className="text-zinc-400 h-[42px]">
                  Cancel
                </Button>
                <Button onClick={handleBulkAddModel} className="bg-indigo-500 hover:bg-indigo-600 text-white font-bold h-[42px] px-6">
                  Bulk Add Models
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pb-20">
        {models.map((model, i) => {
          const theme = getProviderTheme(model.provider_slug, model.provider_type);
          return (
            <motion.div 
              key={model.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="p-4 rounded-xl bg-white/[0.02] border border-white/5 backdrop-blur-sm flex flex-col justify-between hover:bg-white/[0.04] transition-colors group"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center border ${theme.bg} ${theme.border}`}>
                  <Server className={theme.color} size={16} />
                </div>
                <div className="flex flex-col truncate">
                  <span className="text-xs font-bold text-zinc-500 uppercase tracking-wider">{model.provider_name}</span>
                  <span className="text-sm font-semibold text-white truncate" title={model.model_name}>{model.display_name || model.model_name}</span>
                </div>
              </div>
              <div className="flex justify-between items-end mt-auto gap-2">
                <span className="text-[10px] font-bold tracking-widest px-2 py-0.5 bg-white/5 text-zinc-400 rounded-md uppercase border border-white/5 truncate">
                  ID: {model.model_name ? model.model_name.split("/").pop() : "unknown"}
                </span>
                <div className="flex items-center gap-1">
                  <button 
                    onClick={async () => {
                      const newSize = prompt("Enter Size in GB (e.g., 18.5) for hardware routing:", model.size_gb?.toString() || "");
                      if (newSize !== null) {
                        const sizeFloat = parseFloat(newSize) || 0;
                        await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/models/${model.id}`, {
                          method: "PUT",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ size_gb: sizeFloat })
                        });
                        fetchModels();
                      }
                    }}
                    className="p-1.5 px-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-lg text-[10px] font-bold tracking-widest uppercase transition-colors opacity-0 group-hover:opacity-100"
                    title="Override model size"
                  >
                    {model.size_gb > 0 ? `${model.size_gb}GB` : "Set Size"}
                  </button>
                  <button 
                    onClick={() => handleDeleteModel(model.id)}
                    className="p-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                    title="Delete model"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </motion.div>
          );
        })}
        {models.length === 0 && !isSyncing && (
          <div className="col-span-full py-24 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-2xl bg-white/[0.01]">
            <Cpu size={48} className="text-zinc-600 mb-6" />
            <h2 className="text-xl font-semibold text-white mb-2">No models found</h2>
            <p className="text-zinc-400 font-medium text-center">Enable a provider like LM Studio in the Providers tab<br/>and click Sync Local Models.</p>
          </div>
        )}
      </div>
    </div>
  );
}
