import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { flushSync } from "react-dom";
import {
  Paperclip,
  ArrowUp,
  ArrowRight,
  ArrowDown,
  Plus,
  Search,
  FileText,
  X,
  ChevronRight,
  ChevronDown,
  ChevronUp,
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
  Sparkles,
  X as XIcon,
  Globe,
  ExternalLink,
} from "lucide-react";

type Toast = { id: string; msg: string; type: "success" | "error" | "info" };

type Lang = "vi" | "en" | "zh" | "ja";

const UI_STRINGS = {
  vi: {
    knowledgeBase: "Kho tài liệu",
    kbDocs: (n: number) => `${n} tài liệu`,
    memory: "Bộ nhớ",
    memoryItems: (n: number) => `${n} mục`,
    clearData: "Xóa dữ liệu & đặt lại",
    today: "Hôm nay",
    thisWeek: "7 ngày trước",
    older: "Cũ hơn",
    pinned: "Đã ghim",
    deleteConfirmTitle: "Xóa chat này?",
    deleteConfirmDesc: "Hành động này không thể hoàn tác. Lịch sử và ghi nhớ sẽ bị xóa vĩnh viễn.",
    deleteBtn: "Xóa",
    cancelBtn: "Hủy",
    language: "Ngôn ngữ",
    newChat: "Chat mới",
    globalMemory: (n: number) => `Kinh nghiệm (${n})`,
    chatMemory: "Chat này",
    noFiles: "Không có tài liệu",
    uploadFiles: "Tải lên tệp",
    syncFolder: "Đồng bộ thư mục",
    syncing: (done: number, total: number) => `Đồng bộ ${done}/${total}...`,
    addToExisting: "Thêm vào thư mục có sẵn",
    createNewFolder: "Tạo thư mục mới",
    selectTargetFolder: "Chọn thư mục đích",
    back: "← Trở lại",
    noFoldersYet: "Chưa có thư mục nào.",
    uploadTo: (name: string) => `Tải vào "${name}"`,
    selectFolderFirst: "Chọn thư mục trước",
    nameThisFolder: "Đặt tên thư mục",
    filesWillUpload: (n: number) => `${n} tệp sẽ được tải lên`,
    folderNamePlaceholder: "Tên thư mục...",
    cancel: "Hủy",
    upload: "Tải lên",
    stepWebSearch: (q: string) => `Đang tìm web: "${q}"`,
    stepEmbedding: (q: string) => `Đang phân tích: "${q}"`,
    stepSearching: (q: string) => `Tìm tài liệu về "${q}"`,
    stepFiltering: "Đọc và lọc các đoạn liên quan…",
    stepGenerating: "Đang soạn câu trả lời…",
    chatPlaceholder: "Hỏi Ciel bất cứ điều gì…",
    webPlaceholder: "Hỏi Ciel — sẽ tự tìm web…",
    chatConversation: "Hội thoại",
    chatNotes: "Ghi chú",
    activeChatBadge: "Đang mở",
    noteCount: (n: number) => `${n} ghi chú`,
    noChatsForNotes: "Chưa có chat nào. Bắt đầu trò chuyện để tạo ghi chú.",
    noQuestionsYet: "Chưa có câu hỏi nào.",
    noNotesYet: "Chưa có ghi chú.",
    addNotePlaceholder: "Thêm ghi chú...",
    addBtn: "Thêm",
    clearNotesTitle: "Xóa toàn bộ ghi chú",
    exportBtn: "Xuất",
    exportTitle: "Xuất hội thoại",
    exportFormatTxt: "Văn bản",
    exportFormatMd: "Markdown",
    exportFormatDocx: "Word",
    exportFormatJson: "JSON",
    exportedToast: (name: string) => `Đã xuất "${name}"`,
    tableColItem: "Mục",
    tableColContent: "Nội dung",
  },
  en: {
    knowledgeBase: "Knowledge base",
    kbDocs: (n: number) => `${n} docs`,
    memory: "Memory",
    memoryItems: (n: number) => `${n} ${n === 1 ? "item" : "items"}`,
    clearData: "Clear all data & reset",
    today: "Today",
    thisWeek: "Previous 7 days",
    older: "Older",
    pinned: "Pinned",
    deleteConfirmTitle: "Delete this chat?",
    deleteConfirmDesc: "This cannot be undone. Chat history and notes will be permanently deleted.",
    deleteBtn: "Delete",
    cancelBtn: "Cancel",
    language: "Language",
    newChat: "New Chat",
    globalMemory: (n: number) => `Experience (${n})`,
    chatMemory: "This chat",
    noFiles: "No files yet",
    uploadFiles: "Upload files",
    syncFolder: "Sync folder",
    syncing: (done: number, total: number) => `Syncing ${done}/${total}...`,
    addToExisting: "Add to existing folder",
    createNewFolder: "Create new folder",
    selectTargetFolder: "Select target folder",
    back: "← back",
    noFoldersYet: "No folders yet. Create one first.",
    uploadTo: (name: string) => `Upload to "${name}"`,
    selectFolderFirst: "Select a folder first",
    nameThisFolder: "Name this folder",
    filesWillUpload: (n: number) => `${n} file${n !== 1 ? "s" : ""} will be uploaded`,
    folderNamePlaceholder: "Folder name...",
    cancel: "Cancel",
    upload: "Upload",
    stepWebSearch: (q: string) => `Searching web: "${q}"`,
    stepEmbedding: (q: string) => `Analyzing: "${q}"`,
    stepSearching: (q: string) => `Finding docs about "${q}"`,
    stepFiltering: "Evaluating relevance…",
    stepGenerating: "Generating answer…",
    chatPlaceholder: "Ask Ciel anything…",
    webPlaceholder: "Ask Ciel — will search the web…",
    chatConversation: "Conversation",
    chatNotes: "Notes",
    activeChatBadge: "Active",
    noteCount: (n: number) => `${n} ${n === 1 ? "note" : "notes"}`,
    noChatsForNotes: "No chats yet. Start a conversation to add notes.",
    noQuestionsYet: "No questions yet.",
    noNotesYet: "No notes yet.",
    addNotePlaceholder: "Add a note...",
    addBtn: "Add",
    clearNotesTitle: "Clear all notes",
    exportBtn: "Export",
    exportTitle: "Export chat",
    exportFormatTxt: "Text",
    exportFormatMd: "Markdown",
    exportFormatDocx: "Word",
    exportFormatJson: "JSON",
    exportedToast: (name: string) => `Exported "${name}"`,
    tableColItem: "Item",
    tableColContent: "Content",
  },
  zh: {
    knowledgeBase: "知识库",
    kbDocs: (n: number) => `${n} 个文档`,
    memory: "记忆",
    memoryItems: (n: number) => `${n} 条`,
    clearData: "清除所有数据并重置",
    today: "今天",
    thisWeek: "近 7 天",
    older: "更早",
    pinned: "已固定",
    deleteConfirmTitle: "删除此对话？",
    deleteConfirmDesc: "此操作无法撤销，聊天记录和笔记将被永久删除。",
    deleteBtn: "删除",
    cancelBtn: "取消",
    language: "语言",
    newChat: "新对话",
    globalMemory: (n: number) => `经验 (${n})`,
    chatMemory: "本对话",
    noFiles: "暂无文档",
    uploadFiles: "上传文件",
    syncFolder: "同步文件夹",
    syncing: (done: number, total: number) => `同步中 ${done}/${total}...`,
    addToExisting: "添加到已有文件夹",
    createNewFolder: "创建新文件夹",
    selectTargetFolder: "选择目标文件夹",
    back: "← 返回",
    noFoldersYet: "暂无文件夹，请先创建。",
    uploadTo: (name: string) => `上传到 "${name}"`,
    selectFolderFirst: "请先选择文件夹",
    nameThisFolder: "命名文件夹",
    filesWillUpload: (n: number) => `将上传 ${n} 个文件`,
    folderNamePlaceholder: "文件夹名称...",
    cancel: "取消",
    upload: "上传",
    stepWebSearch: (q: string) => `搜索网络: "${q}"`,
    stepEmbedding: (q: string) => `分析中: "${q}"`,
    stepSearching: (q: string) => `查找文档: "${q}"`,
    stepFiltering: "筛选相关内容…",
    stepGenerating: "生成回答…",
    chatPlaceholder: "向 Ciel 提问…",
    webPlaceholder: "向 Ciel 提问 — 将自动搜索网络…",
    chatConversation: "对话",
    chatNotes: "笔记",
    activeChatBadge: "进行中",
    noteCount: (n: number) => `${n} 条笔记`,
    noChatsForNotes: "暂无对话。开始聊天以添加笔记。",
    noQuestionsYet: "暂无问题。",
    noNotesYet: "暂无笔记。",
    addNotePlaceholder: "添加笔记...",
    addBtn: "添加",
    clearNotesTitle: "清除全部笔记",
    exportBtn: "导出",
    exportTitle: "导出对话",
    exportFormatTxt: "文本",
    exportFormatMd: "Markdown",
    exportFormatDocx: "Word",
    exportFormatJson: "JSON",
    exportedToast: (name: string) => `已导出 "${name}"`,
    tableColItem: "项目",
    tableColContent: "内容",
  },
  ja: {
    knowledgeBase: "ナレッジベース",
    kbDocs: (n: number) => `${n} 件`,
    memory: "メモリ",
    memoryItems: (n: number) => `${n} 件`,
    clearData: "全データをクリアしてリセット",
    today: "今日",
    thisWeek: "直近 7 日間",
    older: "それ以前",
    pinned: "ピン留め",
    deleteConfirmTitle: "このチャットを削除しますか？",
    deleteConfirmDesc: "この操作は元に戻せません。チャット履歴とメモが完全に削除されます。",
    deleteBtn: "削除",
    cancelBtn: "キャンセル",
    language: "言語",
    newChat: "新しいチャット",
    globalMemory: (n: number) => `経験 (${n})`,
    chatMemory: "このチャット",
    noFiles: "ファイルなし",
    uploadFiles: "ファイルをアップロード",
    syncFolder: "フォルダを同期",
    syncing: (done: number, total: number) => `同期中 ${done}/${total}...`,
    addToExisting: "既存フォルダに追加",
    createNewFolder: "新しいフォルダを作成",
    selectTargetFolder: "対象フォルダを選択",
    back: "← 戻る",
    noFoldersYet: "フォルダがありません。先に作成してください。",
    uploadTo: (name: string) => `"${name}" にアップロード`,
    selectFolderFirst: "先にフォルダを選択",
    nameThisFolder: "フォルダ名を入力",
    filesWillUpload: (n: number) => `${n} ファイルがアップロードされます`,
    folderNamePlaceholder: "フォルダ名...",
    cancel: "キャンセル",
    upload: "アップロード",
    stepWebSearch: (q: string) => `ウェブ検索中: "${q}"`,
    stepEmbedding: (q: string) => `解析中: "${q}"`,
    stepSearching: (q: string) => `ドキュメント検索: "${q}"`,
    stepFiltering: "関連箇所を絞り込み中…",
    stepGenerating: "回答を生成中…",
    chatPlaceholder: "Ciel に何でも質問…",
    webPlaceholder: "Ciel に質問 — ウェブで検索します…",
    chatConversation: "会話",
    chatNotes: "メモ",
    activeChatBadge: "開いています",
    noteCount: (n: number) => `${n} 件のメモ`,
    noChatsForNotes: "チャットがまだありません。会話を始めるとメモを追加できます。",
    noQuestionsYet: "質問はまだありません。",
    noNotesYet: "メモはまだありません。",
    addNotePlaceholder: "メモを追加...",
    addBtn: "追加",
    clearNotesTitle: "メモを全て削除",
    exportBtn: "エクスポート",
    exportTitle: "チャットをエクスポート",
    exportFormatTxt: "テキスト",
    exportFormatMd: "Markdown",
    exportFormatDocx: "Word",
    exportFormatJson: "JSON",
    exportedToast: (name: string) => `"${name}" をエクスポートしました`,
    tableColItem: "項目",
    tableColContent: "内容",
  },
} as const;

type UploadJob = {
  jobId: string;
  filename: string;
  status: "queued" | "extracting" | "chunking" | "embedding" | "completed" | "failed";
  step?: string;
  error?: string;
  progress?: number;
  progressAt?: number;
};

type KBDocument = {
  document_id: string;
  source: string;
  pages: number | null;
  chunk_count: number;
  collection?: string;
  has_file?: boolean;
  file_path?: string;
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
  documentId?: string;
  filename?: string;
};

type WebSource = { title: string; href: string; domain: string; snippet?: string };

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  webSources?: WebSource[];
  isStreaming?: boolean;
  followUps?: string[];
  confidence?: number | null;
};

type Chat = {
  id: string;
  title: string;
  createdAt: number;
  messages: Message[];
  pinned?: boolean;
  notes?: string[];
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


async function translateStreamDirect(
  text: string,
  apiKey: string,
  _provider: string,
  onChunk: (t: string) => void,
  onDone: () => void,
  onError: (msg: string) => void,
  model?: string
) {
  try {
    const resp = await fetch("/chat/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, api_key: apiKey || null, model: model || null }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err?.detail || `HTTP ${resp.status}`);
    }
    const reader = resp.body!.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const raw = line.slice(6).trim();
        try {
          const json = JSON.parse(raw);
          if (json.type === "token" && json.token) onChunk(json.token);
        } catch {}
      }
    }
    onDone();
  } catch (err: unknown) {
    onError(err instanceof Error ? err.message : "Lỗi không xác định");
  }
}

const CJK_RESIDUAL_RE = /[぀-ヿ㐀-䶿一-鿿豈-﫿]/g;

function countResidualCJK(text: string): number {
  return (text.match(CJK_RESIDUAL_RE) || []).length;
}

function crc32(bytes: Uint8Array): number {
  let c = ~0;
  for (let i = 0; i < bytes.length; i++) {
    c ^= bytes[i];
    for (let k = 0; k < 8; k++) c = (c >>> 1) ^ (0xedb88320 & -(c & 1));
  }
  return ~c >>> 0;
}

function zipStore(files: { name: string; data: Uint8Array }[]): Blob {
  const enc = new TextEncoder();
  const u16 = (n: number) => [n & 0xff, (n >>> 8) & 0xff];
  const u32 = (n: number) => [n & 0xff, (n >>> 8) & 0xff, (n >>> 16) & 0xff, (n >>> 24) & 0xff];
  const parts: (Uint8Array | number[])[] = [];
  const central: (Uint8Array | number[])[] = [];
  let offset = 0;
  for (const f of files) {
    const nameBytes = enc.encode(f.name);
    const crc = crc32(f.data);
    const size = f.data.length;
    const header = [
      0x50, 0x4b, 0x03, 0x04, ...u16(20), ...u16(0), ...u16(0), ...u16(0), ...u16(0),
      ...u32(crc), ...u32(size), ...u32(size), ...u16(nameBytes.length), ...u16(0),
    ];
    parts.push(header, nameBytes, f.data);
    central.push([
      0x50, 0x4b, 0x01, 0x02, ...u16(20), ...u16(20), ...u16(0), ...u16(0), ...u16(0), ...u16(0),
      ...u32(crc), ...u32(size), ...u32(size), ...u16(nameBytes.length),
      ...u16(0), ...u16(0), ...u16(0), ...u16(0), ...u32(0), ...u32(offset),
    ], nameBytes);
    offset += header.length + nameBytes.length + size;
  }
  const centralSize = central.reduce((a, c) => a + c.length, 0);
  const end = [
    0x50, 0x4b, 0x05, 0x06, ...u16(0), ...u16(0), ...u16(files.length), ...u16(files.length),
    ...u32(centralSize), ...u32(offset), ...u16(0),
  ];
  const toBytes = (x: Uint8Array | number[]) => (x instanceof Uint8Array ? x : new Uint8Array(x));
  const blobParts = [...parts, ...central, end].map(toBytes);
  return new Blob(blobParts as BlobPart[], {
    type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  });
}

