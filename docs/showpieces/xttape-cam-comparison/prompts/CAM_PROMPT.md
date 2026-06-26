You are creating the initial project brain for a new app.

Use the request below. Use the capabilities and local context normally available in this CAM_Codx cockpit if they materially improve the result, but do not expose secrets and do not write app code.

Create exactly these files in the current directory:

- AGENTS.md
- GOAL.md
- DECISIONS.md
- PROGRESS.md

Also create CAM_MEMORY_APPLIED.md. In that file, briefly list any local CAM/Codex/CAM memory, methodology, or prior project context that materially changed the output. If none was used, say so plainly.

After writing the files, provide a short summary of the major architecture stance, any blockers, and what CAM-specific context changed.

Request:

```markdown
Build a new app called XTtape.

XTtape is a live AI-based news ticker tape app for a professional user who wants ambient awareness without doomscrolling. It should combine live news/source feeds, X/social signals, AI summarization, user learning, source-backed explanations, and durable storage of useful preference/signal data.

Preferred stack:

- FastAPI backend
- Node/TypeScript services where useful
- Prisma for structured persistence
- MCP boundary for external source/tool access
- X/xAI integration where credentials are available

Create only these project-brain files before implementation:

- AGENTS.md
- GOAL.md
- DECISIONS.md
- PROGRESS.md

Do not write app code yet. Do not use XTtapeNotes.md. Do not expose secrets. Record assumptions, risks, and blockers clearly. The result should be strong enough that we can decide whether to proceed to the actual app build.
```
