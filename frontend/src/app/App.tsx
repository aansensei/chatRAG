import { useState, useRef, useEffect, useCallback } from "react";
import {
  Paperclip,
  ArrowUp,
  Plus,
  Search,
  FileText,
  X,
  ChevronRight,
  Database,
  BookOpen,
  BarChart3,
  Shield,
  Upload,
  CheckCircle,
  AlertCircle,
  Loader,
} from "lucide-react";

type UploadJob = {
  jobId: string;
  filename: string;
  status: "queued" | "extracting" | "chunking" | "embedding" | "completed" | "failed";
  step?: string;
  error?: string;
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
  date: "today" | "week";
  preview: string;
};

// ── Seed Data ──────────────────────────────────────────────────────────────

const HISTORY: Chat[] = [
  { id: "1", title: "Q3 Revenue Forecast Analysis", date: "today", preview: "Based on internal ERP data..." },
  { id: "2", title: "Compliance Policy Summary", date: "today", preview: "ISO 27001 certification requires..." },
  { id: "3", title: "Vendor Contract Comparison", date: "today", preview: "The three shortlisted vendors..." },
  { id: "4", title: "Employee Onboarding Workflow", date: "week", preview: "HR policy document v4.2 states..." },
  { id: "5", title: "Product Roadmap Q4 2025", date: "week", preview: "Engineering allocated 40% of cycles..." },
  { id: "6", title: "Data Retention Guidelines", date: "week", preview: "GDPR Article 17 requires personal..." },
  { id: "7", title: "Board Presentation Draft", date: "week", preview: "FY25 EBITDA margin expanded by..." },
];

const SOURCES: Source[] = [
  {
    id: "s1",
    title: "Q3 Financial Report 2025.pdf",
    type: "pdf",
    excerpt:
      "Total consolidated revenue for Q3 2025 reached $142.8M, representing a 23.4% YoY increase. EBITDA margin expanded to 31.2% from 28.7% in Q3 2024. The growth was primarily driven by enterprise segment expansion in APAC (+41%) and EMEA (+28%).",
    page: 14,
    date: "2025-10-15",
    confidence: 97,
  },
  {
    id: "s2",
    title: "Enterprise Sales CRM Database",
    type: "database",
    excerpt:
      "Pipeline value as of Q3 close: $89.4M qualified (Stage 3+). Win rate: 34.2% (up from 29.1% prior quarter). Average deal size: $187K. Top verticals: Financial Services (28%), Healthcare (22%), Manufacturing (19%).",
    date: "2025-10-14",
    confidence: 94,
  },
  {
    id: "s3",
    title: "Analyst Consensus Report — Internal",
    type: "doc",
    excerpt:
      "Internal analyst consensus projects Q4 revenue of $158–165M with base-case scenario at $161.2M. Key risk factors: (1) macro headwinds in EU market, (2) competitor pricing pressure in SMB segment, (3) delayed ERP integrations in 3 enterprise accounts.",
    date: "2025-10-12",
    confidence: 88,
  },
];

const SEED_MESSAGES: Message[] = [
  {
    id: "m1",
    role: "user",
    content: "Give me a summary of Q3 financial performance and what's driving the revenue growth.",
  },
  {
    id: "m2",
    role: "assistant",
    content:
      "Based on your internal financial documentation and CRM data, here's a comprehensive view of Q3 2025 performance:\n\n**Revenue & Margins**\nConsolidated revenue reached **$142.8M**, a 23.4% year-over-year increase. EBITDA margin expanded meaningfully to **31.2%** (up from 28.7% in Q3 2024), signaling strong operational leverage.\n\n**Growth Drivers**\nThe primary growth vectors were geographic: APAC delivered exceptional expansion at +41% YoY, while EMEA grew +28%. The enterprise segment continues to be the primary contributor, with average deal sizes of $187K and a win rate improvement to 34.2%.\n\n**Pipeline Health**\nQualified pipeline (Stage 3+) stands at $89.4M. Financial Services, Healthcare, and Manufacturing account for 69% of the qualified pipeline by vertical.\n\n**Q4 Outlook**\nInternal analyst consensus projects Q4 revenue of $158–165M, with base case at $161.2M. Key monitoring areas include EU macro conditions and 3 pending ERP integration closures.",
    sources: SOURCES,
  },
  {
    id: "m3",
    role: "user",
    content: "What are the biggest risks heading into Q4?",
  },
  {
    id: "m4",
    role: "assistant",
    content:
      "The internal analyst consensus report flags three primary risk vectors for Q4:\n\n1. **EU Macro Headwinds** — Ongoing softness in European enterprise spending could pressure the EMEA segment, which contributed significantly to Q3 growth.\n\n2. **SMB Pricing Pressure** — Competitive pricing actions in the SMB segment may compress win rates below the current 34.2% benchmark in that tier.\n\n3. **Delayed ERP Integrations** — Three enterprise accounts have outstanding integration milestones. These deals represent meaningful revenue that may slip into Q1 2026 if timelines extend.",
    sources: [SOURCES[2]],
  },
];

