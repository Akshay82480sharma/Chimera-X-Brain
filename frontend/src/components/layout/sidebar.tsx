"use client";

import { Home, MessageSquare, Database, Settings, Box, Network, BookOpen, Layers, BookTemplate, Wrench, Bot, Zap } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

export function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { icon: Home, label: "Dashboard", href: "/" },
    { icon: MessageSquare, label: "Chat", href: "/chat" },
    { icon: Bot, label: "Agents", href: "/agents" },
    { icon: Zap, label: "Skills", href: "/skills" },
    { icon: Database, label: "Memory", href: "/memory" },
    { icon: Layers, label: "Projects", href: "/projects" },
    { icon: BookOpen, label: "Knowledge", href: "/knowledge" },
    { icon: BookTemplate, label: "Prompts", href: "/prompts" },
    { icon: Network, label: "Providers", href: "/providers" },
    { icon: Box, label: "Models", href: "/models" },
  ];

  return (
    <div className="w-[260px] h-full bg-surface-container border-r border-outline-variant flex flex-col hidden md:flex shrink-0">
      <div className="h-14 flex items-center px-6 border-b border-outline-variant">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded bg-primary-solid flex items-center justify-center shadow-1">
            <span className="text-[10px] font-extrabold text-on-primary-solid tracking-tighter">CX</span>
          </div>
          <span className="text-headline-sm text-foreground">Chimera-X Brain</span>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto py-4 flex flex-col gap-1">
        <div className="px-6 mb-2">
          <span className="text-label-caps text-on-surface-variant">Menu</span>
        </div>
        {navItems.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link 
              key={item.label} 
              href={item.href}
              className={`flex items-center gap-3 px-6 py-2.5 text-body-sm transition-all border-l-[3px] ${
                isActive 
                  ? "bg-surface-container-high text-on-surface border-primary-solid" 
                  : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50 border-transparent"
              }`}
            >
              <item.icon className="w-[18px] h-[18px] shrink-0" />
              {item.label}
            </Link>
          );
        })}
      </div>
      
      <div className="py-4 border-t border-outline-variant">
        <Link 
          href="/settings"
          className={`flex items-center gap-3 px-6 py-2.5 text-body-sm transition-all border-l-[3px] ${
            pathname === "/settings"
              ? "bg-surface-container-high text-on-surface border-primary-solid"
              : "text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high/50 border-transparent"
          }`}
        >
          <Settings className="w-[18px] h-[18px] shrink-0" />
          Settings
        </Link>
      </div>
    </div>
  );
}
