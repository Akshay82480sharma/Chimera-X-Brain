"use client";

import { useState, useEffect } from "react";
import { Plus, Search, Trash2, Edit2, Bot, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface Agent {
  id: number;
  name: string;
  system_prompt: string;
  tools_allowed: number[];
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  
  // For Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [formData, setFormData] = useState({ name: "", system_prompt: "" });

  const fetchAgents = async () => {
    try {
      const res = await fetch(`${API}/v1/agents`);
      const data = await res.json();
      setAgents(data);
    } catch (err) {
      console.error("Failed to fetch agents", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleSave = async () => {
    try {
      const url = editingAgent 
        ? `${API}/v1/agents/${editingAgent.id}` 
        : `${API}/v1/agents`;
        
      const res = await fetch(url, {
        method: editingAgent ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      
      if (res.ok) {
        setIsModalOpen(false);
        fetchAgents();
      } else {
        const err = await res.json();
        alert(err.detail || "Error saving agent");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this agent?")) return;
    try {
      await fetch(`${API}/v1/agents/${id}`, { method: "DELETE" });
      fetchAgents();
    } catch (e) {
      console.error(e);
    }
  };

  const openModal = (agent?: Agent) => {
    if (agent) {
      setEditingAgent(agent);
      setFormData({ name: agent.name, system_prompt: agent.system_prompt });
    } else {
      setEditingAgent(null);
      setFormData({ name: "", system_prompt: "" });
    }
    setIsModalOpen(true);
  };

  const filteredAgents = agents.filter(a => a.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="flex-1 h-full flex flex-col min-w-0 bg-[#0A0A0C]">
      {/* Header */}
      <header className="h-14 border-b border-zinc-800/50 bg-[#0A0A0C]/80 backdrop-blur-xl flex items-center justify-between px-6 shrink-0 sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <Bot className="w-5 h-5 text-zinc-400" />
          <h1 className="font-semibold text-sm tracking-wide text-zinc-100">Dynamic Agent Factory</h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search agents..."
              className="w-[250px] pl-9 h-8 bg-zinc-900/50 border-zinc-800/50 focus-visible:ring-emerald-500/20 placeholder:text-zinc-600 text-xs"
            />
          </div>
          <Button 
            onClick={() => openModal()}
            size="sm" 
            className="h-8 gap-2 bg-emerald-500 hover:bg-emerald-600 text-white border-0"
          >
            <Plus className="w-4 h-4" />
            New Agent
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {loading ? (
              <div className="col-span-full text-center text-zinc-500 text-sm mt-10">Loading agents...</div>
            ) : filteredAgents.length === 0 ? (
              <div className="col-span-full text-center text-zinc-500 text-sm mt-10">
                No agents found. Create your first specialized agent!
              </div>
            ) : (
              filteredAgents.map(agent => (
                <div key={agent.id} className="bg-[#131316] rounded-xl border border-zinc-800/50 p-5 flex flex-col gap-4 group">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                        <Bot className="w-4 h-4 text-emerald-400" />
                      </div>
                      <h3 className="font-medium text-zinc-100 text-sm">{agent.name}</h3>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button variant="ghost" size="icon" className="w-7 h-7 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800" onClick={() => openModal(agent)}>
                        <Edit2 className="w-3 h-3" />
                      </Button>
                      <Button variant="ghost" size="icon" className="w-7 h-7 text-red-400 hover:text-red-300 hover:bg-red-400/10" onClick={() => handleDelete(agent.id)}>
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                  
                  <div className="text-xs text-zinc-400 line-clamp-3 bg-zinc-900/50 p-3 rounded-lg border border-zinc-800/30">
                    {agent.system_prompt}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#131316] border border-zinc-800/80 rounded-xl w-full max-w-lg shadow-2xl flex flex-col overflow-hidden">
            <div className="px-5 py-4 border-b border-zinc-800/50 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-zinc-100">
                {editingAgent ? "Edit Agent" : "Create Specialized Agent"}
              </h2>
            </div>
            <div className="p-5 flex flex-col gap-5">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-400">Agent Name</label>
                <Input 
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g. Backend Architect"
                  className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-emerald-500/20 text-sm"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-400">System Prompt / Persona</label>
                <textarea 
                  value={formData.system_prompt}
                  onChange={e => setFormData({...formData, system_prompt: e.target.value})}
                  placeholder="You are an expert Backend Architect..."
                  className="w-full h-40 bg-zinc-900/50 border border-zinc-800 focus:border-zinc-700 focus:ring-1 focus:ring-emerald-500/20 rounded-md p-3 text-sm text-zinc-100 outline-none resize-none"
                />
              </div>
            </div>
            <div className="px-5 py-4 border-t border-zinc-800/50 bg-zinc-900/20 flex items-center justify-end gap-3">
              <Button variant="ghost" onClick={() => setIsModalOpen(false)} className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800">
                Cancel
              </Button>
              <Button onClick={handleSave} className="bg-emerald-500 hover:bg-emerald-600 text-white">
                {editingAgent ? "Save Changes" : "Create Agent"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
