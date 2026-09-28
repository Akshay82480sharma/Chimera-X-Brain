import { BrainCircuit, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/atom-one-dark.css";
import { motion } from "framer-motion";

interface MessageBubbleProps {
  role: "user" | "assistant" | "system";
  content: any; // Can be string or vision array
  providerName?: string;
  modelName?: string;
  isFallback?: boolean;
}

export function MessageBubble({ role, content, providerName, modelName, isFallback }: MessageBubbleProps) {
  const isUser = role === "user";
  const isSystem = role === "system";

  let parsedContent = typeof content === "string" ? content : "";
  let toolCalls: any[] | null = null;
  let isToolResponse = false;
  let imageParts: string[] = [];

  if (Array.isArray(content)) {
    const textPart = content.find((p: any) => p.type === "text");
    const images = content.filter((p: any) => p.type === "image_url").map((p: any) => p.image_url.url);
    parsedContent = textPart ? textPart.text : "";
    imageParts = images;
  } else if (typeof content === "string") {
    try {
      const json = JSON.parse(content);
      if (Array.isArray(json)) {
        // Vision format
        const textPart = json.find(p => p.type === "text");
        const images = json.filter(p => p.type === "image_url").map(p => p.image_url.url);
        parsedContent = textPart ? textPart.text : "";
        imageParts = images;
      } else if (json && typeof json === 'object') {
        if (json.tool_call_id) {
          isToolResponse = true;
          parsedContent = `🔧 **Tool Result:** \`${json.name}\`\n\n\`\`\`text\n${json.content}\n\`\`\``;
        } else if (json.text !== undefined || json.tool_calls) {
          parsedContent = json.text || "";
          toolCalls = json.tool_calls;
        }
      }
    } catch (e) {
      // Normal text, do nothing
    }
  }

  if (isSystem) {
    return (
      <div className="flex w-full mb-6 justify-center">
        <div className="max-w-[85%] px-6 py-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center shadow-lg shadow-red-500/5">
          <ReactMarkdown>{parsedContent}</ReactMarkdown>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex w-full mb-6 ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex max-w-[85%] min-w-0 gap-4 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
        {/* Avatar */}
        <motion.div 
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
          className={`w-10 h-10 shrink-0 rounded flex items-center justify-center border shadow-1 ${
          isUser 
            ? "bg-surface-bright border-outline-variant text-on-surface-variant" 
            : "bg-surface-container-highest border-outline-variant text-on-surface"
        }`}>
          {isUser ? <User size={20} /> : <BrainCircuit size={20} />}
        </motion.div>

        {/* Message Content */}
        <div className={`relative px-6 py-4 rounded-lg shadow-1 min-w-0 overflow-hidden ${
          isUser 
            ? "bg-surface-container-lowest border border-primary text-foreground" 
            : "bg-surface-container-high border border-outline-variant text-foreground"
        }`}>
          <div className="prose prose-invert max-w-none break-words overflow-x-auto prose-pre:bg-surface-container-lowest prose-pre:border prose-pre:border-outline-variant prose-pre:shadow-1 prose-pre:font-mono text-body-md">
            {imageParts.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {imageParts.map((src, i) => (
                  <img key={i} src={src} alt="attachment" className="max-w-[300px] max-h-[300px] rounded object-contain border border-outline-variant shadow-sm" />
                ))}
              </div>
            )}
            <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
              {parsedContent}
            </ReactMarkdown>
          </div>
          
          {toolCalls && toolCalls.length > 0 && (
            <div className="mt-4 flex flex-col gap-2 border-t border-outline-variant pt-3">
              {toolCalls.map((tc: any, i: number) => (
                <div key={i} className="text-code-md bg-surface-container-lowest border border-outline-variant rounded p-2 text-primary shadow-inner overflow-x-auto">
                  <span className="font-bold mr-2">⚡ SYSTEM_CALL:</span>
                  {tc.function?.name}({tc.function?.arguments})
                </div>
              ))}
            </div>
          )}
          
          {providerName && (
            <div className="mt-3 pt-3 border-t border-outline-variant flex items-center justify-end">
              <span className={`text-label-caps flex items-center gap-1.5 ${isFallback ? 'text-amber-500 font-bold' : 'text-on-surface-variant'}`}>
                <span className={`w-2 h-2 rounded-full animate-pulse ${isFallback ? 'bg-amber-500' : 'bg-primary'}`} />
                via {providerName} {modelName && `(${modelName})`}
                {isFallback && " (auto-fallback)"}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
