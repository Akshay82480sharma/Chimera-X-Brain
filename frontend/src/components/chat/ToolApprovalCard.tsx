import { useState } from "react";
import { Check, X, Code, Terminal, FileCode2, FolderTree } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface PendingToolCall {
  id: string;
  function: {
    name: string;
    arguments: string; // JSON string
  };
}

export interface ResolvedToolCall {
  id: string;
  status: "approved" | "rejected";
  name: string;
  arguments: Record<string, any>;
}

interface ToolApprovalCardProps {
  toolCalls: PendingToolCall[];
  onResolve: (resolved: ResolvedToolCall[]) => void;
}

export function ToolApprovalCard({ toolCalls, onResolve }: ToolApprovalCardProps) {
  // Parse arguments and keep them in local state so the user can edit them
  const [editedArgs, setEditedArgs] = useState<Record<string, Record<string, any>>>(() => {
    const initial: Record<string, Record<string, any>> = {};
    toolCalls.forEach((tc) => {
      try {
        initial[tc.id] = JSON.parse(tc.function.arguments);
      } catch (e) {
        initial[tc.id] = {};
      }
    });
    return initial;
  });

  const handleArgChange = (id: string, key: string, value: string) => {
    setEditedArgs((prev) => ({
      ...prev,
      [id]: {
        ...prev[id],
        [key]: value,
      },
    }));
  };

  const handleApproveAll = () => {
    const resolved = toolCalls.map((tc) => ({
      id: tc.id,
      status: "approved" as const,
      name: tc.function.name,
      arguments: editedArgs[tc.id] || {},
    }));
    onResolve(resolved);
  };

  const handleRejectAll = () => {
    const resolved = toolCalls.map((tc) => ({
      id: tc.id,
      status: "rejected" as const,
      name: tc.function.name,
      arguments: editedArgs[tc.id] || {},
    }));
    onResolve(resolved);
  };

  const getIcon = (name: string) => {
    if (name.includes("file")) return <FileCode2 size={16} className="text-secondary" />;
    if (name.includes("dir")) return <FolderTree size={16} className="text-secondary" />;
    if (name.includes("command")) return <Terminal size={16} className="text-secondary" />;
    return <Code size={16} className="text-secondary" />;
  };

  return (
    <div className="w-full bg-surface-container border border-outline-variant rounded-lg p-5 shadow-1 relative overflow-hidden my-4">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-brand-start to-brand-end" />
      
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-foreground font-bold text-lg flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-tertiary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-tertiary"></span>
            </span>
            Action Required
          </h3>
          <p className="text-zinc-400 text-sm mt-1">Chimera-X wants to execute the following actions. You can edit the paths below.</p>
        </div>
      </div>

      <div className="space-y-4 mb-6">
        {toolCalls.map((tc) => {
          const args = editedArgs[tc.id] || {};
          return (
            <div key={tc.id} className="bg-white/5 border border-white/10 rounded-xl p-4 transition-colors hover:bg-white/10">
              <div className="flex items-center gap-2 mb-3">
                {getIcon(tc.function.name)}
                <span className="text-zinc-200 font-mono text-sm font-semibold">{tc.function.name}</span>
              </div>
              
              <div className="space-y-3 pl-6 border-l border-white/10 ml-2">
                {Object.entries(args).map(([key, val]) => (
                  <div key={key} className="flex flex-col gap-1.5">
                    <label className="text-xs text-zinc-500 uppercase font-bold tracking-wider">{key}</label>
                    {key === "path" || key === "cwd" || key === "command" ? (
                      <input
                        type="text"
                        value={val as string}
                        onChange={(e) => handleArgChange(tc.id, key, e.target.value)}
                        className="bg-surface-container-lowest border border-outline-variant rounded-sm px-3 py-2 text-sm text-primary font-mono focus:outline-none focus:shadow-glow-primary transition-shadow w-full"
                      />
                    ) : (
                      <div className="bg-black/40 border border-white/10 rounded-lg p-3 text-sm text-zinc-300 font-mono overflow-x-auto max-h-32">
                        {typeof val === 'string' && val.includes('\n') ? (
                          <pre className="text-xs">{val}</pre>
                        ) : (
                          <span>{JSON.stringify(val)}</span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex gap-3 justify-end border-t border-white/5 pt-4">
        <Button 
          variant="ghost" 
          onClick={handleRejectAll}
          className="text-red-400 hover:text-red-300 hover:bg-red-400/10 transition-colors px-6"
        >
          <X size={16} className="mr-2" />
          Reject All
        </Button>
        <Button 
          onClick={handleApproveAll}
          className="bg-primary-solid text-on-primary-solid rounded-sm hover:bg-primary-solid/90 transition-all shadow-1 px-6"
        >
          <Check size={16} className="mr-2" />
          Approve & Run
        </Button>
      </div>
    </div>
  );
}
