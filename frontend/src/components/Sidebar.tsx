"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Server, BrainCircuit, MessageSquare, Settings, FolderGit2 } from "lucide-react";
import { motion } from "framer-motion";

export function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "Chat", href: "/chat", icon: MessageSquare },
    { name: "Projects", href: "/projects", icon: FolderGit2 },
    { name: "Providers", href: "/providers", icon: Server },
    { name: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <div className="w-64 border-r border-white/5 bg-[#0a0a0c]/80 backdrop-blur-xl h-screen flex flex-col relative z-20">
      <div className="p-6 pb-2">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-emerald-500 to-emerald-300 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <BrainCircuit className="text-[#050505]" size={18} />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white leading-tight">
              Chimera-X
            </h1>
            <div className="text-[0.65rem] font-bold tracking-[0.2em] text-emerald-500 uppercase">
              Local Brain
            </div>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 px-3 space-y-1 mt-6">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          
          return (
            <Link 
              key={item.name} 
              href={item.href} 
              className={`relative flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-300 group ${
                isActive ? "text-white" : "text-zinc-400 hover:text-white"
              }`}
            >
              {isActive && (
                <motion.div 
                  layoutId="activeTab" 
                  className="absolute inset-0 bg-white/5 border border-white/10 rounded-xl"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <Icon 
                size={18} 
                className={`relative z-10 transition-colors duration-300 ${isActive ? "text-emerald-400" : "group-hover:text-emerald-400/70"}`} 
              />
              <span className="relative z-10">{item.name}</span>
            </Link>
          );
        })}
      </nav>
      
      <div className="p-4 mt-auto">
        <div className="rounded-xl bg-gradient-to-b from-white/[0.04] to-transparent p-4 border border-white/5 shadow-2xl relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/0 via-emerald-500/10 to-emerald-500/0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out" />
          <div className="flex items-center justify-between mb-3 relative z-10">
            <span className="text-xs font-semibold text-zinc-400">Memory Usage</span>
            <span className="text-xs font-bold text-emerald-400">2.1 GB</span>
          </div>
          <div className="h-1.5 bg-black/50 rounded-full overflow-hidden border border-white/5 relative z-10">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: "33%" }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.5)]" 
            />
          </div>
        </div>
      </div>
    </div>
  );
}