const SUGGESTIONS = [
  { icon: BarChart3, title: "Summarize Q3 earnings", sub: "Revenue, margins, and growth drivers" },
  { icon: Shield, title: "Compliance status overview", sub: "ISO 27001, GDPR, SOC 2 posture" },
  { icon: BookOpen, title: "Onboarding policy brief", sub: "Latest HR policy document summary" },
  { icon: Database, title: "Vendor contract comparison", sub: "Shortlisted vendors side-by-side" },
];

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
  if (message.role === "user") {
    return (
      <div className="flex justify-end mb-6">
        <div
          className="max-w-[70%] px-4 py-3 text-sm leading-relaxed"
          style={{
            background: "#2C2C2E",
            borderRadius: "18px 18px 4px 18px",
            color: "#F5F5F7",
          }}
        >
          {message.content}
        </div>
      </div>
    );
  }

  const lines = message.content.split("\n");

  return (
    <div className="flex gap-3 mb-8">
      {/* chatRAG icon */}
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
              <SourceChip
                key={src.id}
                source={src}
                onClick={() => onSourceClick(src)}
                active={activeSource === src.id}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function RAGProcessing() {
  return (
    <div className="flex gap-3 mb-8">
      <LogoIcon size={24} />
      <div className="flex items-center gap-2.5 pt-1">
        <div
          className="w-4 h-4 rounded-full border-2 border-transparent animate-spin"
          style={{
            borderTopColor: "#3B82F6",
            borderRightColor: "rgba(59,130,246,0.3)",
          }}
        />
        <span
          className="text-sm animate-pulse"
          style={{ color: "#86868B" }}
        >
          Scanning internal knowledge base...
        </span>
      </div>
    </div>
  );
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

function EmptyState({ onSuggestion }: { onSuggestion: (text: string) => void }) {
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
        <p className="text-sm" style={{ color: "rgba(134,134,139,0.6)" }}>
          Query your internal knowledge base
        </p>
      </div>

      {/* Suggestion cards */}
      <div className="grid grid-cols-2 gap-3 w-full max-w-xl">
        {SUGGESTIONS.map((s, i) => (
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
              <s.icon size={14} />
            </div>
            <div>
              <p className="text-[13px] font-medium" style={{ color: "#F5F5F7" }}>
                {s.title}
              </p>
              <p className="text-[11px] mt-0.5" style={{ color: "#86868B" }}>
                {s.sub}
              </p>
            </div>
          </button>
        ))}
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

function UploadZone({ onUploaded }: { onUploaded: (job: UploadJob) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const upload = async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    form.append("collection", "default");
    const res = await fetch("/ingest/upload", { method: "POST", body: form });
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    const data = await res.json();
    onUploaded({ jobId: data.job_id, filename: file.name, status: "queued" });
  };

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    Array.from(files).forEach((f) => upload(f).catch(console.error));
  };

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files); }}
      className="mx-3 mb-3 flex flex-col items-center gap-1.5 py-3 rounded-xl cursor-pointer transition-all duration-200"
      style={{
        border: `1px dashed ${dragging ? "rgba(59,130,246,0.6)" : "rgba(255,255,255,0.1)"}`,
        background: dragging ? "rgba(59,130,246,0.06)" : "transparent",
      }}
    >
      <input ref={inputRef} type="file" accept=".pdf,.png,.jpg,.jpeg" multiple className="hidden" onChange={(e) => handleFiles(e.target.files)} />
      <Upload size={13} style={{ color: "#86868B" }} />
      <span className="text-[11px]" style={{ color: "#86868B" }}>Upload document</span>
    </div>
  );
}

