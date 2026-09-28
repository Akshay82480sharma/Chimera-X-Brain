"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Database, Trash2, BrainCircuit } from "lucide-react";

export default function MemoryPage() {
  const [memories, setMemories] = useState<any[]>([]);

  async function fetchMemory() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/memory`);
      if (res.ok) setMemories(await res.json());
    } catch (e) {
      console.warn(e);
    }
  };

  async function deleteMemory(id: number) {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/memory/${id}`, { method: "DELETE" });
      if (res.ok) fetchMemory();
    } catch (e) {
      console.warn(e);
    }
  };



  useEffect(() => {
    fetchMemory();
  }, []);

  return (
    <div className="h-full overflow-y-auto p-10 max-w-7xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10"
      >
        <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-teal-300 flex items-center gap-3">
          <Database size={36} className="text-emerald-400" /> Persistent Memory
        </h1>
        <p className="text-zinc-400 mt-2 font-medium">Facts automatically extracted from your conversations.</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pb-20">
        <AnimatePresence>
          {memories.map((mem, i) => (
            <motion.div 
              key={mem.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ delay: i * 0.05 }}
              className="p-5 rounded-2xl bg-white/[0.02] border border-emerald-500/10 backdrop-blur-sm flex flex-col group relative overflow-hidden"
            >
              <div className="absolute -top-10 -right-10 w-32 h-32 blur-[50px] rounded-full bg-emerald-500/5 group-hover:bg-emerald-500/10 transition-colors pointer-events-none" />
              
              <div className="flex justify-between items-start mb-3 relative z-10">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20">
                  {mem.key}
                </span>
                <button 
                  onClick={() => deleteMemory(mem.id)}
                  className="text-zinc-500 hover:text-red-400 transition-colors p-1"
                >
                  <Trash2 size={16} />
                </button>
              </div>
              <p className="text-white font-medium text-lg leading-relaxed relative z-10 mt-2">
                {mem.content}
              </p>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {memories.length === 0 && (
          <div className="col-span-full py-24 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-3xl bg-white/[0.01]">
            <BrainCircuit size={48} className="text-zinc-600 mb-6" />
            <h2 className="text-xl font-semibold text-white mb-2">No memories yet</h2>
            <p className="text-zinc-400 font-medium text-center">Chat with the Brain and it will automatically<br/>extract facts and preferences here.</p>
          </div>
        )}
      </div>
    </div>
  );
}
