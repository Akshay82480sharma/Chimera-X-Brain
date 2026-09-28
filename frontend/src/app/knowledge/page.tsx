"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { BookOpen, UploadCloud, FileText, CheckCircle2 } from "lucide-react";

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function fetchDocuments() {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/knowledge/documents`);
      if (res.ok) setDocuments(await res.json());
    } catch (e) {
      console.warn(e);
    }
  };

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/v1/knowledge/upload`, {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        fetchDocuments();
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    } catch (error) {
      console.warn("Upload failed", error);
    } finally {
      setIsUploading(false);
    }
  };


  useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <div className="h-full overflow-y-auto p-10 max-w-7xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10"
      >
        <h1 className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-amber-400 to-orange-300 flex items-center gap-3">
          <BookOpen size={36} className="text-amber-400" /> Knowledge Base
        </h1>
        <p className="text-zinc-400 mt-2 font-medium">Upload documents for RAG (Retrieval-Augmented Generation).</p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Zone */}
        <div className="lg:col-span-2">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="border-2 border-dashed border-amber-500/30 rounded-3xl p-12 flex flex-col items-center justify-center text-center bg-amber-500/5 hover:bg-amber-500/10 transition-colors cursor-pointer"
          >
            <div className="w-20 h-20 rounded-full bg-amber-500/20 flex items-center justify-center mb-6">
              <UploadCloud className="w-10 h-10 text-amber-400" />
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">Drag & Drop files here</h3>
            <p className="text-zinc-400 mb-6">Supports Markdown (.md), Text (.txt), and PDF (.pdf) files.</p>
            <input 
              type="file" 
              accept=".txt,.md,.pdf" 
              className="hidden" 
              ref={fileInputRef}
              onChange={handleUpload}
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-[#050505] font-bold rounded-xl transition-colors disabled:opacity-50"
            >
              {isUploading ? "Uploading..." : "Browse Files"}
            </button>
          </motion.div>
        </div>

        {/* Uploaded Documents List */}
        <div>
          <div className="bg-white/[0.02] border border-white/5 rounded-3xl p-6 h-full flex flex-col">
            <h3 className="text-lg font-bold text-white mb-4">Indexed Documents</h3>
            
            <div className="flex-1 flex flex-col gap-3 overflow-y-auto pr-2">
              {documents.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center text-center opacity-60">
                  <FileText className="w-12 h-12 text-zinc-600 mb-3" />
                  <p className="text-sm text-zinc-400">No documents indexed yet.</p>
                </div>
              ) : (
                documents.map(doc => (
                  <div key={doc.id} className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                    <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
                      <FileText className="w-5 h-5 text-amber-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{doc.filename}</p>
                      <p className="text-xs text-zinc-400">{new Date(doc.created_at).toLocaleDateString()}</p>
                    </div>
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
