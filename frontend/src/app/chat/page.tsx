"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Settings2, Plus, MessageSquare, Trash2, Wifi, WifiOff, Sparkles, Mic, ArrowUp, X, Paperclip, FileText, Image as ImageIcon } from "lucide-react";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ToolApprovalCard, PendingToolCall, ResolvedToolCall } from "@/components/chat/ToolApprovalCard";
import { AttachedFile, processUploadedFiles } from "@/utils/fileUpload";
import { SettingsModal } from "@/components/chat/SettingsModal";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";

interface Message {
  role: "user" | "assistant" | "system";
  content: any; // Can be string or array of objects for vision
  provider_name?: string;
  model_name?: string;
  isFallback?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatId, setChatId] = useState<number | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [providersMap, setProvidersMap] = useState<Record<number, string>>({});
  const [modelsMap, setModelsMap] = useState<Record<number, string>>({});
  const [selectedModel, setSelectedModel] = useState<string>("auto");
  const [agents, setAgents] = useState<{id: number, name: string}[]>([]);
  const [skills, setSkills] = useState<{id: number, name: string}[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>("auto");
  const [selectedSkills, setSelectedSkills] = useState<number[]>([]);
  const [isSkillsDropdownOpen, setIsSkillsDropdownOpen] = useState(false);
  const [autoSkills, setAutoSkills] = useState(true);
  const [pendingTools, setPendingTools] = useState<PendingToolCall[] | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isOnline, setIsOnline] = useState(true);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [pastedTexts, setPastedTexts] = useState<{id: string, text: string}[]>([]);
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [fallbackToast, setFallbackToast] = useState<{message: string, provider: string} | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<BlobPart[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setIsLoading(true);
      try {
        const processed = await processUploadedFiles(e.target.files);
        setAttachedFiles(prev => [...prev, ...processed]);
      } catch (err) {
        console.error("Upload error:", err);
      } finally {
        setIsLoading(false);
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
        setIsRecording(false);
        setIsTranscribing(true);
      }
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          stream.getTracks().forEach(track => track.stop());

          const formData = new FormData();
          formData.append("file", audioBlob, "recording.webm");

          try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
            const res = await fetch(`${apiUrl}/v1/audio/transcriptions`, {
              method: "POST",
              body: formData,
            });

            if (res.ok) {
              const data = await res.json();
              if (data.text) {
                setInput(prev => (prev ? prev + " " : "") + data.text);
                // Trigger resize
                setTimeout(() => {
                  const textarea = document.querySelector('textarea');
                  if (textarea) {
                    textarea.style.height = 'auto';
                    textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
                  }
                }, 10);
              }
            } else {
              console.error("Transcription failed", await res.text());
            }
          } catch (error) {
            console.error("Error sending audio to backend", error);
          } finally {
            setIsTranscribing(false);
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (err) {
        console.error("Error accessing microphone:", err);
        alert("Could not access microphone. Please ensure you have granted permission.");
      }
    }
  };

  async function fetchProviders() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/v1/providers`);
      if (res.ok) {
        const data = await res.json();
        const map: Record<number, string> = {};
        data.forEach((p: any /* eslint-disable-line @typescript-eslint/no-explicit-any */) => {
          map[p.id] = p.name;
        });
        setProvidersMap(map);
      }
    } catch (e) {
      console.warn("Failed to fetch providers", e);
    }
  };

  const cleanTitle = (title: string) => {
    if (!title) return "New Chat";
    try {
      const json = JSON.parse(title);
      if (json && typeof json === 'object' && json.text) {
        title = json.text;
      }
    } catch(e) {}
    // Strip common markdown
    return title
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/`(.*?)`/g, '$1')
      .replace(/^#+\s+/g, '');
  };

  async function fetchModels() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/v1/models`);
      if (res.ok) {
        const data = await res.json();
        const modelsArray = Array.isArray(data) ? data : data.data || [];
        const map: Record<number, string> = {};
        modelsArray.forEach((m: any) => {
          map[m.id] = m.display_name || m.model_name;
        });
        setModelsMap(map);
      }
    } catch (e) {
      console.warn("Failed to fetch models", e);
    }
  };

  async function fetchHistory() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/v1/chats`);
      if (res.ok) setHistory(await res.json());
    } catch (e) {
      console.warn(e);
    }
  };

  async function loadChat(id: number) {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/v1/chats/${id}/messages`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
        setChatId(id);
      }
    } catch (e) {
      console.warn(e);
    }
  };

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  };

  async function handleClearHistory() {
    if (!confirm("Are you sure you want to completely delete all chat history and extracted memories? This cannot be undone.")) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/v1/chats/all/clear`, { method: "DELETE" });
      if (res.ok) {
        setHistory([]);
        setMessages([]);
        setChatId(null);
      }
    } catch (e) {
      console.warn(e);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if ((!input.trim() && pastedTexts.length === 0 && attachedFiles.length === 0) || isLoading) return;

    let textInput = input;
    if (pastedTexts.length > 0) {
      textInput = pastedTexts.map(pt => pt.text).join('\n\n') + (input.trim() ? '\n\n' + input : '');
    }

    let finalContent: any = textInput;
    if (attachedFiles.length > 0) {
      finalContent = [];
      if (textInput.trim()) {
        finalContent.push({ type: "text", text: textInput });
      } else {
        finalContent.push({ type: "text", text: "What is in this file?" });
      }
      
      for (const af of attachedFiles) {
        finalContent.push({
          type: "image_url",
          image_url: { url: af.base64Data }
        });
      }
    }

    const newMessages = [...messages, { role: "user", content: finalContent } as Message];
    setMessages(newMessages);
    setInput("");
    setPastedTexts([]);
    setAttachedFiles([]);
    setIsLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/v1/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          model: selectedModel, 
          messages: newMessages,
          stream: true,
          chat_id: chatId,
          agent_id: selectedAgent === "auto" ? null : parseInt(selectedAgent),
          skill_ids: selectedSkills,
          auto_agent: selectedAgent === "auto",
          auto_skills: autoSkills
        }),
      });

      if (!response.ok) {
        let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
        try {
          const errData = await response.json();
          if (errData.detail) errorMsg = errData.detail;
        } catch {
          try {
            const errText = await response.text();
            if (errText) errorMsg = errText;
          } catch {}
        }
        throw new Error(errorMsg);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let assistantContent = "";
      setMessages([...newMessages, { role: "assistant", content: "" }]);
      
      let currentEvent = "";

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
            continue; 
          }
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              fetchHistory();
              break;
            }
            try {
              const parsed = JSON.parse(data);
              
              if (currentEvent === "tool_calls_pending") {
                setPendingTools(parsed);
                currentEvent = "";
                if (assistantContent === "") {
                  setMessages((prev) => prev.slice(0, -1));
                }
                break;
              }
              
              if (currentEvent === "chat_meta" && parsed.chat_id) {
                setChatId(parsed.chat_id);
                // Also capture provider_id and model_id from chat_meta if present
                if (parsed.provider_id) {
                  const pName = providersMap[parsed.provider_id] || `Provider ${parsed.provider_id}`;
                  setMessages((prev) => {
                    const updated = [...prev];
                    updated[updated.length - 1].provider_name = pName;
                    if (parsed.is_fallback) {
                      updated[updated.length - 1].isFallback = true;
                    }
                    return updated;
                  });
                  if (parsed.is_fallback) {
                    setFallbackToast({ message: "Auto-fallback triggered to maintain uptime.", provider: pName });
                    setTimeout(() => setFallbackToast(null), 5000);
                  }
                }
                if (parsed.model_id) {
                  const mName = modelsMap[parsed.model_id];
                  if (mName) {
                    setMessages((prev) => {
                      const updated = [...prev];
                      updated[updated.length - 1].model_name = mName;
                      return updated;
                    });
                  }
                }
              } else if (parsed.choices?.[0]?.delta?.content) {
                assistantContent += parsed.choices[0].delta.content;
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1].content = assistantContent;
                  return updated;
                });
              }
            } catch (e) {
              // ignore parse errors for partial chunks
            }
          }
        }
      }
    } catch (error: any) {
      console.warn("Error:", error);
      setMessages((prev) => [
        ...prev,
        { 
          role: "system", 
          content: `⚠️ **Error connecting to AI Provider:**\n\n${error.message || "Unknown error occurred"}\n\nCheck your backend logs for more details.` 
        } as Message
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  async function handleResolveTools(resolvedTools: ResolvedToolCall[]) {
    if (!chatId) return;
    
    setPendingTools(null);
    setIsLoading(true);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/v1/chat/tools/resolve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          chat_id: chatId,
          tool_calls: resolvedTools,
          agent_id: selectedAgent === "auto" ? null : parseInt(selectedAgent),
          skill_ids: selectedSkills,
          auto_agent: selectedAgent === "auto",
          auto_skills: autoSkills
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP Error ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let assistantContent = "";
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      
      let currentEvent = "";

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
            continue; 
          }
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              fetchHistory();
              break;
            }
            try {
              const parsed = JSON.parse(data);
              
              if (currentEvent === "tool_calls_pending") {
                setPendingTools(parsed);
                currentEvent = "";
                if (assistantContent === "") {
                  setMessages((prev) => prev.slice(0, -1));
                }
                break; // Stop reading this stream, wait for user resolution
              }
              
              if (currentEvent === "chat_meta" && parsed.chat_id) {
                setChatId(parsed.chat_id);
                if (parsed.provider_id) {
                  const pName = providersMap[parsed.provider_id] || `Provider ${parsed.provider_id}`;
                  setMessages((prev) => {
                    const updated = [...prev];
                    updated[updated.length - 1].provider_name = pName;
                    if (parsed.is_fallback) updated[updated.length - 1].isFallback = true;
                    return updated;
                  });
                }
                if (parsed.model_id) {
                  const mName = modelsMap[parsed.model_id];
                  if (mName) {
                    setMessages((prev) => {
                      const updated = [...prev];
                      updated[updated.length - 1].model_name = mName;
                      return updated;
                    });
                  }
                }
              } else if (parsed.choices?.[0]?.delta?.content) {
                assistantContent += parsed.choices[0].delta.content;
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1].content = assistantContent;
                  return updated;
                });
              }
            } catch (e) {}
          }
        }
      }
    } catch (error: any) {
      console.warn("Error resolving tools:", error);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleEnhance() {
    if (!input.trim() || isEnhancing || isLoading) return;
    
    setIsEnhancing(true);
    setInput("");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/v1/chat/enhance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: input }),
      });
      if (!res.ok) throw new Error("Enhance failed");

      const reader = res.body?.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let enhancedText = "";
      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") break;
            try {
              const parsed = JSON.parse(data);
              if (parsed.text) {
                enhancedText += parsed.text;
                setInput(enhancedText);
                // Trigger resize
                const textarea = document.querySelector('textarea');
                if (textarea) {
                  textarea.style.height = 'auto';
                  textarea.style.height = `${Math.min(textarea.scrollHeight, 400)}px`;
                }
              }
            } catch(e) {}
          }
        }
      }
    } catch (e) {
      console.warn("Enhance failed", e);
    } finally {
      setIsEnhancing(false);
    }
  }



  async function fetchAgents() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/v1/agents`);
      if (res.ok) setAgents(await res.json());
    } catch (e) {
      console.warn(e);
    }
  }

  async function fetchSkills() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/v1/skills`);
      if (res.ok) setSkills(await res.json());
    } catch (e) {
      console.warn(e);
    }
  }

  useEffect(() => {
    fetchHistory();
    fetchProviders();
    fetchModels();
    fetchAgents();
    fetchSkills();
    
    // Check initial online status
    setIsOnline(navigator.onLine);
    
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="flex h-full w-full bg-[#030303] overflow-hidden">
      {/* Sidebar History */}
      <div className="w-72 border-r border-white/5 bg-[#0a0a0c]/80 backdrop-blur-xl flex flex-col relative z-20 hidden md:flex">
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <h2 className="font-bold text-white flex items-center gap-2">
            <MessageSquare size={18} className="text-emerald-400" /> History
          </h2>
          <div className="flex items-center gap-1">
            <Button 
              variant="ghost" 
              size="icon" 
              title="Clear all history"
              className="h-8 w-8 text-red-400/70 hover:text-red-400 hover:bg-red-400/10"
              onClick={handleClearHistory}
            >
              <Trash2 size={16} />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              title="New Chat"
              className="h-8 w-8 text-zinc-400 hover:text-white"
              onClick={() => { setMessages([]); setChatId(null); }}
            >
              <Plus size={18} />
            </Button>
          </div>
        </div>
        <ScrollArea className="flex-1 p-2">
          <div className="space-y-1">
            {history.map((chat) => (
              <button
                key={chat.id}
                onClick={() => loadChat(chat.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors truncate ${chatId === chat.id ? "bg-white/10 text-white font-medium" : "text-zinc-400 hover:bg-white/5 hover:text-white"}`}
              >
                {cleanTitle(chat.title)}
              </button>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative min-w-0">
        <AnimatePresence>
          {fallbackToast && (
            <motion.div 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="absolute top-16 left-1/2 -translate-x-1/2 z-50 bg-amber-500/10 border border-amber-500/20 text-amber-500 px-4 py-2 rounded-full shadow-lg shadow-amber-500/5 backdrop-blur-md flex items-center gap-2 text-sm font-medium"
            >
              <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
              {fallbackToast.message}
            </motion.div>
          )}
        </AnimatePresence>
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-[400px] bg-emerald-500/5 blur-[120px] rounded-full pointer-events-none -z-10" />

        {/* Header */}
        <header className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-transparent backdrop-blur-md z-10">
          <div className="flex items-center gap-3">
            <div className="relative">
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="appearance-none bg-white/5 border border-white/10 hover:bg-white/10 text-xs font-semibold text-zinc-300 rounded-full px-4 py-1.5 pr-8 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-colors cursor-pointer"
              >
                <option value="auto" className="bg-[#131316] text-zinc-300">✨ Auto-Route</option>
                {Object.entries(modelsMap).map(([id, name]) => (
                  <option key={id} value={id} className="bg-[#131316] text-zinc-300">
                    {name}
                  </option>
                ))}
              </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-400">
                <svg width="10" height="6" viewBox="0 0 10 6" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>

            <div className="relative">
              <select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                className="appearance-none bg-white/5 border border-white/10 hover:bg-white/10 text-xs font-semibold text-zinc-300 rounded-full px-4 py-1.5 pr-8 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-colors cursor-pointer"
              >
                <option value="auto" className="bg-[#131316] text-zinc-300">✨ Auto Agent</option>
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id} className="bg-[#131316] text-zinc-300">
                    {agent.name}
                  </option>
                ))}
              </select>
              <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-400">
                <svg width="10" height="6" viewBox="0 0 10 6" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M1 1L5 5L9 1" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>

            <div className="relative">
              <button
                onClick={() => setIsSkillsDropdownOpen(!isSkillsDropdownOpen)}
                className={`appearance-none bg-white/5 border border-white/10 hover:bg-white/10 text-xs font-semibold rounded-full px-4 py-1.5 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-colors cursor-pointer flex items-center gap-2 ${autoSkills && selectedSkills.length === 0 ? "text-emerald-400" : "text-zinc-300"}`}
              >
                ⚡ Skills {selectedSkills.length > 0 && `(${selectedSkills.length})`} {autoSkills && selectedSkills.length === 0 && "(Auto)"}
              </button>
              
              {isSkillsDropdownOpen && (
                <div className="absolute top-full left-0 mt-2 w-56 bg-[#131316] border border-white/10 rounded-xl shadow-xl overflow-hidden z-50">
                  <div className="max-h-64 overflow-y-auto p-2 flex flex-col gap-1">
                    
                    <label className="flex items-center gap-2 p-2 hover:bg-white/5 rounded-lg cursor-pointer border-b border-white/5 pb-3 mb-1">
                      <input
                        type="checkbox"
                        checked={autoSkills}
                        onChange={(e) => {
                          setAutoSkills(e.target.checked);
                          if (e.target.checked) setSelectedSkills([]);
                        }}
                        className="rounded border-zinc-700 bg-zinc-900 text-emerald-500 focus:ring-emerald-500/20"
                      />
                      <span className="text-xs font-bold text-emerald-400">✨ Auto-Select Skills</span>
                    </label>

                    {skills.length === 0 ? (
                      <div className="text-xs text-zinc-500 p-2">No skills available</div>
                    ) : (
                      skills.map((skill) => (
                        <label key={skill.id} className="flex items-center gap-2 p-2 hover:bg-white/5 rounded-lg cursor-pointer">
                          <input
                            type="checkbox"
                            checked={selectedSkills.includes(skill.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedSkills([...selectedSkills, skill.id]);
                                setAutoSkills(false);
                              } else {
                                setSelectedSkills(selectedSkills.filter(id => id !== skill.id));
                              }
                            }}
                            className="rounded border-zinc-700 bg-zinc-900 text-emerald-500 focus:ring-emerald-500/20"
                          />
                          <span className="text-xs text-zinc-300">{skill.name}</span>
                        </label>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
            
            
            <div className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-full border ${isOnline ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'}`}>
              <div className="relative flex h-2 w-2">
                {isOnline && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
                <span className={`relative inline-flex rounded-full h-2 w-2 ${isOnline ? 'bg-emerald-500' : 'bg-zinc-500'}`}></span>
              </div>
              {isOnline ? 'Online' : 'Offline / Local Only'}
            </div>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setIsSettingsOpen(true)}
            className="text-zinc-400 hover:text-white gap-2"
          >
            <Settings2 size={16} /> Parameters
          </Button>
        </header>

        {/* Messages */}
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto p-4 md:p-10 scroll-smooth"
        >
          <div className="max-w-3xl mx-auto">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full mt-32 opacity-70">
                <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-brand-start/20 to-brand-end/20 flex items-center justify-center border border-brand-end/30 mb-6 shadow-glow-success">
                  <MessageSquare className="text-secondary" size={32} />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">How can I help you today?</h2>
                <p className="text-zinc-400 text-center max-w-sm">I'm your personal AI Brain. I can route requests to your local machines or cloud APIs automatically.</p>
              </div>
            ) : (
              <AnimatePresence>
                {messages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 15, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ type: "spring", stiffness: 300, damping: 25 }}
                    layout
                  >
                    <MessageBubble 
                      role={msg.role} 
                      content={msg.content} 
                      providerName={msg.provider_name}
                      modelName={msg.model_name}
                      isFallback={msg.isFallback}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            )}
            {isLoading && messages[messages.length - 1]?.role === "user" && (
                <div className="flex gap-2 p-6">
                  <div className="w-2 h-2 rounded-full bg-secondary animate-bounce" style={{ animationDelay: "0ms" }} />
                  <div className="w-2 h-2 rounded-full bg-secondary animate-bounce" style={{ animationDelay: "150ms" }} />
                  <div className="w-2 h-2 rounded-full bg-secondary animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
            )}
            
            {pendingTools && pendingTools.length > 0 && (
              <ToolApprovalCard 
                toolCalls={pendingTools} 
                onResolve={handleResolveTools} 
              />
            )}
          </div>
        </div>

        {/* Input */}
        <div className="p-4 md:p-6 bg-gradient-to-t from-background via-background to-transparent z-10">
          <div className="max-w-3xl mx-auto relative">
            <form onSubmit={handleSubmit} className="relative flex flex-col bg-surface-container-lowest border border-outline-variant rounded-lg shadow-1 transition-shadow focus-within:shadow-glow-primary overflow-hidden">
              <div className="flex-1 flex flex-col min-w-0 w-full">
                {(pastedTexts.length > 0 || attachedFiles.length > 0) && (
                  <div className="flex flex-wrap gap-2 px-5 pt-4 pb-1">
                    {pastedTexts.map(pt => (
                      <div key={pt.id} className="relative group bg-white/5 border border-white/10 rounded-xl p-3 flex flex-col gap-1.5 max-w-[220px] shadow-sm">
                        <button 
                          type="button" 
                          onClick={() => setPastedTexts(prev => prev.filter(p => p.id !== pt.id))} 
                          className="absolute -top-2 -right-2 w-6 h-6 bg-zinc-800 rounded-full flex items-center justify-center border border-zinc-600 opacity-0 group-hover:opacity-100 transition-opacity z-10 hover:bg-zinc-700 text-white shadow-md"
                        >
                          <X size={14}/>
                        </button>
                        <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider bg-black/40 w-fit px-1.5 py-0.5 rounded border border-white/5">PASTED</span>
                        <span className="text-xs text-zinc-300 line-clamp-3 overflow-hidden text-ellipsis whitespace-pre-wrap leading-relaxed">{pt.text}</span>
                      </div>
                    ))}
                    {attachedFiles.map(af => (
                      <div key={af.id} className="relative group bg-white/5 border border-white/10 rounded-xl flex flex-col items-center justify-center h-[76px] w-[76px] overflow-hidden shadow-sm">
                        <button 
                          type="button" 
                          onClick={() => setAttachedFiles(prev => prev.filter(f => f.id !== af.id))} 
                          className="absolute -top-2 -right-2 w-6 h-6 bg-zinc-800 rounded-full flex items-center justify-center border border-zinc-600 opacity-0 group-hover:opacity-100 transition-opacity z-20 hover:bg-zinc-700 text-white shadow-md"
                        >
                          <X size={14}/>
                        </button>
                        {af.type === 'image' || af.type === 'pdf' ? (
                          <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${af.previewUrl})` }} />
                        ) : (
                          <FileText size={24} className="text-zinc-400 z-10" />
                        )}
                        {af.type === 'pdf' && (
                          <div className="absolute bottom-1 left-1 bg-black/60 px-1 py-0.5 rounded text-[8px] font-bold text-white z-10 border border-white/20 uppercase tracking-wider">PDF</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                
                <textarea
                  value={input}
                  onChange={(e) => {
                    setInput(e.target.value);
                    e.target.style.height = 'auto';
                    e.target.style.height = `${Math.min(e.target.scrollHeight, 400)}px`;
                  }}
                  onPaste={(e) => {
                    const pastedData = e.clipboardData.getData('text');
                    if (pastedData && (pastedData.length > 400 || pastedData.split('\n').length > 10)) {
                      e.preventDefault();
                      setPastedTexts(prev => [...prev, { id: Math.random().toString(36).substring(7), text: pastedData }]);
                    }
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      if ((input.trim() || pastedTexts.length > 0) && !isLoading && !isEnhancing) {
                        handleSubmit(e as any);
                      }
                    }
                  }}
                  placeholder="Message Chimera-X Brain..."
                  rows={2}
                  className={`w-full bg-transparent border-none outline-none px-5 ${pastedTexts.length > 0 || attachedFiles.length > 0 ? 'pt-2' : 'pt-4'} pb-2 text-white placeholder:text-zinc-500 resize-none overflow-y-auto min-h-[56px] max-h-[400px] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-track]:my-2 [&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-white/20 focus:ring-0 leading-relaxed text-[15px]`}
                  disabled={isLoading || isEnhancing}
                  suppressHydrationWarning
                />
              </div>

              <div className="flex items-center justify-between px-3 pb-3 pt-1">
                <div className="flex items-center gap-1">
                  <input type="file" ref={fileInputRef} className="hidden" accept="image/*,application/pdf" multiple onChange={handleFileUpload} />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading}
                    title="Attach file"
                    className="w-9 h-9 rounded-lg flex items-center justify-center transition-all bg-transparent text-zinc-400 hover:text-white hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Paperclip size={18} />
                  </button>

                  <button
                    type="button"
                    onClick={toggleRecording}
                    disabled={isLoading}
                    title="Voice Typing"
                    suppressHydrationWarning
                    className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all ${
                      isRecording 
                        ? 'bg-red-500/20 text-red-400 animate-pulse' 
                        : isTranscribing
                          ? 'bg-amber-500/20 text-amber-400 animate-pulse'
                          : 'bg-transparent text-zinc-400 hover:text-white hover:bg-white/10'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    <Mic size={18} />
                  </button>

                  <button
                    type="button"
                    onClick={handleEnhance}
                    disabled={(!input.trim() && pastedTexts.length === 0) || isLoading || isEnhancing || isRecording || isTranscribing}
                    title="Enhance prompt with Local AI"
                    suppressHydrationWarning
                    className={`w-9 h-9 rounded-lg flex items-center justify-center transition-all ${isEnhancing ? 'bg-amber-500/20 text-amber-400' : 'bg-transparent text-zinc-400 hover:text-amber-400 hover:bg-amber-500/10'} disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    <Sparkles size={18} className={isEnhancing ? "animate-pulse" : ""} />
                  </button>
                </div>
                
                <button 
                  type="submit"
                  disabled={(!input.trim() && pastedTexts.length === 0) || isLoading || isEnhancing || isRecording || isTranscribing}
                  suppressHydrationWarning
                  className="w-10 h-10 rounded-sm bg-primary-solid flex items-center justify-center text-on-primary-solid disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary-solid/90 transition-colors shadow-1"
                >
                  <Send size={18} className="ml-1" />
                </button>
              </div>
            </form>
            <div className="text-center mt-3">
              <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-semibold">Chimera-X can make mistakes. Verify important information.</span>
            </div>
          </div>
        </div>
      </div>
      
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
    </div>
  );
}