function buildDocx(title: string, messages: { role: string; content: string }[]): Blob {
  const enc = new TextEncoder();
  const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const para = (text: string, bold = false) => {
    const runs = esc(text).split("\n").map((ln, i) => (i > 0 ? "<w:br/>" : "") + `<w:t xml:space="preserve">${ln}</w:t>`).join("");
    return `<w:p><w:r>${bold ? "<w:rPr><w:b/></w:rPr>" : ""}${runs}</w:r></w:p>`;
  };
  const body = [para(title, true)];
  for (const m of messages) {
    body.push(para(m.role === "user" ? "Bạn:" : "Ciel:", true));
    body.push(para(m.content.trim()));
  }
  const documentXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>${body.join("")}<w:sectPr/></w:body></w:document>`;
  const contentTypes = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>`;
  const rels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>`;
  return zipStore([
    { name: "[Content_Types].xml", data: enc.encode(contentTypes) },
    { name: "_rels/.rels", data: enc.encode(rels) },
    { name: "word/document.xml", data: enc.encode(documentXml) },
  ]);
}

const BULLET_KV_RE = /^[-*]\s+([^:：]+)[:：]\s*(.+)$/;

function tryConvertListToTable(text: string, colItem: string, colContent: string): string {
  if (text.includes("|")) return text;
  const lines = text.split("\n");
  const items: { label: string; value: string }[] = [];
  let start = -1;
  let end = -1;
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(BULLET_KV_RE);
    if (m) {
      if (start === -1) start = i;
      end = i;
      items.push({ label: m[1].trim(), value: m[2].trim() });
    } else if (start !== -1) {
      break;
    }
  }
  if (items.length < 3) return text;
  const table = [
    `| ${colItem} | ${colContent} |`,
    "|---|---|",
    ...items.map((it) => `| ${it.label} | ${it.value} |`),
  ];
  return [...lines.slice(0, start), ...table, ...lines.slice(end + 1)].join("\n");
}

// ── Sub-components ─────────────────────────────────────────────────────────

function LogoIcon({ size = 24 }: { size?: number }) {
  return (
    <img
      src="/favicon-96x96.png"
      alt="chatRAG"
      draggable={false}
      onDragStart={(e) => e.preventDefault()}
      className="shrink-0 select-none"
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
  id,
}: {
  source: Source;
  onClick: () => void;
  active: boolean;
  id?: string;
}) {
  return (
    <button
      id={id}
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

declare global {
  interface Window {
    katex?: { renderToString: (tex: string, opts: object) => string };
  }
}

function renderLatex(tex: string, display: boolean): string {
  try {
    if (window.katex) {
      return window.katex.renderToString(tex, { displayMode: display, throwOnError: false, output: "html" });
    }
  } catch { /* noop */ }
  return display ? `$$${tex}$$` : `$${tex}$`;
}

function InlineContent({ text, sources, onSourceClick }: {
  text: string;
  sources?: Source[];
  onSourceClick: (s: Source) => void;
}) {
  const SPLIT_RE = /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$|\[\d+\]|\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`]+`)/g;
  const parts = text.split(SPLIT_RE);

  return (
    <>
      {parts.map((part, i) => {
        if (!part) return null;
        if (part.startsWith("$$") && part.endsWith("$$"))
          return <span key={i} dangerouslySetInnerHTML={{ __html: renderLatex(part.slice(2, -2), true) }} />;
        if (part.startsWith("$") && part.endsWith("$") && part.length > 2)
          return <span key={i} dangerouslySetInnerHTML={{ __html: renderLatex(part.slice(1, -1), false) }} />;
        const cm = part.match(/^\[(\d+)\]$/);
        if (cm) {
          const n = parseInt(cm[1], 10);
          const src = sources?.[n - 1];
          if (src) {
            return (
              <button key={i} onClick={() => onSourceClick(src)} title={src.title}
                className="inline-flex items-center justify-center mx-0.5 px-1.5 rounded text-[10px] font-semibold transition-all"
                style={{ background: "rgba(59,130,246,0.18)", border: "1px solid rgba(59,130,246,0.35)", color: "#93c5fd", verticalAlign: "middle", lineHeight: "1.4" }}
                onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(59,130,246,0.32)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(59,130,246,0.18)"; }}>
                {part}
              </button>
            );
          }
          return <span key={i}>{part}</span>;
        }
        if (part.startsWith("**") && part.endsWith("**"))
          return <strong key={i} style={{ color: "#F5F5F7", fontWeight: 600 }}>{part.slice(2, -2)}</strong>;
        if (part.startsWith("*") && part.endsWith("*") && part.length > 2)
          return <em key={i} style={{ fontStyle: "italic", color: "#d1d1d6" }}>{part.slice(1, -1)}</em>;
        if (part.startsWith("`") && part.endsWith("`"))
          return <code key={i} className="px-1 py-0.5 rounded text-[12px] font-mono"
            style={{ background: "rgba(255,255,255,0.08)", color: "#a5f3fc" }}>{part.slice(1, -1)}</code>;
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

const _KEYWORDS: Record<string, RegExp> = {
  python: /\b(def|class|return|if|elif|else|import|from|as|for|while|in|not|and|or|None|True|False|with|try|except|finally|raise|lambda|yield|pass|break|continue|self|async|await)\b/g,
  py: /\b(def|class|return|if|elif|else|import|from|as|for|while|in|not|and|or|None|True|False|with|try|except|finally|raise|lambda|yield|pass|break|continue|self|async|await)\b/g,
  js: /\b(const|let|var|function|return|if|else|for|while|in|of|new|class|extends|import|from|export|default|async|await|true|false|null|undefined|typeof|instanceof|this|try|catch|finally|throw)\b/g,
  ts: /\b(const|let|var|function|return|if|else|for|while|in|of|new|class|extends|import|from|export|default|async|await|true|false|null|undefined|typeof|instanceof|this|try|catch|finally|throw|interface|type|enum|public|private|protected|readonly)\b/g,
  typescript: /\b(const|let|var|function|return|if|else|for|while|in|of|new|class|extends|import|from|export|default|async|await|true|false|null|undefined|typeof|instanceof|this|try|catch|finally|throw|interface|type|enum|public|private|protected|readonly)\b/g,
  sql: /\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP|BY|ORDER|LIMIT|OFFSET|INSERT|INTO|VALUES|UPDATE|SET|DELETE|CREATE|TABLE|ALTER|DROP|INDEX|AS|AND|OR|NOT|NULL|IS|IN|LIKE|BETWEEN|DISTINCT|UNION|HAVING|CASE|WHEN|THEN|END)\b/gi,
  bash: /\b(if|then|else|elif|fi|for|while|do|done|case|esac|in|function|return|echo|export|local|read|cd|ls|grep|sed|awk|cat|sudo)\b/g,
  sh: /\b(if|then|else|elif|fi|for|while|do|done|case|esac|in|function|return|echo|export|local|read|cd|ls|grep|sed|awk|cat|sudo)\b/g,
  json: /\b(true|false|null)\b/g,
};

function highlightCode(src: string, lang: string): React.ReactNode {
  const kw = _KEYWORDS[lang?.toLowerCase()];
  if (!kw) return src;
  const TOKEN = /(\/\/.*$|#[^\n]*|\/\*[\s\S]*?\*\/|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`|\b\d+(?:\.\d+)?\b)/gm;
  const out: React.ReactNode[] = [];
  let last = 0;
  let match: RegExpExecArray | null;
  while ((match = TOKEN.exec(src))) {
    if (match.index > last) {
      const seg = src.slice(last, match.index);
      const parts = seg.split(kw);
      parts.forEach((p, idx) => {
        if (idx % 2 === 0) out.push(p);
        else out.push(<span key={`kw-${last}-${idx}`} style={{ color: "#c084fc" }}>{p}</span>);
      });
    }
    const m0 = match[0];
    if (m0.startsWith("//") || m0.startsWith("#") || m0.startsWith("/*")) {
      out.push(<span key={`cm-${match.index}`} style={{ color: "#6b7280" }}>{m0}</span>);
    } else if (m0.startsWith('"') || m0.startsWith("'") || m0.startsWith("`")) {
      out.push(<span key={`st-${match.index}`} style={{ color: "#86efac" }}>{m0}</span>);
    } else {
      out.push(<span key={`nm-${match.index}`} style={{ color: "#fbbf24" }}>{m0}</span>);
    }
    last = match.index + m0.length;
  }
  if (last < src.length) {
    const seg = src.slice(last);
    const parts = seg.split(kw);
    parts.forEach((p, idx) => {
      if (idx % 2 === 0) out.push(p);
      else out.push(<span key={`kw-end-${idx}`} style={{ color: "#c084fc" }}>{p}</span>);
    });
  }
  return out;
}

