import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import {
  Paperclip,
  ArrowUp,
  ArrowRight,
  Plus,
  Search,
  FileText,
  X,
  ChevronRight,
  ChevronDown,
  Database,
  BookOpen,
  BarChart3,
  Shield,
  Upload,
  FolderOpen,
  CheckCircle,
  AlertCircle,
  Loader,
  RefreshCw,
  Copy,
  Check,
  Trash2,
  Table2,
  FileType2,
  Cpu,
  Pencil,
  Square,
  Settings,
  Eye,
  EyeOff,
} from "lucide-react";

type Toast = { id: string; msg: string; type: "success" | "error" | "info" };

type UploadJob = {
  jobId: string;
  filename: string;
  status: "queued" | "extracting" | "chunking" | "embedding" | "completed" | "failed";
  step?: string;
  error?: string;
  progress?: number;
};

type KBDocument = {
  document_id: string;
  source: string;
  pages: number | null;
  chunk_count: number;
  collection?: string;
};

// ── Types ──────────────────────────────────────────────────────────────────

type Source = {
  id: string;
  title: string;
  type: "pdf" | "database" | "doc";
  excerpt: string;
  page?: number;
  date: string;
  confidence: number;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isStreaming?: boolean;
};

type Chat = {
  id: string;
  title: string;
  createdAt: number;
  messages: Message[];
};

const STORAGE_KEY = "chatrag_sessions";

function loadChatsFromStorage(): Chat[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveChatsToStorage(chats: Chat[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(chats));
}

function chatGroup(createdAt: number): "today" | "week" | "older" {
  const diff = Date.now() - createdAt;
  if (diff < 86_400_000) return "today";
  if (diff < 7 * 86_400_000) return "week";
  return "older";
}

type Collection = { name: string; doc_count: number };
type ChatScope = { type: "all" } | { type: "selected"; collections: string[] };
type Suggestion = { title: string; subtitle: string };

const SUGGESTION_ICONS = [BarChart3, BookOpen, Shield, Database];

// ── Sub-components ─────────────────────────────────────────────────────────

function LogoIcon({ size = 24 }: { size?: number }) {
  return (
    <img
      src="/favicon-96x96.png"
      alt="chatRAG"
      className="shrink-0"
      style={{ width: size, height: size, borderRadius: size * 0.32 }}
    />
  );
}

/* SVG gradient text — avoids backgroundClip:text which breaks in some renderers */
function RAGText({ fontSize, opacity = 1 }: { fontSize: number; opacity?: number }) {
  const id = `rag-grad-${fontSize}`;
  /* Approximate glyph metrics for Inter Bold "RAG":
     width ≈ fontSize * 2.05, cap-height ≈ fontSize * 0.72 */
  const w = Math.ceil(fontSize * 2.15);
  const h = Math.ceil(fontSize * 1.1);
  const baseline = Math.ceil(fontSize * 0.82);
  return (
    <svg
      width={w}
      height={h}
      viewBox={`0 0 ${w} ${h}`}
      style={{ display: "inline-block", verticalAlign: "middle", overflow: "visible", filter: "drop-shadow(0 3px 14px rgba(139,92,246,0.18))" }}
      aria-label="RAG"
    >
      <defs>
        <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%"   stopColor="#06B6D4" stopOpacity={opacity} />
          <stop offset="35%"  stopColor="#2563EB" stopOpacity={opacity} />
          <stop offset="70%"  stopColor="#8B5CF6" stopOpacity={opacity} />
          <stop offset="100%" stopColor="#F43F5E" stopOpacity={opacity} />
        </linearGradient>
      </defs>
      <text
        x="0"
        y={baseline}
        fill={`url(#${id})`}
        fontFamily="Inter, -apple-system, BlinkMacSystemFont, Helvetica Neue, sans-serif"
        fontSize={fontSize}
        fontWeight="700"
        letterSpacing="-0.01em"
      >
        RAG
      </text>
    </svg>
  );
}

function Logo() {
  return (
    <span className="flex items-center gap-2 select-none">
      <LogoIcon size={24} />
      <span className="flex items-center" style={{ gap: 0 }}>
        <span className="text-[15px] font-semibold tracking-tight" style={{ color: "#F5F5F7" }}>chat</span>
        <RAGText fontSize={15} />
      </span>
    </span>
  );
}

function SourceIcon({ type }: { type: Source["type"] }) {
  if (type === "pdf") return <FileText size={11} className="shrink-0" />;
  if (type === "database") return <Database size={11} className="shrink-0" />;
  return <BookOpen size={11} className="shrink-0" />;
}

function ConfidenceDot({ value }: { value: number }) {
  const color = value >= 90 ? "#10b981" : value >= 75 ? "#f59e0b" : "#ef4444";
  return (
    <span
      className="inline-block w-1.5 h-1.5 rounded-full shrink-0"
      style={{ backgroundColor: color }}
      title={`${value}% confidence`}
    />
  );
}

function SourceChip({
  source,
  onClick,
  active,
}: {
  source: Source;
  onClick: () => void;
  active: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className="group flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-medium transition-all duration-200"
      style={{
        background: active
          ? "rgba(59,130,246,0.15)"
          : "rgba(28,28,30,0.9)",
        border: active
          ? "1px solid rgba(59,130,246,0.4)"
          : "1px solid rgba(255,255,255,0.07)",
        color: active ? "#93c5fd" : "#86868B",
        boxShadow: active ? "0 0 10px rgba(59,130,246,0.12)" : "none",
      }}
    >
      <ConfidenceDot value={source.confidence} />
      <SourceIcon type={source.type} />
      <span className="max-w-[140px] truncate">{source.title}</span>
      <ChevronRight
        size={10}
        className="shrink-0 opacity-40 transition-transform duration-200 group-hover:translate-x-0.5"
      />
    </button>
  );
}

function ChatMessage({
  message,
  onSourceClick,
  activeSource,
}: {
  message: Message;
  onSourceClick: (source: Source) => void;
  activeSource: string | null;
}) {
  const [copied, setCopied] = useState(false);
  const copyText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  if (message.role === "user") {
    return (
      <div className="flex justify-end mb-6 msg-animate">
        <div
          className="max-w-[70%] px-4 py-3 text-sm leading-relaxed"
          style={{ background: "#2C2C2E", borderRadius: "18px 18px 4px 18px", color: "#F5F5F7" }}
        >
          {message.content}
        </div>
      </div>
    );
  }

  const lines = message.content.split("\n");

  return (
    <div className="flex gap-3 mb-8 msg-animate group/msg">
      <LogoIcon size={24} />
      <div className="flex-1 min-w-0">
        <div
          className="text-sm leading-[1.7] mb-3"
          style={{ color: "#F5F5F7" }}
        >
          {lines.map((line, i) => {
            if (line.startsWith("**") && line.endsWith("**")) {
              return (
                <p key={i} className="font-semibold mb-1 mt-3 first:mt-0" style={{ color: "#F5F5F7" }}>
                  {line.slice(2, -2)}
                </p>
              );
            }
            const parts = line.split(/(\*\*[^*]+\*\*)/g);
            return (
              <p key={i} className={line === "" ? "mb-2" : "mb-0"}>
                {parts.map((part, j) =>
                  part.startsWith("**") && part.endsWith("**") ? (
                    <strong key={j} style={{ color: "#F5F5F7", fontWeight: 600 }}>
                      {part.slice(2, -2)}
                    </strong>
                  ) : (
                    <span key={j}>{part}</span>
                  )
                )}
              </p>
            );
          })}
        </div>

        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {message.sources.map((src) => (
              <SourceChip key={src.id} source={src} onClick={() => onSourceClick(src)} active={activeSource === src.id} />
            ))}
          </div>
        )}

        <button
          onClick={() => copyText(message.content)}
          className="mt-2 flex items-center gap-1.5 opacity-0 group-hover/msg:opacity-100 transition-opacity duration-200"
          style={{ color: "#86868B" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "#d1d1d6")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "#86868B")}
        >
          {copied ? <Check size={11} style={{ color: "#10b981" }} /> : <Copy size={11} />}
          <span className="text-[10px]">{copied ? "Copied" : "Copy"}</span>
        </button>
      </div>
    </div>
  );
}

