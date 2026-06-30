# chatRAG — Frontend

React 18 + TypeScript + Tailwind chat UI for Ciel. Dev mode runs on
`localhost:5173` and proxies API calls to the backend on `:8000`. Production
build is served as static files by FastAPI at `localhost:8000`.

---

## Stack

- React 18 + TypeScript
- Vite (build tool, dev proxy)
- Tailwind 4 + Radix UI primitives + lucide-react icons
- MUI (used for a few rich components)
- No router — single-page `App.tsx` with view state

---

## Develop

```bash
cd frontend
pnpm install
pnpm dev          # http://localhost:5173, hot reload, API proxied to :8000
```

Vite proxy (in `vite.config.ts`) forwards `/chat` and `/ingest` to
`http://localhost:8000`, so the backend must be running for chat / upload to work.

---

## Build for production

```bash
pnpm build        # output -> frontend/dist/
```

After building, copy the output into the backend static dir so FastAPI serves it:

```bash
# from frontend/
rm -rf ../backend/app/static/*
cp -r dist/* ../backend/app/static/
```

Then visit `http://localhost:8000` — the backend serves `index.html` with
no-cache so the new hash-named bundle (`assets/index-XXXX.js`) is picked up
immediately.

---

## Key features

| Feature | Notes |
|---|---|
| SSE streaming chat | Reads `text/event-stream` from `POST /chat`, renders tokens as they arrive |
| Multi-turn memory | Sends last 6 messages as `history` so Ciel understands follow-ups |
| Folder scope | ContextBar above the input limits retrieval to selected folders |
| Hybrid mode | Toggle to blend KB results with general LLM knowledge |
| Model switcher | Ollama (local) vs Groq cloud, with API key field |
| Stop button | Aborts in-flight fetch and saves the partial response |
| Sources panel | Click a citation chip to see the chunk and open the source file |
| KB sidebar | Browse / move / rename / delete docs and folders inline |
| Background streaming | Stays alive when user navigates to a different chat |
| File viewer | PDFs and images render inline in the browser; office docs download |

---

## File layout

```
frontend/
  src/
    main.tsx                React root, mounts App
    app/
      App.tsx               single-file app (chat, sidebar, settings, sync)
      components/           reusable UI bits (Source chips, ContextBar, etc.)
    imports/                Figma-imported assets
    styles/                 Tailwind entry + global CSS
  index.html
  vite.config.ts            proxy /chat /ingest to :8000
  package.json
```

`App.tsx` is intentionally a single large file — easier to ship from
Figma exports. Components get extracted as the codebase grows.

---

## API contract

`POST /chat` body (sent by `sendMessage` in `App.tsx`):

```ts
{
  question: string,
  collections: string[] | null,    // null = search all folders
  hybrid: boolean,
  model: string,                   // e.g. "gemma3:12b" or "llama-3.3-70b-versatile"
  api_key?: string,                // Groq key, only when model is a Groq one
  history: { role: "user"|"assistant", content: string }[],  // last 6 messages
}
```

Response: `text/event-stream` with events:

| event type | payload |
|---|---|
| `step` | `{ step: "embedding" \| "searching" \| "filtering" \| "generating" }` |
| `sources` | `{ sources: [...] }` — list of cited chunks (sent once before tokens) |
| `token` | `{ token: string }` — incremental LLM text |
| `done` | `{ sources?, answer? }` — final marker |