function MarkdownRenderer({ content, sources, onSourceClick }: {
  content: string;
  sources?: Source[];
  onSourceClick: (s: Source) => void;
}) {
  const ic = (text: string) => <InlineContent text={text} sources={sources} onSourceClick={onSourceClick} />;
  const lines = content.split("\n");
  const nodes: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const raw = lines[i];

    if (raw.trimStart().startsWith("```")) {
      const lang = raw.trim().slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trimStart().startsWith("```")) { codeLines.push(lines[i]); i++; }
      i++;
      nodes.push(
        <div key={`cb-${i}`} className="my-3 rounded-xl overflow-hidden" style={{ background: "rgba(0,0,0,0.4)", border: "1px solid rgba(255,255,255,0.08)" }}>
          {lang && <div className="px-3 py-1 text-[10px] font-mono border-b" style={{ color: "#86868B", borderColor: "rgba(255,255,255,0.06)" }}>{lang}</div>}
          <pre className="px-4 py-3 overflow-x-auto text-[12px] font-mono leading-relaxed m-0" style={{ color: "#e5e7eb" }}><code>{highlightCode(codeLines.join("\n"), lang)}</code></pre>
        </div>
      );
      continue;
    }

    if (raw.trim() === "$$") {
      const texLines: string[] = [];
      i++;
      while (i < lines.length && lines[i].trim() !== "$$") { texLines.push(lines[i]); i++; }
      i++;
      nodes.push(<div key={`dl-${i}`} className="my-3 overflow-x-auto text-center" dangerouslySetInnerHTML={{ __html: renderLatex(texLines.join("\n"), true) }} />);
      continue;
    }

    if (/^(-{3,}|\*{3,}|_{3,})$/.test(raw.trim())) {
      nodes.push(<hr key={`hr-${i}`} style={{ borderColor: "rgba(255,255,255,0.08)", margin: "12px 0" }} />);
      i++; continue;
    }

    const hm = raw.match(/^(#{1,3})\s+(.+)/);
    if (hm) {
      const lvl = hm[1].length;
      const sz = ["text-base", "text-[13px]", "text-[12px]"][lvl - 1];
      const mt = ["mt-5 mb-2", "mt-4 mb-1.5", "mt-3 mb-1"][lvl - 1];
      nodes.push(<p key={`h-${i}`} className={`font-semibold ${sz} ${mt} first:mt-0`} style={{ color: "#F5F5F7" }}>{ic(hm[2])}</p>);
      i++; continue;
    }

    if (raw.startsWith("> ")) {
      nodes.push(
        <div key={`bq-${i}`} className="my-2 pl-3 py-0.5" style={{ borderLeft: "3px solid rgba(139,92,246,0.5)" }}>
          <span className="text-sm italic" style={{ color: "#a3a3a3" }}>{ic(raw.slice(2))}</span>
        </div>
      );
      i++; continue;
    }

    if (/^\s*[-*]\s/.test(raw)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*]\s/.test(lines[i])) { items.push(lines[i].replace(/^\s*[-*]\s+/, "")); i++; }
      nodes.push(
        <ul key={`ul-${i}`} className="my-2 space-y-1" style={{ paddingLeft: "1rem" }}>
          {items.map((item, j) => (
            <li key={j} className="flex gap-2 text-sm leading-relaxed">
              <span style={{ color: "#3B82F6", flexShrink: 0, marginTop: "0.35em", fontSize: "0.45em" }}>●</span>
              <span style={{ color: "#d1d1d6" }}>{ic(item)}</span>
            </li>
          ))}
        </ul>
      );
      continue;
    }

    if (/^\d+\.\s/.test(raw)) {
      const items: string[] = [];
      let start = 1;
      const sm = raw.match(/^(\d+)\./);
      if (sm) start = parseInt(sm[1]);
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) { items.push(lines[i].replace(/^\d+\.\s+/, "")); i++; }
      nodes.push(
        <ol key={`ol-${i}`} className="my-2 space-y-1" style={{ paddingLeft: "0.5rem", listStyleType: "none" }}>
          {items.map((item, j) => (
            <li key={j} className="flex gap-2 text-sm leading-relaxed">
              <span style={{ color: "#3B82F6", flexShrink: 0, minWidth: "1.4em", fontVariantNumeric: "tabular-nums" }}>{start + j}.</span>
              <span style={{ color: "#d1d1d6" }}>{ic(item)}</span>
            </li>
          ))}
        </ol>
      );
      continue;
    }

    const sepRow = /^\|?[\s\-:]+\|[\s\-:|]+\|?\s*$/;
    let look = i + 1;
    while (look < lines.length && lines[look].trim() === "") look++;
    if (raw.includes("|") && look < lines.length && sepRow.test(lines[look])) {
      const rows: string[][] = [];
      const pushRow = (line: string) => {
        rows.push(line.split("|").map((c) => c.trim()).filter((_, ci, a) => ci > 0 && ci < a.length - 1));
      };
      pushRow(raw);
      i = look + 1;
      while (i < lines.length) {
        const ln = lines[i];
        if (ln.trim() === "") { i++; continue; }
        if (!ln.includes("|")) break;
        if (sepRow.test(ln)) { i++; continue; }
        pushRow(ln);
        i++;
      }
      const [head, ...body] = rows;
      nodes.push(
        <div key={`tbl-${i}`} className="my-3 overflow-x-auto rounded-lg" style={{ border: "1px solid rgba(255,255,255,0.08)" }}>
          <table className="w-full text-[12px]" style={{ borderCollapse: "collapse" }}>
            {head && <thead><tr style={{ background: "rgba(59,130,246,0.08)" }}>
              {head.map((c, ci) => <th key={ci} className="px-3 py-2 text-left font-semibold" style={{ color: "#93c5fd", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>{ic(c)}</th>)}
            </tr></thead>}
            <tbody>{body.map((row, ri) => (
              <tr key={ri} style={{ background: ri % 2 ? "rgba(255,255,255,0.02)" : "transparent" }}>
                {row.map((c, ci) => <td key={ci} className="px-3 py-2" style={{ color: "#d1d1d6", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>{ic(c)}</td>)}
              </tr>
            ))}</tbody>
          </table>
        </div>
      );
      continue;
    }

    if (raw.trim() === "") { nodes.push(<div key={`sp-${i}`} className="h-2" />); i++; continue; }

    nodes.push(<p key={`p-${i}`} className="mb-0 leading-[1.7]" style={{ color: "#d1d1d6" }}>{ic(raw)}</p>);
    i++;
  }

  return <>{nodes}</>;
}

function ChatMessage({
  message,
  onSourceClick,
  activeSource,
  onFollowUp,
}: {
  message: Message;
  onSourceClick: (source: Source) => void;
  activeSource: string | null;
  onFollowUp?: (text: string) => void;
}) {
  const [copied, setCopied] = useState(false);
  const [sourcesExpanded, setSourcesExpanded] = useState(false);
  const copyText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleCitationClick = (src: Source) => {
    if (!message.sources) return;
    const n = message.sources.indexOf(src) + 1;
    if (n <= 0) return;

    if (n > 3) {
      setSourcesExpanded(true);
    }

    setTimeout(() => {
      const elementId = `source-${message.id}-${n}`;
      const el = document.getElementById(elementId);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "nearest" });
        el.classList.add("source-card-highlight");
        setTimeout(() => {
          el.classList.remove("source-card-highlight");
        }, 800);
      }
    }, n > 3 ? 100 : 0);
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

  return (
    <div className="flex gap-3 mb-8 msg-animate group/msg">
      <LogoIcon size={24} />
      <div className="flex-1 min-w-0">
        <div className="text-sm leading-[1.7] mb-3" style={{ color: "#F5F5F7" }}>
          <MarkdownRenderer content={message.content} sources={message.sources} onSourceClick={handleCitationClick} />
        </div>

        {message.confidence !== undefined && message.confidence !== null && message.confidence >= 0.55 && (
          <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium mb-2.5" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.06)", color: "#86868B" }}>
            <span>◈ {Math.round(message.confidence * 100)}% confidence</span>
          </div>
        )}

        {message.sources && message.sources.length > 0 && (() => {
          const SHOW = 3;
          const visible = sourcesExpanded ? message.sources : message.sources.slice(0, SHOW);
          const hidden = message.sources.length - SHOW;
          return (
            <div className="mt-3">
              <div className="flex flex-wrap gap-2">
                {visible.map((src) => {
                  const n = message.sources!.indexOf(src) + 1;
                  return (
                    <SourceChip
                      key={src.id}
                      id={`source-${message.id}-${n}`}
                      source={src}
                      onClick={() => onSourceClick(src)}
                      active={activeSource === src.id}
                    />
                  );
                })}
                {!sourcesExpanded && hidden > 0 && (
                  <button
                    onClick={() => setSourcesExpanded(true)}
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[11px] transition-all"
                    style={{ background: "rgba(28,28,30,0.9)", border: "1px solid rgba(255,255,255,0.07)", color: "#86868B" }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = "#d1d1d6")}
                    onMouseLeave={(e) => (e.currentTarget.style.color = "#86868B")}
                  >
                    <ChevronDown size={10} />
                    {hidden} more
                  </button>
                )}
                {sourcesExpanded && hidden > 0 && (
                  <button
                    onClick={() => setSourcesExpanded(false)}
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[11px] transition-all"
                    style={{ background: "rgba(28,28,30,0.9)", border: "1px solid rgba(255,255,255,0.07)", color: "#86868B" }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = "#d1d1d6")}
                    onMouseLeave={(e) => (e.currentTarget.style.color = "#86868B")}
                  >
                    <ChevronDown size={10} style={{ transform: "rotate(180deg)" }} />
                    collapse
                  </button>
                )}
              </div>
            </div>
          );
        })()}

        {message.webSources && message.webSources.length > 0 && !message.isStreaming && (
          <div className="mt-3">
            <div className="flex items-center gap-1.5 mb-2">
              <Globe size={10} style={{ color: "#86868B" }} />
              <span className="text-[11px]" style={{ color: "#86868B" }}>Nguồn từ web</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {message.webSources.map((src, i) => (
                <a
                  key={i}
                  href={src.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] transition-all"
                  style={{
                    background: "rgba(59,130,246,0.07)",
                    border: "1px solid rgba(59,130,246,0.2)",
                    color: "#93C5FD",
                    textDecoration: "none",
                    maxWidth: 200,
                  }}
                  title={src.title}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(59,130,246,0.15)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(59,130,246,0.07)")}
                >
                  <Globe size={10} style={{ flexShrink: 0 }} />
                  <span className="truncate">{src.domain}</span>
                  <ExternalLink size={9} style={{ flexShrink: 0, opacity: 0.6 }} />
                </a>
              ))}
            </div>
          </div>
        )}

        {message.followUps && message.followUps.length > 0 && !message.isStreaming && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.followUps.map((f, idx) => (
              <button
                key={idx}
                onClick={() => onFollowUp?.(f)}
                className="px-3 py-1.5 rounded-full text-[11px] transition-all"
                style={{ background: "rgba(139,92,246,0.10)", border: "1px solid rgba(139,92,246,0.28)", color: "#c4b5fd" }}
                onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(139,92,246,0.22)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(139,92,246,0.10)"; }}
              >
                {f}
              </button>
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

function RAGProcessing({ step, label, sources }: { step: string; label?: string; sources: string[] }) {
  const [sourcesExpanded, setSourcesExpanded] = useState(false);
  const [displayStep, setDisplayStep] = useState(step);
  const [displayLabel, setDisplayLabel] = useState(label ?? "");
  const [phase, setPhase] = useState<"active" | "done" | "exit">("active");

  const LABELS: Record<string, string> = {
    "web-search": "Researching online...",
    embedding: "Embedding query...",
    searching: "Searching knowledge base...",
    filtering: "Evaluating relevance...",
    generating: "Generating answer...",
  };

  useEffect(() => {
    if (step === displayStep) return;
    setPhase("done");
    const t1 = setTimeout(() => setPhase("exit"), 280);
    const t2 = setTimeout(() => {
      setDisplayStep(step);
      setDisplayLabel(label ?? "");
      setPhase("active");
    }, 460);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [step, label]);

  const isDone = phase === "done";
  const isExit = phase === "exit";
  const visibleSources = sourcesExpanded ? sources : sources.slice(0, 3);

  return (
    <div className="flex gap-4 mb-8 items-start">
      <svg style={{ position: "absolute", width: 0, height: 0, pointerEvents: "none" }} aria-hidden="true">
        <defs>
          <filter id="gooey-filter">
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur" />
            <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 20 -9" result="goo" />
            <feComposite in="SourceGraphic" in2="goo" operator="atop" />
          </filter>
        </defs>
      </svg>

      <div className="relative w-12 h-12 shrink-0 flex items-center justify-center overflow-visible mt-0.5">
        <div className="slime-stage scale-[0.48] origin-center">
          <div className="core-glow-aura"></div>
          <div className="blobs-wrapper">
            <div className="blob blob-core"></div>
            <div className="blob sat sat-1"></div>
            <div className="blob sat sat-2"></div>
            <div className="blob sat sat-3"></div>
            <div className="blob sat sat-4"></div>
            <div className="blob sat sat-5"></div>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-1.5 pt-1.5">
        <div
          className="flex items-center gap-2"
          style={{
            opacity: isExit ? 0 : 1,
            transform: isExit ? "translateY(-3px)" : "translateY(0)",
            transition: "opacity 0.18s ease, transform 0.18s ease",
          }}
        >
          {isDone || isExit ? (
            <CheckCircle size={13} style={{ color: "#10b981", flexShrink: 0 }} />
          ) : (
            <div className="w-2.5 h-2.5 rounded-full bg-[#00e1fd] animate-pulse shrink-0" />
          )}
          <span
            className="text-[13px]"
            style={{
              color: isDone || isExit ? "#10b981" : "#86868b",
              transition: "color 0.15s ease",
            }}
          >
            {displayLabel || LABELS[displayStep] || displayStep}
          </span>
        </div>
        
        {sources.length > 0 && (
          <div className="flex flex-col gap-1 ml-5 mt-1.5 transition-all duration-300">
            {visibleSources.map((f, i) => {
              const isWeb = /^[a-z0-9\-]+\.[a-z]{2,}$/i.test(f) && !f.includes(" ");
              return (
                <div key={i} className="flex items-center gap-1.5 step-item-enter">
                  {isWeb
                    ? <Globe size={10} style={{ color: "#3b82f6" }} />
                    : <FileText size={10} style={{ color: "#3b82f6" }} />
                  }
                  <span className="text-[11px]" style={{ color: "#93c5fd" }}>
                    {isWeb ? f : `Reading ${f}`}
                  </span>
                </div>
              );
            })}

            {sources.length > 3 && (
              <button
                onClick={() => setSourcesExpanded(!sourcesExpanded)}
                className="flex items-center gap-1 mt-1 text-[10px] hover:text-[#93c5fd] transition-colors self-start cursor-pointer"
                style={{ color: "#86868b" }}
              >
                {sourcesExpanded ? (
                  <>Collapse <ChevronUp size={10} /></>
                ) : (
                  <>+ {sources.length - 3} more <ChevronDown size={10} /></>
                )}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function useTypewriter(phrases: string[], speed = 60, pause = 3200) {
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

function SourcePanel({ source, onClose, onOpenDoc }: { source: Source; onClose: () => void; onOpenDoc?: (title: string) => void }) {
  const [copied, setCopied] = useState(false);
  const copyExcerpt = () => {
    navigator.clipboard.writeText(source.excerpt || "").then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };
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
              onClick={() => {
                if (source.documentId) {
                  window.open(`/ingest/documents/${source.documentId}/file`, "_blank");
                } else {
                  onOpenDoc?.(source.title);
                  onClose();
                }
              }}
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
              onClick={copyExcerpt}
              className="px-4 py-2.5 rounded-xl text-xs font-medium transition-all duration-200 flex items-center gap-1.5"
              style={{
                background: copied ? "rgba(16,185,129,0.12)" : "rgba(255,255,255,0.04)",
                border: `1px solid ${copied ? "rgba(16,185,129,0.25)" : "rgba(255,255,255,0.08)"}`,
                color: copied ? "#10b981" : "#86868B",
              }}
              onMouseEnter={(e) => { if (!copied) e.currentTarget.style.background = "rgba(255,255,255,0.08)"; }}
              onMouseLeave={(e) => { if (!copied) e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
            >
              {copied ? <><Check size={11} />Copied</> : <><Copy size={11} />Copy</>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const TYPEWRITER_PHRASES = [
  "Search your documents...",
  "Hỏi tôi bất cứ điều gì về tài liệu của bạn...",
  "What's in that PDF?",
  "Tóm tắt tài liệu, trích dẫn nguồn...",
  "Ask me anything...",
  "ドキュメントについて何でも聞いてください...",
  "Ciel sẵn sàng giúp bạn.",
  "Find answers across all your files...",
  "Khám phá kho tài liệu nội bộ...",
  "What would you like to know today?",
  "Ciel đây, bạn cần tôi giúp gì?",
];

function TypewriterSubtitle() {
  const text = useTypewriter(TYPEWRITER_PHRASES);
  return (
    <p
      className="font-semibold tracking-tight text-center"
      style={{
        fontSize: "1.75rem",
        lineHeight: 1.3,
        minHeight: "1.4em",
        textAlign: "center",
        background: "linear-gradient(135deg, #f5f5f7 0%, #93c5fd 55%, #8b5cf6 100%)",
        WebkitBackgroundClip: "text",
        backgroundClip: "text",
        WebkitTextFillColor: "transparent",
        color: "transparent",
      }}
    >
      {text}
      <span
        className="inline-block w-[3px] ml-1 align-middle animate-pulse"
        style={{ height: "0.95em", background: "#8b5cf6", WebkitTextFillColor: "initial" }}
      />
    </p>
  );
}

function EmptyState({ onSuggestion, suggestions, loadingSuggestions }: {
  onSuggestion: (text: string) => void;
  suggestions: Suggestion[];
  loadingSuggestions: boolean;
}) {
  return (
    <div className="flex-1 flex flex-col items-center px-6 py-6">
      <div className="flex-1" />
      <div className="w-full max-w-2xl flex items-center justify-center" style={{ minHeight: 64 }}>
        <TypewriterSubtitle />
      </div>
      <div className="flex-1" />

      {/* Suggestion cards */}
      <div className="grid grid-cols-2 gap-3 w-full max-w-xl pb-6">
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

function SyncPanel({ onUploaded, onToast, targetCollection = "default", collections = [], lang = "vi" }: {
  onUploaded: (job: UploadJob) => void;
  onToast: (msg: string, type: Toast["type"]) => void;
  targetCollection?: string;
  collections?: Collection[];
  lang?: Lang;
}) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const existingUploadRef = useRef<HTMLInputElement>(null);
  const syncMenuRef = useRef<HTMLDivElement>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncProgress, setSyncProgress] = useState({ done: 0, total: 0 });
  const [syncMenu, setSyncMenu] = useState<null | "choose" | "existing">(null);
  const [existingTarget, setExistingTarget] = useState("");
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [nameDialog, setNameDialog] = useState<{ open: boolean; value: string }>({ open: false, value: "" });

  useEffect(() => {
    if (!syncMenu) return;
    const close = (e: MouseEvent) => {
      if (syncMenuRef.current && !syncMenuRef.current.contains(e.target as Node)) setSyncMenu(null);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [syncMenu]);

  const doUpload = async (files: File[], collection: string) => {
    for (const file of files) {
      const form = new FormData();
      form.append("file", file);
      form.append("collection", collection);
      onToast(`Uploading "${file.name}"...`, "info");
      try {
        const res = await fetch("/ingest/upload", { method: "POST", body: form });
        if (!res.ok) { onToast(`Failed: "${file.name}"`, "error"); continue; }
        const data = await res.json();
        onUploaded({ jobId: data.job_id, filename: file.name, status: "queued" });
        setSyncProgress((p) => ({ ...p, done: p.done + 1 }));
      } catch { onToast(`Failed: "${file.name}"`, "error"); }
    }
  };

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const valid = Array.from(files).filter((f) => /\.(pdf|png|jpg|jpeg|docx|xlsx|csv)$/i.test(f.name));
    doUpload(valid, targetCollection);
  };

  const handleFolderPicked = (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const valid = Array.from(files).filter((f) => /\.(pdf|png|jpg|jpeg|docx|xlsx|csv)$/i.test(f.name));
    if (!valid.length) { onToast("No supported files found in folder", "error"); return; }
    const rawPath = (valid[0] as { webkitRelativePath?: string }).webkitRelativePath || "";
    const folderName = rawPath.split("/")[0] || "New Folder";
    setPendingFiles(valid);
    setNameDialog({ open: true, value: folderName });
  };

  const confirmNewFolder = async () => {
    const name = nameDialog.value.trim();
    if (!name) return;
    setNameDialog({ open: false, value: "" });
    setSyncing(true);
    setSyncProgress({ done: 0, total: pendingFiles.length });
    await doUpload(pendingFiles, name);
    setSyncing(false);
    setPendingFiles([]);
  };

  const handleExistingUpload = async (files: FileList | null) => {
    if (!files || !existingTarget) return;
    const valid = Array.from(files).filter((f) => /\.(pdf|png|jpg|jpeg|docx|xlsx|csv)$/i.test(f.name));
    if (!valid.length) return;
    setSyncing(true);
    setSyncProgress({ done: 0, total: valid.length });
    await doUpload(valid, existingTarget);
    setSyncing(false);
    setSyncMenu(null);
    setExistingTarget("");
  };

  const T = UI_STRINGS[lang];
  const otherCollections = collections.filter((c) => c.name !== "default");

  return (
    <div className="mx-3 mb-2 flex flex-col gap-1.5">
      <input ref={fileInputRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx,.csv" multiple className="hidden"
        onChange={(e) => handleFiles(e.target.files)} />
      <input ref={folderInputRef} type="file" className="hidden" {...({ webkitdirectory: "" } as object)}
        onChange={(e) => handleFolderPicked((e.target as HTMLInputElement).files)} />
      <input ref={existingUploadRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx,.csv" multiple className="hidden"
        onChange={(e) => handleExistingUpload(e.target.files)} />

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
        {T.uploadFiles}
      </button>

      <div className="relative" ref={syncMenuRef}>
        <button
          onMouseDown={() => { if (!syncing) setSyncMenu((m) => (m ? null : "choose")); }}
          disabled={syncing}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-[11px] font-medium transition-all duration-200"
          style={{
            border: "1px solid rgba(59,130,246,0.25)",
            color: syncing ? "#86868B" : "#93c5fd",
            background: "rgba(59,130,246,0.06)",
            cursor: syncing ? "not-allowed" : "pointer",
          }}
        >
          {syncing
            ? <><RefreshCw size={12} className="animate-spin" />{T.syncing(syncProgress.done, syncProgress.total)}</>
            : <><FolderOpen size={12} />{T.syncFolder}</>
          }
        </button>

        {syncMenu === "choose" && (
          <div className="absolute bottom-full left-0 right-0 mb-1.5 rounded-xl overflow-hidden"
            style={{ background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", zIndex: 60, boxShadow: "0 8px 32px rgba(0,0,0,0.5)" }}>
            <button
              onMouseDown={(e) => { e.stopPropagation(); setSyncMenu("existing"); setExistingTarget(""); }}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left text-[11px] transition-colors"
              style={{ color: "#c7c7cc" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              <FolderOpen size={12} style={{ color: "#93c5fd" }} />
              {T.addToExisting}
            </button>
            <div style={{ height: 1, background: "rgba(255,255,255,0.05)" }} />
            <button
              onMouseDown={(e) => { e.stopPropagation(); setSyncMenu(null); setTimeout(() => folderInputRef.current?.click(), 0); }}
              className="w-full flex items-center gap-2.5 px-3 py-2.5 text-left text-[11px] transition-colors"
              style={{ color: "#c7c7cc" }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              <Plus size={12} style={{ color: "#86efac" }} />
              {T.createNewFolder}
            </button>
          </div>
        )}

        {syncMenu === "existing" && (
          <div className="absolute bottom-full left-0 right-0 mb-1.5 rounded-xl p-2"
            style={{ background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", zIndex: 60, boxShadow: "0 8px 32px rgba(0,0,0,0.5)" }}>
            <div className="flex items-center justify-between mb-1.5 px-1">
              <p className="text-[10px]" style={{ color: "rgba(134,134,139,0.7)" }}>{T.selectTargetFolder}</p>
              <button onMouseDown={() => setSyncMenu("choose")} className="text-[10px]" style={{ color: "rgba(134,134,139,0.5)" }}>{T.back}</button>
            </div>
            <div className="flex flex-col gap-0.5 max-h-36 overflow-y-auto mb-2">
              {otherCollections.length === 0
                ? <p className="text-[10px] px-2 py-1" style={{ color: "rgba(134,134,139,0.4)" }}>{T.noFoldersYet}</p>
                : otherCollections.map((c) => (
                  <button
                    key={c.name}
                    onMouseDown={() => setExistingTarget(c.name)}
                    className="flex items-center justify-between px-2 py-1.5 rounded-lg text-[11px] text-left transition-colors"
                    style={{ background: existingTarget === c.name ? "rgba(59,130,246,0.2)" : "transparent", color: existingTarget === c.name ? "#93c5fd" : "#c7c7cc" }}
                    onMouseEnter={(e) => { if (existingTarget !== c.name) e.currentTarget.style.background = "rgba(255,255,255,0.04)"; }}
                    onMouseLeave={(e) => { if (existingTarget !== c.name) e.currentTarget.style.background = "transparent"; }}
                  >
                    <span className="flex items-center gap-1.5"><FolderOpen size={10} />{c.name}</span>
                    <span style={{ color: "rgba(134,134,139,0.5)", fontSize: 9 }}>{c.doc_count} docs</span>
                  </button>
                ))
              }
            </div>
            <button
              disabled={!existingTarget}
              onMouseDown={() => existingUploadRef.current?.click()}
              className="w-full flex items-center justify-center gap-1.5 px-2 py-1.5 rounded-lg text-[11px] font-medium transition-all"
              style={{
                background: existingTarget ? "rgba(59,130,246,0.25)" : "rgba(255,255,255,0.04)",
                color: existingTarget ? "#93c5fd" : "rgba(134,134,139,0.4)",
                cursor: existingTarget ? "pointer" : "not-allowed",
              }}
            >
              <Upload size={10} />
              {existingTarget ? T.uploadTo(existingTarget) : T.selectFolderFirst}
            </button>
          </div>
        )}
      </div>

      {nameDialog.open && (
        <div className="fixed inset-0 flex items-center justify-center" style={{ background: "rgba(0,0,0,0.6)", zIndex: 200 }}>
          <div className="rounded-2xl p-5 w-72" style={{ background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 24px 60px rgba(0,0,0,0.7)" }}>
            <p className="text-[13px] font-semibold mb-1" style={{ color: "#f5f5f7" }}>{T.nameThisFolder}</p>
            <p className="text-[11px] mb-4" style={{ color: "rgba(134,134,139,0.7)" }}>
              {T.filesWillUpload(pendingFiles.length)}
            </p>
            <input
              value={nameDialog.value}
              onChange={(e) => setNameDialog((d) => ({ ...d, value: e.target.value }))}
              onKeyDown={(e) => { if (e.key === "Enter") confirmNewFolder(); if (e.key === "Escape") { setNameDialog({ open: false, value: "" }); setPendingFiles([]); } }}
              autoFocus
              className="w-full text-[12px] rounded-xl px-3 py-2 mb-4 outline-none"
              style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.12)", color: "#f5f5f7" }}
              placeholder={T.folderNamePlaceholder}
            />
            <div className="flex gap-2">
              <button
                onClick={() => { setNameDialog({ open: false, value: "" }); setPendingFiles([]); }}
                className="flex-1 px-3 py-1.5 rounded-xl text-[11px] font-medium"
                style={{ background: "rgba(255,255,255,0.06)", color: "#86868B" }}
              >
                {T.cancel}
              </button>
              <button
                onClick={confirmNewFolder}
                disabled={!nameDialog.value.trim()}
                className="flex-1 px-3 py-1.5 rounded-xl text-[11px] font-medium transition-opacity"
                style={{ background: "#3B82F6", color: "white", opacity: nameDialog.value.trim() ? 1 : 0.4 }}
              >
                {T.upload}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const STATUS_FALLBACK_PCT: Record<UploadJob["status"], number> = {
  queued: 0, extracting: 10, chunking: 55, embedding: 65, completed: 100, failed: 100,
};

function JobBadge({ job, onCancel }: { job: UploadJob; onCancel?: () => void }) {
  const pct = job.progress ?? STATUS_FALLBACK_PCT[job.status];
  const isRunning = !["completed", "failed"].includes(job.status);
  const isStuck = isRunning && !!job.progressAt && (Date.now() - job.progressAt > 5 * 60 * 1000);
  const color = job.status === "completed" ? "#10b981" : job.status === "failed" ? "#ef4444" : isStuck ? "#f59e0b" : "#3B82F6";
  const icon = job.status === "completed"
    ? <CheckCircle size={11} style={{ color: "#10b981" }} />
    : job.status === "failed"
    ? <AlertCircle size={11} style={{ color: "#ef4444" }} />
    : isStuck
    ? <AlertCircle size={11} style={{ color: "#f59e0b" }} />
    : <Loader size={11} className="animate-spin" style={{ color: "#3B82F6" }} />;

  return (
    <div className="flex items-center gap-2 px-2.5 py-2 rounded-lg mx-3 mb-1"
      style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
      {icon}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <p className="text-[11px] truncate max-w-[110px]" style={{ color: isRunning ? "#d1d1d6" : color }}>
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
                : isStuck
                ? "#f59e0b"
                : `linear-gradient(90deg, #2563EB, ${job.status === "completed" ? "#10b981" : "#3B82F6"})`,
            }}
          />
        </div>
        <p className="text-[10px] mt-0.5" style={{ color: isStuck ? "#f59e0b" : "rgba(134,134,139,0.6)" }}>
          {isStuck ? "Stuck? Try cancelling" : STATUS_LABEL[job.status]}
        </p>
      </div>
      {isRunning && onCancel && (
        <button
          onClick={onCancel}
          title="Cancel"
          className="shrink-0 rounded p-0.5 transition-colors"
          style={{ color: "rgba(134,134,139,0.5)" }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "#ef4444")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(134,134,139,0.5)")}
        >
          <X size={11} />
        </button>
      )}
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
  { id: "llama-3.3-70b-versatile",                   label: "Llama 3.3 · 70B",    note: "280 t/s" },
  { id: "openai/gpt-oss-20b",                        label: "GPT-OSS · 20B",       note: "1000 t/s" },
  { id: "meta-llama/llama-4-scout-17b-16e-instruct", label: "Llama 4 Scout · 17B", note: "New" },
  { id: "qwen/qwen3-32b",                            label: "Qwen3 · 32B",          note: "60 RPM" },
  { id: "llama-3.1-8b-instant",                      label: "Llama 3.1 · 8B",       note: "560 t/s" },
];

const OPENAI_MODELS = [
  { id: "gpt-4o",                  label: "GPT-4o",          note: "Omni" },
  { id: "gpt-4o-mini",             label: "GPT-4o Mini",     note: "Fast" },
  { id: "o1-mini",                 label: "o1-Mini",         note: "Reason" },
];

const GEMINI_MODELS = [
  { id: "gemini-2.5-flash",     label: "Gemini 2.5 Flash",  note: "Latest" },
  { id: "gemini-2.0-flash",     label: "Gemini 2.0 Flash",  note: "Stable" },
  { id: "gemini-2.0-flash-lite",label: "Gemini 2.0 Lite",   note: "Fast"   },
];

const OPENROUTER_MODELS_FALLBACK = [
  { id: "nvidia/nemotron-3-ultra-550b-a55b:free",           label: "Nemotron Ultra 550B", note: "1M ctx" },
  { id: "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", label: "Nemotron Nano 30B",   note: "Reason" },
  { id: "poolside/laguna-m.1:free",                          label: "Laguna M.1",           note: "262K" },
  { id: "cohere/north-mini-code:free",                       label: "North Mini Code",       note: "Code" },
];

const OPENROUTER_MODELS = OPENROUTER_MODELS_FALLBACK;

const CEREBRAS_MODELS = [
  { id: "gpt-oss-120b", label: "GPT-OSS 120B", note: "3000 t/s" },
  { id: "gemma-4-31b",  label: "Gemma 4 31B",  note: "1850 t/s" },
  { id: "zai-glm-4.7",  label: "Z.ai GLM 4.7", note: "355B"     },
];

const ANTHROPIC_MODELS = [
  { id: "claude-opus-4-8",                label: "Claude Opus 4.8",   note: "Best"     },
  { id: "claude-sonnet-5",                label: "Claude Sonnet 5",   note: "Fast"     },
  { id: "claude-haiku-4-5-20251001",      label: "Claude Haiku 4.5",  note: "Cheapest" },
];

const MODEL_MIGRATIONS: Record<string, string> = {
  "llama3-8b-8192":                     "llama-3.1-8b-instant",
  "mixtral-8x7b-32768":                 "llama-3.3-70b-versatile",
  "llama3-70b-8192":                    "llama-3.3-70b-versatile",
  "gemini-2.5-flash-preview-05-20":     "gemini-2.5-flash",
  "gemini-2.5-flash-preview-04-17":     "gemini-2.5-flash",
  "gemini-2.5-pro-preview-06-05":       "gemini-2.5-flash",
  "gemini-1.5-flash":                   "gemini-2.0-flash",
  "gemini-1.5-pro":                     "gemini-2.0-flash",
  "qwen/qwen-2.5-72b-instruct:free":    "nvidia/nemotron-3-ultra-550b-a55b:free",
  "microsoft/phi-4-reasoning:free":     "nvidia/nemotron-3-ultra-550b-a55b:free",
  "google/gemma-3-27b-it:free":         "nvidia/nemotron-3-ultra-550b-a55b:free",
  "llama3.1-8b":                        "gpt-oss-120b",
  "llama3.1-70b":                       "gpt-oss-120b",
  "llama-3.3-70b":                      "gpt-oss-120b",
};

function migrateModel(id: string): string {
  return MODEL_MIGRATIONS[id] ?? id;
}

const LOCAL_MODELS = [
  { id: "gemma3:4b",        label: "Gemma 3 · 4B",    note: "Fast"   },
  { id: "gemma2:9b",        label: "Gemma 2 · 9B",    note: "Logic"  },
  { id: "llama3:8b",        label: "Llama 3 · 8B",    note: "8K ctx" },
  { id: "phi3:mini",        label: "Phi-3 Mini · 3.8B", note: "128K" },
  { id: "qwen2.5-coder:7b", label: "Qwen 2.5 · 7B",  note: "Code"   },
  { id: "gemma3:12b",       label: "Gemma 3 · 12B",   note: "OOM ⚠" },
];

const MODELS = [
  ...LOCAL_MODELS,
  ...GROQ_MODELS,
  ...OPENAI_MODELS,
  ...GEMINI_MODELS,
  ...OPENROUTER_MODELS,
  ...CEREBRAS_MODELS,
  ...ANTHROPIC_MODELS,
];

function isGroqModel(id: string) {
  return GROQ_MODELS.some((m) => m.id === id);
}

function isOpenAIModel(id: string) {
  return OPENAI_MODELS.some((m) => m.id === id);
}

function isGeminiModel(id: string) {
  return GEMINI_MODELS.some((m) => m.id === id);
}

function isOpenRouterModel(id: string) {
  return id.includes("/") && !GROQ_MODELS.some((m) => m.id === id) && !CEREBRAS_MODELS.some((m) => m.id === id);
}

function isCerebrasModel(id: string) {
  return CEREBRAS_MODELS.some((m) => m.id === id);
}

function isAnthropicModel(id: string) {
  return ANTHROPIC_MODELS.some((m) => m.id === id);
}

const getActiveApiKey = (modelId: string) => {
  if (isGroqModel(modelId)) return localStorage.getItem("chatrag_api_key_groq") || localStorage.getItem("chatrag_api_key") || "";
  if (isOpenAIModel(modelId)) return localStorage.getItem("chatrag_api_key_openai") || "";
  if (isGeminiModel(modelId)) return localStorage.getItem("chatrag_api_key_gemini") || "";
  if (isOpenRouterModel(modelId)) return localStorage.getItem("chatrag_api_key_openrouter") || "";
  if (isCerebrasModel(modelId)) return localStorage.getItem("chatrag_api_key_cerebras") || "";
  if (isAnthropicModel(modelId)) return localStorage.getItem("chatrag_api_key_anthropic") || "";
  return "";
};

const getProviderOfModel = (modelId: string) => {
  if (isGroqModel(modelId)) return "groq";
  if (isOpenAIModel(modelId)) return "openai";
  if (isGeminiModel(modelId)) return "gemini";
  if (isOpenRouterModel(modelId)) return "openrouter";
  if (isCerebrasModel(modelId)) return "cerebras";
  if (isAnthropicModel(modelId)) return "anthropic";
  return "ollama";
};

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

function ContextBar({
  scope, collections, hybridMode, totalDocs, onScopeChange, onHybridChange,
}: {
  scope: ChatScope;
  collections: Collection[];
  hybridMode: boolean;
  totalDocs: number;
  onScopeChange: (s: ChatScope) => void;
  onHybridChange: (h: boolean) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const selectedNames = scope.type === "selected" ? scope.collections : [];
  const label = scope.type === "all"
    ? `All folders · ${totalDocs}`
    : selectedNames.length === 1
      ? `${selectedNames[0]} · ${collections.find(c => c.name === selectedNames[0])?.doc_count ?? 0}`
      : `${selectedNames.length} folders selected`;

  const toggle = (name: string) => {
    const cur = scope.type === "selected" ? scope.collections : [];
    const next = cur.includes(name) ? cur.filter((c) => c !== name) : [...cur, name];
    onScopeChange(next.length === 0 ? { type: "all" } : { type: "selected", collections: next });
  };

  return (
    <div className="flex items-center gap-2 pb-2">
      <div className="relative" ref={ref}>
        <button
          onClick={() => setOpen((o) => !o)}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all"
          style={{
            background: scope.type === "all" ? "rgba(255,255,255,0.05)" : "rgba(59,130,246,0.12)",
            border: `1px solid ${scope.type === "all" ? "rgba(255,255,255,0.1)" : "rgba(59,130,246,0.3)"}`,
            color: scope.type === "all" ? "#86868B" : "#93c5fd",
            whiteSpace: "nowrap",
          }}
        >
          {scope.type === "all" ? <Database size={10} /> : <FolderOpen size={10} />}
          {label}
          <ChevronDown size={9} style={{ opacity: 0.6, transform: open ? "rotate(180deg)" : "none", transition: "transform 0.15s" }} />
        </button>

        {open && (
          <div className="absolute bottom-full left-0 mb-1.5 rounded-xl overflow-hidden"
            style={{ background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 -8px 32px rgba(0,0,0,0.5)", zIndex: 200, minWidth: 210 }}>
            <div className="p-1">
              <button
                onClick={() => { onScopeChange({ type: "all" }); setOpen(false); }}
                className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[11px] text-left transition-colors"
                style={{ background: scope.type === "all" ? "rgba(59,130,246,0.12)" : "transparent", color: scope.type === "all" ? "#93c5fd" : "#c7c7cc" }}
                onMouseEnter={(e) => { if (scope.type !== "all") e.currentTarget.style.background = "rgba(255,255,255,0.05)"; }}
                onMouseLeave={(e) => { if (scope.type !== "all") e.currentTarget.style.background = "transparent"; }}
              >
                <Database size={11} style={{ flexShrink: 0 }} />
                <span className="flex-1">All folders</span>
                <span style={{ color: "rgba(134,134,139,0.5)", fontSize: 10 }}>{totalDocs}</span>
                {scope.type === "all" && <Check size={10} style={{ color: "#93c5fd", flexShrink: 0 }} />}
              </button>
              {collections.length > 0 && (
                <div style={{ height: 1, background: "rgba(255,255,255,0.05)", margin: "2px 8px" }} />
              )}
              {collections.map((col) => {
                const sel = selectedNames.includes(col.name);
                return (
                  <button
                    key={col.name}
                    onClick={() => toggle(col.name)}
                    className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-[11px] text-left transition-colors"
                    style={{ background: sel ? "rgba(59,130,246,0.1)" : "transparent", color: sel ? "#93c5fd" : "#c7c7cc" }}
                    onMouseEnter={(e) => { if (!sel) e.currentTarget.style.background = "rgba(255,255,255,0.05)"; }}
                    onMouseLeave={(e) => { if (!sel) e.currentTarget.style.background = "transparent"; }}
                  >
                    <FolderOpen size={11} style={{ flexShrink: 0 }} />
                    <span className="flex-1 truncate">{col.name}</span>
                    <span style={{ color: "rgba(134,134,139,0.5)", fontSize: 10 }}>{col.doc_count}</span>
                    {sel && <Check size={10} style={{ color: "#93c5fd", flexShrink: 0 }} />}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <button
        onClick={() => onHybridChange(!hybridMode)}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all duration-200 shrink-0"
        style={{
          background: hybridMode ? "linear-gradient(135deg, #1e40af, #3b82f6)" : "rgba(255,255,255,0.04)",
          border: `1px solid ${hybridMode ? "rgba(59,130,246,0.5)" : "rgba(255,255,255,0.08)"}`,
          color: hybridMode ? "#fff" : "rgba(134,134,139,0.5)",
          boxShadow: hybridMode ? "0 0 10px rgba(59,130,246,0.3)" : "none",
        }}
      >
        <span style={{ fontSize: 9 }}>⚡</span>
        Hybrid
      </button>
    </div>
  );
}

function TranslatorPanel({
  apiKeyGemini,
  apiKeyGroq,
  apiKeyOpenRouter,
  apiKeyOpenAI,
  apiKeyCerebras,
  apiKeyAnthropic,
  activeModel,
  serverProviders,
}: {
  apiKeyGemini: string;
  apiKeyGroq: string;
  apiKeyOpenRouter: string;
  apiKeyOpenAI: string;
  apiKeyCerebras: string;
  apiKeyAnthropic: string;
  activeModel: string;
  serverProviders: Record<string, boolean>;
}) {
  const [jpInput, setJpInput] = useState("");
  const [vnOutput, setVnOutput] = useState("");
  const [txStatus, setTxStatus] = useState<"idle" | "loading" | "streaming" | "done" | "error">("idle");
  const [txError, setTxError] = useState("");
  const [txCopied, setTxCopied] = useState(false);
  const txAbortRef = useRef(false);

  const getTranslateProvider = (): { key: string; provider: string; model: string } => {
    const provider = getProviderOfModel(activeModel);
    if (isGeminiModel(activeModel) && apiKeyGemini) return { key: apiKeyGemini, provider, model: activeModel };
    if (isGroqModel(activeModel) && apiKeyGroq) return { key: apiKeyGroq, provider, model: activeModel };
    if (isOpenRouterModel(activeModel) && apiKeyOpenRouter) return { key: apiKeyOpenRouter, provider, model: activeModel };
    if (isCerebrasModel(activeModel) && apiKeyCerebras) return { key: apiKeyCerebras, provider, model: activeModel };
    if (isOpenAIModel(activeModel) && apiKeyOpenAI) return { key: apiKeyOpenAI, provider, model: activeModel };
    if (isAnthropicModel(activeModel) && apiKeyAnthropic) return { key: apiKeyAnthropic, provider, model: activeModel };
    return { key: "", provider, model: activeModel };
  };

  const handleTranslate = async () => {
    if (!jpInput.trim() || txStatus === "loading" || txStatus === "streaming") return;
    const prov = getTranslateProvider();
    if (!prov.key && !serverProviders[prov.provider]) {
      setTxError(`Chưa có API Key cho ${prov.provider}. Vào ⚙ Model → nhập key, hoặc set ${prov.provider.toUpperCase()}_API_KEY trong .env`);
      setTxStatus("error");
      return;
    }
    txAbortRef.current = false;
    setVnOutput("");
    setTxError("");
    setTxStatus("loading");
    await new Promise((r) => setTimeout(r, 180));
    if (txAbortRef.current) return;
    setTxStatus("streaming");
    translateStreamDirect(
      jpInput,
      prov.key,
      prov.provider,
      (chunk) => { if (!txAbortRef.current) setVnOutput((p) => p + chunk); },
      () => { if (!txAbortRef.current) setTxStatus("done"); },
      (msg) => { setTxError(msg); setTxStatus("error"); },
      prov.model
    );
  };

  const handleAbort = () => {
    txAbortRef.current = true;
    setTxStatus("idle");
  };

  const handleReset = () => {
    txAbortRef.current = true;
    setJpInput("");
    setVnOutput("");
    setTxStatus("idle");
    setTxError("");
  };

  const isLoading = txStatus === "loading";
  const isStreaming = txStatus === "streaming";
  const prov = getTranslateProvider();
  const txProgress = txStatus === "done" ? 100
    : txStatus === "streaming" ? Math.min(95, Math.round((vnOutput.length / Math.max(1, jpInput.length * 1.7)) * 100))
    : txStatus === "loading" ? 5
    : 0;

  return (
    <div className="flex-1 flex flex-col h-full min-w-0 overflow-hidden">
      {/* Translator header bar */}
      <div
        className="shrink-0 flex items-center justify-between px-6 py-2.5"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
      >
        <div className="flex items-center gap-3">
          <span className="text-[13px] font-semibold" style={{ color: "#F5F5F7" }}>日本語 Translator</span>
          <span
            className="px-2 py-0.5 rounded-full text-[10px] font-semibold"
            style={{ background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.25)", color: "#fca5a5" }}
          >
            JP → VN
          </span>
          {(prov.key || serverProviders[prov.provider]) && (
            <span
              className="px-2 py-0.5 rounded-full text-[10px]"
              style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", color: "#86868B" }}
            >
              via {prov.provider}{!prov.key && serverProviders[prov.provider] ? " (env)" : ""}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isStreaming && (
            <button
              onClick={handleAbort}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium"
              style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#f87171" }}
            >
              <Square size={10} fill="#f87171" />
              Dừng
            </button>
          )}
          {(jpInput || vnOutput) && !isStreaming && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] transition-all"
              style={{ border: "1px solid rgba(255,255,255,0.1)", color: "#86868B" }}
              onMouseEnter={(e) => { e.currentTarget.style.color = "#F5F5F7"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.25)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = "#86868B"; e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; }}
            >
              <RefreshCw size={11} />
              Làm mới
            </button>
          )}
        </div>
      </div>

      {/* 2-panel layout */}
      <div className="flex-1 flex min-h-0">
        {/* Left panel — JP input */}
        <div
          className="flex-1 flex flex-col min-w-0"
          style={{ borderRight: "1px solid rgba(255,255,255,0.06)" }}
        >
          <div
            className="shrink-0 flex items-center justify-between px-4 py-2"
            style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
          >
            <span className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: "#86868B" }}>
              🇯🇵 Nhật
            </span>
            {jpInput && (
              <div className="flex items-center gap-2">
                <span className="text-[10px]" style={{ color: "rgba(134,134,139,0.5)" }}>
                  {jpInput.length.toLocaleString()} ký tự
                </span>
                <button
                  onClick={() => setJpInput("")}
                  style={{ color: "rgba(134,134,139,0.4)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = "#86868B")}
                  onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(134,134,139,0.4)")}
                >
                  <X size={12} />
                </button>
              </div>
            )}
          </div>

          <textarea
            value={jpInput}
            onChange={(e) => setJpInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); handleTranslate(); } }}
            placeholder={"日本語のテキストをここに貼り付けてください…\n\nCtrl+Enter để dịch nhanh"}
            className="flex-1 bg-transparent resize-none outline-none p-4 text-sm leading-relaxed scrollbar-hide"
            style={{
              color: "#F5F5F7",
              caretColor: "#3B82F6",
              fontFamily: "inherit",
              minHeight: 0,
            }}
            spellCheck={false}
          />

          <div
            className="shrink-0 flex items-center justify-end px-4 py-2.5 gap-2"
            style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
          >
            <button
              onClick={handleTranslate}
              disabled={!jpInput.trim() || isLoading || isStreaming}
              className="flex items-center gap-2 px-5 py-1.5 rounded-full text-[12px] font-semibold transition-all duration-200"
              style={{
                background: jpInput.trim() && !isLoading && !isStreaming
                  ? "linear-gradient(135deg, #2563EB, #3B82F6)"
                  : "rgba(255,255,255,0.06)",
                color: jpInput.trim() && !isLoading && !isStreaming ? "#fff" : "rgba(134,134,139,0.4)",
                boxShadow: jpInput.trim() && !isLoading && !isStreaming ? "0 0 14px rgba(59,130,246,0.25)" : "none",
                cursor: !jpInput.trim() || isLoading || isStreaming ? "not-allowed" : "pointer",
              }}
            >
              {isLoading || isStreaming ? (
                <><Loader size={11} className="animate-spin" />Đang dịch…</>
              ) : (
                "Dịch ngay →"
              )}
            </button>
          </div>
        </div>

        {/* Right panel — VN output */}
        <div className="flex-1 flex flex-col min-w-0">
          <div
            className="shrink-0 flex items-center justify-between px-4 py-2"
            style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
          >
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: "#86868B" }}>
                🇻🇳 Việt
              </span>
              {txStatus === "streaming" && (
                <span className="text-[10px]" style={{ color: "#3B82F6" }}>Đang dịch… {txProgress}%</span>
              )}
              {txStatus === "done" && (
                <span className="text-[10px]" style={{ color: "#10b981" }}>✓ Hoàn tất</span>
              )}
              {txStatus === "error" && (
                <span className="text-[10px]" style={{ color: "#f87171" }}>Lỗi</span>
              )}
            </div>
            {vnOutput && !isStreaming && (
              <button
                onClick={() => {
                  navigator.clipboard.writeText(vnOutput);
                  setTxCopied(true);
                  setTimeout(() => setTxCopied(false), 1500);
                }}
                className="flex items-center gap-1 text-[10px] transition-all"
                style={{ color: txCopied ? "#10b981" : "#86868B" }}
                onMouseEnter={(e) => { if (!txCopied) e.currentTarget.style.color = "#d1d1d6"; }}
                onMouseLeave={(e) => { if (!txCopied) e.currentTarget.style.color = "#86868B"; }}
              >
                {txCopied ? <Check size={11} /> : <Copy size={11} />}
                {txCopied ? "Copied" : "Copy"}
              </button>
            )}
          </div>

          {(isLoading || isStreaming || txStatus === "done") && (
            <div className="shrink-0 h-[2px] w-full" style={{ background: "rgba(255,255,255,0.05)" }}>
              <div
                className="h-[2px] transition-all duration-300"
                style={{
                  width: `${txProgress}%`,
                  background: txStatus === "done"
                    ? "#10b981"
                    : "linear-gradient(90deg, #2563EB, #3B82F6)",
                }}
              />
            </div>
          )}

          <div className="flex-1 overflow-y-auto px-4 py-4 scrollbar-hide">
            {txStatus === "error" ? (
              <div
                className="text-[13px] p-3 rounded-xl leading-relaxed"
                style={{ background: "rgba(239,68,68,0.08)", border: "1px solid rgba(239,68,68,0.2)", color: "#f87171" }}
              >
                ⚠ {txError}
              </div>
            ) : isLoading ? (
              <div className="flex flex-col gap-3 pt-1">
                {[75, 60, 70, 50, 65].map((w, i) => (
                  <div
                    key={i}
                    className="h-3.5 rounded-md animate-pulse"
                    style={{ width: `${w}%`, background: "rgba(255,255,255,0.05)" }}
                  />
                ))}
              </div>
            ) : vnOutput ? (
              <div
                className="text-[14px] leading-[1.9] whitespace-pre-wrap break-words"
                style={{ color: "#d1d1d6", fontFamily: "inherit" }}
              >
                {vnOutput}
                {isStreaming && (
                  <span
                    className="inline-block w-[2px] h-[1em] ml-0.5 align-middle animate-pulse"
                    style={{ background: "#3B82F6", verticalAlign: "middle" }}
                  />
                )}
                {txStatus === "done" && countResidualCJK(vnOutput) > 0 && (
                  <div
                    className="mt-4 flex items-start gap-2 px-3 py-2 rounded-lg text-[12px]"
                    style={{ background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.3)", color: "#fcd34d" }}
                  >
                    <AlertCircle size={13} className="mt-0.5 shrink-0" />
                    <span>
                      Bản dịch còn sót {countResidualCJK(vnOutput)} ký tự Hán/Nhật chưa dịch — dấu hiệu model chưa xử lý hết văn bản khó. Thử lại với model mạnh hơn (Claude, Gemini 2.5) để có kết quả sạch.
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div
                className="h-full flex flex-col items-center justify-center gap-2"
                style={{ color: "rgba(134,134,139,0.25)" }}
              >
                <span style={{ fontSize: 36, fontFamily: "serif" }}>翻</span>
                <span className="text-[12px]">Bản dịch sẽ hiển thị ở đây</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────

export default function App() {
  const [chats, setChats] = useState<Chat[]>(loadChatsFromStorage);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [mode, setMode] = useState<"chat" | "translate">("chat");

  const getProviderKeyInfo = (provider: string) => {
    switch (provider) {
      case "groq":
        return {
          key: apiKeyGroq,
          setKey: setApiKeyGroq,
          localKey: "chatrag_api_key_groq",
          label: "Groq",
          placeholder: "gsk_...",
          models: GROQ_MODELS,
          link: "console.groq.com",
        };
      case "openai":
        return {
          key: apiKeyOpenAI,
          setKey: setApiKeyOpenAI,
          localKey: "chatrag_api_key_openai",
          label: "OpenAI",
          placeholder: "sk-...",
          models: OPENAI_MODELS,
          link: "platform.openai.com",
        };
      case "gemini":
        return {
          key: apiKeyGemini,
          setKey: setApiKeyGemini,
          localKey: "chatrag_api_key_gemini",
          label: "Gemini",
          placeholder: "AIzaSy...",
          models: GEMINI_MODELS,
          link: "aistudio.google.com",
        };
      case "openrouter":
        return {
          key: apiKeyOpenRouter,
          setKey: setApiKeyOpenRouter,
          localKey: "chatrag_api_key_openrouter",
          label: "OpenRouter",
          placeholder: "sk-or-...",
          models: OPENROUTER_MODELS,
          link: "openrouter.ai/keys",
        };
      case "cerebras":
        return {
          key: apiKeyCerebras,
          setKey: setApiKeyCerebras,
          localKey: "chatrag_api_key_cerebras",
          label: "Cerebras",
          placeholder: "csk-...",
          models: CEREBRAS_MODELS,
          link: "cloud.cerebras.ai",
        };
      case "anthropic":
        return {
          key: apiKeyAnthropic,
          setKey: setApiKeyAnthropic,
          localKey: "chatrag_api_key_anthropic",
          label: "Anthropic",
          placeholder: "sk-ant-...",
          models: ANTHROPIC_MODELS,
          link: "console.anthropic.com",
        };
      default:
        return null;
    }
  };

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [inputFocused, setInputFocused] = useState(false);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const [browsePreview, setBrowsePreview] = useState<{ url: string; domain: string } | null>(null);
  const [isBrowsing, setIsBrowsing] = useState(false);
  const [webSearchMode, setWebSearchMode] = useState(false);
  const [isWebSearching, setIsWebSearching] = useState(false);
  const webSearchResultsRef = useRef<WebSource[]>([]);
  const isWebSearchActiveRef = useRef(false);
  const activeChat = chats.find((c) => c.id === activeChatId) ?? null;
  const [activeSource, setActiveSource] = useState<Source | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const streamingChatIdRef = useRef<string | null>(null);
  const activeChatIdRef = useRef<string | null>(null);
  const chatsRef = useRef<Chat[]>(chats);
  const [processingStep, setProcessingStep] = useState("embedding");
  const [processingLabel, setProcessingLabel] = useState("");
  const [readingSources, setReadingSources] = useState<string[]>([]);

  const getContextualLabel = (step: string, question: string): string => {
    const q = question.length > 36 ? question.slice(0, 36) + "…" : question;
    const map: Record<string, string> = {
      "web-search": S.stepWebSearch(q),
      embedding: S.stepEmbedding(q),
      searching: S.stepSearching(q),
      filtering: S.stepFiltering,
      generating: S.stepGenerating,
    };
    return map[step] ?? step;
  };
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
    const migrated = MODEL_MIGRATIONS[stored];
    if (migrated) {
      localStorage.setItem("chatrag_model", migrated);
      return migrated;
    }
    return stored;
  });
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);
  const [deletingChatId, setDeletingChatId] = useState<string | null>(null);
  const [uiLang, setUiLang] = useState<Lang>(() => (localStorage.getItem("ui_lang") as Lang) || "vi");
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const S = UI_STRINGS[uiLang];
  const handleSetLang = (lang: Lang) => { localStorage.setItem("ui_lang", lang); setUiLang(lang); };
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
  const [apiKeyGroq, setApiKeyGroq] = useState(() => localStorage.getItem("chatrag_api_key_groq") || localStorage.getItem("chatrag_api_key") || "");
  const [apiKeyOpenAI, setApiKeyOpenAI] = useState(() => localStorage.getItem("chatrag_api_key_openai") || "");
  const [apiKeyGemini, setApiKeyGemini] = useState(() => localStorage.getItem("chatrag_api_key_gemini") || "");
  const [apiKeyOpenRouter, setApiKeyOpenRouter] = useState(() => localStorage.getItem("chatrag_api_key_openrouter") || "");
  const [apiKeyCerebras, setApiKeyCerebras] = useState(() => localStorage.getItem("chatrag_api_key_cerebras") || "");
  const [apiKeyAnthropic, setApiKeyAnthropic] = useState(() => localStorage.getItem("chatrag_api_key_anthropic") || "");
  const [serverProviders, setServerProviders] = useState<Record<string, boolean>>({});
  const [orModels, setOrModels] = useState<{id:string,label:string,note:string}[]>(OPENROUTER_MODELS_FALLBACK);
  const [orLoading, setOrLoading] = useState(false);

  const [modelMenuView, setModelMenuView] = useState<"providers" | "ollama" | "groq" | "openai" | "gemini" | "openrouter" | "cerebras" | "anthropic">("providers");
  const [editingProviderKey, setEditingProviderKey] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [memoryPanelOpen, setMemoryPanelOpen] = useState(false);
  const [memoryTab, setMemoryTab] = useState<"global" | "chat">("global");
  const [chatNoteInputs, setChatNoteInputs] = useState<Record<string, string>>({});
  const [expandedChatNotes, setExpandedChatNotes] = useState<Set<string>>(new Set());
  const [kbBrowserOpen, setKbBrowserOpen] = useState(false);
  const [kbBrowserFolder, setKbBrowserFolder] = useState<string | null>(null);
  const [kbBrowserSearch, setKbBrowserSearch] = useState("");
  const [kbViewerDoc, setKbViewerDoc] = useState<KBDocument | null>(null);
  const [kbBrowserConfirmDeleteDoc, setKbBrowserConfirmDeleteDoc] = useState<string | null>(null);
  const [memories, setMemories] = useState<{ id: string; content: string; created_at: number }[]>([]);
  const [newMemory, setNewMemory] = useState("");
  const [memParticles, setMemParticles] = useState<string[]>([]);
  const avatarBtnRef = useRef<HTMLButtonElement>(null);

  const refreshMemories = async () => {
    try {
      const r = await fetch("/memory");
      if (r.ok) setMemories(await r.json());
    } catch {}
  };
  const addMemory = async () => {
    const c = newMemory.trim();
    if (!c) return;
    const r = await fetch("/memory", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: c }) });
    if (r.ok) { setNewMemory(""); refreshMemories(); }
    else { const err = await r.json().catch(() => ({})); addToast(err?.detail || "Không thể lưu bộ nhớ", "error"); }
  };
  const deleteMemory = async (id: string) => {
    const r = await fetch(`/memory/${id}`, { method: "DELETE" });
    if (r.ok) refreshMemories();
  };
  const addChatNote = (chatId: string, text: string) => {
    const t = text.trim();
    if (!chatId || !t) return;
    setChats((prev) => {
      const updated = prev.map((c) => {
        if (c.id !== chatId) return c;
        const existing = Array.isArray(c.notes) ? c.notes : c.notes ? [c.notes as unknown as string] : [];
        return { ...c, notes: [...existing, t] };
      });
      saveChatsToStorage(updated);
      return updated;
    });
    setChatNoteInputs((prev) => ({ ...prev, [chatId]: "" }));
  };
  const deleteChatNote = (chatId: string, idx: number) => {
    if (!chatId) return;
    setChats((prev) => {
      const updated = prev.map((c) => {
        if (c.id !== chatId) return c;
        const existing = Array.isArray(c.notes) ? c.notes : c.notes ? [c.notes as unknown as string] : [];
        return { ...c, notes: existing.filter((_, i) => i !== idx) };
      });
      saveChatsToStorage(updated);
      return updated;
    });
  };
  const clearChatNotes = (chatId: string) => {
    if (!chatId) return;
    setChats((prev) => {
      const updated = prev.map((c) => (c.id === chatId ? { ...c, notes: [] } : c));
      saveChatsToStorage(updated);
      return updated;
    });
  };
  const toggleChatNoteExpand = (chatId: string) => {
    setExpandedChatNotes((prev) => {
      const next = new Set(prev);
      if (next.has(chatId)) next.delete(chatId);
      else next.add(chatId);
      return next;
    });
  };
  useEffect(() => { refreshMemories(); }, []);
  useEffect(() => {
    if (!memoryPanelOpen || memoryTab !== "chat") return;
    const id = activeChatId ?? chats[0]?.id;
    if (id) setExpandedChatNotes((prev) => (prev.has(id) ? prev : new Set(prev).add(id)));
  }, [memoryPanelOpen, memoryTab, activeChatId]);

  useEffect(() => {
    fetch("/chat/providers").then(r => r.ok ? r.json() : {}).then(setServerProviders).catch(() => {});
  }, []);

  useEffect(() => {
    sessionStorage.setItem("uploadJobs", JSON.stringify(uploadJobs));
  }, [uploadJobs]);

  useEffect(() => {
    const raw = sessionStorage.getItem("uploadJobs");
    if (!raw) return;
    try {
      const saved: UploadJob[] = JSON.parse(raw);
      if (!saved.length) return;
      setUploadJobs(saved);
      saved
        .filter((j) => !["completed", "failed"].includes(j.status))
        .forEach((j) => pollJob(j.jobId, j.filename));
    } catch {}
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const profileRef = useRef<HTMLDivElement>(null);
  const chatFileInputRef = useRef<HTMLInputElement>(null);
  const kbSectionRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const pollIntervalsRef = useRef<Map<string, ReturnType<typeof setInterval>>>(new Map());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const userScrolledRef = useRef(false);
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
    if (pollIntervalsRef.current.has(jobId)) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/ingest/jobs/${jobId}`);
        if (!res.ok) return;
        const data = await res.json();
        const status = data.status as UploadJob["status"];
        const progress = data.progress !== undefined ? parseInt(data.progress) : undefined;
        setUploadJobs((prev) => prev.map((j) => {
          if (j.jobId !== jobId) return j;
          const progressChanged = progress !== undefined && progress !== j.progress;
          return { ...j, status, step: data.step, error: data.error, progress, progressAt: progressChanged ? Date.now() : j.progressAt };
        }));
        if (status === "completed") {
          addToast(`"${filename}" is ready to query`, "success");
          clearInterval(interval);
          pollIntervalsRef.current.delete(jobId);
        } else if (status === "failed") {
          const isCancelled = data.error === "Cancelled by user";
          if (!isCancelled) addToast(`"${filename}" failed to process`, "error");
          clearInterval(interval);
          pollIntervalsRef.current.delete(jobId);
        }
      } catch {
        clearInterval(interval);
        pollIntervalsRef.current.delete(jobId);
      }
    }, 2000);
    pollIntervalsRef.current.set(jobId, interval);
  }, [addToast]);

  const cancelJob = useCallback(async (jobId: string) => {
    const iv = pollIntervalsRef.current.get(jobId);
    if (iv) { clearInterval(iv); pollIntervalsRef.current.delete(jobId); }
    await fetch(`/ingest/jobs/${jobId}`, { method: "DELETE" }).catch(() => {});
    setUploadJobs((prev) => prev.map((j) => j.jobId === jobId ? { ...j, status: "failed", error: "Cancelled by user" } : j));
  }, []);

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

  const fetchSuggestions = useCallback(async (scope: ChatScope, lang?: Lang) => {
    setLoadingSuggestions(true);
    try {
      const params = new URLSearchParams();
      if (scope.type === "selected") params.set("collections", scope.collections.map(encodeURIComponent).join(","));
      params.set("lang", lang || "vi");
      const res = await fetch(`/chat/suggestions?${params}`);
      if (res.ok) setSuggestions(await res.json());
    } finally {
      setLoadingSuggestions(false);
    }
  }, []);

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsProcessing(false);
    setIsStreaming(false);
    setReadingSources([]);
    streamingChatIdRef.current = null;
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

  useEffect(() => { activeChatIdRef.current = activeChatId; }, [activeChatId]);
  useEffect(() => { chatsRef.current = chats; }, [chats]);

  useEffect(() => {
    if (modelMenuOpen) {
      const currentProvider = getProviderOfModel(activeModel);
      setModelMenuView(currentProvider);
      setEditingProviderKey(null);
    }
  }, [modelMenuOpen, activeModel]);

  useEffect(() => {
    if (userScrolledRef.current) return;
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isProcessing]);

  useEffect(() => {
    if (!modelMenuOpen) return;
    const close = (e: MouseEvent) => {
      if (modelMenuRef.current?.contains(e.target as Node)) return;
      setModelMenuOpen(false);
      setModelSettingsOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [modelMenuOpen]);

  useEffect(() => {
    if (!exportMenuOpen) return;
    const close = (e: MouseEvent) => {
      if (exportMenuRef.current?.contains(e.target as Node)) return;
      setExportMenuOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [exportMenuOpen]);

  useEffect(() => { if (!profileOpen) setLangMenuOpen(false); }, [profileOpen]);
  useEffect(() => {
    if (!profileOpen) return;
    const close = (e: MouseEvent) => {
      if (profileRef.current?.contains(e.target as Node)) return;
      setProfileOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [profileOpen]);

  useEffect(() => {
    fetchCollections();
    fetchSuggestions({ type: "all" }, uiLang);
    loadKbDocs();
    fetch("/chat/models")
      .then((r) => r.ok ? r.json() : { models: [] })
      .then((data) => setOllamaModels(data.models ?? []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const m = input.match(/https?:\/\/[^\s]+/);
    if (m) {
      try {
        const domain = new URL(m[0]).hostname;
        setBrowsePreview({ url: m[0], domain });
      } catch {
        setBrowsePreview(null);
      }
    } else {
      setBrowsePreview(null);
    }
  }, [input]);

  useEffect(() => {
    if (modelMenuView !== "openrouter") return;
    setOrLoading(true);
    fetch("https://openrouter.ai/api/v1/models")
      .then((r) => r.json())
      .then((data) => {
        const free = (data.data || [])
          .filter((m: any) => m.id.endsWith(":free"))
          .sort((a: any, b: any) => (b.context_length || 0) - (a.context_length || 0))
          .slice(0, 10)
          .map((m: any) => ({
            id: m.id,
            label: (m.name || m.id.split("/")[1] || m.id).replace(/:free$/i, ""),
            note: "Free",
          }));
        if (free.length > 0) setOrModels(free);
      })
      .catch(() => {})
      .finally(() => setOrLoading(false));
  }, [modelMenuView]);

  const serverSyncReadyRef = useRef(false);

  useEffect(() => {
    fetch("/chat/sessions")
      .then((r) => r.json())
      .then((serverChats: Chat[]) => {
        if (Array.isArray(serverChats) && serverChats.length > 0) {
          setChats(serverChats);
        }
      })
      .catch(() => {})
      .finally(() => { serverSyncReadyRef.current = true; });
  }, []);

  useEffect(() => {
    if (!serverSyncReadyRef.current) return;
    const t = setTimeout(() => {
      fetch("/chat/sessions", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(chats),
      }).catch(() => {});
    }, 1500);
    return () => clearTimeout(t);
  }, [chats]);

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

    flushSync(() => {
      setInput("");
    });
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    const userMsg: Message = { id: Date.now().toString(), role: "user", content };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    userScrolledRef.current = false;
    setShowScrollBtn(false);

    // If URL detected, fetch page content and inject as context
    let questionToSend = content;
    const urlMatch = content.match(/https?:\/\/[^\s]+/);
    if (urlMatch) {
      const url = urlMatch[0];
      setIsBrowsing(true);
      try {
        const browseRes = await fetch("/chat/browse", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
        });
        if (browseRes.ok) {
          const data = await browseRes.json();
          if (data.text) {
            questionToSend = `[Nội dung trang ${url}:\n${data.text}]\n\n${content}`;
          }
        }
      } catch {
        // browse failed — send original question
      }
      setIsBrowsing(false);
      setBrowsePreview(null);
    }

    // Web search mode — call DuckDuckGo and inject results as context
    isWebSearchActiveRef.current = false;
    webSearchResultsRef.current = [];
    const hasWebIntent = /tìm trên web|trên web|duyệt web|tìm web|tìm trên mạng|trên mạng|tìm kiếm trên|search (the )?web|search online|look (it )?up online|find online|google (it|this)|搜索网络|网上搜|上网搜|搜一下|ウェブで|ネットで調べ|検索して/i.test(content);
    if (hasWebIntent) setWebSearchMode(true);
    if ((webSearchMode || hasWebIntent) && !urlMatch) {
      isWebSearchActiveRef.current = true;
      setIsProcessing(true);
      setProcessingStep("web-search");
      const shortQ = content.split(/[\n.。]/)[0].trim().slice(0, 50);
      setProcessingLabel(getContextualLabel("web-search", shortQ || content));
      setIsWebSearching(true);
      try {
        const buildSearchQuery = (text: string): string => {
          // Cut off at meta-instruction keywords that follow the real search intent
          const cutoffMatch = text.match(/\b(kẻ bảng|lịch trình chi tiết|vag gửi|vag|gửi cho|tìm trên web mà|xuất phát từ)\b/i);
          let q = cutoffMatch ? text.slice(0, cutoffMatch.index) : text;
          // Strip remaining meta-instruction phrases
          q = q
            .replace(/\btìm trên web\b/gi, "")
            .replace(/\bduyệt web\b/gi, "")
            .replace(/\btrên web\b/gi, "")
            .replace(/\bweb\b/gi, "")
            .replace(/\s{2,}/g, " ")
            .trim();
          // Prefer first line/sentence, fall back to full cleaned text
          const firstLine = q.split(/[\n.。]/)[0].trim();
          return (firstLine || q).slice(0, 80);
        };
        const searchQuery = buildSearchQuery(content);
        const searchRes = await fetch("/chat/web-search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: searchQuery }),
        });
        if (searchRes.ok) {
          const data = await searchRes.json();
          if (data.results && data.results.length > 0) {
            const results = data.results as { title: string; body: string; href: string }[];
            // Store as WebSource for display
            webSearchResultsRef.current = results.slice(0, 5).map((r) => {
              let domain = r.href;
              try { domain = new URL(r.href).hostname.replace(/^www\./, ""); } catch {}
              return { title: r.title, href: r.href, domain, snippet: r.body };
            });
            // Show domains in step indicator
            setReadingSources(webSearchResultsRef.current.map((s) => s.domain));
            const snippets = results
              .map((r, i) => `${i + 1}. ${r.title}\n${r.body}\nURL: ${r.href}`)
              .join("\n\n");
            const fullSection = data.top_content
              ? `\n\nNội dung đầy đủ từ ${data.top_url}:\n${data.top_content}`
              : "";
            questionToSend = `[Kết quả tìm web cho "${content}":\n${snippets}${fullSection}]\n\n${content}`;
          }
        }
      } catch {
        // search failed — send without web context
      }
      setIsWebSearching(false);
    }

    setIsProcessing(true);
    setProcessingStep("embedding");
    setReadingSources([]);

    let chatId = activeChatId;
    if (!chatId) {
      chatId = Date.now().toString();
      const title = content.length > 48 ? content.slice(0, 48) + "…" : content;
      const newChatEntry: Chat = { id: chatId, title, createdAt: Date.now(), messages: nextMessages };
      setChats((prev) => { const u = [newChatEntry, ...prev]; saveChatsToStorage(u); return u; });
      setActiveChatId(chatId);
      activeChatIdRef.current = chatId;
    } else {
      persistChat(chatId, nextMessages);
    }

    streamingChatIdRef.current = chatId;
    const aiId = (Date.now() + 1).toString();
    let finalSources: Source[] = [];
    let finalConfidence: number | null = null;

    // Update messages for the streaming chat — if user has navigated away, update chats store directly
    const updateStreamMsg = (updater: (prev: Message[]) => Message[]) => {
      const cid = streamingChatIdRef.current;
      if (!cid) return;
      setChats((prevChats) => {
        const chat = prevChats.find((c) => c.id === cid);
        if (!chat) return prevChats;
        const newMsgs = updater(chat.messages);
        const updated = prevChats.map((c) => c.id === cid ? { ...c, messages: newMsgs } : c);
        saveChatsToStorage(updated);
        return updated;
      });
      if (activeChatIdRef.current === cid) {
        setMessages(updater);
      }
    };

    try {
      const controller = new AbortController();
      abortControllerRef.current = controller;
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          question: questionToSend,
          collections: chatScope.type === "selected" ? chatScope.collections : null,
          hybrid: hybridMode,
          model: migrateModel(activeModel),
          history: messages.slice(-6).map((m) => ({ role: m.role, content: m.content })),
          chat_notes: (() => { const n = chats.find((c) => c.id === activeChatId)?.notes; return Array.isArray(n) ? n.join("\n") : (n as unknown as string) || ""; })(),
          api_key: getActiveApiKey(migrateModel(activeModel)),
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const mapSrc = (s: { id: string; content: string; section?: string; similarity: number; filename: string; document_id?: string }, i: number): Source => ({
        id: `src-${Date.now()}-${i}`,
        title: s.section ?? s.filename ?? `Source ${i + 1}`,
        type: (s.filename?.endsWith(".pdf") ? "pdf" : "doc") as Source["type"],
        excerpt: s.content,
        date: new Date().toISOString().slice(0, 10),
        confidence: Math.round(s.similarity * 100),
        documentId: s.document_id,
        filename: s.filename,
      });

      const handleLine = (line: string) => {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data: ")) return;
        let ev: Record<string, unknown>;
        try { ev = JSON.parse(trimmed.slice(6)); } catch { return; }
        if (ev.type === "memory_saved") {
          const pid = Date.now().toString(36) + Math.random().toString(36).slice(2);
          setMemParticles((p) => [...p, pid]);
          setTimeout(() => setMemParticles((p) => p.filter((x) => x !== pid)), 1600);
          setTimeout(() => refreshMemories(), 200);
        } else if (ev.type === "step") {
          const s = ev.step as string;
          setProcessingStep(s);
          setProcessingLabel(getContextualLabel(s, content));
        } else if (ev.type === "sources") {
          const srcs = ev.sources as Array<{ id: string; content: string; section?: string; similarity: number; filename: string }>;
          setReadingSources(srcs.map((s) => s.filename));
          finalSources = srcs.map(mapSrc);
        } else if (ev.type === "token") {
          const token = ev.token as string;
          setIsProcessing(false);
          setIsStreaming(true);
          updateStreamMsg((prev) => {
            const existing = prev.find((m) => m.id === aiId);
            const newContent = (existing?.content ?? "") + token;
            if (existing) return prev.map((m) => m.id === aiId ? { ...m, content: newContent, isStreaming: true } : m);
            return [...prev, { id: aiId, role: "assistant" as const, content: newContent, isStreaming: true }];
          });
        } else if (ev.type === "done") {
          if (ev.confidence !== undefined) {
            finalConfidence = ev.confidence as number | null;
          }
          if (Array.isArray(ev.sources)) {
            finalSources = (ev.sources as Array<{ id: string; content: string; section?: string; similarity: number; filename: string }>).map(mapSrc);
          }
        }
      };

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";
          lines.forEach(handleLine);
        }
        if (buffer.trim()) handleLine(buffer);
      } finally {
        reader.releaseLock();
      }

      // Finalize: mark streaming done, attach sources + web sources, fallback if empty
      const capturedWebSources = isWebSearchActiveRef.current && webSearchResultsRef.current.length > 0
        ? webSearchResultsRef.current
        : undefined;
      isWebSearchActiveRef.current = false;
      let finalContent = "";
      updateStreamMsg((prev) => {
        const existing = prev.find((m) => m.id === aiId);
        const content = existing?.content?.trim() ? tryConvertListToTable(existing.content, S.tableColItem, S.tableColContent) : "No answer returned.";
        finalContent = content;
        const finalMsg: Message = { id: aiId, role: "assistant", content, sources: capturedWebSources ? [] : finalSources, webSources: capturedWebSources, confidence: finalConfidence, isStreaming: false };
        return existing
          ? prev.map((m) => m.id === aiId ? finalMsg : m)
          : [...prev, finalMsg];
      });
      // Fire-and-forget: fetch follow-up suggestions, attach to message when ready
      (async () => {
        try {
          const r = await fetch("/chat/follow-ups", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              question: content,
              answer: finalContent.slice(0, 800),
              source_filenames: finalSources.slice(0, 3).map((s) => s.filename || s.title),
              model: migrateModel(activeModel),
              api_key: getActiveApiKey(migrateModel(activeModel)),
            }),
          });
          if (!r.ok) return;
          const data = await r.json();
          const sugg: string[] = Array.isArray(data?.suggestions) ? data.suggestions : [];
          if (!sugg.length) return;
          updateStreamMsg((prev) =>
            prev.map((m) => (m.id === aiId ? { ...m, followUps: sugg } : m))
          );
        } catch {}
      })();
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === "AbortError") {
        updateStreamMsg((prev) => {
          const existing = prev.find((m) => m.id === aiId);
          const stoppedNote = "\n\n_— Generation stopped._";
          if (!existing) {
            const stoppedMsg: Message = {
              id: aiId,
              role: "assistant",
              content: "_Generation stopped before any output._",
              sources: finalSources,
              confidence: finalConfidence,
            };
            return [...prev, stoppedMsg];
          }
          return prev.map((m) =>
            m.id === aiId
              ? { ...m, isStreaming: false, sources: finalSources, confidence: finalConfidence, content: (m.content || "") + stoppedNote }
              : m
          );
        });
      } else {
        const errMsg: Message = {
          id: aiId,
          role: "assistant",
          content: "Something went wrong connecting to the knowledge base. Please try again.",
        };
        updateStreamMsg((prev) => [...prev, errMsg]);
      }
    } finally {
      setIsProcessing(false);
      setIsStreaming(false);
      setReadingSources([]);
      streamingChatIdRef.current = null;
    }
  };

  const loadChat = (chat: Chat) => {
    const latest = chatsRef.current.find((c) => c.id === chat.id) ?? chat;
    setActiveChatId(latest.id);
    activeChatIdRef.current = latest.id;
    setMessages(latest.messages);
    setActiveSource(null);
    setActiveSourceId(null);
    userScrolledRef.current = false;
    setShowScrollBtn(false);
  };

  const newChat = () => {
    setMessages([]);
    setActiveChatId(null);
    activeChatIdRef.current = null;
    setActiveSource(null);
    setActiveSourceId(null);
    setInput("");
    userScrolledRef.current = false;
    setShowScrollBtn(false);
    // Don't abort ongoing stream — let it complete in background chat
  };

  const deleteChat = (chatId: string) => {
    setChats((prev) => {
      const updated = prev.filter((c) => c.id !== chatId);
      saveChatsToStorage(updated);
      return updated;
    });
    if (activeChatId === chatId) newChat();
  };

  const exportActiveChat = (format: "txt" | "md" | "docx" | "json") => {
    const chat = chats.find((c) => c.id === activeChatId);
    if (!chat) return;
    const title = chat.title || "chat";
    const date = new Date(chat.createdAt).toISOString().slice(0, 19).replace("T", " ");
    const now = new Date().toISOString().slice(0, 19).replace("T", " ");
    const safeTitle = title.replace(/[^\w\d\-_. ]/g, "").slice(0, 60).trim() || "chat";

    let blob: Blob;
    if (format === "json") {
      const data = {
        title,
        created: date,
        exported: now,
        messages: chat.messages.map((m) => ({
          role: m.role,
          content: m.content,
          sources: (m.sources || []).map((s) => s.filename || s.title),
        })),
      };
      blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json;charset=utf-8" });
    } else if (format === "docx") {
      blob = buildDocx(title, chat.messages);
    } else if (format === "txt") {
      const lines: string[] = [title, `Exported: ${now}`, `Created: ${date}`, ""];
      for (const m of chat.messages) {
        lines.push(m.role === "user" ? "Bạn:" : "Ciel:", m.content.trim(), "");
        if (m.sources && m.sources.length) {
          lines.push("Nguồn: " + m.sources.map((s) => s.filename || s.title).join(", "), "");
        }
      }
      blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
    } else {
      const lines: string[] = [`# ${title}`, "", `_Exported: ${now}_`, `_Created: ${date}_`, ""];
      for (const m of chat.messages) {
        const speaker = m.role === "user" ? "**You**" : "**Ciel**";
        lines.push(`${speaker}:`, "", m.content.trim(), "");
        if (m.sources && m.sources.length) {
          lines.push("_Sources:_");
          for (const s of m.sources) lines.push(`- ${s.filename || s.title}`);
          lines.push("");
        }
        lines.push("---", "");
      }
      blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${safeTitle}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    addToast(S.exportedToast(`${safeTitle}.${format}`), "success");
    setExportMenuOpen(false);
  };

  const togglePinChat = (chatId: string) => {
    setChats((prev) => {
      const updated = prev.map((c) => c.id === chatId ? { ...c, pinned: !c.pinned } : c);
      saveChatsToStorage(updated);
      return updated;
    });
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
            {S.newChat}
          </button>
        </div>

        {/* History */}
        <div className="flex-1 overflow-y-auto px-3 py-2 scrollbar-hide">
          {chats.length === 0 ? (
            <p className="text-center text-[11px] py-4" style={{ color: "rgba(134,134,139,0.4)" }}>No chats yet</p>
          ) : (
            (["pinned", "today", "week", "older"] as const).map((group) => {
              const sq = searchQuery.trim().toLowerCase();
              const items = chats
                .filter((c) => group === "pinned" ? c.pinned : !c.pinned && chatGroup(c.createdAt) === group)
                .filter((c) => {
                  if (!sq) return true;
                  if (c.title.toLowerCase().includes(sq)) return true;
                  return c.messages.some((m) => m.content.toLowerCase().includes(sq));
                });
              if (items.length === 0) return null;
              const label = group === "pinned" ? S.pinned : group === "today" ? S.today : group === "week" ? S.thisWeek : S.older;
              return (
                <div key={group} className="mb-4">
                  <p className="text-[10px] font-medium uppercase tracking-widest px-2 mb-1.5"
                    style={{ color: group === "pinned" ? "rgba(251,191,36,0.6)" : "rgba(134,134,139,0.5)" }}>{label}</p>
                  {items.map((chat) => (
                    <div key={chat.id} className="group relative mb-0.5">
                      <button
                        onClick={() => loadChat(chat)}
                        className="w-full text-left px-2.5 py-2 rounded-lg transition-all duration-150 pr-12"
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
                        <p className="text-[12px] font-medium truncate flex items-center gap-1.5"
                          style={{ color: activeChatId === chat.id ? "#93c5fd" : "#d1d1d6" }}>
                          {chat.pinned && <span style={{ color: "#fbbf24", fontSize: 9 }}>★</span>}
                          {chat.title}
                        </p>
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); togglePinChat(chat.id); }}
                        className={`absolute right-6 top-1/2 -translate-y-1/2 ${chat.pinned ? "opacity-100" : "opacity-0 group-hover:opacity-100"} transition-opacity p-1 rounded`}
                        style={{ color: chat.pinned ? "#fbbf24" : "#86868B" }}
                        title={chat.pinned ? "Unpin" : "Pin"}
                      >
                        <span style={{ fontSize: 11 }}>★</span>
                      </button>
                      <button
                          onClick={(e) => { e.stopPropagation(); setDeletingChatId(chat.id); }}
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
        <div ref={kbSectionRef} className="flex flex-col min-h-0 flex-1 overflow-hidden" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>

          {/* KB header */}
          <div className="flex items-center justify-between px-3 pt-3 pb-1.5 shrink-0 gap-2">
            <span className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-widest shrink-0" style={{ color: "rgba(134,134,139,0.5)" }}>
              <Database size={10} />
              {S.knowledgeBase}
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
                <p className="text-[10px]" style={{ color: "rgba(134,134,139,0.35)" }}>{S.noFiles}</p>
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
            {uploadJobs.slice(-4).reverse().map((j) => <JobBadge key={j.jobId} job={j} onCancel={() => cancelJob(j.jobId)} />)}
          </div>
        )}

        {/* Upload buttons */}
        <div className="shrink-0" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
          <SyncPanel
            onToast={addToast}
            lang={uiLang}
            targetCollection={kbFilter || "default"}
            collections={Object.entries(folderMap)
              .filter(([name]) => name !== "default")
              .map(([name, docs]) => ({ name, doc_count: docs.length }))
              .sort((a, b) => a.name.localeCompare(b.name))}
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
            {/* Mode toggle */}
            <div
              className="flex items-center rounded-full p-0.5"
              style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.09)" }}
            >
              <button
                onClick={() => setMode("chat")}
                className="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-medium transition-all duration-200"
                style={{
                  background: mode === "chat" ? "#1C1C1E" : "transparent",
                  color: mode === "chat" ? "#F5F5F7" : "rgba(134,134,139,0.6)",
                  boxShadow: mode === "chat" ? "0 1px 4px rgba(0,0,0,0.35)" : "none",
                }}
              >
                💬 Chat
              </button>
              <button
                onClick={() => setMode("translate")}
                className="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-medium transition-all duration-200"
                style={{
                  background: mode === "translate" ? "#1C1C1E" : "transparent",
                  color: mode === "translate" ? "#F5F5F7" : "rgba(134,134,139,0.6)",
                  boxShadow: mode === "translate" ? "0 1px 4px rgba(0,0,0,0.35)" : "none",
                }}
              >
                🇯🇵 Dịch JP
              </button>
            </div>
            {mode === "chat" && activeChat && (
              <>
                <span style={{ color: "rgba(255,255,255,0.15)" }}>/</span>
                <span className="text-[13px] truncate max-w-[220px]" style={{ color: "#86868B" }}>
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
              {S.newChat}
            </button>
            {activeChatId && messages.length > 0 && (
              <div className="relative" ref={exportMenuRef}>
                <button
                  onClick={() => setExportMenuOpen((o) => !o)}
                  title={S.exportTitle}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-medium transition-all"
                  style={{ border: "1px solid rgba(255,255,255,0.1)", color: "#86868B" }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = "rgba(59,130,246,0.4)"; e.currentTarget.style.color = "#F5F5F7"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)"; e.currentTarget.style.color = "#86868B"; }}
                >
                  <Upload size={12} style={{ transform: "rotate(180deg)" }} />
                  {S.exportBtn}
                  <ChevronDown size={10} />
                </button>
                {exportMenuOpen && (
                  <div
                    className="absolute right-0 top-full mt-1.5 rounded-xl overflow-hidden z-50 py-1"
                    style={{ minWidth: 150, background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 8px 32px rgba(0,0,0,0.5)" }}
                  >
                    {([
                      { fmt: "txt", label: S.exportFormatTxt, ext: ".txt" },
                      { fmt: "md", label: S.exportFormatMd, ext: ".md" },
                      { fmt: "docx", label: S.exportFormatDocx, ext: ".docx" },
                      { fmt: "json", label: S.exportFormatJson, ext: ".json" },
                    ] as const).map((opt) => (
                      <button
                        key={opt.fmt}
                        onClick={() => exportActiveChat(opt.fmt)}
                        className="w-full flex items-center justify-between px-3 py-2 text-[11px] transition-colors text-left"
                        style={{ color: "#c7c7cc" }}
                        onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
                        onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                      >
                        <span>{opt.label}</span>
                        <span className="text-[10px] font-mono" style={{ color: "#52525b" }}>{opt.ext}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
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
                {MODELS.find((m) => m.id === activeModel)?.label
                  ?? orModels.find((m) => m.id === activeModel)?.label
                  ?? (activeModel.includes("/") ? activeModel.split("/")[1].replace(/:free$/, "").split("-").slice(0,3).join(" ") : activeModel)}
                <ChevronDown size={10} />
              </button>
              {modelMenuOpen && (
                <div
                  className="absolute right-0 top-full mt-1.5 rounded-xl overflow-hidden z-50 flex flex-col"
                  style={{ width: 230, maxHeight: "380px", background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 8px 32px rgba(0,0,0,0.5)" }}
                >
                  <div className="overflow-y-auto flex-1 scrollbar-hide">
                    {modelMenuView === "providers" && (
                      <div className="px-1 py-1.5">
                        <div className="px-3 py-2">
                          <p className="text-[9px] font-semibold tracking-wider uppercase" style={{ color: "rgba(134,134,139,0.5)" }}>Chọn API Provider</p>
                        </div>
                        {[
                          { id: "ollama",     label: "Local · Ollama" },
                          { id: "groq",       label: "Cloud · Groq" },
                          { id: "cerebras",   label: "Cloud · Cerebras" },
                          { id: "openai",     label: "Cloud · OpenAI" },
                          { id: "gemini",     label: "Cloud · Gemini" },
                          { id: "openrouter", label: "Cloud · OpenRouter" },
                          { id: "anthropic",  label: "Cloud · Anthropic" },
                        ].map((prov) => {
                          const isCurrent = getProviderOfModel(activeModel) === prov.id;
                          const localKeyMap: Record<string, string> = {
                            groq: apiKeyGroq, openai: apiKeyOpenAI, gemini: apiKeyGemini,
                            openrouter: apiKeyOpenRouter, cerebras: apiKeyCerebras, anthropic: apiKeyAnthropic,
                          };
                          const hasLocalKey = !!localKeyMap[prov.id];
                          const hasServerKey = !!serverProviders[prov.id];
                          return (
                            <button
                              key={prov.id}
                              onClick={() => setModelMenuView(prov.id as any)}
                              className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-[11px] font-medium transition-colors text-left"
                              style={{
                                background: isCurrent ? "rgba(59,130,246,0.12)" : "transparent",
                                color: isCurrent ? "#93c5fd" : "#c7c7cc",
                              }}
                              onMouseEnter={(e) => { if (!isCurrent) e.currentTarget.style.background = "rgba(255,255,255,0.05)"; }}
                              onMouseLeave={(e) => { if (!isCurrent) e.currentTarget.style.background = "transparent"; }}
                            >
                              <span>{prov.label}</span>
                              <div className="flex items-center gap-1.5">
                                {hasServerKey && !hasLocalKey && (
                                  <span className="text-[9px] px-1.5 py-0.5 rounded-full" style={{ background: "rgba(16,185,129,0.15)", color: "#34d399", border: "1px solid rgba(16,185,129,0.25)" }}>via .env</span>
                                )}
                                {hasLocalKey && (
                                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: "#10b981" }} />
                                )}
                                <ChevronRight size={10} style={{ opacity: 0.5 }} />
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {modelMenuView === "ollama" && (
                      <div className="px-1 py-1.5">
                        <div className="px-3 py-2 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", marginBottom: 4 }}>
                          <button onClick={() => setModelMenuView("providers")} className="text-[9px] transition-colors" style={{ color: "rgba(134,134,139,0.6)" }} onMouseEnter={(e) => e.currentTarget.style.color = "#fff"} onMouseLeave={(e) => e.currentTarget.style.color = "rgba(134,134,139,0.6)"}>← Providers</button>
                          <span className="text-[9px] font-semibold uppercase" style={{ color: "rgba(134,134,139,0.5)" }}>Ollama</span>
                        </div>
                        {LOCAL_MODELS.map((m) => {
                          const notInstalled = ollamaModels.length > 0 && !ollamaModels.some((n) => n === m.id || n.startsWith(m.id.split(":")[0]));
                          return (
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
                              {notInstalled
                                ? <span className="text-[9px] px-1 py-0.5 rounded" style={{ background: "rgba(248,113,113,0.12)", color: "#f87171", border: "1px solid rgba(248,113,113,0.25)" }}>⚠ Not installed</span>
                                : <span className="text-[10px]" style={{ color: m.id === "gemma3:12b" ? "#f87171" : "rgba(134,134,139,0.6)" }}>{m.note}</span>
                              }
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {modelMenuView !== "providers" && modelMenuView !== "ollama" && (() => {
                      const info = getProviderKeyInfo(modelMenuView);
                      if (!info) return null;
                      const hasKey = !!info.key.trim();
                      const hasServerKey = !!serverProviders[modelMenuView];
                      const isEditing = editingProviderKey === modelMenuView || (!hasKey && !hasServerKey);

                      if (isEditing) {
                        return (
                          <div className="px-3 py-3" onMouseDown={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-between mb-2">
                              <button onClick={() => setModelMenuView("providers")} className="text-[9px] transition-colors" style={{ color: "rgba(134,134,139,0.6)" }} onMouseEnter={(e) => e.currentTarget.style.color = "#fff"} onMouseLeave={(e) => e.currentTarget.style.color = "rgba(134,134,139,0.6)"}>← Providers</button>
                              <span className="text-[9px] font-semibold uppercase" style={{ color: "rgba(134,134,139,0.5)" }}>{info.label} Key</span>
                            </div>
                            <p className="text-[10px] mb-1.5" style={{ color: "rgba(134,134,139,0.7)" }}>Nhập API Key cho {info.label}:</p>
                            <div className="relative mb-2">
                              <input
                                type={showApiKey ? "text" : "password"}
                                value={info.key}
                                onChange={(e) => {
                                  info.setKey(e.target.value);
                                  localStorage.setItem(info.localKey, e.target.value);
                                  // Sync legacy chatrag_api_key for backward compatibility if it's groq
                                  if (modelMenuView === "groq") {
                                    localStorage.setItem("chatrag_api_key", e.target.value);
                                    setApiKey(e.target.value);
                                  }
                                }}
                                className="w-full text-[10px] rounded-lg px-2.5 py-1.5 pr-7 outline-none"
                                style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#c7c7cc" }}
                                placeholder={info.placeholder}
                              />
                              <button
                                onMouseDown={(e) => { e.stopPropagation(); setShowApiKey((s) => !s); }}
                                className="absolute right-1.5 top-1/2 -translate-y-1/2"
                                style={{ color: "#86868B" }}
                              >
                                {showApiKey ? <EyeOff size={11} /> : <Eye size={11} />}
                              </button>
                            </div>
                            <button
                              onClick={() => {
                                if (info.key.trim()) {
                                  setEditingProviderKey(null);
                                } else {
                                  addToast("Vui lòng nhập API key", "error");
                                }
                              }}
                              className="w-full py-1.5 rounded-lg text-[10px] font-semibold transition-all"
                              style={{
                                background: info.key.trim() ? "linear-gradient(135deg, #0A66C2, #3B82F6)" : "rgba(255,255,255,0.04)",
                                color: info.key.trim() ? "#fff" : "rgba(134,134,139,0.4)",
                                cursor: info.key.trim() ? "pointer" : "not-allowed",
                              }}
                            >
                              Save &amp; Continue
                            </button>
                            <p className="text-[9px] mt-2 text-center" style={{ color: "rgba(134,134,139,0.4)" }}>
                              Lấy key tại <a href={`https://${info.link}`} target="_blank" rel="noreferrer" className="underline hover:text-white transition-colors">{info.link}</a>
                            </p>
                          </div>
                        );
                      }

                      const displayModels = modelMenuView === "openrouter" ? orModels : info.models;
                      return (
                        <div className="px-1 py-1.5 flex flex-col h-full justify-between">
                          <div>
                            <div className="px-3 py-2 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", marginBottom: 4 }}>
                              <button onClick={() => setModelMenuView("providers")} className="text-[9px] transition-colors" style={{ color: "rgba(134,134,139,0.6)" }} onMouseEnter={(e) => e.currentTarget.style.color = "#fff"} onMouseLeave={(e) => e.currentTarget.style.color = "rgba(134,134,139,0.6)"}>← Providers</button>
                              {modelMenuView === "openrouter" && orLoading
                                ? <span className="text-[9px]" style={{ color: "rgba(134,134,139,0.5)" }}>loading...</span>
                                : <span className="text-[9px] font-semibold uppercase text-green-400">connected</span>}
                            </div>
                            {displayModels.map((m) => (
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
                                <span className="text-[10px]" style={{ color: "rgba(134,134,139,0.6)" }}>{m.note}</span>
                              </button>
                            ))}
                          </div>
                          <div className="mt-2 pt-1" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
                            <button
                              onClick={() => setEditingProviderKey(modelMenuView)}
                              className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-[9px] transition-colors"
                              style={{ color: "rgba(134,134,139,0.55)" }}
                              onMouseEnter={(e) => e.currentTarget.style.color = "#fff"}
                              onMouseLeave={(e) => e.currentTarget.style.color = "rgba(134,134,139,0.55)"}
                            >
                              <Settings size={9} />
                              Thay đổi API Key
                            </button>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                </div>
              )}
            </div>
            {/* Avatar + profile dropdown */}
            <div className="relative" ref={profileRef}>
              <button
                ref={avatarBtnRef}
                onClick={() => setProfileOpen((o) => !o)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold transition-all"
                style={{
                  background: memParticles.length > 0
                    ? "linear-gradient(135deg, #7c3aed, #3B82F6)"
                    : "linear-gradient(135deg, #0A66C2, #3B82F6)",
                  color: "#fff",
                  outline: profileOpen ? "2px solid rgba(59,130,246,0.5)" : memParticles.length > 0 ? "2px solid rgba(124,58,237,0.6)" : "none",
                  transition: "background 0.4s, outline 0.4s",
                }}
                title="Profile"
              >
                A
              </button>
              {profileOpen && (
                <div
                  className="absolute right-0 top-full mt-2 rounded-xl z-50 overflow-hidden"
                  style={{ width: 220, background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 8px 32px rgba(0,0,0,0.5)" }}
                >
                  <div className="px-4 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold shrink-0"
                        style={{ background: "linear-gradient(135deg, #0A66C2, #3B82F6)", color: "#fff" }}>A</div>
                      <div>
                        <p className="text-[12px] font-medium" style={{ color: "#f5f5f7" }}>AanSensei</p>
                        <p className="text-[10px]" style={{ color: "#86868B" }}>Admin</p>
                      </div>
                    </div>
                  </div>
                  <div className="px-2 py-1.5">
                    <button
                      onClick={() => { setProfileOpen(false); setKbBrowserOpen(true); setKbBrowserFolder(null); setKbBrowserSearch(""); }}
                      className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[11px] transition-colors text-left"
                      style={{ color: "#c7c7cc" }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    >
                      <Database size={12} style={{ color: "#86868B" }} />
                      {S.knowledgeBase}: {S.kbDocs(kbDocs.length)}
                    </button>
                    <button
                      onClick={() => { setProfileOpen(false); setMemoryPanelOpen(true); refreshMemories(); }}
                      className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[11px] transition-colors text-left"
                      style={{ color: "#c7c7cc" }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    >
                      <Sparkles size={12} style={{ color: "#86868B" }} />
                      {S.memory}: {S.memoryItems(memories.length)}
                    </button>
                    <button
                      onClick={() => setLangMenuOpen((o) => !o)}
                      className="w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-[11px] transition-colors text-left"
                      style={{ color: "#c7c7cc" }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    >
                      <div className="flex items-center gap-2.5">
                        <Globe size={12} style={{ color: "#86868B" }} />
                        {S.language}
                      </div>
                      <ChevronRight size={10} style={{ color: "#86868B", transform: langMenuOpen ? "rotate(90deg)" : "none", transition: "transform 0.15s" }} />
                    </button>
                    {langMenuOpen && (
                      <div className="mx-1 mb-1 rounded-lg overflow-hidden" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }}>
                        {(([["vi", "Tiếng Việt"], ["en", "English"], ["zh", "中文"], ["ja", "日本語"]] as [Lang, string][]).map(([code, label]) => (
                          <button
                            key={code}
                            onClick={() => { handleSetLang(code); setLangMenuOpen(false); }}
                            className="w-full flex items-center justify-between px-3 py-2 text-[11px] transition-colors text-left"
                            style={{ color: uiLang === code ? "#f5f5f7" : "#86868B" }}
                            onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
                            onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                          >
                            <span>{label}</span>
                            {uiLang === code && <Check size={11} style={{ color: "#c7c7cc" }} />}
                          </button>
                        )))}
                      </div>
                    )}
                    <button
                      onClick={() => {
                        localStorage.clear();
                        window.location.reload();
                      }}
                      className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[11px] transition-colors text-left"
                      style={{ color: "#f87171" }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(248,113,113,0.08)")}
                      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                    >
                      <RefreshCw size={12} />
                      {S.clearData}
                    </button>
                  </div>
                  <div className="px-4 py-2" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                    <p className="text-[9px]" style={{ color: "rgba(134,134,139,0.4)" }}>chatRAG · aansensei</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {mode === "translate" && (
          <TranslatorPanel
            apiKeyGemini={apiKeyGemini}
            apiKeyGroq={apiKeyGroq}
            apiKeyOpenRouter={apiKeyOpenRouter}
            apiKeyOpenAI={apiKeyOpenAI}
            apiKeyCerebras={apiKeyCerebras}
            apiKeyAnthropic={apiKeyAnthropic}
            activeModel={activeModel}
            serverProviders={serverProviders}
          />
        )}

        {memoryPanelOpen && (
          <div
            className="fixed inset-0 z-[100] flex items-center justify-center"
            style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }}
            onClick={() => setMemoryPanelOpen(false)}
          >
            <div
              className="rounded-2xl flex flex-col"
              style={{ width: 500, maxHeight: "80vh", background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 24px 64px rgba(0,0,0,0.6)" }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                <div className="flex items-center gap-2">
                  <Sparkles size={14} style={{ color: "#a78bfa" }} />
                  <h2 className="text-[13px] font-semibold" style={{ color: "#f5f5f7" }}>Memory</h2>
                </div>
                <button onClick={() => setMemoryPanelOpen(false)} className="p-1 rounded hover:bg-white/5">
                  <XIcon size={14} style={{ color: "#86868B" }} />
                </button>
              </div>

              {/* Tabs */}
              <div className="flex px-5 pt-3 gap-1" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                {(["global", "chat"] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setMemoryTab(tab)}
                    className="px-3 py-1.5 rounded-t text-[11px] font-medium transition-colors"
                    style={{
                      background: memoryTab === tab ? "rgba(139,92,246,0.15)" : "transparent",
                      color: memoryTab === tab ? "#a78bfa" : "#86868B",
                      borderBottom: memoryTab === tab ? "2px solid #a78bfa" : "2px solid transparent",
                    }}
                  >
                    {tab === "global" ? S.globalMemory(memories.length) : S.chatMemory}
                  </button>
                ))}
              </div>

              {/* Tab: Kinh nghiệm (global) */}
              {memoryTab === "global" && (
                <>
                  <div className="px-5 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                    <p className="text-[10px] mb-2" style={{ color: "#86868B" }}>
                      Ciel sẽ luôn nhớ những điều này trong <strong style={{ color: "#c7c7cc" }}>mọi cuộc trò chuyện</strong>. Paste prompt dài cũng được.
                    </p>
                    <div className="flex gap-2 items-start">
                      <textarea
                        value={newMemory}
                        onChange={(e) => setNewMemory(e.target.value)}
                        placeholder="VD: Tôi tên Phong, làm AI engineer..."
                        rows={4}
                        className="flex-1 rounded-lg px-3 py-2 text-[12px] resize-y outline-none"
                        style={{ background: "#0f0f10", border: "1px solid rgba(255,255,255,0.08)", color: "#f5f5f7", minHeight: 72 }}
                      />
                      <button
                        onClick={addMemory}
                        disabled={!newMemory.trim()}
                        className="px-3 py-2 rounded-lg text-[11px] font-medium shrink-0"
                        style={{
                          background: newMemory.trim() ? "linear-gradient(135deg, #8b5cf6, #6366f1)" : "rgba(255,255,255,0.04)",
                          color: newMemory.trim() ? "#fff" : "#52525b",
                          cursor: newMemory.trim() ? "pointer" : "not-allowed",
                        }}
                      >
                        Add
                      </button>
                    </div>
                  </div>
                  <div className="flex-1 overflow-y-auto scrollbar-hide px-3 py-2">
                    {memories.length === 0 ? (
                      <p className="text-center py-8 text-[11px]" style={{ color: "#52525b" }}>
                        Chưa có memory nào. Thêm thông tin trên để Ciel ghi nhớ.
                      </p>
                    ) : (
                      memories.map((m) => (
                        <div key={m.id} className="group flex items-start gap-2 px-3 py-2 rounded-lg hover:bg-white/5">
                          <Sparkles size={10} className="mt-1 shrink-0" style={{ color: "#a78bfa" }} />
                          <p className="flex-1 text-[12px] leading-relaxed" style={{ color: "#d1d1d6", whiteSpace: "pre-wrap" }}>{m.content}</p>
                          <button onClick={() => deleteMemory(m.id)} className="opacity-0 group-hover:opacity-100 p-1 rounded transition-opacity">
                            <Trash2 size={11} style={{ color: "#f87171" }} />
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </>
              )}

              {/* Tab: Chat này (per-chat, accordion) */}
              {memoryTab === "chat" && (() => {
                const noteChats = chats
                  .filter((c) => (c.messages && c.messages.length > 0) || (Array.isArray(c.notes) && c.notes.length > 0))
                  .sort((a, b) => {
                    if (a.id === activeChatId) return -1;
                    if (b.id === activeChatId) return 1;
                    return b.createdAt - a.createdAt;
                  })
                  .slice(0, 20);
                return (
                  <div className="flex-1 overflow-y-auto scrollbar-hide px-3 py-3">
                    {noteChats.length === 0 ? (
                      <p className="text-center py-8 text-[11px]" style={{ color: "#52525b" }}>
                        {S.noChatsForNotes}
                      </p>
                    ) : (
                      noteChats.map((chat) => {
                        const notes: string[] = Array.isArray(chat.notes) ? chat.notes : chat.notes ? [chat.notes as unknown as string] : [];
                        const isOpen = expandedChatNotes.has(chat.id);
                        const isActive = chat.id === activeChatId;
                        const questions = chat.messages.filter((m) => m.role === "user").slice(-10);
                        const noteInput = chatNoteInputs[chat.id] || "";
                        return (
                          <div key={chat.id} className="mb-2 rounded-lg overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.06)" }}>
                            <div
                              className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-white/5"
                              onClick={() => toggleChatNoteExpand(chat.id)}
                            >
                              <div className="flex items-center gap-2 min-w-0">
                                {isOpen ? <ChevronDown size={12} style={{ color: "#86868B" }} /> : <ChevronRight size={12} style={{ color: "#86868B" }} />}
                                <span className="text-[12px] truncate" style={{ color: "#f5f5f7" }}>{chat.title || S.newChat}</span>
                                {isActive && (
                                  <span className="text-[9px] px-1.5 py-0.5 rounded shrink-0" style={{ background: "rgba(139,92,246,0.15)", color: "#a78bfa" }}>
                                    {S.activeChatBadge}
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-2 shrink-0">
                                <span className="text-[10px]" style={{ color: "#52525b" }}>{S.noteCount(notes.length)}</span>
                                <button
                                  onClick={(e) => { e.stopPropagation(); clearChatNotes(chat.id); }}
                                  className="p-1 rounded hover:bg-white/10"
                                  title={S.clearNotesTitle}
                                >
                                  <XIcon size={12} style={{ color: "#f87171" }} />
                                </button>
                              </div>
                            </div>
                            {isOpen && (
                              <div className="px-3 pb-3 pt-1" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                                <div className="mb-3">
                                  <p className="text-[10px] font-medium mb-1.5" style={{ color: "#86868B" }}>{S.chatConversation}</p>
                                  {questions.length === 0 ? (
                                    <p className="text-[11px]" style={{ color: "#52525b" }}>{S.noQuestionsYet}</p>
                                  ) : (
                                    <div className="flex flex-col gap-1">
                                      {questions.map((m) => (
                                        <p key={m.id} className="text-[11px] leading-relaxed truncate" style={{ color: "#a1a1a6" }}>• {m.content}</p>
                                      ))}
                                    </div>
                                  )}
                                </div>
                                <div>
                                  <p className="text-[10px] font-medium mb-1.5" style={{ color: "#86868B" }}>{S.chatNotes}</p>
                                  {notes.length === 0 ? (
                                    <p className="text-[11px] mb-2" style={{ color: "#52525b" }}>{S.noNotesYet}</p>
                                  ) : (
                                    notes.map((note, idx) => (
                                      <div key={idx} className="group flex items-start gap-2 px-2 py-1.5 rounded hover:bg-white/5">
                                        <Sparkles size={10} className="mt-0.5 shrink-0" style={{ color: "#a78bfa" }} />
                                        <p className="flex-1 text-[11px] leading-relaxed" style={{ color: "#d1d1d6", whiteSpace: "pre-wrap" }}>{note}</p>
                                        <button onClick={() => deleteChatNote(chat.id, idx)} className="opacity-0 group-hover:opacity-100 p-1 rounded transition-opacity">
                                          <Trash2 size={10} style={{ color: "#f87171" }} />
                                        </button>
                                      </div>
                                    ))
                                  )}
                                  <div className="flex gap-2 items-start mt-2">
                                    <textarea
                                      value={noteInput}
                                      onChange={(e) => setChatNoteInputs((prev) => ({ ...prev, [chat.id]: e.target.value }))}
                                      onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); addChatNote(chat.id, noteInput); } }}
                                      placeholder={S.addNotePlaceholder}
                                      rows={2}
                                      className="flex-1 rounded-lg px-2.5 py-1.5 text-[11px] resize-y outline-none"
                                      style={{ background: "#0f0f10", border: "1px solid rgba(255,255,255,0.08)", color: "#f5f5f7", minHeight: 44 }}
                                    />
                                    <button
                                      onClick={() => addChatNote(chat.id, noteInput)}
                                      disabled={!noteInput.trim()}
                                      className="px-2.5 py-1.5 rounded-lg text-[11px] font-medium shrink-0"
                                      style={{
                                        background: noteInput.trim() ? "linear-gradient(135deg, #8b5cf6, #6366f1)" : "rgba(255,255,255,0.04)",
                                        color: noteInput.trim() ? "#fff" : "#52525b",
                                        cursor: noteInput.trim() ? "pointer" : "not-allowed",
                                      }}
                                    >
                                      {S.addBtn}
                                    </button>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {kbBrowserOpen && (
          <div
            className="fixed inset-0 z-[100] flex items-center justify-center"
            style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }}
            onClick={() => setKbBrowserOpen(false)}
          >
            <div
              className="rounded-2xl flex flex-col"
              style={{ width: 680, maxHeight: "78vh", background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 24px 64px rgba(0,0,0,0.6)" }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                <div className="flex items-center gap-2">
                  <Database size={14} style={{ color: "#3B82F6" }} />
                  <h2 className="text-[13px] font-semibold" style={{ color: "#f5f5f7" }}>Knowledge Base</h2>
                  <span className="text-[10px]" style={{ color: "#86868B" }}>{kbDocs.length} docs · {Object.keys(folderMap).filter(k => k !== "default").length} folders</span>
                </div>
                <button onClick={() => setKbBrowserOpen(false)} className="p-1 rounded hover:bg-white/5">
                  <XIcon size={14} style={{ color: "#86868B" }} />
                </button>
              </div>
              <div className="px-5 py-3 flex items-center gap-2" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                <input
                  value={kbBrowserSearch}
                  onChange={(e) => setKbBrowserSearch(e.target.value)}
                  placeholder="Search files..."
                  className="flex-1 rounded-lg px-3 py-2 text-[12px] outline-none"
                  style={{ background: "#0f0f10", border: "1px solid rgba(255,255,255,0.08)", color: "#f5f5f7" }}
                />
                {kbBrowserFolder && (
                  <button
                    onClick={() => setKbBrowserFolder(null)}
                    className="px-3 py-2 rounded-lg text-[11px]"
                    style={{ background: "rgba(255,255,255,0.04)", color: "#c7c7cc" }}
                  >
                    ← All folders
                  </button>
                )}
              </div>
              <div className="flex-1 overflow-y-auto scrollbar-hide">
                {!kbBrowserFolder ? (
                  <div className="px-3 py-2">
                    {Object.entries(folderMap)
                      .filter(([name]) => name !== "default")
                      .sort((a, b) => a[0].localeCompare(b[0]))
                      .map(([name, docs]) => {
                        const matchCount = kbBrowserSearch
                          ? docs.filter((d) => d.source.toLowerCase().includes(kbBrowserSearch.toLowerCase())).length
                          : docs.length;
                        if (kbBrowserSearch && matchCount === 0) return null;
                        return (
                          <div key={name} className="group/kbf flex items-center gap-2 px-3 py-2.5 rounded-lg hover:bg-white/5">
                            <FolderOpen size={14} style={{ color: "#fbbf24", flexShrink: 0 }} />
                            {renamingFolder === name ? (
                              <input
                                autoFocus
                                value={renameValue}
                                onChange={(e) => setRenameValue(e.target.value)}
                                onFocus={(e) => e.target.select()}
                                onKeyDown={(e) => {
                                  e.stopPropagation();
                                  if (e.key === "Enter") { const v = renameValue.trim(); setRenamingFolder(null); if (v && v !== name) renameFolder(name, v); }
                                  if (e.key === "Escape") setRenamingFolder(null);
                                }}
                                onBlur={() => setRenamingFolder(null)}
                                onClick={(e) => e.stopPropagation()}
                                className="flex-1 text-[12px] bg-transparent outline-none"
                                style={{ border: "0.5px solid rgba(59,130,246,0.4)", borderRadius: 4, padding: "1px 4px", color: "#f5f5f7" }}
                              />
                            ) : (
                              <button
                                className="flex-1 text-left text-[12px] font-medium truncate"
                                style={{ color: "#f5f5f7" }}
                                onClick={() => setKbBrowserFolder(name)}
                              >
                                {name}
                              </button>
                            )}
                            <span className="text-[10px] shrink-0" style={{ color: "#86868B" }}>{matchCount} {matchCount === 1 ? "file" : "files"}</span>
                            {confirmingDelete === name ? (
                              <div className="flex items-center gap-1 shrink-0">
                                <span className="text-[10px]" style={{ color: "#f87171" }}>Xóa?</span>
                                <button onClick={(e) => { e.stopPropagation(); deleteFolder(name); setConfirmingDelete(null); }} className="px-1.5 py-0.5 rounded text-[10px] font-medium" style={{ background: "rgba(239,68,68,0.15)", color: "#f87171", border: "1px solid rgba(239,68,68,0.3)" }}>Có</button>
                                <button onClick={(e) => { e.stopPropagation(); setConfirmingDelete(null); }} className="px-1.5 py-0.5 rounded text-[10px]" style={{ color: "#86868B", border: "1px solid rgba(255,255,255,0.1)" }}>✕</button>
                              </div>
                            ) : (
                              <div className="flex items-center gap-0.5 shrink-0 opacity-0 group-hover/kbf:opacity-100 transition-opacity">
                                <button onClick={(e) => { e.stopPropagation(); setRenamingFolder(name); setRenameValue(name); }} className="p-1 rounded hover:bg-white/10" title="Rename">
                                  <Pencil size={11} style={{ color: "#86868B" }} />
                                </button>
                                <button onClick={(e) => { e.stopPropagation(); setConfirmingDelete(name); }} className="p-1 rounded hover:bg-white/10" title="Delete folder">
                                  <Trash2 size={11} style={{ color: "#86868B" }} />
                                </button>
                              </div>
                            )}
                          </div>
                        );
                      })}
                  </div>
                ) : (
                  <div className="px-3 py-2">
                    {(folderMap[kbBrowserFolder] || [])
                      .filter((d) => !kbBrowserSearch || d.source.toLowerCase().includes(kbBrowserSearch.toLowerCase()))
                      .map((d) => {
                        const filename = d.source.split("/").pop()?.split("\\").pop() || d.source;
                        const broken = d.has_file === false;
                        return (
                          <div key={d.document_id} className="group/kbdoc flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-white/5">
                            <FileType2 size={12} style={{ color: broken ? "#f59e0b" : "#86868B", flexShrink: 0 }} />
                            <span className="flex-1 text-[12px] truncate" style={{ color: broken ? "#d4b48a" : "#d1d1d6" }} title={filename + (broken ? " (file missing)" : "")}>
                              {filename}{broken && <span className="ml-1.5 text-[9px]" style={{ color: "#f59e0b" }}>· no file</span>}
                            </span>
                            <span className="text-[10px] shrink-0" style={{ color: "#52525b" }}>{d.chunk_count} chunks</span>
                            {kbBrowserConfirmDeleteDoc === d.document_id ? (
                              <div className="flex items-center gap-1 shrink-0">
                                <span className="text-[10px]" style={{ color: "#f87171" }}>Xóa?</span>
                                <button onClick={() => { deleteKbDoc(d.document_id, filename); setKbBrowserConfirmDeleteDoc(null); }} className="px-1.5 py-0.5 rounded text-[10px] font-medium" style={{ background: "rgba(239,68,68,0.15)", color: "#f87171", border: "1px solid rgba(239,68,68,0.3)" }}>Có</button>
                                <button onClick={() => setKbBrowserConfirmDeleteDoc(null)} className="px-1.5 py-0.5 rounded text-[10px]" style={{ color: "#86868B", border: "1px solid rgba(255,255,255,0.1)" }}>✕</button>
                              </div>
                            ) : (
                              <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover/kbdoc:opacity-100 transition-opacity">
                                <select
                                  value=""
                                  onChange={(e) => { if (e.target.value) { moveDocument(d.document_id, e.target.value); setKbBrowserFolder(e.target.value); } }}
                                  className="text-[10px] rounded px-1 py-0.5 outline-none cursor-pointer"
                                  style={{ background: "rgba(255,255,255,0.06)", color: "#c7c7cc", border: "1px solid rgba(255,255,255,0.1)" }}
                                  title="Move to folder"
                                >
                                  <option value="">Move to…</option>
                                  {Object.keys(folderMap).filter((f) => f !== kbBrowserFolder).map((f) => (
                                    <option key={f} value={f}>{f}</option>
                                  ))}
                                </select>
                                {broken ? (
                                  <label className="px-2 py-1 rounded text-[10px] cursor-pointer" style={{ background: "rgba(245,158,11,0.18)", color: "#fcd34d" }}>
                                    Re-upload
                                    <input type="file" className="hidden" onChange={async (e) => {
                                      const f = e.target.files?.[0]; if (!f) return;
                                      const form = new FormData(); form.append("file", f);
                                      const r = await fetch(`/ingest/documents/${d.document_id}/relink`, { method: "POST", body: form });
                                      if (r.ok) { addToast(`Relinked "${filename}"`, "success"); loadKbDocs(); } else { addToast("Re-upload failed", "error"); }
                                      e.target.value = "";
                                    }} />
                                  </label>
                                ) : (
                                  <button onClick={() => setKbViewerDoc(d)} className="px-2 py-1 rounded text-[10px]" style={{ background: "rgba(59,130,246,0.18)", color: "#93c5fd" }}>View</button>
                                )}
                                <button onClick={() => setKbBrowserConfirmDeleteDoc(d.document_id)} className="p-1 rounded hover:bg-white/10" title="Delete document">
                                  <Trash2 size={11} style={{ color: "#86868B" }} />
                                </button>
                              </div>
                            )}
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Memory save particle animation */}
        {memParticles.map((pid) => {
          const avatarRect = avatarBtnRef.current?.getBoundingClientRect();
          const tx = avatarRect ? `${avatarRect.left + avatarRect.width / 2}px` : "calc(100vw - 32px)";
          const ty = avatarRect ? `${avatarRect.top + avatarRect.height / 2}px` : "24px";
          return (
            <div key={pid} className="pointer-events-none" style={{ position: "fixed", inset: 0, zIndex: 9999 }}>
              {[...Array(8)].map((_, i) => {
                const angle = (i / 8) * 360;
                const spread = 28 + Math.random() * 18;
                const ox = Math.cos((angle * Math.PI) / 180) * spread;
                const oy = Math.sin((angle * Math.PI) / 180) * spread;
                return (
                  <div
                    key={i}
                    style={{
                      position: "absolute",
                      left: "50%",
                      bottom: "80px",
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      background: i % 2 === 0 ? "#a78bfa" : "#60a5fa",
                      boxShadow: `0 0 6px 2px ${i % 2 === 0 ? "#7c3aed" : "#3b82f6"}`,
                      animation: `mem-fly-${pid.slice(-4)}-${i} 1.5s cubic-bezier(.4,0,.2,1) forwards`,
                    }}
                  />
                );
              })}
              <style>{`
                ${[...Array(8)].map((_, i) => {
                  const angle = (i / 8) * 360;
                  const spread = 28 + (i * 4);
                  const ox = Math.cos((angle * Math.PI) / 180) * spread;
                  const oy = Math.sin((angle * Math.PI) / 180) * spread;
                  return `
                    @keyframes mem-fly-${pid.slice(-4)}-${i} {
                      0%   { opacity:0; transform:translate(${ox}px, ${oy}px) scale(0.5); }
                      25%  { opacity:1; transform:translate(${ox * 0.5}px, ${oy * 0.5}px) scale(1); }
                      55%  { opacity:1; transform:translate(0,0) scale(1.3); }
                      100% { opacity:0; transform:translate(calc(${tx} - 50vw), calc(${ty} - (100vh - 80px))) scale(0.2); }
                    }
                  `;
                }).join("")}
              `}</style>
            </div>
          );
        })}

        {/* Document viewer modal */}
        {kbViewerDoc && (() => {
          const filename = kbViewerDoc.source.split("/").pop()?.split("\\").pop() || kbViewerDoc.source;
          const ext = filename.split(".").pop()?.toLowerCase() || "";
          const fileUrl = `/ingest/documents/${kbViewerDoc.document_id}/file`;
          const isPdf = ext === "pdf";
          const isImage = ["png", "jpg", "jpeg", "gif", "webp"].includes(ext);
          const downloadFile = async () => {
            try {
              const res = await fetch(fileUrl);
              if (!res.ok) return;
              const blob = await res.blob();
              const a = document.createElement("a");
              a.href = URL.createObjectURL(blob);
              a.download = filename;
              a.click();
              URL.revokeObjectURL(a.href);
            } catch { /* ignore */ }
          };
          return (
            <div
              className="fixed inset-0 z-[200] flex items-center justify-center"
              style={{ background: "rgba(0,0,0,0.75)", backdropFilter: "blur(4px)" }}
              onClick={(e) => { if (e.target === e.currentTarget) setKbViewerDoc(null); }}
            >
              <div
                className="flex flex-col rounded-2xl overflow-hidden"
                style={{
                  width: "min(900px, 92vw)",
                  height: "min(700px, 90vh)",
                  background: "#1C1C1E",
                  border: "1px solid rgba(255,255,255,0.1)",
                  boxShadow: "0 32px 80px rgba(0,0,0,0.6)",
                }}
              >
                {/* Header */}
                <div className="flex items-center gap-3 px-5 py-3.5 shrink-0" style={{ borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                  <FileType2 size={15} style={{ color: "#86868B", flexShrink: 0 }} />
                  <span className="flex-1 text-[13px] font-medium truncate" style={{ color: "#f5f5f7" }} title={filename}>{filename}</span>
                  <button
                    onClick={downloadFile}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-medium transition-all"
                    style={{ background: "rgba(59,130,246,0.15)", color: "#93c5fd", border: "1px solid rgba(59,130,246,0.2)" }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(59,130,246,0.28)"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(59,130,246,0.15)"; }}
                  >
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    Download
                  </button>
                  <button
                    onClick={() => setKbViewerDoc(null)}
                    className="w-7 h-7 flex items-center justify-center rounded-lg transition-colors"
                    style={{ color: "#86868B" }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(255,255,255,0.08)"; e.currentTarget.style.color = "#fff"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#86868B"; }}
                  >
                    <X size={14} />
                  </button>
                </div>

                {/* Body */}
                <div className="flex-1 min-h-0 relative" style={{ background: "#111" }}>
                  {isPdf ? (
                    <iframe
                      src={`${fileUrl}#toolbar=1&navpanes=0&scrollbar=1`}
                      className="w-full h-full border-0"
                      title={filename}
                    />
                  ) : isImage ? (
                    <div className="w-full h-full flex items-center justify-center p-6">
                      <img src={fileUrl} alt={filename} className="max-w-full max-h-full object-contain rounded-lg" />
                    </div>
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center gap-4">
                      <FileType2 size={48} style={{ color: "#3C3C3E" }} />
                      <div className="text-center">
                        <p className="text-[14px] font-medium" style={{ color: "#f5f5f7" }}>{filename}</p>
                        <p className="text-[12px] mt-1" style={{ color: "#86868B" }}>Không thể xem trực tiếp — hãy tải về để mở</p>
                      </div>
                      <button
                        onClick={downloadFile}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-[13px] font-medium transition-all"
                        style={{ background: "rgba(59,130,246,0.2)", color: "#93c5fd", border: "1px solid rgba(59,130,246,0.25)" }}
                        onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(59,130,246,0.35)"; }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = "rgba(59,130,246,0.2)"; }}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        Tải xuống {filename}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })()}

        {/* Messages area */}
        <div
          ref={messagesContainerRef}
          className={`flex-1 ${isEmpty ? "overflow-hidden" : "overflow-y-auto"} scrollbar-hide relative`}
          style={{ display: mode === "translate" ? "none" : undefined }}
          onScroll={(e) => {
            const el = e.currentTarget;
            const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
            const scrolled = distFromBottom > 120;
            userScrolledRef.current = scrolled;
            setShowScrollBtn(scrolled);
          }}
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
                <ChatMessage key={msg.id} message={msg} onSourceClick={handleSourceClick} activeSource={activeSourceId} onFollowUp={(t) => sendMessage(t)} />
              ))}
              {isProcessing && <RAGProcessing step={processingStep} label={processingLabel} sources={readingSources} />}
              <div ref={messagesEndRef} />
            </div>
          )}
          <div className="sticky bottom-6 w-full h-0 overflow-visible pointer-events-none z-10">
            <button
              onClick={() => {
                userScrolledRef.current = false;
                setShowScrollBtn(false);
                messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
              }}
              className="absolute bottom-0 right-6 flex items-center justify-center rounded-full transition-opacity duration-300 pointer-events-auto"
              style={{
                width: "36px",
                height: "36px",
                background: "rgba(28,28,30,0.9)",
                border: "1px solid rgba(255,255,255,0.12)",
                color: "#fff",
                opacity: showScrollBtn ? 1 : 0,
                pointerEvents: showScrollBtn ? "auto" : "none",
              }}
            >
              <ArrowDown size={18} />
            </button>
          </div>
        </div>

        {/* Input area */}
        <div
          className="shrink-0 px-6 pb-4 pt-2"
          style={{
            background: "linear-gradient(to top, #121214 60%, transparent)",
            display: mode === "translate" ? "none" : undefined,
          }}
        >
          <div className="max-w-[850px] mx-auto">
            {browsePreview && (
              <div
                className="flex items-center gap-2 mb-2 px-3 py-1.5 rounded-xl text-xs"
                style={{ background: "rgba(10,102,194,0.12)", border: "1px solid rgba(10,102,194,0.25)", color: "#8BB8E8" }}
              >
                {isBrowsing ? (
                  <span style={{ animation: "spin 1s linear infinite", display: "inline-block" }}>⏳</span>
                ) : (
                  <span>📄</span>
                )}
                <span className="font-medium">{isBrowsing ? "Đang đọc..." : "Đang đọc:"}</span>
                <span style={{ color: "#A8C8F0" }}>{browsePreview.domain}</span>
                <span className="truncate opacity-60" style={{ maxWidth: 260 }}>{browsePreview.url}</span>
              </div>
            )}
            <ContextBar
              scope={chatScope}
              collections={[
                ...Object.entries(folderMap)
                  .filter(([name]) => name !== "default")
                  .map(([name, docs]) => ({ name, doc_count: docs.length }))
                  .sort((a, b) => a.name.localeCompare(b.name)),
                ...pendingFolders
                  .filter((pf) => !folderMap[pf])
                  .map((pf) => ({ name: pf, doc_count: 0 })),
              ]}
              hybridMode={hybridMode}
              totalDocs={kbDocs.length}
              onScopeChange={(s) => { setChatScope(s); fetchSuggestions(s, uiLang); }}
              onHybridChange={(h) => { setHybridMode(h); localStorage.setItem("chatrag_hybrid", String(h)); }}
            />
            <div
              className="flex items-end gap-3 px-4 py-3 rounded-3xl transition-all duration-250"
              style={{
                background: "#1C1C1E",
                ...(webSearchMode
                  ? {
                      border: "1px solid rgba(59,130,246,0.45)",
                      animation: "siri-glow 2.8s ease-in-out infinite",
                    }
                  : {
                      border: inputFocused ? "1px solid #0A66C2" : "1px solid rgba(255,255,255,0.1)",
                      boxShadow: inputFocused
                        ? "0 0 12px rgba(10,102,194,0.2), inset 0 0 12px rgba(10,102,194,0.04)"
                        : "none",
                    }),
              }}
            >
              <input
                ref={chatFileInputRef}
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx"
                multiple
                className="hidden"
                onChange={(e) => {
                  const files = Array.from(e.target.files || []);
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
                  e.target.value = "";
                }}
              />
              <button
                className="shrink-0 mb-0.5 transition-all duration-150"
                title={webSearchMode ? "Tắt tìm web (DuckDuckGo)" : "Bật tìm web (DuckDuckGo)"}
                onClick={() => setWebSearchMode((v) => !v)}
                style={{
                  color: webSearchMode ? "#3B82F6" : "rgba(134,134,139,0.6)",
                  filter: webSearchMode ? "drop-shadow(0 0 6px rgba(59,130,246,0.5))" : "none",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#60a5fa")}
                onMouseLeave={(e) => (e.currentTarget.style.color = webSearchMode ? "#3B82F6" : "rgba(134,134,139,0.6)")}
              >
                <Globe size={16} />
              </button>
              <button
                className="shrink-0 mb-0.5 transition-colors duration-150"
                title="Upload file to knowledge base"
                onClick={() => chatFileInputRef.current?.click()}
                style={{ color: "rgba(134,134,139,0.6)" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#60a5fa")}
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
                placeholder={webSearchMode ? S.webPlaceholder : S.chatPlaceholder}
                className="flex-1 bg-transparent resize-none outline-none text-sm leading-relaxed"
                style={{
                  color: "#F5F5F7",
                  caretColor: "#3B82F6",
                  maxHeight: "160px",
                  overflowY: "auto",
                  fontFamily: "inherit",
                }}
              />

              {(isProcessing || isStreaming) ? (
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
          onOpenDoc={(title) => {
            // Scroll KB section into view and highlight the doc
            setTimeout(() => kbSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50);
            // Expand all folders to find the doc
            setExpandedFolders(new Set(collections.map((c) => c.name).concat(["default"])));
          }}
        />
      )}

      {deletingChatId && (
        <div
          className="fixed inset-0 z-[200] flex items-center justify-center"
          style={{ background: "rgba(0,0,0,0.65)", backdropFilter: "blur(8px)" }}
          onClick={() => setDeletingChatId(null)}
        >
          <div
            className="rounded-2xl p-5 flex flex-col gap-4"
            style={{ width: 320, background: "#1c1c1e", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 24px 64px rgba(0,0,0,0.7)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0" style={{ background: "rgba(239,68,68,0.15)" }}>
                <Trash2 size={16} style={{ color: "#f87171" }} />
              </div>
              <div>
                <p className="text-[13px] font-semibold" style={{ color: "#f5f5f7" }}>{S.deleteConfirmTitle}</p>
                <p className="text-[11px] mt-1 leading-relaxed" style={{ color: "#86868B" }}>{S.deleteConfirmDesc}</p>
              </div>
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setDeletingChatId(null)}
                className="px-4 py-2 rounded-xl text-[12px] font-medium transition-all"
                style={{ background: "rgba(255,255,255,0.06)", color: "#c7c7cc" }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.1)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.06)")}
              >
                {S.cancelBtn}
              </button>
              <button
                onClick={() => { deleteChat(deletingChatId); setDeletingChatId(null); }}
                className="px-4 py-2 rounded-xl text-[12px] font-medium transition-all"
                style={{ background: "#ef4444", color: "#fff" }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "#dc2626")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "#ef4444")}
              >
                {S.deleteBtn}
              </button>
            </div>
          </div>
        </div>
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
        .msg-animate { animation: msg-in 0.15s ease forwards; }
        textarea::placeholder { color: rgba(134,134,139,0.45); }
      `}</style>
    </div>
  );
}