function RAGProcessing({ step, sources }: { step: string; sources: string[] }) {
  const FIXED_STEPS = ["embedding", "searching"];
  const LABELS: Record<string, string> = {
    embedding: "Embedding query...",
    searching: "Searching knowledge base...",
    generating: "Generating answer...",
  };
  const ORDER = ["embedding", "searching", "generating"];
  const currentIdx = ORDER.indexOf(step);

  return (
    <div className="flex gap-3 mb-8">
      <LogoIcon size={24} />
      <div className="flex flex-col gap-1.5 pt-1">
        {ORDER.map((s, i) => {
          const done = i < currentIdx;
          const active = i === currentIdx;
          return (
            <div key={s} className="flex items-center gap-2 transition-all duration-300"
              style={{ opacity: i <= currentIdx ? 1 : 0.2 }}>
              {done
                ? <CheckCircle size={12} style={{ color: "#10b981" }} />
                : <Loader size={12} className={active ? "animate-spin" : ""} style={{ color: "#86868B" }} />}
              <span className="text-sm" style={{ color: done ? "#10b981" : active ? "#d1d1d6" : "#86868B" }}>
                {LABELS[s]}
              </span>
            </div>
          );
        })}
        {sources.length > 0 && (
          <div className="flex flex-col gap-1 ml-5 mt-1">
            {sources.map((f, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <FileText size={10} style={{ color: "#3B82F6" }} />
                <span className="text-[11px]" style={{ color: "#93c5fd" }}>Reading {f}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function useTypewriter(phrases: string[], speed = 55, pause = 1800) {
  const [displayed, setDisplayed] = useState("");
  const [phraseIdx, setPhraseIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const current = phrases[phraseIdx];
    if (!deleting) {
      if (charIdx < current.length) {
        const t = setTimeout(() => setCharIdx((c) => c + 1), speed);
        setDisplayed(current.slice(0, charIdx + 1));
        return () => clearTimeout(t);
      } else {
        const t = setTimeout(() => setDeleting(true), pause);
        return () => clearTimeout(t);
      }
    } else {
      if (charIdx > 0) {
        const t = setTimeout(() => setCharIdx((c) => c - 1), speed / 2);
        setDisplayed(current.slice(0, charIdx - 1));
        return () => clearTimeout(t);
      } else {
        setDeleting(false);
        setPhraseIdx((p) => (p + 1) % phrases.length);
      }
    }
  }, [charIdx, deleting, phraseIdx, phrases, speed, pause]);

  return displayed;
}

function SourcePanel({ source, onClose }: { source: Source; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-stretch justify-end"
      style={{ backdropFilter: "blur(8px)", background: "rgba(0,0,0,0.5)" }}
      onClick={onClose}
    >
      <div
        className="w-[480px] h-full flex flex-col overflow-hidden animate-slide-in"
        style={{
          background: "#1C1C1E",
          borderLeft: "1px solid rgba(255,255,255,0.08)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Panel header */}
        <div
          className="flex items-center justify-between px-6 py-4 shrink-0"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
        >
          <div className="flex items-center gap-2.5">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: "rgba(59,130,246,0.12)", border: "1px solid rgba(59,130,246,0.2)" }}
            >
              <SourceIcon type={source.type} />
            </div>
            <div>
              <p className="text-[13px] font-medium truncate max-w-[300px]" style={{ color: "#F5F5F7" }}>
                {source.title}
              </p>
              <p className="text-[11px]" style={{ color: "#86868B" }}>
                {source.date}{source.page ? ` · Page ${source.page}` : ""}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-lg flex items-center justify-center transition-colors duration-150"
            style={{ color: "#86868B" }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.06)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
          >
            <X size={14} />
          </button>
        </div>

        {/* Confidence bar */}
        <div className="px-6 py-3 shrink-0" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[11px]" style={{ color: "#86868B" }}>Retrieval Confidence</span>
            <span className="text-[11px] font-medium" style={{ color: source.confidence >= 90 ? "#10b981" : "#f59e0b" }}>
              {source.confidence}%
            </span>
          </div>
          <div className="h-1 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
            <div
              className="h-1 rounded-full transition-all duration-500"
              style={{
                width: `${source.confidence}%`,
                background: source.confidence >= 90
                  ? "linear-gradient(90deg, #059669, #10b981)"
                  : "linear-gradient(90deg, #d97706, #f59e0b)",
              }}
            />
          </div>
        </div>

        {/* Excerpt */}
        <div className="flex-1 overflow-y-auto px-6 py-5">
          <p className="text-[11px] font-medium uppercase tracking-widest mb-3" style={{ color: "#86868B" }}>
            Retrieved Excerpt
          </p>
          <div
            className="rounded-xl p-4 text-sm leading-relaxed"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.06)",
              color: "#d1d1d6",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "12.5px",
              lineHeight: "1.75",
            }}
          >
            {source.excerpt}
          </div>

          <div className="mt-6 flex gap-2">
            <button
              className="flex-1 py-2.5 rounded-xl text-xs font-medium transition-all duration-200"
              style={{
                background: "rgba(59,130,246,0.12)",
                border: "1px solid rgba(59,130,246,0.2)",
                color: "#93c5fd",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(59,130,246,0.2)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(59,130,246,0.12)")}
            >
              Open Full Document
            </button>
            <button
              className="px-4 py-2.5 rounded-xl text-xs font-medium transition-all duration-200"
              style={{
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.08)",
                color: "#86868B",
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.08)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.04)")}
            >
              Copy
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const TYPEWRITER_PHRASES = [
  "What's on your mind?",
  "Ask me anything...",
  "Search your documents...",
  "What would you like to know?",
  "Let's explore your knowledge base.",
];

function TypewriterSubtitle() {
  const text = useTypewriter(TYPEWRITER_PHRASES);
  return (
    <p className="text-sm" style={{ color: "rgba(134,134,139,0.65)", minHeight: "1.4em" }}>
      {text}
      <span className="inline-block w-[2px] h-[0.9em] ml-0.5 align-middle animate-pulse"
        style={{ background: "rgba(134,134,139,0.5)" }} />
    </p>
  );
}

function EmptyState({ onSuggestion, suggestions, loadingSuggestions }: {
  onSuggestion: (text: string) => void;
  suggestions: Suggestion[];
  loadingSuggestions: boolean;
}) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 pb-24">
      {/* Faded logo */}
      <div className="mb-12 text-center">
        <div className="mb-5 flex items-center justify-center gap-3">
          <img
            src="/favicon-96x96.png"
            alt="chatRAG"
            style={{ width: 48, height: 48, borderRadius: 15 }}
          />

          <div className="flex items-center gap-0">
            <span
              className="text-[2.6rem] font-semibold tracking-tight leading-none"
              style={{ color: "rgba(245,245,247,0.18)" }}
            >
              chat
            </span>
            <span
              className="leading-none"
            >
              <RAGText fontSize={41} opacity={0.4} />
            </span>
          </div>
        </div>
        <TypewriterSubtitle />
      </div>

      {/* Suggestion cards */}
      <div className="grid grid-cols-2 gap-3 w-full max-w-xl">
        {loadingSuggestions
          ? [...Array(4)].map((_, i) => (
              <div key={i} className="h-[84px] rounded-2xl animate-pulse" style={{ background: "rgba(28,28,30,0.5)", border: "1px solid rgba(255,255,255,0.05)" }} />
            ))
          : suggestions.map((s, i) => {
              const Icon = SUGGESTION_ICONS[i % SUGGESTION_ICONS.length];
              return (
                <button
                  key={i}
                  onClick={() => onSuggestion(s.title)}
                  className="group flex flex-col gap-2 p-4 rounded-2xl text-left transition-all duration-250"
                  style={{
                    background: "rgba(28,28,30,0.7)",
                    border: "1px solid rgba(255,255,255,0.07)",
                    backdropFilter: "blur(12px)",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "rgba(28,28,30,0.95)";
                    e.currentTarget.style.borderColor = "rgba(59,130,246,0.25)";
                    e.currentTarget.style.boxShadow = "0 0 20px rgba(59,130,246,0.07)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "rgba(28,28,30,0.7)";
                    e.currentTarget.style.borderColor = "rgba(255,255,255,0.07)";
                    e.currentTarget.style.boxShadow = "none";
                  }}
                >
                  <div
                    className="w-7 h-7 rounded-lg flex items-center justify-center"
                    style={{ background: "rgba(59,130,246,0.1)", color: "#3B82F6" }}
                  >
                    <Icon size={14} />
                  </div>
                  <div>
                    <p className="text-[13px] font-medium" style={{ color: "#F5F5F7" }}>{s.title}</p>
                    <p className="text-[11px] mt-0.5" style={{ color: "#86868B" }}>{s.subtitle}</p>
                  </div>
                </button>
              );
            })}
      </div>
    </div>
  );
}

const STATUS_LABEL: Record<UploadJob["status"], string> = {
  queued: "Queued",
  extracting: "Extracting text...",
  chunking: "Chunking...",
  embedding: "Embedding...",
  completed: "Ready",
  failed: "Failed",
};

function SyncPanel({ onUploaded, onToast, targetCollection = "default" }: {
  onUploaded: (job: UploadJob) => void;
  onToast: (msg: string, type: Toast["type"]) => void;
  targetCollection?: string;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState({ done: 0, total: 0 });

  const uploadFiles = async (files: File[]) => {
    for (const file of files) {
      const form = new FormData();
      form.append("file", file);
      form.append("collection", targetCollection);
      onToast(`Uploading "${file.name}"...`, "info");
      try {
        const res = await fetch("/ingest/upload", { method: "POST", body: form });
        if (!res.ok) { onToast(`Failed to upload "${file.name}"`, "error"); continue; }
        const data = await res.json();
        onUploaded({ jobId: data.job_id, filename: file.name, status: "queued" });
        setSyncProgress((p) => ({ ...p, done: p.done + 1 }));
      } catch { onToast(`Failed to upload "${file.name}"`, "error"); }
    }
  };

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const valid = Array.from(files).filter((f) => /\.(pdf|png|jpg|jpeg|docx|xlsx)$/i.test(f.name));
    uploadFiles(valid);
  };

  const handleFolder = async (files: FileList | null) => {
    if (!files) return;
    const valid = Array.from(files).filter((f) => /\.(pdf|png|jpg|jpeg|docx|xlsx)$/i.test(f.name));
    if (!valid.length) return;
    setSyncing(true);
    setSyncProgress({ done: 0, total: valid.length });
    await uploadFiles(valid);
    setSyncing(false);
  };

  return (
    <div className="mx-3 mb-2 flex flex-col gap-1.5">
      <input ref={fileInputRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx" multiple className="hidden"
        onChange={(e) => handleFiles(e.target.files)} />
      <input ref={folderInputRef} type="file" className="hidden" {...({ webkitdirectory: "" } as object)}
        onChange={(e) => handleFolder((e.target as HTMLInputElement).files)} />

      {targetCollection !== "default" && (
        <p className="text-[10px] px-1 pb-0.5" style={{ color: "rgba(134,134,139,0.5)" }}>
          → <span style={{ color: "#93c5fd" }}>{targetCollection}</span>
        </p>
      )}

      <button
        onClick={() => fileInputRef.current?.click()}
        className="flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] font-medium transition-all duration-200"
        style={{ border: "1px dashed rgba(255,255,255,0.1)", color: "#86868B" }}
        onMouseEnter={(e) => { e.currentTarget.style.borderColor = "rgba(59,130,246,0.4)"; e.currentTarget.style.color = "#d1d1d6"; }}
        onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; e.currentTarget.style.color = "#86868B"; }}
      >
        <Upload size={12} />
        Upload files
      </button>

      <button
        onClick={() => folderInputRef.current?.click()}
        disabled={syncing}
        className="flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] font-medium transition-all duration-200"
        style={{
          border: "1px solid rgba(59,130,246,0.25)",
          color: syncing ? "#86868B" : "#93c5fd",
          background: "rgba(59,130,246,0.06)",
          cursor: syncing ? "not-allowed" : "pointer",
        }}
      >
        {syncing
          ? <><RefreshCw size={12} className="animate-spin" />Syncing {syncProgress.done}/{syncProgress.total}...</>
          : <><FolderOpen size={12} />Sync folder</>
        }
      </button>
    </div>
  );
}

const STATUS_FALLBACK_PCT: Record<UploadJob["status"], number> = {
  queued: 0, extracting: 10, chunking: 55, embedding: 65, completed: 100, failed: 100,
};

function JobBadge({ job }: { job: UploadJob }) {
  const pct = job.progress ?? STATUS_FALLBACK_PCT[job.status];
  const isRunning = !["completed", "failed"].includes(job.status);
  const color = job.status === "completed" ? "#10b981" : job.status === "failed" ? "#ef4444" : "#3B82F6";
  const icon = job.status === "completed"
    ? <CheckCircle size={11} style={{ color: "#10b981" }} />
    : job.status === "failed"
    ? <AlertCircle size={11} style={{ color: "#ef4444" }} />
    : <Loader size={11} className="animate-spin" style={{ color: "#3B82F6" }} />;

  return (
    <div className="flex items-center gap-2 px-2.5 py-2 rounded-lg mx-3 mb-1"
      style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
      {icon}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <p className="text-[11px] truncate max-w-[120px]" style={{ color: isRunning ? "#d1d1d6" : color }}>
            {job.filename}
          </p>
          <span className="text-[10px] shrink-0 ml-1" style={{ color }}>
            {pct}%
          </span>
        </div>
        <div className="h-[3px] rounded-full w-full" style={{ background: "rgba(255,255,255,0.07)" }}>
          <div
            className="h-[3px] rounded-full transition-all duration-500"
            style={{
              width: `${pct}%`,
              background: job.status === "failed"
                ? "#ef4444"
                : `linear-gradient(90deg, #2563EB, ${job.status === "completed" ? "#10b981" : "#3B82F6"})`,
            }}
          />
        </div>
        <p className="text-[10px] mt-0.5" style={{ color: "rgba(134,134,139,0.6)" }}>
          {STATUS_LABEL[job.status]}
        </p>
      </div>
    </div>
  );
}

function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: string) => void }) {
  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="animate-toast-in flex items-center gap-2.5 px-4 py-3 rounded-2xl pointer-events-auto"
          style={{
            background: t.type === "success" ? "rgba(16,185,129,0.12)" : t.type === "error" ? "rgba(239,68,68,0.12)" : "rgba(59,130,246,0.12)",
            border: `1px solid ${t.type === "success" ? "rgba(16,185,129,0.35)" : t.type === "error" ? "rgba(239,68,68,0.35)" : "rgba(59,130,246,0.35)"}`,
            backdropFilter: "blur(16px)",
            boxShadow: "0 4px 24px rgba(0,0,0,0.35)",
          }}
        >
          {t.type === "success"
            ? <CheckCircle size={14} style={{ color: "#10b981", flexShrink: 0 }} />
            : t.type === "error"
            ? <AlertCircle size={14} style={{ color: "#ef4444", flexShrink: 0 }} />
            : <Loader size={14} className="animate-spin shrink-0" style={{ color: "#93c5fd" }} />}
          <span className="text-[12px] font-medium" style={{ color: t.type === "success" ? "#10b981" : t.type === "error" ? "#ef4444" : "#93c5fd" }}>
            {t.msg}
          </span>
          <button onClick={() => onDismiss(t.id)} className="ml-2 shrink-0" style={{ color: "rgba(255,255,255,0.25)" }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.6)")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.25)")}
          >
            <X size={11} />
          </button>
        </div>
      ))}
    </div>
  );
}

