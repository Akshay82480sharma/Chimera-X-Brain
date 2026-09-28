import { useState, useEffect } from "react";
import { X, Server, Globe, Save } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Provider {
  id: number;
  slug: string;
  name: string;
  type: string;
  base_url: string | null;
  priority: number;
  is_active: boolean;
}

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchProviders = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/providers`);
      if (res.ok) {
        setProviders(await res.json());
      }
    } catch (e) {
      console.warn("Failed to fetch providers", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchProviders();
    }
  }, [isOpen]);

  const handleUpdate = async (slug: string, updates: Partial<Provider>) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/providers/${slug}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
      if (res.ok) {
        fetchProviders(); // Refresh
      }
    } catch (e) {
      console.warn("Failed to update provider", e);
    }
  };

  if (!isOpen) return null;

  const localProviders = providers.filter(p => p.type === "local");
  const cloudProviders = providers.filter(p => p.type === "cloud");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-[#0e0e11] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden relative">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 to-emerald-300" />
        
        <div className="p-5 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Parameters & Settings
          </h2>
          <button onClick={onClose} className="text-zinc-400 hover:text-white transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          
          {/* Offline Mode Section */}
          <section>
            <div className="flex items-center gap-2 mb-4 text-emerald-400">
              <Server size={18} />
              <h3 className="text-lg font-semibold text-white">Offline Mode (Local LLM)</h3>
            </div>
            <p className="text-sm text-zinc-400 mb-6">
              Configure your local inference engines (LM Studio, Ollama). These act as your offline fallback if the cloud is unreachable.
            </p>

            <div className="space-y-4">
              {localProviders.map(provider => (
                <div key={provider.slug} className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="font-semibold text-zinc-200">{provider.name}</h4>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <span className="text-xs text-zinc-400">Enable Fallback</span>
                      <input 
                        type="checkbox" 
                        checked={provider.is_active}
                        onChange={(e) => handleUpdate(provider.slug, { is_active: e.target.checked })}
                        className="rounded bg-black/50 border-white/20 text-emerald-500 focus:ring-emerald-500/50"
                      />
                    </label>
                  </div>
                  
                  <div className="space-y-2">
                    <label className="text-xs text-zinc-500 uppercase tracking-wider font-semibold">Local Server URL</label>
                    <div className="flex gap-2">
                      <input 
                        type="text" 
                        defaultValue={provider.base_url || ""}
                        placeholder="e.g. http://localhost:11434"
                        onBlur={(e) => handleUpdate(provider.slug, { base_url: e.target.value })}
                        className="flex-1 bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-sm text-emerald-300 font-mono focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      />
                      <Button variant="ghost" size="sm" className="bg-white/5 hover:bg-white/10 px-4" onClick={(e) => {
                         const input = e.currentTarget.previousElementSibling as HTMLInputElement;
                         handleUpdate(provider.slug, { base_url: input.value });
                      }}>
                        <Save size={14} className="text-zinc-400" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Cloud Providers Section */}
          <section>
            <div className="flex items-center gap-2 mb-4 text-blue-400">
              <Globe size={18} />
              <h3 className="text-lg font-semibold text-white">Cloud Providers</h3>
            </div>
            <p className="text-sm text-zinc-400 mb-4">
              Your primary cloud APIs. These are prioritized automatically in Auto-Route mode.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {cloudProviders.map(provider => (
                <div key={provider.slug} className="bg-white/5 border border-white/10 rounded-xl p-3 flex items-center justify-between">
                  <span className="text-sm font-medium text-zinc-300">{provider.name}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] text-zinc-500 font-mono">Pri: {provider.priority}</span>
                    <label className="flex items-center">
                      <input 
                        type="checkbox" 
                        checked={provider.is_active}
                        onChange={(e) => handleUpdate(provider.slug, { is_active: e.target.checked })}
                        className="rounded bg-black/50 border-white/20 text-emerald-500 focus:ring-emerald-500/50"
                      />
                    </label>
                  </div>
                </div>
              ))}
            </div>
          </section>
          
        </div>
      </div>
    </div>
  );
}
