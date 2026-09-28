"use client";

import { useState, useEffect } from "react";
import { Plus, Search, Trash2, Edit2, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Skill {
  id: number;
  name: string;
  content: string;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  
  // For Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);
  const [formData, setFormData] = useState({ name: "", content: "" });

  const fetchSkills = async () => {
    try {
      const res = await fetch(`${API}/v1/skills`);
      const data = await res.json();
      setSkills(data);
    } catch (err) {
      console.error("Failed to fetch skills", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSkills();
  }, []);

  const handleSave = async () => {
    try {
      const url = editingSkill 
        ? `${API}/v1/skills/${editingSkill.id}` 
        : `${API}/v1/skills`;
        
      const res = await fetch(url, {
        method: editingSkill ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      
      if (res.ok) {
        setIsModalOpen(false);
        fetchSkills();
      } else {
        const err = await res.json();
        alert(err.detail || "Error saving skill");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this skill?")) return;
    try {
      await fetch(`${API}/v1/skills/${id}`, { method: "DELETE" });
      fetchSkills();
    } catch (e) {
      console.error(e);
    }
  };

  const openModal = (skill?: Skill) => {
    if (skill) {
      setEditingSkill(skill);
      setFormData({ name: skill.name, content: skill.content });
    } else {
      setEditingSkill(null);
      setFormData({ name: "", content: "" });
    }
    setIsModalOpen(true);
  };

  const filteredSkills = skills.filter(s => s.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="flex-1 h-full flex flex-col min-w-0 bg-[#0A0A0C]">
      {/* Header */}
      <header className="h-14 border-b border-zinc-800/50 bg-[#0A0A0C]/80 backdrop-blur-xl flex items-center justify-between px-6 shrink-0 sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <Zap className="w-5 h-5 text-amber-400" />
          <h1 className="font-semibold text-sm tracking-wide text-zinc-100">Discrete Skills</h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search skills..."
              className="w-[250px] pl-9 h-8 bg-zinc-900/50 border-zinc-800/50 focus-visible:ring-amber-500/20 placeholder:text-zinc-600 text-xs"
            />
          </div>
          <Button 
            onClick={() => openModal()}
            size="sm" 
            className="h-8 gap-2 bg-amber-500 hover:bg-amber-600 text-white border-0"
          >
            <Plus className="w-4 h-4" />
            New Skill
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {loading ? (
              <div className="col-span-full text-center text-zinc-500 text-sm mt-10">Loading skills...</div>
            ) : filteredSkills.length === 0 ? (
              <div className="col-span-full text-center text-zinc-500 text-sm mt-10">
                No skills found. Sync from ECC or create your first skill!
              </div>
            ) : (
              filteredSkills.map(skill => (
                <div key={skill.id} className="bg-[#131316] rounded-xl border border-zinc-800/50 p-5 flex flex-col gap-4 group">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                        <Zap className="w-4 h-4 text-amber-400" />
                      </div>
                      <h3 className="font-medium text-zinc-100 text-sm">{skill.name}</h3>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button variant="ghost" size="icon" className="w-7 h-7 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800" onClick={() => openModal(skill)}>
                        <Edit2 className="w-3 h-3" />
                      </Button>
                      <Button variant="ghost" size="icon" className="w-7 h-7 text-red-400 hover:text-red-300 hover:bg-red-400/10" onClick={() => handleDelete(skill.id)}>
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                  
                  <div className="text-xs text-zinc-400 line-clamp-3 bg-zinc-900/50 p-3 rounded-lg border border-zinc-800/30 whitespace-pre-wrap">
                    {skill.content}
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
                {editingSkill ? "Edit Skill" : "Create Skill"}
              </h2>
            </div>
            <div className="p-5 flex flex-col gap-5">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-400">Skill Name</label>
                <Input 
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g. Next.js Routing"
                  className="bg-zinc-900/50 border-zinc-800 focus-visible:ring-amber-500/20 text-sm"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-zinc-400">Skill Content</label>
                <textarea 
                  value={formData.content}
                  onChange={e => setFormData({...formData, content: e.target.value})}
                  placeholder="Instructions for this skill..."
                  className="w-full h-40 bg-zinc-900/50 border border-zinc-800 focus:border-zinc-700 focus:ring-1 focus:ring-amber-500/20 rounded-md p-3 text-sm text-zinc-100 outline-none resize-none font-mono"
                />
              </div>
            </div>
            <div className="px-5 py-4 border-t border-zinc-800/50 bg-zinc-900/20 flex items-center justify-end gap-3">
              <Button variant="ghost" onClick={() => setIsModalOpen(false)} className="text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800">
                Cancel
              </Button>
              <Button onClick={handleSave} className="bg-amber-500 hover:bg-amber-600 text-white">
                {editingSkill ? "Save Changes" : "Create Skill"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