const GROQ_MODELS = [
  { id: "llama-3.3-70b-versatile", label: "Llama 3.3 · 70B", note: "Best" },
  { id: "llama-3.1-8b-instant",    label: "Llama 3.1 · 8B",  note: "Fast" },
  { id: "gemma2-9b-it",            label: "Gemma 2 · 9B",    note: "Google" },
  { id: "openai/gpt-oss-20b",      label: "GPT-OSS · 20B",   note: "OpenAI" },
];

const MODELS = [
  { id: "gemma3:4b",        label: "Gemma 3 · 4B",   note: "Fast" },
  { id: "qwen2.5-coder:7b", label: "Qwen 2.5 · 7B",  note: "Better" },
  { id: "gemma3:12b",       label: "Gemma 3 · 12B",   note: "OOM ⚠" },
];

function fileIcon(name: string) {
  const ext = name.split(".").pop()?.toLowerCase();
  if (ext === "pdf")  return <FileText size={12} style={{ color: "#f87171", flexShrink: 0 }} />;
  if (ext === "xlsx" || ext === "xls") return <Table2 size={12} style={{ color: "#4ade80", flexShrink: 0 }} />;
  if (ext === "docx" || ext === "doc") return <FileType2 size={12} style={{ color: "#60a5fa", flexShrink: 0 }} />;
  return <FileText size={12} style={{ color: "#a3a3a3", flexShrink: 0 }} />;
}

