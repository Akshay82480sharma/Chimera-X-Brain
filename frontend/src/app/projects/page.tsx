"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Layers, Plus, FolderGit2, Trash2 } from "lucide-react";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [isAdding, setIsAdding] = useState(false);
  const [newProject, setNewProject] = useState({ name: "", description: "" });

  async function fetchProjects() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/projects`);
      if (res.ok) setProjects(await res.json());
    } catch (e) {
      console.warn(e);
    }
  }

  useEffect(() => {
    fetchProjects();
  }, []);

  async function handleSave() {
    if (!newProject.name) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/projects?name=${encodeURIComponent(newProject.name)}&description=${encodeURIComponent(newProject.description)}`, {
        method: "POST"
      });
      if (res.ok) {
        setIsAdding(false);
        setNewProject({ name: "", description: "" });
        fetchProjects();
      }
    } catch (e) {
      console.warn(e);
    }
  }

  async function handleDelete(id: number) {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/projects/${id}`, { method: "DELETE" });
      if (res.ok) fetchProjects();
    } catch (e) {
      console.warn(e);
    }
  }
  return (
    <div className="h-full overflow-y-auto p-10 max-w-7xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10 flex items-end justify-between"
      >
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60 flex items-center gap-3">
            <Layers size={36} className="text-indigo-400" /> Workspaces & Projects
          </h1>
          <p className="text-zinc-400 mt-2 font-medium">Manage your active coding environments and context.</p>
        </div>
        {!isAdding && (
          <button 
            onClick={() => setIsAdding(true)} 
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl font-medium transition-colors shadow-lg shadow-indigo-500/20"
          >
            <Plus className="w-5 h-5" />
            New Project
          </button>
        )}
      </motion.div>

      <AnimatePresence mode="wait">
        {isAdding ? (
          <motion.div 
            key="add-form"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-[#131316] border border-zinc-800/60 rounded-2xl p-8 shadow-2xl mb-8"
          >
            <h2 className="text-xl font-bold text-white mb-6">Create New Workspace</h2>
            
            <div className="grid grid-cols-1 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Project Name</label>
                <input 
                  type="text" 
                  value={newProject.name} 
                  onChange={e => setNewProject({...newProject, name: e.target.value})} 
                  className="w-full bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-indigo-500/50 outline-none" 
                  placeholder="e.g., Chimera-X"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-zinc-400">Description</label>
                <textarea 
                  value={newProject.description} 
                  onChange={e => setNewProject({...newProject, description: e.target.value})} 
                  className="w-full h-24 bg-zinc-900/50 border border-zinc-800 rounded-lg p-3 text-white focus:ring-2 focus:ring-indigo-500/50 outline-none resize-none" 
                  placeholder="A brief description of this workspace..."
                />
              </div>
            </div>
            <div className="mt-8 flex gap-4 justify-end">
              <button onClick={() => setIsAdding(false)} className="px-6 py-2.5 text-zinc-400 hover:text-white transition-colors">Cancel</button>
              <button onClick={handleSave} className="bg-indigo-500 hover:bg-indigo-600 text-white font-bold rounded-lg px-6 py-2.5 transition-colors">Create Project</button>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {projects.map((project, i) => (
            <motion.div 
              key={project.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ delay: i * 0.05 }}
              className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 backdrop-blur-sm group cursor-pointer hover:bg-white/[0.04] transition-all relative overflow-hidden"
            >
              <div className="absolute -top-10 -right-10 w-32 h-32 blur-[50px] rounded-full bg-indigo-500/5 group-hover:bg-indigo-500/10 transition-colors pointer-events-none" />
              
              <div className="flex justify-between items-start mb-4 relative z-10">
                <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                  <FolderGit2 className="w-6 h-6 text-indigo-400" />
                </div>
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(project.id);
                    }}
                    className="p-2 bg-red-500/10 hover:bg-red-500/20 rounded-lg text-red-400 transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              <h3 className="text-xl font-bold text-white mb-2 relative z-10">{project.name}</h3>
              <p className="text-sm text-zinc-400 mb-4 relative z-10">{project.description || "No description provided."}</p>
              <div className="flex gap-2 relative z-10">
                <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded uppercase border border-emerald-500/20">
                  Workspace Ready
                </span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {projects.length === 0 && !isAdding && (
          <div className="col-span-full py-24 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-3xl bg-white/[0.01]">
            <FolderGit2 size={48} className="text-zinc-600 mb-6" />
            <h2 className="text-xl font-semibold text-white mb-2">No Projects Found</h2>
            <p className="text-zinc-400 font-medium text-center">Create your first workspace to start organizing your files and context.</p>
          </div>
        )}
      </div>
    </div>
  );
}