function JobBadge({ job }: { job: UploadJob }) {
  const isRunning = !["completed", "failed"].includes(job.status);
  const icon = job.status === "completed"
    ? <CheckCircle size={11} style={{ color: "#10b981" }} />
    : job.status === "failed"
    ? <AlertCircle size={11} style={{ color: "#ef4444" }} />
    : <Loader size={11} className="animate-spin" style={{ color: "#86868B" }} />;

  return (
    <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg mx-3 mb-1"
      style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
      {icon}
      <div className="flex-1 min-w-0">
        <p className="text-[11px] truncate" style={{ color: isRunning ? "#d1d1d6" : job.status === "completed" ? "#10b981" : "#ef4444" }}>
          {job.filename}
        </p>
        <p className="text-[10px]" style={{ color: "rgba(134,134,139,0.6)" }}>
          {STATUS_LABEL[job.status]}
        </p>
      </div>
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [inputFocused, setInputFocused] = useState(false);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [activeSource, setActiveSource] = useState<Source | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeSourceId, setActiveSourceId] = useState<string | null>(null);
  const [uploadJobs, setUploadJobs] = useState<UploadJob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const pollJob = useCallback((jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/ingest/jobs/${jobId}`);
        if (!res.ok) return;
        const data = await res.json();
        const status = data.status as UploadJob["status"];
        setUploadJobs((prev) => prev.map((j) => j.jobId === jobId ? { ...j, status, step: data.step, error: data.error } : j));
        if (status === "completed" || status === "failed") clearInterval(interval);
      } catch { clearInterval(interval); }
    }, 2000);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  };

  const sendMessage = async (text?: string) => {
    const content = (text ?? input).trim();
    if (!content || isProcessing) return;

    const userMsg: Message = { id: Date.now().toString(), role: "user", content };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
    setIsProcessing(true);

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: content }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const sources: Source[] = (data.sources ?? []).map(
        (s: { content: string; section?: string; similarity: number }, i: number) => ({
          id: `src-${Date.now()}-${i}`,
          title: s.section ?? `Source ${i + 1}`,
          type: "doc" as const,
          excerpt: s.content,
          date: new Date().toISOString().slice(0, 10),
          confidence: Math.round(s.similarity * 100),
        })
      );

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer ?? "No answer returned.",
        sources,
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Something went wrong connecting to the knowledge base. Please try again.",
        },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const loadChat = (chat: Chat) => {
    setActiveChat(chat.id);
    if (chat.id === "1") {
      setMessages(SEED_MESSAGES);
    } else {
      setMessages([]);
    }
    setActiveSource(null);
    setActiveSourceId(null);
  };

  const newChat = () => {
    setMessages([]);
    setActiveChat(null);
    setActiveSource(null);
    setActiveSourceId(null);
    setInput("");
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
              onClick={() => {/* search */}}
              className="w-6 h-6 flex items-center justify-center rounded-md transition-colors duration-150"
              style={{ color: "#86868B" }}
              onMouseEnter={(e) => (e.currentTarget.style.color = "#F5F5F7")}
              onMouseLeave={(e) => (e.currentTarget.style.color = "#86868B")}
            >
              <Search size={13} />
            </button>
          </div>
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
          {(["today", "week"] as const).map((group) => (
            <div key={group} className="mb-4">
              <p
                className="text-[10px] font-medium uppercase tracking-widest px-2 mb-1.5"
                style={{ color: "rgba(134,134,139,0.5)" }}
              >
                {group === "today" ? "Today" : "Previous 7 Days"}
              </p>
              {HISTORY.filter((c) => c.date === group).map((chat) => (
                <button
                  key={chat.id}
                  onClick={() => loadChat(chat)}
                  className="w-full text-left px-2.5 py-2 rounded-lg mb-0.5 transition-all duration-150"
                  style={{
                    background: activeChat === chat.id ? "rgba(59,130,246,0.1)" : "transparent",
                    border: activeChat === chat.id ? "1px solid rgba(59,130,246,0.15)" : "1px solid transparent",
                  }}
                  onMouseEnter={(e) => {
                    if (activeChat !== chat.id)
                      e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                  }}
                  onMouseLeave={(e) => {
                    if (activeChat !== chat.id)
                      e.currentTarget.style.background = "transparent";
                  }}
                >
                  <p
                    className="text-[12px] font-medium truncate"
                    style={{ color: activeChat === chat.id ? "#93c5fd" : "#d1d1d6" }}
                  >
                    {chat.title}
                  </p>
                </button>
              ))}
            </div>
          ))}
        </div>

        {/* Upload section */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
          {uploadJobs.length > 0 && (
            <div className="pt-2 max-h-[140px] overflow-y-auto scrollbar-hide">
              {uploadJobs.slice(-4).reverse().map((j) => <JobBadge key={j.jobId} job={j} />)}
            </div>
          )}
          <UploadZone onUploaded={(job) => { setUploadJobs((prev) => [job, ...prev]); pollJob(job.jobId); }} />
        </div>

        {/* Sidebar footer */}
        <div
          className="px-4 py-2 text-center"
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
                  {HISTORY.find((c) => c.id === activeChat)?.title}
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
        <div className="flex-1 overflow-y-auto scrollbar-hide">
          {isEmpty ? (
            <EmptyState onSuggestion={(text) => sendMessage(text)} />
          ) : (
            <div className="max-w-[850px] mx-auto px-6 pt-8 pb-4">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onSourceClick={handleSourceClick}
                  activeSource={activeSourceId}
                />
              ))}
              {isProcessing && <RAGProcessing />}
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

              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || isProcessing}
                className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-all duration-200"
                style={{
                  background:
                    input.trim() && !isProcessing
                      ? "linear-gradient(135deg, #0A66C2 0%, #3B82F6 100%)"
                      : "rgba(255,255,255,0.06)",
                  boxShadow:
                    input.trim() && !isProcessing
                      ? "0 0 10px rgba(59,130,246,0.35)"
                      : "none",
                  cursor: input.trim() && !isProcessing ? "pointer" : "not-allowed",
                }}
              >
                <ArrowUp
                  size={14}
                  color={input.trim() && !isProcessing ? "#fff" : "rgba(255,255,255,0.25)"}
                  strokeWidth={2.5}
                />
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

      <style>{`
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
        @keyframes slide-in {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
        .animate-slide-in { animation: slide-in 0.28s cubic-bezier(0.16,1,0.3,1) forwards; }
        textarea::placeholder { color: rgba(134,134,139,0.45); }
      `}</style>
    </div>
  );
}
