"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BookTemplate, Plus, Trash2, Edit2, CheckCircle2, FileText, Settings2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const Github = ({ className, size = 24 }: { className?: string, size?: number }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
    <path d="M9 18c-4.51 2-5-2-7-2" />
  </svg>
);

export default function PromptsPage() {
  const [prompts, setPrompts] = useState<any[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<any /* eslint-disable-line @typescript-eslint/no-explicit-any */>({
    id: null, name: "", content: "", tags: [], is_default: false
  });
  const [isSyncing, setIsSyncing] = useState(false);
  const [eccStats, setEccStats] = useState<any /* eslint-disable-line @typescript-eslint/no-explicit-any */>(null);

  async function fetchPrompts() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/prompts`);
      if (res.ok) setPrompts(await res.json());
      
      const statsRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/ecc/status`);
      if (statsRes.ok) setEccStats(await statsRes.json());
    } catch (e) {
      console.warn(e);
    }
  };

  async function handleEccSync() {
    setIsSyncing(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/ecc/sync`, { method: "POST" });
      if (res.ok) {
        await fetchPrompts();
      }
    } catch (e) {
      console.warn("Failed to sync ECC", e);
    } finally {
      setIsSyncing(false);
    }
  };

  async function handleSave() {
    try {
      const url = `${process.env.NEXT_PUBLIC_API_URL}/v1/prompts${formData.id ? `/${formData.id}` : ''}`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        setIsEditing(false);
        fetchPrompts();
      }
    } catch (e) {
      console.warn(e);
    }
  };

  async function handleDelete(id: number) {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/prompts/${id}`, { method: "DELETE" });
      if (res.ok) fetchPrompts();
    } catch (e) {
      console.warn(e);
    }
  };


  
  useEffect(() => {
    fetchPrompts();
  }, []);

  return (
    <div className="h-full overflow-y-auto p-10 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-10">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
          <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-teal-300 flex items-center gap-3">
            <BookTemplate size={36} className="text-emerald-400" /> Prompt Library
          </h1>
          <p className="text-zinc-400 mt-2 font-medium">Manage reusable, provider-agnostic system prompts.</p>
        </motion.div>
        
        {!isEditing && (
          <div className="flex items-center gap-4">
            <Button 
              onClick={handleEccSync}
              disabled={isSyncing}
              className="bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-bold rounded-xl px-6 py-5 shadow-lg border border-zinc-700"
            >
              {isSyncing ? <Loader2 className="mr-2 animate-spin" /> : <Github className="mr-2" />}
              {isSyncing ? "Syncing ECC..." : "Sync ECC Hub"}
            </Button>
            <Button 
              onClick={() => {
                setFormData({ id: null, name: "", content: "", tags: [], is_default: false });
                setIsEditing(true);
              }}
              className="bg-emerald-500 hover:bg-emerald-600 text-[#050505] font-bold rounded-xl px-6 py-5 shadow-lg shadow-emerald-500/20"
            >
              <Plus className="mr-2" /> New Template
            </Button>
          </div>
        )}
      </div>

      <AnimatePresence mode="wait">
        {isEditing ? (
          <motion.div 
            key="edit"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-[#131316] border border-zinc-800/60 rounded-2xl p-8 shadow-2xl"
          >
            <h2 className="text-xl font-bold text-white mb-6">{formData.id ? "Edit Template" : "New Template"}</h2>
            <div className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Template Name</label>
                <input 
                  type="text" 
                  value={formData.name} 
                  onChange={e => setFormData({...formData, name: e.target.value})} 
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-emerald-500/50 outline-none" 
                  placeholder="e.g., Coding Assistant"
                />
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">System Prompt</label>
                <textarea 
                  value={formData.content} 
                  onChange={e => setFormData({...formData, content: e.target.value})} 
                  rows={8}
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-emerald-500/50 outline-none resize-y"
                  placeholder="You are a helpful assistant..." 
                />
              </div>

              <div className="flex items-center gap-3">
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" className="sr-only peer" checked={formData.is_default} onChange={() => setFormData({...formData, is_default: !formData.is_default})} />
                  <div className="w-11 h-6 bg-zinc-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                </label>
                <span className="text-sm font-medium text-zinc-300">Set as default system prompt</span>
              </div>
            </div>
            
            <div className="mt-8 flex gap-4 justify-end">
              <Button variant="ghost" onClick={() => setIsEditing(false)} className="text-zinc-400">Cancel</Button>
              <Button onClick={handleSave} className="bg-emerald-500 hover:bg-emerald-600 text-[#050505] font-bold rounded-lg px-6">Save Template</Button>
            </div>
          </motion.div>
        ) : (
          <motion.div key="list" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {prompts.map((prompt) => (
              <div key={prompt.id} className="bg-[#131316] border border-zinc-800/60 rounded-2xl p-6 shadow-xl relative group flex flex-col h-64">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
                      <FileText size={20} />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-white flex items-center gap-2 line-clamp-1">
                        {prompt.name}
                        {prompt.is_default && <span title="Default Prompt"><CheckCircle2 size={14} className="text-emerald-500" /></span>}
                      </h3>
                      {prompt.tags && prompt.tags.includes("ecc-") && (
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/20 mt-1 inline-block">
                          {prompt.tags}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      onClick={() => {
                        setFormData(prompt);
                        setIsEditing(true);
                      }} 
                      className="p-2 bg-zinc-800/50 hover:bg-zinc-700 rounded-lg text-zinc-400 transition-colors"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button 
                      onClick={() => handleDelete(prompt.id)} 
                      className="p-2 bg-red-500/10 hover:bg-red-500/20 rounded-lg text-red-400 transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                
                <div className="flex-1 bg-zinc-900/30 rounded-xl p-4 border border-zinc-800/40 overflow-hidden text-sm text-zinc-400 whitespace-pre-wrap relative">
                  {prompt.content}
                  <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-[#16161a] to-transparent pointer-events-none" />
                </div>
              </div>
            ))}
            
            {prompts.length === 0 && (
              <div className="col-span-full py-20 text-center border-2 border-dashed border-zinc-800/50 rounded-3xl">
                <BookTemplate className="mx-auto h-12 w-12 text-zinc-700 mb-4" />
                <h3 className="text-lg font-bold text-white mb-2">No Prompts Found</h3>
                <p className="text-zinc-500">Create a reusable template to instruct your AI models.</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