function ScopePicker({ scope, collections, onChange }: {
  scope: ChatScope;
  collections: Collection[];
  onChange: (s: ChatScope) => void;
}) {
  const [open, setOpen] = useState(false);
  const total = collections.reduce((s, c) => s + c.doc_count, 0);

  const selectedCols = scope.type === "selected" ? scope.collections : [];
  const selectedCount = scope.type === "selected"
    ? selectedCols.reduce((s, n) => s + (collections.find(c => c.name === n)?.doc_count ?? 0), 0)
    : total;

  const label = scope.type === "all"
    ? `All · ${total} files`
    : selectedCols.length === 1
      ? `${selectedCols[0]} · ${selectedCount} files`
      : `${selectedCols.length} folders · ${selectedCount} files`;

  const toggle = (name: string) => {
    const cur = scope.type === "selected" ? scope.collections : [];
    const next = cur.includes(name) ? cur.filter(c => c !== name) : [...cur, name];
    onChange(next.length === 0 ? { type: "all" } : { type: "selected", collections: next });
  };

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (!(e.target as HTMLElement).closest("[data-scope-picker]")) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <div className="relative" data-scope-picker="">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium transition-all"
        style={{
          border: `1px solid ${scope.type === "selected" ? "rgba(59,130,246,0.4)" : "rgba(255,255,255,0.1)"}`,
          color: scope.type === "selected" ? "#93c5fd" : "rgba(134,134,139,0.7)",
          background: scope.type === "selected" ? "rgba(59,130,246,0.1)" : "transparent",
        }}
      >
        <FolderOpen size={11} />
        {label}
        <ChevronDown size={10} />
      </button>

      {open && (
        <div
          className="absolute bottom-full mb-2 left-0 rounded-xl overflow-hidden z-50"
          style={{ minWidth: 220, background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 -8px 32px rgba(0,0,0,0.5)" }}
          data-scope-picker=""
        >
          <button
            onClick={() => { onChange({ type: "all" }); setOpen(false); }}
            className="w-full flex items-center justify-between px-3 py-2.5 text-[12px] transition-colors"
            style={{
              background: scope.type === "all" ? "rgba(59,130,246,0.12)" : "transparent",
              color: scope.type === "all" ? "#93c5fd" : "#c7c7cc",
              borderBottom: "1px solid rgba(255,255,255,0.06)",
            }}
            onMouseEnter={(e) => { if (scope.type !== "all") e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
            onMouseLeave={(e) => { if (scope.type !== "all") e.currentTarget.style.background = "transparent"; }}
          >
            <span className="flex items-center gap-2 font-medium">
              {scope.type === "all" && <span style={{ color: "#93c5fd" }}>✓</span>}
              All files
            </span>
            <span className="text-[10px]" style={{ color: "rgba(134,134,139,0.5)" }}>{total}</span>
          </button>

          {collections.map(col => {
            const isSelected = scope.type === "selected" && selectedCols.includes(col.name);
            return (
              <button
                key={col.name}
                onClick={() => toggle(col.name)}
                className="w-full flex items-center justify-between px-3 py-2 text-[12px] transition-colors"
                style={{
                  background: isSelected ? "rgba(59,130,246,0.1)" : "transparent",
                  color: isSelected ? "#93c5fd" : "#c7c7cc",
                }}
                onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
                onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.background = "transparent"; }}
              >
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded flex items-center justify-center text-[9px]"
                    style={{ border: `1px solid ${isSelected ? "#93c5fd" : "rgba(255,255,255,0.2)"}`, color: "#93c5fd" }}>
                    {isSelected ? "✓" : ""}
                  </span>
                  <FolderOpen size={11} style={{ opacity: 0.6 }} />
                  {col.name}
                </span>
                <span className="text-[10px]" style={{ color: "rgba(134,134,139,0.5)" }}>{col.doc_count}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────

export default function App() {
  const [chats, setChats] = useState<Chat[]>(loadChatsFromStorage);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [inputFocused, setInputFocused] = useState(false);
  const activeChat = chats.find((c) => c.id === activeChatId) ?? null;
  const [activeSource, setActiveSource] = useState<Source | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState("embedding");
  const [readingSources, setReadingSources] = useState<string[]>([]);
  const [activeSourceId, setActiveSourceId] = useState<string | null>(null);
  const [uploadJobs, setUploadJobs] = useState<UploadJob[]>([]);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [kbDocs, setKbDocs] = useState<KBDocument[]>([]);
  const [kbOpen, setKbOpen] = useState(false);
  const [kbLoading, setKbLoading] = useState(false);
  const [kbFilter, setKbFilter] = useState<string | null>(null);
  const [pendingFolders, setPendingFolders] = useState<string[]>([]);
  const [addingFolder, setAddingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [chatScope, setChatScope] = useState<ChatScope>({ type: "all" });
  const [collections, setCollections] = useState<Collection[]>([]);
  const [hybridMode, setHybridMode] = useState(() => localStorage.getItem("chatrag_hybrid") === "true");
  const [activeModel, setActiveModel] = useState(() => {
    const stored = localStorage.getItem("chatrag_model") || "gemma3:4b";
    const decommissioned: Record<string, string> = {
      "llama3-8b-8192": "llama-3.1-8b-instant",
      "mixtral-8x7b-32768": "llama-3.3-70b-versatile",
      "llama3-70b-8192": "llama-3.3-70b-versatile",
    };
    if (decommissioned[stored]) {
      localStorage.setItem("chatrag_model", decommissioned[stored]);
      return decommissioned[stored];
    }
    return stored;
  });
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const modelMenuRef = useRef<HTMLDivElement>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(true);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(["default"]));
  const [renamingFolder, setRenamingFolder] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const [movingDoc, setMovingDoc] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState<string | null>(null);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [modelSettingsOpen, setModelSettingsOpen] = useState(false);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("chatrag_api_key") || "");
  const [showApiKey, setShowApiKey] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const addToast = useCallback((msg: string, type: Toast["type"] = "info") => {
    const id = Date.now().toString();
    setToasts((prev) => [...prev, { id, msg, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const pollJob = useCallback((jobId: string, filename: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/ingest/jobs/${jobId}`);
        if (!res.ok) return;
        const data = await res.json();
        const status = data.status as UploadJob["status"];
        const progress = data.progress !== undefined ? parseInt(data.progress) : undefined;
        setUploadJobs((prev) => prev.map((j) => j.jobId === jobId ? { ...j, status, step: data.step, error: data.error, progress } : j));
        if (status === "completed") {
          addToast(`"${filename}" is ready to query`, "success");
          clearInterval(interval);
        } else if (status === "failed") {
          addToast(`"${filename}" failed to process`, "error");
          clearInterval(interval);
        }
      } catch { clearInterval(interval); }
    }, 2000);
  }, [addToast]);

  const loadKbDocs = useCallback(async () => {
    setKbLoading(true);
    try {
      const res = await fetch("/ingest/documents");
      if (res.ok) setKbDocs(await res.json());
    } finally {
      setKbLoading(false);
    }
  }, []);

  const fetchCollections = useCallback(async () => {
    const res = await fetch("/ingest/collections");
    if (res.ok) setCollections(await res.json());
  }, []);

  const fetchSuggestions = useCallback(async (scope: ChatScope) => {
    setLoadingSuggestions(true);
    try {
      const param = scope.type === "selected"
        ? `?collections=${scope.collections.map(encodeURIComponent).join(",")}`
        : "";
      const res = await fetch(`/chat/suggestions${param}`);
      if (res.ok) setSuggestions(await res.json());
    } finally {
      setLoadingSuggestions(false);
    }
  }, []);

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsProcessing(false);
    setReadingSources([]);
  }, []);

  const deleteKbDoc = useCallback(async (docId: string, name: string) => {
    await fetch(`/ingest/documents/${docId}`, { method: "DELETE" });
    setKbDocs((prev) => prev.filter((d) => d.document_id !== docId));
    addToast(`Deleted "${name}"`, "info");
  }, [addToast]);

  const renameFolder = useCallback(async (oldName: string, newName: string) => {
    try {
      const res = await fetch(`/ingest/collections/${encodeURIComponent(oldName)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_name: newName }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
    } catch (err) {
      addToast(`Đổi tên thất bại: ${err}`, "error");
      return;
    }
    setKbFilter((f) => (f === oldName ? newName : f));
    setPendingFolders((prev) => prev.map((f) => (f === oldName ? newName : f)));
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(oldName)) { next.delete(oldName); next.add(newName); }
      return next;
    });
    addToast(`Đã đổi tên thành "${newName}"`, "success");
    await fetchCollections();
    await loadKbDocs();
  }, [fetchCollections, loadKbDocs, addToast]);

  const deleteFolder = useCallback(async (name: string) => {
    await fetch(`/ingest/collections/${encodeURIComponent(name)}`, { method: "DELETE" });
    setKbFilter((f) => (f === name ? null : f));
    setPendingFolders((prev) => prev.filter((f) => f !== name));
    setExpandedFolders((prev) => { const next = new Set(prev); next.delete(name); return next; });
    setConfirmingDelete(null);
    await fetchCollections();
    await loadKbDocs();
  }, [fetchCollections, loadKbDocs]);

  const moveDocument = useCallback(async (docId: string, targetCollection: string) => {
    await fetch(`/ingest/documents/${docId}/collection`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ collection: targetCollection }),
    });
    setMovingDoc(null);
    await fetchCollections();
    await loadKbDocs();
  }, [fetchCollections, loadKbDocs]);

  const folderMap = useMemo(() => {
    const map: Record<string, KBDocument[]> = {};
    for (const doc of kbDocs) {
      const col = doc.collection || "default";
      if (!map[col]) map[col] = [];
      map[col].push(doc);
    }
    for (const col of collections) {
      if (!map[col.name]) map[col.name] = [];
    }
    for (const pf of pendingFolders) {
      if (!map[pf]) map[pf] = [];
    }
    return map;
  }, [kbDocs, collections, pendingFolders]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  useEffect(() => {
    if (!modelMenuOpen) return;
    const close = (e: MouseEvent) => {
      if (modelMenuRef.current?.contains(e.target as Node)) return;
      setModelMenuOpen(false);
      setModelSettingsOpen(false);
    };
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [modelMenuOpen]);

  useEffect(() => {
    fetchCollections();
    fetchSuggestions({ type: "all" });
    loadKbDocs();
  }, []);

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  };

  const persistChat = useCallback((chatId: string, updatedMessages: Message[]) => {
    setChats((prev) => {
      const updated = prev.map((c) => c.id === chatId ? { ...c, messages: updatedMessages } : c);
      saveChatsToStorage(updated);
      return updated;
    });
  }, []);

  const sendMessage = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || isProcessing) return;

    const userMsg: Message = { id: Date.now().toString(), role: "user", content };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setIsProcessing(true);
    setProcessingStep("embedding");
    setReadingSources([]);

    let chatId = activeChatId;
    if (!chatId) {
      chatId = Date.now().toString();
      const title = content.length > 48 ? content.slice(0, 48) + "…" : content;
      const newChat: Chat = { id: chatId, title, createdAt: Date.now(), messages: nextMessages };
      setChats((prev) => { const u = [newChat, ...prev]; saveChatsToStorage(u); return u; });
      setActiveChatId(chatId);
    } else {
      persistChat(chatId, nextMessages);
    }

    const aiId = (Date.now() + 1).toString();
    let finalSources: Source[] = [];

    try {
      const controller = new AbortController();
      abortControllerRef.current = controller;
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          question: content,
          collections: chatScope.type === "selected" ? chatScope.collections : null,
          hybrid: hybridMode,
          model: activeModel,
          ...(apiKey ? { api_key: apiKey } : {}),
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      // Read the full SSE response into a single string, then parse events.
      // This is simpler and avoids closure/chunk-boundary bugs with streaming.
      const raw = await res.text();

      for (const line of raw.split("\n")) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) continue;
        let ev: Record<string, unknown>;
        try { ev = JSON.parse(trimmed.slice(6)); } catch { continue; }

        if (ev.type === "step") {
          setProcessingStep(ev.step as string);
        } else if (ev.type === "sources") {
          const srcs = ev.sources as Array<{ id: string; content: string; section?: string; similarity: number; filename: string }>;
          setReadingSources(srcs.map((s) => s.filename));
          finalSources = srcs.map((s, i) => ({
            id: `src-${Date.now()}-${i}`,
            title: s.section ?? s.filename ?? `Source ${i + 1}`,
            type: (s.filename?.endsWith(".pdf") ? "pdf" : "doc") as Source["type"],
            excerpt: s.content,
            date: new Date().toISOString().slice(0, 10),
            confidence: Math.round(s.similarity * 100),
          }));
        } else if (ev.type === "token") {
          const token = ev.token as string;
          setIsProcessing(false);
          setMessages((prev) => {
            const existing = prev.find((m) => m.id === aiId);
            const newContent = (existing?.content ?? "") + token;
            if (existing) return prev.map((m) => m.id === aiId ? { ...m, content: newContent, isStreaming: true } : m);
            return [...prev, { id: aiId, role: "assistant" as const, content: newContent, isStreaming: true }];
          });
        } else if (ev.type === "done" && (ev.sources as unknown[])?.length > 0) {
          finalSources = (ev.sources as Array<{ id: string; content: string; section?: string; similarity: number; filename: string }>).map((s, i) => ({
            id: `src-${Date.now()}-${i}`,
            title: s.section ?? s.filename ?? `Source ${i + 1}`,
            type: (s.filename?.endsWith(".pdf") ? "pdf" : "doc") as Source["type"],
            excerpt: s.content,
            date: new Date().toISOString().slice(0, 10),
            confidence: Math.round(s.similarity * 100),
          }));
        }
      }

      // Finalize: mark streaming done, attach sources, fallback if empty
      setMessages((prev) => {
        const existing = prev.find((m) => m.id === aiId);
        const content = existing?.content?.trim() ? existing.content : "No answer returned.";
        const finalMsg: Message = { id: aiId, role: "assistant", content, sources: finalSources, isStreaming: false };
        return existing
          ? prev.map((m) => m.id === aiId ? finalMsg : m)
          : [...prev, finalMsg];
      });

      // Persist after state settles
      setTimeout(() => {
        setMessages((prev) => {
          const finalMsg = prev.find((m) => m.id === aiId);
          if (finalMsg) persistChat(chatId, [...nextMessages, finalMsg]);
          return prev;
        });
      }, 0);
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        // User stopped generation — leave partial message as-is
      } else {
        const errMsg: Message = {
          id: aiId,
          role: "assistant",
          content: "Something went wrong connecting to the knowledge base. Please try again.",
        };
        setMessages((prev) => [...prev, errMsg]);
        persistChat(chatId, [...nextMessages, errMsg]);
      }
    } finally {
      setIsProcessing(false);
      setReadingSources([]);
    }
  };

  const loadChat = (chat: Chat) => {
    setActiveChatId(chat.id);
    setMessages(chat.messages);
    setActiveSource(null);
    setActiveSourceId(null);
  };

  const newChat = () => {
    setMessages([]);
    setActiveChatId(null);
    setActiveSource(null);
    setActiveSourceId(null);
    setInput("");
  };

  const deleteChat = (chatId: string) => {
    setChats((prev) => {
      const updated = prev.filter((c) => c.id !== chatId);
      saveChatsToStorage(updated);
      return updated;
    });
    if (activeChatId === chatId) newChat();
  };

  const handleSourceClick = (source: Source) => {
    if (activeSourceId === source.id) {
      setActiveSource(null);
      setActiveSourceId(null);
    } else {
      setActiveSource(source);
      setActiveSourceId(source.id);
    }
  };

  const isEmpty = messages.length === 0 && !isProcessing;

  return (
    <div
      className="flex h-screen w-screen overflow-hidden"
      style={{ background: "#121214", fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" }}
    >
      {/* ── Sidebar ── */}
      <aside
        className="w-[240px] shrink-0 flex flex-col h-full"
        style={{
          background: "rgba(28,28,30,0.85)",
          backdropFilter: "blur(20px)",
          borderRight: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        {/* Sidebar top */}
        <div className="px-3 pt-4 pb-2">
          <div className="flex items-center justify-between px-2 mb-3">
            <Logo />
            <button
              onClick={() => { setShowSearch((s) => !s); setSearchQuery(""); }}
              className="w-6 h-6 flex items-center justify-center rounded-md transition-colors duration-150"
              style={{ color: showSearch ? "#93c5fd" : "#86868B", background: showSearch ? "rgba(59,130,246,0.1)" : "transparent" }}
              onMouseEnter={(e) => { if (!showSearch) e.currentTarget.style.color = "#F5F5F7"; }}
              onMouseLeave={(e) => { if (!showSearch) e.currentTarget.style.color = "#86868B"; }}
            >
              <Search size={13} />
            </button>
          </div>
          {showSearch && (
            <div className="px-2 mb-2">
              <input
                autoFocus
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Escape") { setShowSearch(false); setSearchQuery(""); } }}
                placeholder="Search chats…"
                className="w-full px-2.5 py-1.5 rounded-lg text-[11px] outline-none"
                style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#c7c7cc" }}
              />
            </div>
          )}
          {/* New Chat */}
          <button
            onClick={newChat}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-[12px] font-medium transition-all duration-200"
            style={{
              border: "1px solid rgba(255,255,255,0.08)",
              color: "#86868B",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "rgba(59,130,246,0.4)";
              e.currentTarget.style.color = "#F5F5F7";
              e.currentTarget.style.boxShadow = "0 0 12px rgba(59,130,246,0.12)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
              e.currentTarget.style.color = "#86868B";
              e.currentTarget.style.boxShadow = "none";
            }}
          >
            <Plus size={12} />
            New Chat
          </button>
        </div>

        {/* History */}
        <div className="flex-1 overflow-y-auto px-3 py-2 scrollbar-hide">
          {chats.length === 0 ? (
            <p className="text-center text-[11px] py-4" style={{ color: "rgba(134,134,139,0.4)" }}>No chats yet</p>
          ) : (
            (["today", "week", "older"] as const).map((group) => {
              const items = chats
                .filter((c) => chatGroup(c.createdAt) === group)
                .filter((c) => !searchQuery || c.title.toLowerCase().includes(searchQuery.toLowerCase()));
              if (items.length === 0) return null;
              const label = group === "today" ? "Today" : group === "week" ? "Previous 7 Days" : "Older";
              return (
                <div key={group} className="mb-4">
                  <p className="text-[10px] font-medium uppercase tracking-widest px-2 mb-1.5"
                    style={{ color: "rgba(134,134,139,0.5)" }}>{label}</p>
                  {items.map((chat) => (
                    <div key={chat.id} className="group relative mb-0.5">
                      <button
                        onClick={() => loadChat(chat)}
                        className="w-full text-left px-2.5 py-2 rounded-lg transition-all duration-150 pr-7"
                        style={{
                          background: activeChatId === chat.id ? "rgba(59,130,246,0.1)" : "transparent",
                          border: activeChatId === chat.id ? "1px solid rgba(59,130,246,0.15)" : "1px solid transparent",
                        }}
                        onMouseEnter={(e) => {
                          if (activeChatId !== chat.id)
                            e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                        }}
                        onMouseLeave={(e) => {
                          if (activeChatId !== chat.id)
                            e.currentTarget.style.background = "transparent";
                        }}
                      >
                        <p className="text-[12px] font-medium truncate"
                          style={{ color: activeChatId === chat.id ? "#93c5fd" : "#d1d1d6" }}>
                          {chat.title}
                        </p>
                      </button>
                      <button
                        onClick={() => deleteChat(chat.id)}
                        className="absolute right-1.5 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded"
                        style={{ color: "#ef4444" }}
                        title="Delete"
                      >
                        <X size={11} />
                      </button>
                    </div>
                  ))}
                </div>
              );
            })
          )}
        </div>

        {/* Knowledge Base */}
        <div className="flex flex-col min-h-0 flex-1 overflow-hidden" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>

          {/* KB header */}
          <div className="flex items-center justify-between px-3 pt-3 pb-1.5 shrink-0 gap-2">
            <span className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-widest shrink-0" style={{ color: "rgba(134,134,139,0.5)" }}>
              <Database size={10} />
              Knowledge base
              {kbDocs.length > 0 && (
                <span className="px-1.5 py-0.5 rounded-full text-[9px] font-bold" style={{ background: "rgba(59,130,246,0.15)", color: "#93c5fd" }}>
                  {kbDocs.length}
                </span>
              )}
            </span>
            {addingFolder ? (
              <div className="flex items-center gap-1 flex-1">
                <input
                  autoFocus
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && newFolderName.trim()) {
                      const name = newFolderName.trim();
                      if (!collections.some(c => c.name === name) && !pendingFolders.includes(name)) {
                        setPendingFolders((prev) => [...prev, name]);
                        setExpandedFolders((prev) => new Set([...prev, name]));
                      }
                      setKbFilter(name);
                      setAddingFolder(false);
                      setNewFolderName("");
                    }
                    if (e.key === "Escape") { setAddingFolder(false); setNewFolderName(""); }
                  }}
                  placeholder="Folder name…"
                  className="flex-1 px-2 py-0.5 rounded-md text-[10px] min-w-0"
                  style={{ background: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.35)", color: "#c7c7cc", outline: "none" }}
                />
                <button onClick={() => { setAddingFolder(false); setNewFolderName(""); }} style={{ color: "#86868B" }}>
                  <X size={10} />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-1">
                <button onClick={() => setAddingFolder(true)} className="p-1 rounded opacity-50 hover:opacity-100 transition-opacity" title="New folder">
                  <Plus size={10} style={{ color: "#86868B" }} />
                </button>
                <button onClick={() => { loadKbDocs(); fetchCollections(); }} className="p-1 rounded opacity-40 hover:opacity-100 transition-opacity" title="Refresh">
                  <RefreshCw size={10} style={{ color: "#86868B" }} className={kbLoading ? "animate-spin" : ""} />
                </button>
              </div>
            )}
          </div>

          {/* Folder accordion */}
          <div className="overflow-y-auto scrollbar-hide flex-1 px-2 pb-1">
            {kbLoading ? (
              <div className="flex items-center justify-center py-5 gap-2" style={{ color: "#86868B" }}>
                <Loader size={12} className="animate-spin" /><span className="text-[11px]">Loading…</span>
              </div>
            ) : Object.keys(folderMap).length === 0 ? (
              <div className="flex flex-col items-center justify-center py-5 gap-1">
                <Database size={18} style={{ color: "rgba(134,134,139,0.2)" }} />
                <p className="text-[10px]" style={{ color: "rgba(134,134,139,0.35)" }}>No files yet</p>
              </div>
            ) : Object.entries(folderMap)
                .sort(([a], [b]) => a === "default" ? -1 : b === "default" ? 1 : a.localeCompare(b))
                .map(([folderName, files]) => {
                  const isExpanded = expandedFolders.has(folderName);
                  const isPending = pendingFolders.includes(folderName) && !collections.some(c => c.name === folderName);
                  const isKbSelected = kbFilter === folderName;
                  return (
                    <div key={folderName} className="mb-0.5">
                      <div
                        className="group/folder flex items-center gap-1.5 px-2 py-1.5 rounded-lg"
                        style={{ background: isKbSelected ? "rgba(59,130,246,0.1)" : "transparent" }}
                        onMouseEnter={(e) => { if (!isKbSelected) e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = isKbSelected ? "rgba(59,130,246,0.1)" : "transparent"; }}
                      >
                        <button
                          onClick={() => setExpandedFolders((prev) => {
                            const next = new Set(prev);
                            next.has(folderName) ? next.delete(folderName) : next.add(folderName);
                            return next;
                          })}
                          className="flex-shrink-0"
                          style={{ color: "#4a9eff" }}
                        >
                          {isExpanded ? <ChevronDown size={10} /> : <ChevronRight size={10} />}
                        </button>
                        <FolderOpen size={11} style={{ color: isKbSelected ? "#93c5fd" : "#6b9fd4", flexShrink: 0 }} />
                        {renamingFolder === folderName ? (
                          <input
                            autoFocus
                            value={renameValue}
                            onChange={(e) => setRenameValue(e.target.value)}
                            onFocus={(e) => e.target.select()}
                            onKeyDown={(e) => {
                              e.stopPropagation();
                              if (e.key === "Enter") {
                                const val = renameValue.trim();
                                setRenamingFolder(null);
                                if (val && val !== folderName) renameFolder(folderName, val);
                              }
                              if (e.key === "Escape") setRenamingFolder(null);
                            }}
                            onBlur={() => setRenamingFolder(null)}
                            className="flex-1 text-[11px] bg-transparent outline-none"
                            style={{ border: "0.5px solid rgba(59,130,246,0.4)", borderRadius: 4, padding: "1px 4px", color: "#c7c7cc" }}
                            onClick={(e) => e.stopPropagation()}
                          />
                        ) : (
                          <button
                            className="flex-1 text-left text-[11px] truncate"
                            style={{ color: isKbSelected ? "#93c5fd" : "#c7c7cc" }}
                            onClick={() => setKbFilter(kbFilter === folderName ? null : folderName)}
                          >
                            {folderName}
                            {isPending && <span style={{ color: "rgba(134,134,139,0.4)", fontSize: 9 }}> ·new</span>}
                          </button>
                        )}
                        <span className="text-[9px] flex-shrink-0" style={{ color: "rgba(134,134,139,0.4)" }}>{files.length}</span>
                        {confirmingDelete === folderName ? (
                          <div className="flex items-center gap-1 flex-shrink-0">
                            <span className="text-[9px]" style={{ color: "#f87171" }}>Xóa?</span>
                            <button
                              onClick={(e) => { e.stopPropagation(); deleteFolder(folderName); }}
                              className="px-1.5 py-0.5 rounded text-[9px] font-medium"
                              style={{ background: "rgba(239,68,68,0.15)", color: "#f87171", border: "1px solid rgba(239,68,68,0.3)" }}
                            >
                              Có
                            </button>
                            <button
                              onClick={(e) => { e.stopPropagation(); setConfirmingDelete(null); }}
                              className="px-1.5 py-0.5 rounded text-[9px]"
                              style={{ color: "#86868B", border: "1px solid rgba(255,255,255,0.1)" }}
                            >
                              Không
                            </button>
                          </div>
                        ) : (
                          <div className="opacity-0 group-hover/folder:opacity-100 flex gap-0.5 flex-shrink-0">
                            <button
                              onClick={(e) => { e.stopPropagation(); setRenamingFolder(folderName); setRenameValue(folderName); }}
                              className="p-0.5 rounded"
                              style={{ color: "#86868B" }}
                              title="Rename"
                              onMouseEnter={(e) => { e.currentTarget.style.color = "#c7c7cc"; (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.06)"; }}
                              onMouseLeave={(e) => { e.currentTarget.style.color = "#86868B"; (e.currentTarget as HTMLElement).style.background = "transparent"; }}
                            >
                              <Pencil size={9} />
                            </button>
                            <button
                              onClick={(e) => { e.stopPropagation(); setConfirmingDelete(folderName); }}
                              className="p-0.5 rounded"
                              style={{ color: "#86868B" }}
                              title="Delete folder"
                              onMouseEnter={(e) => { e.currentTarget.style.color = "#f87171"; (e.currentTarget as HTMLElement).style.background = "rgba(239,68,68,0.1)"; }}
                              onMouseLeave={(e) => { e.currentTarget.style.color = "#86868B"; (e.currentTarget as HTMLElement).style.background = "transparent"; }}
                            >
                              <Trash2 size={9} />
                            </button>
                          </div>
                        )}
                      </div>

                      {isExpanded && (
                        <div>
                          {files.map((doc) => {
                            const name = doc.source.split(/[\\/]/).pop() || doc.document_id.slice(0, 12);
                            return (
                              <div
                                key={doc.document_id}
                                className="group/file flex items-center gap-1.5 pl-6 pr-2 py-1 rounded-lg"
                                onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.03)")}
                                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                              >
                                {fileIcon(name)}
                                <span className="flex-1 truncate text-[10px]" style={{ color: "#888" }} title={name}>{name}</span>
                                {movingDoc === doc.document_id ? (
                                  <select
                                    autoFocus
                                    onChange={(e) => { if (e.target.value) moveDocument(doc.document_id, e.target.value); }}
                                    onBlur={() => setMovingDoc(null)}
                                    className="text-[10px] rounded"
                                    style={{ background: "#1c1c1e", border: "1px solid rgba(59,130,246,0.4)", color: "#c7c7cc", padding: "1px 3px", maxWidth: 80, outline: "none" }}
                                  >
                                    <option value="">Move to…</option>
                                    {Object.keys(folderMap).filter((f) => f !== folderName).map((f) => (
                                      <option key={f} value={f}>{f}</option>
                                    ))}
                                  </select>
                                ) : (
                                  <div className="opacity-0 group-hover/file:opacity-100 flex gap-0.5 flex-shrink-0">
                                    <button
                                      onClick={() => setMovingDoc(doc.document_id)}
                                      className="p-0.5 rounded"
                                      style={{ color: "#86868B" }}
                                      title="Move to folder"
                                      onMouseEnter={(e) => { e.currentTarget.style.color = "#93c5fd"; (e.currentTarget as HTMLElement).style.background = "rgba(59,130,246,0.08)"; }}
                                      onMouseLeave={(e) => { e.currentTarget.style.color = "#86868B"; (e.currentTarget as HTMLElement).style.background = "transparent"; }}
                                    >
                                      <ArrowRight size={9} />
                                    </button>
                                    <button
                                      onClick={() => deleteKbDoc(doc.document_id, name)}
                                      className="p-0.5 rounded"
                                      style={{ color: "#86868B" }}
                                      title="Delete file"
                                      onMouseEnter={(e) => { e.currentTarget.style.color = "#f87171"; (e.currentTarget as HTMLElement).style.background = "rgba(239,68,68,0.1)"; }}
                                      onMouseLeave={(e) => { e.currentTarget.style.color = "#86868B"; (e.currentTarget as HTMLElement).style.background = "transparent"; }}
                                    >
                                      <Trash2 size={9} />
                                    </button>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                          {files.length === 0 && (
                            <p className="pl-6 py-1 text-[10px]" style={{ color: "rgba(134,134,139,0.3)" }}>Empty folder</p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
            }
          </div>
        </div>

        {/* Upload jobs */}
        {uploadJobs.length > 0 && (
          <div className="max-h-[140px] overflow-y-auto scrollbar-hide shrink-0"
            style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
            {uploadJobs.slice(-4).reverse().map((j) => <JobBadge key={j.jobId} job={j} />)}
          </div>
        )}

        {/* Upload buttons */}
        <div className="shrink-0" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
          <SyncPanel
            onToast={addToast}
            targetCollection={kbFilter || "default"}
            onUploaded={(job) => {
              setUploadJobs((prev) => [job, ...prev]);
              pollJob(job.jobId, job.filename);
              loadKbDocs();
              fetchCollections();
            }}
          />
        </div>

        {/* Sidebar footer */}
        <div
          className="px-4 py-2 text-center shrink-0"
          style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}
        >
          <p className="text-[10px]" style={{ color: "rgba(134,134,139,0.45)" }}>
            Copyright © aansensei
          </p>
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        {/* Header */}
        <header
          className="shrink-0 flex items-center justify-between px-6 h-14"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
        >
          <div className="flex items-center gap-3">
            <Logo />
            {activeChat && (
              <>
                <span style={{ color: "rgba(255,255,255,0.15)" }}>/</span>
                <span className="text-[13px] truncate max-w-[320px]" style={{ color: "#86868B" }}>
                  {activeChat.title}
                </span>
              </>
            )}
          </div>
          <div className="flex items-center gap-2.5">
            <button
              onClick={newChat}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[12px] font-medium transition-all duration-250"
              style={{
                border: "1px solid rgba(255,255,255,0.1)",
                color: "#86868B",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "#3B82F6";
                e.currentTarget.style.color = "#F5F5F7";
                e.currentTarget.style.boxShadow = "0 0 14px rgba(59,130,246,0.2)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)";
                e.currentTarget.style.color = "#86868B";
                e.currentTarget.style.boxShadow = "none";
              }}
            >
              <Plus size={12} />
              New Chat
            </button>
            {/* Model switcher */}
            <div className="relative" ref={modelMenuRef}>
              <button
                onClick={() => { setModelMenuOpen((o) => !o); setModelSettingsOpen(false); }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium transition-all"
                style={{
                  border: "1px solid rgba(255,255,255,0.1)",
                  color: "#86868B",
                  background: modelMenuOpen ? "rgba(255,255,255,0.06)" : "transparent",
                }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.2)"; e.currentTarget.style.color = "#d1d1d6"; }}
                onMouseLeave={(e) => { if (!modelMenuOpen) { e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; e.currentTarget.style.color = "#86868B"; } }}
              >
                <Cpu size={11} />
                {(MODELS.find((m) => m.id === activeModel) ?? GROQ_MODELS.find((m) => m.id === activeModel))?.label ?? activeModel}
                <ChevronDown size={10} />
              </button>
              {modelMenuOpen && (
                <div
                  className="absolute right-0 top-full mt-1.5 rounded-xl overflow-hidden z-50"
                  style={{ width: 220, background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 8px 32px rgba(0,0,0,0.5)" }}
                >
                  {/* Model list */}
                  {!modelSettingsOpen && MODELS.map((m) => (
                    <button
                      key={m.id}
                      onClick={() => { setActiveModel(m.id); localStorage.setItem("chatrag_model", m.id); setModelMenuOpen(false); }}
                      className="w-full flex items-center justify-between px-3 py-2 text-[11px] transition-colors text-left"
                      style={{
                        background: activeModel === m.id ? "rgba(59,130,246,0.12)" : "transparent",
                        color: activeModel === m.id ? "#93c5fd" : "#c7c7cc",
                      }}
                      onMouseEnter={(e) => { if (activeModel !== m.id) e.currentTarget.style.background = "rgba(255,255,255,0.05)"; }}
                      onMouseLeave={(e) => { if (activeModel !== m.id) e.currentTarget.style.background = "transparent"; }}
                    >
                      <span className="font-medium">{m.label}</span>
                      <span className="text-[10px]" style={{ color: m.id === "gemma3:12b" ? "#f87171" : "rgba(134,134,139,0.6)" }}>{m.note}</span>
                    </button>
                  ))}

                  {/* Settings panel */}
                  {modelSettingsOpen && (
                    <div className="px-3 py-3">
                      <p className="text-[10px] mb-1" style={{ color: "rgba(134,134,139,0.6)" }}>Groq API Key</p>
                      <div className="relative mb-2">
                        <input
                          type={showApiKey ? "text" : "password"}
                          value={apiKey}
                          onChange={(e) => { setApiKey(e.target.value); localStorage.setItem("chatrag_api_key", e.target.value); }}
                          className="w-full text-[10px] rounded-lg px-2 py-1.5 pr-7 outline-none"
                          style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#c7c7cc" }}
                          placeholder="gsk_..."
                        />
                        <button
                          onClick={() => setShowApiKey((s) => !s)}
                          className="absolute right-1.5 top-1/2 -translate-y-1/2"
                          style={{ color: "#86868B" }}
                        >
                          {showApiKey ? <EyeOff size={11} /> : <Eye size={11} />}
                        </button>
                      </div>

                      {apiKey.startsWith("gsk_") ? (
                        <>
                          <p className="text-[10px] mb-1.5" style={{ color: "#4ade80", fontSize: 9 }}>Groq connected</p>
                          <p className="text-[10px] mb-1" style={{ color: "rgba(134,134,139,0.6)" }}>Groq model</p>
                          {GROQ_MODELS.map((m) => (
                            <button
                              key={m.id}
                              onClick={() => { setActiveModel(m.id); localStorage.setItem("chatrag_model", m.id); setModelMenuOpen(false); setModelSettingsOpen(false); }}
                              className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg mb-0.5 text-[10px] transition-colors text-left"
                              style={{
                                background: activeModel === m.id ? "rgba(59,130,246,0.15)" : "rgba(255,255,255,0.03)",
                                color: activeModel === m.id ? "#93c5fd" : "#c7c7cc",
                                border: activeModel === m.id ? "1px solid rgba(59,130,246,0.3)" : "1px solid transparent",
                              }}
                            >
                              <span className="font-medium">{m.label}</span>
                              <span style={{ color: "rgba(134,134,139,0.5)", fontSize: 9 }}>{m.note}</span>
                            </button>
                          ))}
                        </>
                      ) : (
                        <p className="text-[9px]" style={{ color: "rgba(134,134,139,0.4)" }}>
                          Nhập Groq API key để dùng Llama / Mixtral tốc độ cao.<br />
                          Lấy key miễn phí tại console.groq.com
                        </p>
                      )}
                    </div>
                  )}

                  {/* Settings toggle */}
                  <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                    <button
                      onClick={() => setModelSettingsOpen((s) => !s)}
                      className="w-full flex items-center gap-2 px-3 py-2 text-[10px] transition-colors"
                      style={{ color: modelSettingsOpen ? "#93c5fd" : "rgba(134,134,139,0.55)" }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.04)")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    >
                      <Settings size={10} />
                      {modelSettingsOpen ? "← Back to models" : "Configure…"}
                    </button>
                  </div>
                </div>
              )}
            </div>
            {/* Avatar */}
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold"
              style={{ background: "linear-gradient(135deg, #0A66C2, #3B82F6)", color: "#fff" }}
            >
              A
            </div>
          </div>
        </header>

        {/* Messages area */}
        <div
          className="flex-1 overflow-y-auto scrollbar-hide relative"
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget as Node)) setDragOver(false); }}
          onDrop={(e) => {
            e.preventDefault(); setDragOver(false);
            const files = Array.from(e.dataTransfer.files).filter((f) => /\.(pdf|png|jpg|jpeg|docx|xlsx)$/i.test(f.name));
            files.forEach(async (file) => {
              const form = new FormData();
              form.append("file", file); form.append("collection", "default");
              addToast(`Uploading "${file.name}"...`, "info");
              try {
                const res = await fetch("/ingest/upload", { method: "POST", body: form });
                if (!res.ok) { addToast(`Failed to upload "${file.name}"`, "error"); return; }
                const data = await res.json();
                const job: UploadJob = { jobId: data.job_id, filename: file.name, status: "queued" };
                setUploadJobs((prev) => [job, ...prev]);
                pollJob(job.jobId, job.filename);
              } catch { addToast(`Failed to upload "${file.name}"`, "error"); }
            });
          }}
        >
          {dragOver && (
            <div className="absolute inset-0 z-20 flex flex-col items-center justify-center animate-toast-in"
              style={{ background: "rgba(10,102,194,0.06)", border: "2px dashed rgba(59,130,246,0.4)", backdropFilter: "blur(4px)" }}>
              <Upload size={32} style={{ color: "#3B82F6", opacity: 0.7 }} />
              <p className="mt-3 text-sm font-medium" style={{ color: "#93c5fd" }}>Drop PDF or image to ingest</p>
            </div>
          )}
          {isEmpty ? (
            <EmptyState onSuggestion={(text) => sendMessage(text)} suggestions={suggestions} loadingSuggestions={loadingSuggestions} />
          ) : (
            <div className="max-w-[850px] mx-auto px-6 pt-8 pb-4">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} onSourceClick={handleSourceClick} activeSource={activeSourceId} />
              ))}
              {isProcessing && <RAGProcessing step={processingStep} sources={readingSources} />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div
          className="shrink-0 px-6 pb-4 pt-2"
          style={{
            background: "linear-gradient(to top, #121214 60%, transparent)",
          }}
        >
          <div className="max-w-[850px] mx-auto">
            <div
              className="flex items-end gap-3 px-4 py-3 rounded-3xl transition-all duration-250"
              style={{
                background: "#1C1C1E",
                border: inputFocused
                  ? "1px solid #0A66C2"
                  : "1px solid rgba(255,255,255,0.1)",
                boxShadow: inputFocused
                  ? "0 0 12px rgba(10,102,194,0.2), inset 0 0 12px rgba(10,102,194,0.04)"
                  : "none",
              }}
            >
              <button
                className="shrink-0 mb-0.5 transition-colors duration-150"
                style={{ color: "rgba(134,134,139,0.6)" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#86868B")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(134,134,139,0.6)")}
              >
                <Paperclip size={16} />
              </button>

              <textarea
                ref={textareaRef}
                rows={1}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  autoResize();
                }}
                onFocus={() => setInputFocused(true)}
                onBlur={() => setInputFocused(false)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder="Ask anything from your knowledge base..."
                className="flex-1 bg-transparent resize-none outline-none text-sm leading-relaxed"
                style={{
                  color: "#F5F5F7",
                  caretColor: "#3B82F6",
                  maxHeight: "160px",
                  overflowY: "auto",
                  fontFamily: "inherit",
                }}
              />

              {isProcessing ? (
                <button
                  onClick={stopGeneration}
                  className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-all duration-200"
                  style={{ background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.35)", cursor: "pointer" }}
                  title="Dừng"
                >
                  <Square size={11} color="#f87171" fill="#f87171" />
                </button>
              ) : (
                <button
                  onClick={() => sendMessage()}
                  disabled={!input.trim()}
                  className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-all duration-200"
                  style={{
                    background: input.trim()
                      ? "linear-gradient(135deg, #0A66C2 0%, #3B82F6 100%)"
                      : "rgba(255,255,255,0.06)",
                    boxShadow: input.trim() ? "0 0 10px rgba(59,130,246,0.35)" : "none",
                    cursor: input.trim() ? "pointer" : "not-allowed",
                  }}
                >
                  <ArrowUp
                    size={14}
                    color={input.trim() ? "#fff" : "rgba(255,255,255,0.25)"}
                    strokeWidth={2.5}
                  />
                </button>
              )}
            </div>

            {/* Scope chips + mode toggle */}
            <div className="flex items-center justify-center gap-1.5 mt-3 flex-wrap">
              <button
                onClick={() => { setChatScope({ type: "all" }); fetchSuggestions({ type: "all" }); }}
                className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium transition-all"
                style={{
                  border: `1px solid ${chatScope.type === "all" ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.08)"}`,
                  color: chatScope.type === "all" ? "#c7c7cc" : "rgba(134,134,139,0.5)",
                  background: chatScope.type === "all" ? "rgba(255,255,255,0.06)" : "transparent",
                }}
              >
                <Database size={10} />
                All · {kbDocs.length}
              </button>
              {[
                ...collections,
                ...pendingFolders
                  .filter((pf) => !collections.some((c) => c.name === pf))
                  .map((pf) => ({ name: pf, doc_count: 0 })),
              ].slice(0, 3).map((col) => {
                const isSelected = chatScope.type === "selected" && chatScope.collections.includes(col.name);
                return (
                  <button
                    key={col.name}
                    onClick={() => {
                      const cur = chatScope.type === "selected" ? chatScope.collections : [];
                      const next = cur.includes(col.name) ? cur.filter((c) => c !== col.name) : [...cur, col.name];
                      const newScope = next.length === 0
                        ? { type: "all" as const }
                        : { type: "selected" as const, collections: next };
                      setChatScope(newScope);
                      fetchSuggestions(newScope);
                    }}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium transition-all"
                    style={{
                      border: `1px solid ${isSelected ? "rgba(59,130,246,0.4)" : "rgba(255,255,255,0.08)"}`,
                      color: isSelected ? "#93c5fd" : "rgba(134,134,139,0.5)",
                      background: isSelected ? "rgba(59,130,246,0.12)" : "transparent",
                    }}
                  >
                    <FolderOpen size={10} />
                    {col.name}{col.doc_count > 0 ? ` · ${col.doc_count}` : ""}
                  </button>
                );
              })}
              <button
                onClick={() => {
                  const next = !hybridMode;
                  setHybridMode(next);
                  localStorage.setItem("chatrag_hybrid", String(next));
                }}
                className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold transition-all duration-200"
                style={{
                  background: hybridMode
                    ? "linear-gradient(135deg, #1e40af 0%, #2563eb 50%, #4f46e5 100%)"
                    : "rgba(255,255,255,0.05)",
                  border: `1px solid ${hybridMode ? "rgba(79,70,229,0.6)" : "rgba(255,255,255,0.1)"}`,
                  color: hybridMode ? "#fff" : "rgba(134,134,139,0.6)",
                  boxShadow: hybridMode ? "0 0 14px rgba(37,99,235,0.35)" : "none",
                  letterSpacing: "0.02em",
                }}
              >
                {hybridMode
                  ? <><span style={{ fontSize: 10 }}>⚡</span> Hybrid</>
                  : <><span style={{ fontSize: 10 }}>📚</span> Docs only</>
                }
              </button>
            </div>

            <p className="text-center text-[11px] mt-2.5" style={{ color: "rgba(134,134,139,0.5)" }}>
              chatRAG can make mistakes. Verify information from internal databases.{" "}
              <span style={{ color: "rgba(134,134,139,0.3)" }}>|</span>{" "}
              Copyright © aansensei
            </p>
          </div>
        </div>
      </div>

      {/* Source Panel */}
      {activeSource && (
        <SourcePanel
          source={activeSource}
          onClose={() => {
            setActiveSource(null);
            setActiveSourceId(null);
          }}
        />
      )}

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      <style>{`
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
        @keyframes slide-in {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
        .animate-slide-in { animation: slide-in 0.28s cubic-bezier(0.16,1,0.3,1) forwards; }
        @keyframes toast-in {
          from { transform: translateY(10px) scale(0.96); opacity: 0; }
          to   { transform: translateY(0) scale(1); opacity: 1; }
        }
        .animate-toast-in { animation: toast-in 0.25s cubic-bezier(0.16,1,0.3,1) forwards; }
        @keyframes msg-in {
          from { transform: translateY(10px); opacity: 0; }
          to   { transform: translateY(0); opacity: 1; }
        }
        .msg-animate { animation: msg-in 0.3s ease forwards; }
        textarea::placeholder { color: rgba(134,134,139,0.45); }
      `}</style>
    </div>
  );
}
