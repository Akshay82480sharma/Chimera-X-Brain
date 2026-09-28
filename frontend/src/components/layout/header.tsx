import { Bell, Search, Activity } from "lucide-react";

export function Header() {
  return (
    <header className="h-14 shrink-0 bg-[#0e0e11]/80 backdrop-blur-md border-b border-zinc-800/50 flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center gap-4 flex-1">
        <div className="relative w-full max-w-md hidden sm:block">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input 
            type="text" 
            placeholder="Search memory, chats, files..." 
            suppressHydrationWarning
            className="w-full bg-[#18181b] border border-zinc-800 rounded-full pl-10 pr-4 py-1.5 text-sm text-zinc-200 placeholder:text-zinc-500 focus:outline-none focus:border-zinc-700 transition-colors"
          />
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
          <Activity className="w-3.5 h-3.5" />
          <span>Local Engine Active</span>
        </div>
        <button suppressHydrationWarning className="text-zinc-400 hover:text-zinc-100 transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-0 right-0 w-2 h-2 bg-indigo-500 rounded-full border-2 border-[#0e0e11]"></span>
        </button>
      </div>
    </header>
  );
}
