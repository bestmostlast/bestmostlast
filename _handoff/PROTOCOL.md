# Calynix Orchestration / Handoff Protocol

Calynix HQ (the `~/Calynix/` window) is the orchestrator. Brand & project
scopes (web, FIBBY, Reveal, BestMostLast) do the actual work in their own
VSCode window + memory. The filesystem is the message bus between them.

## Roles
- **HQ** = company-level admin/finance/strategy + the single point the user
  talks to first. HQ dispatches tasks and rolls up reports. HQ never edits
  brand/website code directly.
- **Scope window** = does the work for its brand/site, keeps the deep memory.

## Channels (per scope, under `<scope>/_handoff/`)
- `inbox/`   — tasks HQ dispatched TO this scope (`task-<ts>.md`).
- `outbox/`  — reports this scope writes BACK to HQ (`<taskid>.report.md`).
- `archive/` — processed items (moved here after roll-up).

## If you are a SCOPE window's Claude
1. On start, check `_handoff/inbox/` for `status: open` tasks.
2. Do the work in this window. Keep brand-specific detail in THIS scope's
   memory — never push code/game detail up to HQ memory.
3. When done or pausing, write `_handoff/outbox/<taskid>.report.md`:
   ```
   ---
   id: <taskid>
   scope: <scope>
   status: done | partial | blocked
   reported: <date>
   ---
   **Input:** what HQ/the user asked.
   **Output:** what changed / produced.
   **Open items / blockers:** (if any)
   ```
4. The user (not you) decides when to "sync" — that's an HQ action.

## If you are HQ
- Dispatch with `_launch/dispatch.sh <scope> "<title>" ["<detail>"]`
  (writes the inbox task AND opens that scope's window).
- On the user's **"sync"** command: read every `<scope>/_handoff/outbox/*`,
  update HQ memory + `calynix-overview.html` Cross-scope section, then move
  processed reports + their inbox tasks to `archive/`. Never auto-merge brand
  detail into HQ memory — summaries only.
