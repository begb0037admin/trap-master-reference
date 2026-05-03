# CLAUDE.md — AI Mix Masters

Project context for future Claude (or Cowork) sessions. Read this first when picking the project back up.

> **Naming history:** the project was renamed in May 2026 from *Master Mix Workbench* (and earlier *Trap Master Reference*) to **AI Mix Masters**. The GitHub repo slug `trap-master-reference` and its live URL stay unchanged for now — the rename is user-facing only.

## What this is

**AI Mix Masters** — a single-page, browser-only mixing/mastering assistant for Kevin's iLok + Waves + Native Access + Plugin Alliance library. Genre-aware plugin picks, per-bus chain builder, platform loudness targets, troubleshooter, snapshot journal, and a voice/text co-pilot powered by the OpenAI Realtime API plus (optionally) Claude with web search for niche-knowledge lookups.

> **Voice migration in flight:** the project is being migrated from OpenAI Realtime to ElevenLabs Conversational AI (Claude Sonnet 4.6 brain, Hope voice, Expressive Mode on). Work happens on the `voice-elevenlabs` branch. The OpenAI path on `main` stays as the production fallback until the new path is solid.

## ⚠️ HANDOVER POINT — read this first if you're picking up the voice-elevenlabs branch

**Session of 2026-05-XX (post-Batch-5 polish):** UI re-shape on the Voice Chat tab + Knowledge tab + Settings tab. Five user-facing changes shipped together, all on `voice-elevenlabs`:

1. **Profile editor moved to the Knowledge tab.** The `🧠 Profile` block (textarea + Save / Clear / status / byte-counter) was cut from the Voice Chat panel and pasted at the bottom of `<div class="panel" id="knowledge">` under a new `Hope's memory` section-head. Every DOM ID survived the move (`profileText` / `profileSave` / `profileClear` / `profileStatus` / `profileLen`) so `renderProfileEditor` / `setProfileStatus` / `maybeExtractProfile` / the init-time event listeners all keep finding their targets unchanged.

2. **Compose box shrunk + Quick Prompts retired.** The AI Chat compose textarea dropped from `rows="9"` (380–640px tall) to `rows="3"` (96–280px tall) by adding a `.aichat-compose-compact` class with override rules. The `.aichat-quick-prompts` column was wrapped in `<div hidden data-dormant="aichat-quickprompts">` per the project's dormant-wrap convention — buttons stay in the DOM so the existing `document.querySelectorAll('.aichat-quick-prompt').forEach(...)` binding in `aichatInit` still runs (returns an empty NodeList, no null-guard needed). To revive: drop the `hidden` attribute on the wrapper.

3. **Session Snapshots panel grown.** `.journal-list` now has `min-height:320px;max-height:560px;overflow-y:auto;padding:6px;background:#0b1220;border:1px solid #1f2937;border-radius:8px`. The panel feels substantial even with few entries; long lists scroll inside the box rather than pushing the page down.

4. **Favourite snapshot pills flanking START CALL.** The space around the START CALL button is now occupied by up to 8 pill buttons (4 each side, vertical stack) sourced from `STATE.journal` entries with `favourite:true`. New constants: `FAV_PILLS_MAX = 8`, `FAV_PILLS_PER_SIDE = 4`. New functions inserted right after `restoreFromJournal` in the SESSION JOURNAL block:
    - `getFavouriteEntries()` — filter `STATE.journal` by `favourite:true`, sort by `ts` descending, slice top 8.
    - `renderFavouritePills()` — fills `#rtPillsLeft` (slice 0..4) and `#rtPillsRight` (slice 4..8). Empty slots render as a dashed-border placeholder pill `+ snapshot a chat`.
    - `recallFavourite(id)` — context-aware. If `EL.active` and the conversation has `sendContextualUpdate`, fires `EL.conversation.sendContextualUpdate("Recalling: <subject>\n\n<text>")` directly into the live call. Otherwise, drops the same string into `#aiChatInput` (preserving any in-progress draft via `\n\n---\n\n` separator), switches to the Voice Chat tab, focuses the textarea, and moves the cursor to the end.
    - `toggleFavourite(id)` — flips `entry.favourite`. When favouriting and the cap is full, FIFO-drops the oldest favourite (sets its `favourite:false`; the entry stays in `STATE.journal`). Calls `saveState` + `renderJournal` + `renderFavouritePills`.
    - **Auto-favourite on TL;DR → Snapshot.** `aichatToJournal` (around line 7110) was extended to set `entry.favourite = true` on creation, with FIFO-drop enforcement before unshift. So every chat summarised via the existing 📜 button becomes a pill automatically.
    - **Star toggle on each Session Snapshots row.** `renderJournal` got a `.journal-star` button (☆ / ★) on each entry's `actions` block. CSS: `.journal-star.on{color:#fbbf24}`, transparent background, no border.
    - **Pill HTML.** `<button class="rt-pill" data-id="..." onclick="recallFavourite(...)"><span class="rt-pill-label">{subject truncated to 30 chars}</span><span class="rt-pill-x" onclick="event.stopPropagation();toggleFavourite(...)">×</span></button>`. The × is hidden until pill hover.
    - **Layout.** New `.rt-call-flank` grid `1fr auto 1fr`, with `.rt-pills-col` flex-columns either side. Mobile breakpoint at 880px collapses to single column (pills wrap horizontally). The original `.rt-main-call` block is now nested inside `.rt-main-wrap` between the two pill columns — no structural changes inside the call button, just the wrapper.
    - **Init.** `renderFavouritePills()` is called right after `renderJournal()` in the init block (around line 9630) inside a `try/catch` so a render failure doesn't break the rest of init. `STATE.journal` is already loaded by `loadState()` higher up.
    - **Backwards compat.** Existing `STATE.journal` entries without a `favourite` field are treated as `favourite:false` (the strict `=== true` filter handles undefined cleanly). No migration needed.

5. **Settings Costs cards full-width + bigger fonts.** `.settings-cost-row` collapsed from `grid-template-columns:1fr 1fr` to `1fr` so each cost card spans the full Settings panel width. New CSS overrides scoped to `.settings-cost-row .rt-cost-card`: padding bumped to `18px 22px`, header to 14px, row labels to 14px, values to 18px (was 11px). Action buttons bumped from 8.5px to 12px font with `8px 14px` padding. The 720px media query is gone — single column already works on narrow viewports.

6. **Snapshot button rename + workbench-snapshot dormant-wrap.** Two related cleanups after Kev pointed out he rarely uses the workbench-snapshot button and forgets what it does:
    - **Green button renamed.** `📜 TL;DR → Snapshot` (`#aiChatToJournal`) → `📋 Snapshot → Claude chat`. Class flipped from `btn green sm` to `btn purple sm` so it visually pairs with the Import plugins button (also `btn purple sm`) — both are Claude-powered actions on the conversation toolbar. Title attribute updated to mention the auto-favourite/pill behaviour. ID stays `aiChatToJournal`, handler stays unchanged.
    - **Purple workbench-snapshot button dormant-wrapped.** The Chain Builder's `📋 Snapshot → Claude` button (`#snapshotBtn`) was wrapped in `<span hidden data-dormant="workbench-snapshot">` per the project's dormant-wrap convention. The element + click handler stay in code (`document.getElementById('snapshotBtn').onclick = ...`) so the back-pocket revival path needs no null guards. Internal label changed to `📋 Snapshot session → Claude` so if revived it disambiguates from the chat-summary button. To revive: drop the `hidden` attribute on the wrapping `<span>`. (The dormant-key name `workbench-snapshot` was kept for the data attribute — describes what the button captures internally; the user-facing label is the friendlier "session".)
    - **Tip-box copy on Chain Builder updated.** The "Snapshot → Claude when dialed in" line was rewritten to point at the new green-now-purple button on the Voice Chat tab, with a note that saved entries auto-favourite as pills.
    - **journalEmpty placeholder updated** (HTML default + `renderJournal` fallback) to reference the new button name and explain the auto-favourite behaviour. The `+ snapshot a chat` empty-pill placeholder's tooltip was also updated.

**Files touched:** `index.html` only. **No new localStorage keys** — `favourite` is a per-entry flag inside the existing `trapMasterState_v1` blob via `STATE.journal[].favourite`. **No SDK / API changes.**

**New dormant-wrap key:** `data-dormant="workbench-snapshot"` on the Chain Builder's `#snapshotBtn`. The full set of dormant tags now includes `openai-realtime`, `aichat-readaloud`, `aichat-dictation`, `aichat-quickprompts`, and `workbench-snapshot` — same `hidden` HTML attribute pattern, same revival flow (drop the `hidden` attr).

7. **Pill capacity bumped to 24 (12 per side) + spacing.** `FAV_PILLS_MAX` 8 → 24 and `FAV_PILLS_PER_SIDE` 4 → 12. CSS changes on `.rt-call-flank` + `.rt-pills-col`: gap 24px → 56px (more breathing room between pill columns and START CALL), pill columns now `align-items:center` so they sit horizontally centred between the call button and the panel edge (was `flex-end` left / `flex-start` right which hugged the button). Pill padding tightened from `8px 14px` to `6px 12px` and font from 12px to 11px so 12 stacked don't tower vertically. `max-width` 240px → 220px, `min-width` 160px → 150px, gap-between-pills 8px → 6px. Mobile breakpoint moved from 880px to 1000px so the pill columns wrap into a single row sooner on narrower viewports.

8. **Time-aware greeting wired into the EL flow.** The `pickGreeting` / `timeOfDay` / `GREETING_LINES` pool (90 combos: 3 moods × 3 time slots × 10 lines each, line 4311) was previously OpenAI-only — now also feeds Hope. Two delivery channels in `elStart`:
    - **`dynamicVariables` on `Conversation.startSession`.** New keys `greeting` and `time_of_day` are passed to the SDK. The agent's dashboard first message can reference these via `{{greeting}}` and `{{time_of_day}}` for a personalised opening line. **DASHBOARD TO-DO** (Kev needs to do this, the SDK side is wired): edit the agent's first message in the ElevenLabs dashboard from `Hey Kev, it's Hope. What are we working on?` to `Hey Kev, it's Hope. {{greeting}}` (or whatever phrasing you prefer using the variables). Click **Publish** at the top-right of the agent page or the change won't propagate. Without this dashboard tweak the dynamic variables flow through harmlessly but Hope keeps using the static first message — channel #2 below still mood-shifts subsequent turns.
    - **Appended to `pendingContext`.** A `GREETING TONE FOR THIS SESSION` block is added to the contextual update bundle: explicit current time-of-day (`morning`/`afternoon`/`evening`), the picked greeting line, and an instruction asking Hope to lead with it verbatim if she has flexibility, otherwise match its mood across the first few replies. So even without the dashboard tweak Hope's tone shifts session-to-session rather than feeling like the same boilerplate every call.
    - **EL state.** New `EL.sessionGreeting` and `EL.sessionTimeOfDay` fields, populated in `elStart` and reset in `elCleanup` so each call re-picks a fresh line from the pool.

**New gotcha to add to the existing Non-obvious gotchas section:**

- **Time-aware greeting needs a dashboard first-message edit.** The SDK now passes `dynamicVariables: { greeting, time_of_day }` to `Conversation.startSession`. For Hope's first spoken line to actually use the greeting, the agent's first message in the dashboard must reference `{{greeting}}` (and/or `{{time_of_day}}`). Without the edit the variables flow through unused; the contextual-update channel (`pendingContext` block) is the safety net that mood-shifts her subsequent turns.

9. **Voice Chat tab redesign — drop the giant START CALL button, full-width pill grid.** The big `#rtCallBtn` was dominating the panel and the side-flank layout left the pills cramped at 12-per-side. New shape:
    - **`.rt-status-strip` at top** — thin horizontal strip with the status dot, status label (`rtStatus`), timer (`rtTimer`), session-cost field (`rtCost`), live cost chip (`elLiveCostChip`), and a right-aligned hint "Tap the floating mic to start a call with Hope · Spacebar to toggle". Replaces the `.rt-status-row` that lived under the old big button. All the IDs the existing handlers use (`rtDot`, `rtStatus`, `rtTimer`, `rtCost`, `elLiveCostChip`) survived the move so `setVoiceState` / `rtTickTimer` / `elRenderLiveCost` etc. find their targets unchanged.
    - **`.rt-pills-grid` full-width** — single grid `repeat(auto-fit, minmax(220px, 1fr))` with 8px gap; pills flow naturally across the available width. Replaces the 3-col `.rt-call-flank` (left pills col | call button | right pills col) layout entirely. `renderFavouritePills()` was rewritten to render into a single `#rtPillsGrid` instead of `#rtPillsLeft` / `#rtPillsRight`.
    - **Pill restyle to match Troubleshooter symptom buttons.** New `.rt-pill` rules mirror `.symptom` from the Diagnose tab — `padding:11px 13px; font-size:13px; border-radius:8px; line-height:1.35`. Populated pills get `.rt-pill.populated` class with `background:#581c87; border-color:#a78bfa; color:#f3e8ff; font-weight:600` (same purple as `.symptom.active`, echoing the Snapshot → Claude chat button colour family). Empty placeholder pills stay dashed-border neutral. Long subjects clamp to 2 lines via `-webkit-line-clamp:2`.
    - **Dormant-wrappers** — `<span hidden data-dormant="big-call-button">` wraps the original `#rtCallBtn` + `#rtCallLabel` so `updateCallButtonState` / `setVoiceState` / `elStart` label updates still find their targets without null guards. `<span hidden data-dormant="rt-pills-flank">` wraps the legacy `#rtPillsLeft` / `#rtPillsRight` columns so revival of the flank layout is mechanical (drop the `hidden` attribute, swap `renderFavouritePills` back to filling left/right). The full set of dormant tags now: `openai-realtime`, `aichat-readaloud`, `aichat-dictation`, `aichat-quickprompts`, `workbench-snapshot`, `big-call-button`, `rt-pills-flank`.
    - **Floating mic is the universal call trigger.** It already worked across tabs; this redesign just commits to it as the single affordance.

10. **Bug fix — float-mic drag-to-reposition no longer starts a call.** The old `mousedown` handler called `micStartFromFloat()` immediately, which kicked off `elStart()` before `dragMove`'s drag-distance threshold could decide whether the press was a tap or a drag. The threshold logic was already cancelling RT-PTT and dictation when crossed, but EL's call had no equivalent cancel path. Fix: removed the `micStartFromFloat()` call from `mousedown` (line ~9018) and from `touchstart` (line ~9090); added it to `mouseup` and `touchend` after the existing `wasDrag` short-circuit. Net behaviour: tap-without-drag still starts a call cleanly; drag-to-move never does. Same logic applies to RT PTT (dormant) — only `RT.active` triggers `rtPttDown` on mousedown now.

11. **Hope's memory window enlarged.** In the Knowledge tab, the profile-panel textarea bumped from `rows="6" / min-height:110px` to `rows="14" / min-height:280px / max-height:560px`. Padding bumped to `14px 16px` (was `10px 12px`), line-height to `1.6` (was `1.55`). 2KB cap unchanged. The Knowledge tab has the vertical space — no reason for the dossier to cramp.

12. **Settings Costs rework — 4-up metric tile grid per provider.** The previous full-width-card layout left labels left and values right with massive horizontal dead space. New shape: each `.rt-cost-card` wraps its 4 `.row` elements (Session / Balance / Spent / Left) in a new `.rt-cost-metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:10px }`. Each `.row` becomes a self-contained tile — label uppercase 11px above (with letter-spacing), value 22px monospace below, dark-blue tile background, 8px radius. Action buttons (Top up / Update balance) sit below the tile row. Mobile breakpoint at 720px collapses the 4-up to 2-up. All DOM IDs (`elSession`, `elBalance`, `anSession` etc.) preserved on the markup change so `renderCostPanels` / `updateBalance` / `elRenderLiveCost` / `rtRenderCost` keep finding their targets.

**Verification.** `node --check` passes on the inline JS block (447 KB, the data-only `application/json` block 0 is unrelated). No duplicate IDs (the apparent `voice` / `knowledge` doubles are inside HTML comments documenting the moves, not actual elements). Markers grep clean: `rt-call-flank`, `rtPillsLeft/Right`, `Hope's memory`, `aichat-compose-compact`, `data-dormant="aichat-quickprompts"`, `renderFavouritePills`, `recallFavourite`, `toggleFavourite`, `FAV_PILLS_MAX` all present. localhost:8765 returns 200, 583 KB. Real browser smoke test still pending — Kev to validate visually.

**Where to resume.** Real-session smoke test on localhost:8000 — confirm the pill layout looks right on a desktop viewport, the star toggle on each Snapshots row works, clicking a pill while idle drops the recall draft into compose and switches to Voice Chat, clicking a pill mid-call sends a `sendContextualUpdate` to Hope (verify in DevTools that the EL conversation receives it). The originally-flagged Open follow-ups (slow Hope voice, `/v1/convai/conversations/{id}` field-name verification, live history bars tile) are untouched.

**Session of 2026-05-06:** Batch 5 shipped — Settings tab split. New rightmost `data-tab="settings"` button (line-art gear icon) + new `<div class="panel" id="settings">` panel with five labelled sections: API keys, Models, Costs, Session safety, Notes. The following blocks moved out of the Voice Chat panel into Settings, with every DOM ID preserved so existing handlers don't need rewiring:

- **API keys section:** Anthropic key (`#rtAntKey` + show/save/clear), ElevenLabs API key (`#elKey` + show/save/clear), ElevenLabs Agent ID (`#elAgentId` + save/clear), and the dormant OpenAI key (`#rtApiKey`, kept under `<div hidden data-dormant="openai-realtime">`).
- **Models section:** Research brain (`#rtClaudeModel`) plus the dormant OpenAI selectors (`#rtModel`, `#rtVoice`, `#voiceProvider` — all `hidden data-dormant="openai-realtime"`).
- **Costs section:** Both cost cards (`#costCardEleven` + `#costCardAnthropic`) wrapped in a new `.settings-cost-row` 2-col grid (no START CALL button between them like the Voice Chat layout had — that grid was 1fr / auto / 1fr).
- **Session safety section:** the `.rt-tools-panel` (cost/min, soft cap, breakdown, auto-pause, usage links) — same card markup, same IDs (`cpmValue`, `budgetCap`, `brEl`, `brResearch`, `autoPause`, `elUsageLink`, `anUsageLink`).
- **Notes section:** the `#browserWarn` banner + the How-it-works tip-box.

What stays on the Voice Chat (Conversation) panel: START CALL button + `.rt-status-row` (timer, status pill, rt-cost) + new live cost chip, profile editor, the merged Conversation block (toolbar / transcript / compose / foot), Live Voice Transcript section + clear button, Session Snapshots panel, `<audio id="rtAudio">`. The old wrapping `<div class="rt-call-row">` (which was a 3-child `1fr auto 1fr` grid sandwiching START CALL between the two cost cards) was removed entirely; the inner rt-main with the call button + status row now sits directly inside the panel as a flex-column centered.

New live cost chip on the Conversation tab: `<span class="rt-live-cost-chip" id="elLiveCostChip" hidden>` next to the rt-status-row. `elRenderLiveCost` writes `Live · {0:42} · ${0.06}` to it once per second while EL.active; chip toggles `.amber` over $1, `.red` over $2; `elCleanup` hides it on call end. CSS: `.rt-live-cost-chip` styled as a small monospace pill matching the status row.

CSS additions at `.section-head` neighbour: `.settings-section{margin:18px 0 28px}`, `.settings-section h3{...}`, `.settings-cost-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}` with a `@media (max-width:720px)` collapse to single-column.

**All five batches shipped. OpenAI removal is complete. Voice migration done.** No active scope. Possible polish items in "Open follow-ups" below — none committed.

**Session of 2026-05-05:** Batch 4 shipped — cost-panel rewire. The OpenAI cost card on the Voice Chat tab has been repurposed into an **ElevenLabs cost card** (`#costCardEleven`, `.rt-cost-card.elevenlabs` with indigo `#818cf8` accent). All `oa*` element IDs renamed to `el*` (`elSession`, `elBalance`, `elSpent`, `elLeft`, `elTopup`, `elUpdate`, `elUsageLink`). Three EL spend feeders wired:

1. **Live in-call estimate.** New `elRenderLiveCost()` ticks once per second from the EL session timer (`elStart` onConnect now wraps `rtTickTimer + elRenderLiveCost` in the same setInterval). Estimate = elapsed minutes × `EL_CONVAI_RATE_PER_MIN` ($0.088/min on Creator plan; constant tweakable when ElevenLabs changes plan structure). Writes to `#elSession` + `#brEl` Session-breakdown tile + cost-per-minute tile + budget-cap watcher (`EL.budgetWarned` flag, reset on cap dropdown change).
2. **Post-disconnect reconcile.** New `elFetchConversationCost(conversationId)` hits `GET /v1/convai/conversations/{conversationId}` after `onDisconnect`. Tries several plausible paths in the response (`metadata.charging.minutes_used`, `metadata.charging.duration_minutes`, `metadata.duration_minutes`, `charging.minutes_used`, `minutes_used`, `duration_seconds/60`, `metadata.duration_seconds/60`) — picks the first that's a valid finite positive number. Diffs against `EL.lastLiveCostEstimate`. If exact > estimate, tops up via `addSpend('el', delta)`. If under, logs only (no refund / double-credit). Hooked AFTER `maybeExtractProfile()` — captures `EL.conversationId` to a local before `elCleanup` wipes it, then fires fire-and-forget so neither blocks the other.
3. **Subscription headroom button.** New `updateElBalance()` hits `GET /v1/user/subscription`, maps known plan tiers (`free` $0 / `starter` $5 / `creator` $22 / `pro` $99 / `scale` $330 / `business` $1320) to monthly $ budgets. Falls back to manual prompt if no key saved or unrecognised tier. `updateBalance('el')` routes here. Top-up button opens `https://elevenlabs.io/app/subscription`. Usage dashboard button opens `https://elevenlabs.io/app/usage`.

The Session breakdown tile collapsed: 4 OpenAI-flavoured rows (audioIn/audioOut/text/research) → 2 active rows (`brEl` voice + `brResearch` Anthropic). The audioIn/audioOut/text rows are dormant-wrapped (`<div class="br-line" hidden data-dormant="openai-realtime">`) so any back-pocket revival of `rtRenderCost` doesn't crash. `SESSION_BREAKDOWN` gained an `el` field. `SPEND_KEY_OAI` stays defined as legacy archive — `addSpend('oai', …)` still routes to it for back-pocket revival, but `renderCostPanels` no longer reads it; `renderHistoryBars` reads EL + ANT (the tile is null right now anyway, just future-proofed). EL state object gained `lastLiveCostEstimate` and `budgetWarned` fields, both reset by `elCleanup`.

`rtRenderCost`'s line writing to `oaSession` is now guarded with a null check — it's a dormant code path (OpenAI Realtime is unwired) but if revived it won't throw because the DOM was renamed.

**All four batches shipped. OpenAI removal is complete.** Batch 5 (Settings tab split) shipped in the next session — see top entry above.

**Session of 2026-05-04 (later):** Batch 3b shipped — the tab merge. AI Chat tab nav button + `<div class="panel" id="aichat">` panel both deleted; the entire AI Chat compose UI (rich transcript, textarea, screenshot attach + preview + file input, Send, quick prompts, Clear input, status pill, foot row, model selector, Web search toggle, TL;DR, Import plugins, Clear chat) relocated into `<div class="panel" id="voice">` as the merged Conversation surface. The dormant TTS dropdowns (`#aiChatTtsVoice`, `#aiChatTtsModel`) + `<audio id="aiChatTtsAudio">` and the dictation `voice-mode-toggle[data-scope="aichat"]` live in two `<div hidden data-dormant="...">` wrappers at the bottom of the panel — DOM elements stay so the dormant `aichatSpeak` / TTS state machine / DICT helpers don't need null guards. Read-aloud button retired from `aichatRender` (Hope speaks every voice reply via the EL WebSocket). EL `onMessage` now writes to `AICHAT.history` only (the `rtAppendTurnText` call into `#rtTranscript` was retired). `snapshotTranscript()` rewritten to read voice turns from `AICHAT.history` filtered by `source:'voice'` so end-of-call profile extraction keeps working — the rt-transcript DOM walk stays as a back-pocket fallback. Diagnose-tab "create troubleshooting tile" handoff now lands on the merged Voice Chat tab. Tool-handling boundary is documented near `aichatSend`: voice = EL `clientTools`, typed = Anthropic `tool_use`. **Next: Batch 4 — cost panel rewire (revised scope: TTS-per-character bucket dropped since Read-aloud retired; only conv-AI minutes + Scribe dictation feed `addSpend('el', ...)`).** See below.

**Session of 2026-05-04 (earlier):** Batch 3 redesigned — original Read-aloud-TTS migration **DROPPED**, replaced with a tab-merge plan. AI Chat tab will fold into Voice Chat as a single always-on Conversation surface (rich-text transcript + screenshot attach + quick prompts + TL;DR + Import plugins + small text fallback input). Floating button rebrands from PTT to **tap-to-toggle Start Call**, spacebar tap-toggles too, focus modes (chain/library/eq/knowledge addenda) retire, dictation (Scribe) goes dormant. Batch 3 is now split into **3a (labelling sweep — shipped earlier this session)** and **3b (the actual merge — shipped later this session, see entry above)**. Batch 3a: floating-button title + setVoiceState dynamic titles + applyFloatMicVisibility tooltip all reworded for always-on tap-to-toggle ("Tap to start a call with Hope · Spacebar"). The mechanics of tap-to-toggle were already correct in the existing EL handlers from prior session — Batch 3a was purely a labelling cleanup.

**Session of 2026-05-03:** Batches 1 + 2 shipped in one session. Batch 1: UI sweep on Voice Chat tab — provider dropdown, OpenAI key field, voice-model + OpenAI-voice dropdowns wrapped in `<div hidden data-dormant="openai-realtime">` so DOM elements stay and the dormant `rtLoadKey` / `rtSavePrefs` / `getVoiceProvider` etc. don't need null guards. `rtCallBtn` click, `micStartFromFloat`, and the spacebar `keydown` handler are now EL-only (the dormant `rtStart` / `rtEnd` / `RT` state / `MIC_SVG_FLOAT` / focus-mode plumbing all stay in the file as the back pocket). New helper `updateCallButtonState()` gates START CALL on EL key + Agent ID. Tip-box + chain-toolbar hint copy rewritten for Hope. Batch 2: AI Chat dictation migrated from OpenAI Whisper to ElevenLabs Scribe v2 — endpoint `api.elevenlabs.io/v1/speech-to-text`, `model_id=scribe_v2`, auth `xi-api-key`, vocab biasing via `keyterms` array (replaces Whisper's `prompt`). Web Speech remains the no-key fallback. Cost rolls into a new `addSpend('el', cost)` bucket (`SPEND_KEY_EL = 'aiMixMastersSpendEleven_v1'`) — the cost-panel UI for it is Batch 4. **Next: Batch 3 (AI Chat Read aloud — OpenAI TTS → ElevenLabs TTS).** See below.

**Last working state:** ElevenLabs Conversational AI is fully working end-to-end and the Voice Chat / Settings split has shipped. All 25 client tools registered + wired, profile system (cross-conversation memory) landed, dual-provider overlap fixed, AI Chat tab merged into Voice Chat as a unified Conversation surface (Batch 3b), cost panel rewired for ElevenLabs spend (Batch 4), and now Settings tab holds keys / models / costs / safety / notes (Batch 5). Voice Chat panel is purely the conversation surface. The OpenAI Realtime path is dormant-wrapped throughout — code paths intact, UI hidden.

**Where to resume — no active scope.**

The voice migration is complete. The five planned batches are done. Voice Chat is ElevenLabs-only end-to-end, with full client tools, cross-conversation memory, real spend tracking, and the keys/safety plumbing tucked into a dedicated Settings tab. **Don't merge `voice-elevenlabs` → `main` yet** — give it a few real sessions on EL first to confirm stability. Kev's preference is to keep the OpenAI code paths (rtStart, RT state, MIC_SVG_FLOAT, etc.) in the file as dormant back-pocket via the `<div hidden data-dormant="openai-realtime">` convention; don't delete them.

Web research from earlier in the migration:

- **STT:** ElevenLabs Scribe v2 batch transcription is $0.22/hr ≈ $0.0037/min — about 40% cheaper than OpenAI Whisper ($0.36/hr). Same use case (POST audio, get text back). Perfect for the AI Chat dictation flow that currently uses Whisper.
- **TTS:** ElevenLabs has their own TTS API (it's their core product). Replaces the OpenAI TTS dropdown on the AI Chat "Read aloud" feature.
- **LLM-side voice:** Already on ElevenLabs Conversational AI with Claude Sonnet 4.6 brain. Done.

#### Batch 1 — UI sweep on Voice Chat tab — ✅ shipped 2026-05-03

See session log above + "What's already done (don't redo this)" item 11. The DOM/JS state is captured there. Don't re-do these edits.

#### Batch 2 — AI Chat dictation: Whisper → Scribe v2 — ✅ shipped 2026-05-03

See "What's already done (don't redo this)" item 12. Endpoint, headers, body shape, keyterms list, cost roll-up are all captured there.

#### ~~Batch 3 — AI Chat "Read aloud": OpenAI TTS → ElevenLabs TTS~~ — **DROPPED 2026-05-04**

Original spec retired. Read-aloud-as-feature goes away in Batch 3b because the AI Chat tab itself folds into Voice Chat, and the merged tab is voice-first (Hope speaks every reply automatically via the Conversational AI WebSocket — no separate TTS endpoint needed). The OpenAI TTS code path stays dormant in `aichatSpeak` for back-pocket revival. Spec preserved in git history for reference.

#### Batch 3a — Floating button labelling sweep — ✅ shipped 2026-05-04

Pure labelling cleanup. The mechanics of tap-to-toggle were already correct in the floating-button mousedown/mouseup handlers + spacebar handler from the prior session's EL wiring. Batch 3a only updated user-visible strings:

- Static `title` attribute on `#floatMic` (markup line ~811): "Push to talk · Spacebar — drag to move" → "Tap to start a call with Hope · Spacebar to toggle · drag to move"
- Dynamic titles in `setVoiceState` (search the function): idle/connecting/responding/waiting strings reworded for always-on (no more "push to talk to extend", "release to send", "push to interrupt"). Idle: "Tap to start a call with Hope · Spacebar". Responding: "Hope is speaking · tap to end the call". Waiting: "Auto-end in {n}s — speak or tap to keep going". Connecting: "Connecting to Hope…".
- `applyFloatMicVisibility` (search the function): the post-session-end title hint changed from "Push to talk · Spacebar" to "Tap to start a call with Hope · Spacebar". Also added EL active/connecting to the early-return guard so setVoiceState's dynamic title doesn't get clobbered when a tab switch happens mid-call.
- The 'recording' branch in setVoiceState is preserved (kept its existing "Recording — release to send" string) because it's only reachable via the dormant OpenAI PTT path. If you ever revive RT PTT for back-pocket reasons, the string still applies.

The AI Chat dictation tooltip ("Hold to dictate into AI Chat · spacebar also works") stays as-is because AI Chat dictation is still active until Batch 3b retires the tab. After Batch 3b, that branch becomes dead code (the `tab === 'aichat'` check never fires) but stays dormant per the project convention.

#### Batch 3b — Tab merge: AI Chat folds into Voice Chat — ✅ shipped 2026-05-04

See "What's already done (don't redo this)" item 13. Implementation specifics — DOM relocation, dormant-wrappers for TTS + dictation, EL `onMessage` rewrite, `snapshotTranscript` rewrite, Diagnose-tab handoff repoint, Read-aloud retirement, tool-handling boundary comment — are all captured there.

#### Batch 4 — Cost panel rewire — ✅ shipped 2026-05-05

See "What's already done" item 14 for the implementation specifics — `costCardEleven` repurposed from `costCardOpenAI`, `el*` IDs, `EL_CONVAI_RATE_PER_MIN` constant ($0.088/min), `elRenderLiveCost` live ticker, `elFetchConversationCost` post-disconnect reconcile, `updateElBalance` subscription-tier mapping, `SESSION_BREAKDOWN.el`, dormant-wrapped audioIn/Out/text Session-breakdown rows, `SPEND_KEY_OAI` kept as legacy archive but no longer rendered.

#### Batch 5 — Settings tab split — ✅ shipped 2026-05-06

See top session-log entry + "What's already done" item 15 for the implementation specifics — Settings tab nav button + 5-section panel, all blocks moved with DOM IDs preserved, new `.settings-cost-row` 2-col grid for the cost cards, new `#elLiveCostChip` on the Conversation tab populated by `elRenderLiveCost`.

The original spec is preserved below as historical context for anyone wanting to understand the design decisions Kev made (rightmost tab, voice-mode stays on Conversation, live cost chip).

##### Original Batch 5 spec (kept for context)

Pull the plumbing out of Voice Chat into a dedicated **Settings** tab so the Voice Chat tab is purely the Conversation surface. Promoted from "polish" to active scope. Design decisions confirmed by Kev:

1. **Settings is the rightmost tab.** Tab nav becomes: `Chain Builder · Diagnose · Voice Chat · Knowledge · Mastering Reference · Plugin Library · Settings`. Add a `data-tab="settings"` button with a gear icon (the project's existing icon set is line-art; use a stroked gear matching the Mastering Reference / Plugin Library aesthetic).
2. **Voice-mode toggle stays on Conversation.** It's a per-session UX choice not a configuration setting. Don't touch it.
3. **Live cost chip on Conversation.** Small inline `Live · 0:42 · $0.06` chip next to the START CALL button so spend is glanceable during a call without tab-switching. Updates from `elRenderLiveCost` (already runs every second from `elStart` onConnect's setInterval).

**What moves from `<div class="panel" id="voice">` to a new `<div class="panel" id="settings">`:**

| Block | Find via |
| --- | --- |
| OpenAI key block (already dormant-wrapped) | `<div hidden data-dormant="openai-realtime">` containing `#rtApiKey` |
| Anthropic API key block | `.rt-key-wrap` containing `#rtAntKey` |
| ElevenLabs API key block | `.rt-key-wrap` containing `#elKey` |
| ElevenLabs Agent ID block | `.rt-key-wrap` containing `#elAgentId` |
| Whole opts column (`<div class="rt-opts">`) | Includes `#rtModel` (dormant), `#rtVoice` (dormant), `#rtClaudeModel`, `#voiceProvider` (dormant) |
| ElevenLabs cost card (`#costCardEleven`) | `.rt-cost-card.elevenlabs` |
| Anthropic cost card (`#costCardAnthropic`) | `.rt-cost-card.anthropic` |
| Session tools panel (`.rt-tools-panel`) | Cost-per-min, Soft cap, Session breakdown, Auto-pause, Usage dashboards |
| Browser warning banner (`#browserWarn`) | warns about non-secure-context mic blocking — better placement is Settings |
| The "How it works" tip-box (`.tip-box.alt`) | the explanatory copy |

**What stays on `<div class="panel" id="voice">` (the Conversation tab):**

- Big START CALL button + `.rt-status-row` (timer, status pill, rt-cost) **+ NEW: live cost chip** (e.g. small `<span class="rt-live-cost-chip" id="elLiveCostChip">` between status row and the rest).
- Profile editor (`#profileText` + Save/Clear)
- Whole `aichat-layout` block (Conversation section-head, toolbar, transcript, compose, foot row, dormant TTS + dictation wrappers)
- Live Voice Transcript section + `#rtTranscriptClear` button
- Session Snapshots panel (`#journalList` + Export/Clear)
- `<audio id="rtAudio">`

**HTML structure for the new Settings tab (suggested):**

```
<div class="panel" id="settings">
  <div class="section-head">
    <h2>⚙ Settings</h2>
    <span class="blurb">Keys, models, costs, session safety. Voice Chat handles the actual conversation; this tab is the plumbing.</span>
  </div>
  
  <!-- API keys section -->
  <div class="settings-section">
    <h3>API Keys</h3>
    <!-- Anthropic, ElevenLabs key, Agent ID. OpenAI dormant-wrapped. -->
  </div>
  
  <!-- Models section -->
  <div class="settings-section">
    <h3>Models</h3>
    <!-- rtClaudeModel + dormant rtModel/rtVoice/voiceProvider. -->
  </div>
  
  <!-- Cost panels — side by side as today -->
  <div class="settings-section">
    <h3>Costs</h3>
    <div class="rt-call-row">
      <!-- costCardEleven on left, costCardAnthropic on right.
           No START CALL button between them — just the two cards. -->
    </div>
  </div>
  
  <!-- Session tools (cost-per-min, soft cap, breakdown, auto-pause, usage links) -->
  <div class="settings-section">
    <h3>Session safety</h3>
    <div class="rt-tools-panel">…</div>
  </div>
  
  <!-- Browser warning + How-it-works tip-box -->
  <div class="settings-section">
    <h3>Notes</h3>
    <div class="tip-box warn" id="browserWarn">…</div>
    <div class="tip-box alt">…</div>
  </div>
</div>
```

The `.rt-call-row` grid currently expects 3 children (left card, START CALL, right card). When relocated to Settings without START CALL, either:
- (a) Update the grid CSS to accept 2 children (simplest — adjust `grid-template-columns` for the Settings instance only via `.settings-section .rt-call-row`)
- (b) Wrap the cards in a different parent class (`.settings-cost-row`) with its own simpler 2-column grid.

Recommend (b) — cleaner separation, doesn't risk breaking the Voice Chat call row if it ever needs adjustment.

**JS — what stays the same vs what changes:**

- **All DOM IDs stay the same** (`elSession`, `elBalance`, `elKey`, etc.) so the existing handlers keep working without modification. The handlers find their elements regardless of which parent panel hosts them.
- **`updateCallButtonState` still gates the START CALL button** on EL key + Agent ID being saved — no change needed since it queries by ID.
- **`browserWarn` element move** — make sure the `#browserWarn` style="display:none;" → block toggle in `rtStart`/`elStart` still finds it after relocation. It will if the ID stays.
- **Live cost chip** — new DOM element. Add `<span class="rt-live-cost-chip" id="elLiveCostChip"></span>` near the status row. Update `elRenderLiveCost()` to also write to `#elLiveCostChip` if present (null-guard so dormant calls don't throw). Suggested format: `Live · 0:42 · $0.06` where 0:42 is `rtFmtTime(Date.now() - EL.startedAt)` and $0.06 is the live estimate.

**CSS additions:**

- `.settings-section` with consistent vertical spacing + h3 styling
- `.rt-live-cost-chip` — small pill-style, monospace digits, subtle background. Hidden by default (`display:none`); `elRenderLiveCost` reveals it when EL.active. Hide it on `elCleanup`.
- For the Settings cost row variant if going with option (b) above.

**Tab nav button** to add at line ~808 (after Plugin Library):

```html
<button class="tab" data-tab="settings"><span class="tab-ico"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3h.1a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8v.1a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg></span> Settings</button>
```

(Standard line-art gear icon matching the project's existing aesthetic.)

**Things deliberately out of scope for Batch 5:**

- No new APIs, no new endpoints, no new client tools.
- No restructuring of the Conversation tab beyond stripping out the moved blocks + adding the live cost chip.
- No changes to the EL agent dashboard.
- The dormant OpenAI Realtime / dictation / TTS code stays untouched.

**Risk + scope:**

Mostly mechanical HTML cut-and-paste with consistent DOM IDs preserved. Estimated 200–400 lines of HTML restructuring + a small CSS pass + the live cost chip. ~1.5–2 hours of careful work. Test path: `node --check` after every meaningful edit + smoke-test on localhost:8000 — confirm the Voice Chat tab still starts a call, the Settings tab shows all moved blocks rendering correctly, the live cost chip ticks during a call.

**CLAUDE.md sync:**

- Add a session-log entry at top of HANDOVER POINT: "Session of 2026-05-XX — Batch 5 shipped: Settings tab split. …"
- Move Batch 5 from this "PENDING" block into "What's already done" as item 15.
- Update Voice Chat-related "Files / sections to read" entries if line numbers changed materially.
- Strike the "Settings tab split" entry from the "Open follow-ups" polish list.

### What's already done (don't redo this)

### What's already done (don't redo this)

1. **Scaffolding in `index.html`** — keys + agent ID UI on the Voice Chat tab, provider toggle (OpenAI / ElevenLabs), `EL` state object parallel to `RT`, `elStart()` / `elEnd()` / `elCleanup()`, transcript hookup. Search for `========== ELEVENLABS` to find the section.

2. **SDK pin: `@elevenlabs/client@0.1.7`** loaded from `https://esm.sh/@elevenlabs/client@0.1.7`. **Do not change this to @latest.** All 0.2.0+ versions pull in livekit-client v2 which expects `/v1/rtc` endpoints, but ElevenLabs' production server is still on LiveKit Server 1.9.0. We hit `NegotiationError: negotiation timed out` for hours before finding this. 0.1.5–0.1.7 use a direct WebSocket transport with zero runtime deps and connect cleanly. When ElevenLabs upgrades their LiveKit server, we can revisit; until then, leave the pin alone.

3. **Prompt override deliberately omitted from `Conversation.startSession()`.** The server rejects `overrides.agent.prompt.prompt` with WebSocket close code 1008 ("Override for field 'prompt' is not allowed by config") **even when** the dashboard's Security → Overrides → System prompt toggle is ON. Likely a field-name / schema mismatch on their side. Workaround: workbench context (RT_INSTRUCTIONS + buildLibraryDigest + buildResearchDigest) is injected via `EL.conversation.sendContextualUpdate(...)` from the `onConnect` callback. See `EL.pendingContext` in elStart for the wiring.

4. **System prompt + first message + Hope voice** are configured directly in the ElevenLabs agent dashboard and Published. The system prompt is the producer-coach version that includes Hope's identity ("Your name is Hope"). If you need to tweak it, edit in the dashboard, then click Publish (top-right of the agent page) — changes don't propagate until published.

5. **Agent config:**
   - Agent ID: `agent_2601kqm4g7txfsvv0pkvpe02389p`
   - URL: `https://elevenlabs.io/app/agents/agents/agent_2601kqm4g7txfsvv0pkvpe02389p`
   - Voice: **Hope** (`WAhoMTNdLdMoq1j3wf3I`)
   - LLM: **Claude Sonnet 4.6**
   - TTS model: **eleven_v3_conversational** with Expressive Mode ON
   - Security: Public, no auth, no allowlist (System prompt override toggle is ON but server rejects anyway — see point 3)
   - First message: "Hey Kev, it's Hope. What are we working on?"

6. **Client tools wired end-to-end.** `clientTools` field on `Conversation.startSession()` is built programmatically from `TOOL_DEFS` — each tool name maps to an async wrapper that funnels into the same `handleToolCall(name, args)` the OpenAI path uses. Returns are `JSON.stringify`-ed because the SDK expects string/number/void. Every tool call is console-logged as `[EL tool] <name> <args> → <result>` so we can watch them fire. See `elStart` in `index.html` — the `clientTools` block sits just above the `Conversation.startSession({...})` call.

7. **Tool registration script + schema dump.** Two new files at the repo root:
   - `elevenlabs-client-tools.json` — the 25 tool schemas extracted from `TOOL_DEFS` (name + description + parameters JSON Schema for each).
   - `register_elevenlabs_tools.py` — pure-Python (stdlib only, runs on macOS's built-in `python3`) bulk-register script. POSTs each tool to `/v1/convai/tools`, collects IDs, then PATCHes the agent's `prompt.tool_ids` list. Run with `EL_API_KEY=... python3 register_elevenlabs_tools.py`. The agent ID is hardcoded as the production agent. Idempotent in a destructive sense: re-running creates fresh tools and re-attaches them; old workspace tools become orphaned and need manual cleanup from the dashboard's Tools list.

8. **Schema-validation quirk handled in the Python script.** ElevenLabs requires every leaf parameter — string/number/integer/boolean properties AND array `items` schemas — to declare one of: `description`, `dynamic_variable`, `is_system_provided`, or `constant_value`. Our `TOOL_DEFS` omits descriptions on enum-only fields and array-item types because OpenAI doesn't need them. The `ensure_param_descriptions` function in the Python script walks each schema and injects a sensible default description before POSTing. If you ever extend `TOOL_DEFS` and re-run the script, the same normalisation handles your new fields automatically.

9. **Profile system — cross-conversation memory.** `STATE.profile` (string, capped at 2 KB by `PROFILE_MAX_LEN`) is persisted in `trapMasterState_v1`. `buildProfileDigest()` formats it as a system-prompt block; both `rtStart` and `elStart` append it to their session instructions (OpenAI via `session.update`, EL via `sendContextualUpdate` in the pendingContext bundle). `maybeExtractProfile()` runs at end-of-call (hooked from `rtEnd` AND `onDisconnect`, BEFORE cleanup wipes the transcript) — `snapshotTranscript()` reads from `RT.transcriptIndex`, then `extractProfile()` fires a Haiku call (`claude-haiku-4-5-20251001`) with a focused system prompt that captures durable preferences only. UI panel between session tools and live transcript: `#profileText` textarea + Save / Clear / status / byte counter. Spend is rolled into the existing `addSpend('an', cost)` Anthropic bucket.

10. **Dual-provider overlap fix.** Earlier the float mic and spacebar always called `rtStart` regardless of the provider dropdown — so pressing PTT while Hope was running started a parallel OpenAI session and both providers played audio into the shared `#rtAudio` element. Five surgical fixes landed: `micStartFromFloat` branches by provider, `rtStart` and `elStart` defensively cross-end any other-provider session at top, the rtCallBtn handler ends ANY active session (not just the matching-provider one), and the float-mic + spacebar handlers became EL-aware (mousedown is a no-op when EL is active; mouseup ends the call; spacebar tap toggles EL start/end since it has no PTT semantics). All this is moot now that Batch 1 has shipped and unwired the dropdown — but the cross-end guards in `rtStart`/`elStart` should stay as belt-and-braces.

11. **Batch 1 — UI sweep on Voice Chat tab.** Shipped 2026-05-03. The dual-provider plumbing is gone from the visible UI; the OpenAI Realtime path is dormant in the file as a back pocket. Specifics worth knowing:

    - **Dormant-wrap pattern.** Four blocks in the Voice Chat tab are wrapped in `<div hidden data-dormant="openai-realtime">`: the OpenAI API key field (input + Save/Show/Clear + status), the `#rtModel` selector, the `#rtVoice` selector, and the `#voiceProvider` selector. Hidden in CSS via the `hidden` attribute, but the elements remain in the DOM so the dormant JS (rtLoadKey/rtSaveKey/rtClearKey, rtSavePrefs/rtLoadPrefs, loadVoiceProvider/saveVoiceProvider/getVoiceProvider) keeps working without null-guard changes. To revive any of them, drop the `hidden` attribute on the wrapper. The voiceProvider dropdown's default-selected option was flipped to `"elevenlabs"` so any dormant code reading `getVoiceProvider()` naturally takes the EL branch.
    - **Anthropic key + `#rtClaudeModel` (Research brain) STAY visible** — they power Claude research, profile extraction, AI Chat itself. The ElevenLabs key + Agent ID rows are unchanged.
    - **JS handlers simplified to EL-only.** `rtCallBtn` click handler: cross-end any active session (RT or EL), then `elStart()`. `micStartFromFloat()`: collapsed to the EL path — guard on `EL_AGENT_ID_STORAGE`, call `elStart()`, jump to Voice Chat tab. Spacebar `keydown`: aichat → dictation as before; every other tab → toggle EL call. The dormant focus-mode / PTT-queue / `micScopeAndMode` / `FOCUS_TAB_SCOPES` plumbing is left alone in the file. The `mousedown`/`mouseup`/`touchstart`/`touchend` handlers on the float mic still have RT branches inside them — those branches are unreachable in normal use (no path now sets RT.active) but stay as the dormant wiring.
    - **START CALL button.** New helper `updateCallButtonState()` (search the file) gates `#rtCallBtn` on `EL_KEY_STORAGE` + `EL_AGENT_ID_STORAGE`. Hooked into `elLoadKey`/`elSaveKey`/`elClearKey`/`elLoadAgentId`/`elSaveAgentId`/`elClearAgentId`. The button-touching lines were removed from `rtLoadKey`/`rtSaveKey`/`rtClearKey` (rtSetKeyStatus still updates the dormant status pill). The static initial label in HTML is `"Save EL key + Agent ID"`. Mid-call states (RT/EL active or connecting) are owned by `setVoiceState`/`rtStart`/`elStart` — `updateCallButtonState` early-returns in those cases so it doesn't stomp the live label.
    - **Mic-mode toggle.** The original handover note suggested hiding a Voice Chat tab toggle and a chain-toolbar pill. In current HTML neither existed — only the AI Chat dictation toggle (`<div class="voice-mode-toggle" data-scope="aichat">` near `#aiChatInput`) is in the DOM, and that one STAYS because PTT vs always-on is meaningful for dictation modes (independent of Realtime). So no toggles were hidden in this batch beyond updating the now-stale chain-toolbar hint text ("Floating mic is push-to-talk on this tab — toggle modes from the Voice Chat tab" → "Tap the floating mic to start a live call with Hope — she reads and edits the chain in real time").
    - **Tip-box copy.** The Voice Chat "How it works" tip-box was rewritten from OpenAI-Realtime flavour to Hope/Claude Sonnet 4.6/EL flavour. Mentions profile auto-extract.
    - **Stale UI still on the page (intentional, deferred to Batch 4):** the OpenAI cost card on the left of the call row (`#costCardOpenAI` with `oaSession`/`oaBalance`/etc.). Batch 4 renames + repurposes this for ElevenLabs spend.

12. **Batch 2 — AI Chat dictation: Whisper → Scribe v2.** Shipped 2026-05-03. The DICT module's PTT path now hits ElevenLabs Scribe v2 instead of OpenAI Whisper. Specifics:

    - **Endpoint + request shape.** `POST https://api.elevenlabs.io/v1/speech-to-text` with `xi-api-key` header. Multipart fields: `file` (the recorded webm Blob), `model_id=scribe_v2`, `language_code=en`, `tag_audio_events=false` (so "(laughter)" doesn't land in chat), and `keyterms` repeated for each plugin / producer / engineering term in the new `SCRIBE_KEYTERMS` constant near the top of the DICT module. Response `.text` is the same shape as Whisper's so the consumer code is unchanged. The multi-channel response shape (`.transcripts[0].text`) is handled defensively even though we don't enable `use_multi_channel`.
    - **Keyterms (vocab biasing).** Replaces Whisper's free-form `prompt` field. ElevenLabs constraints: max 1000 entries; each <50 chars; each ≤5 words after normalisation; >100 entries triggers a 20-second minimum-billing rule, so the list stays under 100. Currently ~50 terms covering plugin houses (FabFilter, Plugin Alliance, iZotope, Brainworx, Soundtoys, etc.), flagship plugins (Pro-Q, Soothe2, OTT, Decapitator, Auto-Tune, Maag EQ4, etc.), classic hardware names (1176, LA-2A, SSL, API), and engineering vocabulary (sidechain, multiband, true peak, etc.). Add new terms by editing `SCRIBE_KEYTERMS` — `dictScribeFlush` re-reads it on every call.
    - **Cost.** Scribe v2 base $0.22/hr ≈ $0.0037/min. Keyterms surcharge +20% → effective $0.00444/min. Still ~26% cheaper than Whisper ($0.006/min) and far better at plugin / producer names. Defined as `SCRIBE_RATE_PER_MIN = 0.0037 * 1.20` inside `dictScribeFlush` — bump if you change keyterms-on/off behaviour.
    - **EL spend bucket.** New `SPEND_KEY_EL = 'aiMixMastersSpendEleven_v1'` localStorage key. `addSpend(provider, delta)` now accepts `'el'` as a third bucket alongside `'oai'` and `'an'/'ant'`. The cost-panel UI in `renderCostPanels` / `renderHistoryBars` doesn't render this bucket yet — that's Batch 4 territory. Until then `addSpend('el', cost)` accumulates silently in localStorage and the existing two cost cards just re-render harmlessly. The console log line `[DICT] Scribe: ...` shows per-call duration + cost so you can sanity-check live.
    - **Engine string + fallback.** `dictPreferredEngine()` returns `'scribe'` when `EL_KEY_STORAGE` is saved, else `'webspeech'`. The `'whisper'` engine string was renamed throughout (`dictPttDown` checks `engine === 'scribe'`; the MediaRecorder onstop handler is `dictScribeFlush` instead of `dictWhisperFlush`). Web Speech fallback path is unchanged — same `Ctor()` continuous + one-shot logic.
    - **What didn't change.** Always-on dictation still uses Web Speech (no Scribe streaming endpoint that fits our use case). PTT vs always-on toggle on the AI Chat tab is unchanged. The transcript-to-textarea handoff (`dictDeliverTranscript`) is unchanged. The `RT_KEY_STORAGE` constant + `rtLoadKey` etc. are still in the file — they're dormant after Batch 1 already and don't gate dictation any more.
    - **Untouched but noted:** `dictWebSpeechCtor`'s no-Web-Speech toast still says "Speech recognition not supported in this browser" — accurate. Mic-permission errors still surface as "Mic blocked or unavailable". The `'No OpenAI key saved'` toast was replaced with `'No ElevenLabs key saved'` in `dictScribeFlush`.

13. **Batch 3b — Tab merge: AI Chat folds into Voice Chat.** Shipped 2026-05-04. Voice Chat is now the unified Conversation surface. Specifics:

    - **HTML — AI Chat tab nav button + panel deleted.** The `data-tab="aichat"` button was replaced with a comment near its old slot. The entire `<div class="panel" id="aichat">…</div>` block (~70 lines) was replaced with a comment pointing at the new home in the Voice Chat panel.
    - **HTML — Voice Chat panel restructured.** The Voice Chat panel now contains, in order: keys row + opts row (unchanged from Batch 1, with the OpenAI bits dormant); rt-call-row (cost cards + START CALL — cost cards still pre-Batch-4 OpenAI-flavoured); session tools panel; profile editor; **NEW: Conversation block** wrapped in `<div class="aichat-layout">` containing a "Conversation" section-head, the AI Chat toolbar (`#aiChatModel`, `#aiChatWebSearch`, `#aiChatToJournal`, `#aiChatImportPlugins`, `#aiChatClear`), `#aiChatTranscript`, `#aiChatImagePreview`, `#aiChatImageInput`, the `aichat-compose` block (textarea + send-col with `#aiChatSend`, `#aiChatImageBtn`, quick prompts, `#aiChatClearInput`, `#aiChatStatus`), and the `aichat-foot` row (`#aiChatSessionCost`, `#aiChatLastCost`, `#aiChatMsgCount`); two dormant-wrapped blocks at the bottom (`data-dormant="aichat-readaloud"` holds `#aiChatTtsVoice` + `#aiChatTtsModel` + `#aiChatTtsAudio`; `data-dormant="aichat-dictation"` holds `voice-mode-toggle[data-scope="aichat"]`); then Session Snapshots panel + tip-box + `#rtAudio` (unchanged from before).
    - **HTML — `#rtTranscript` retired.** The "Live Voice Transcript" section header + `<div class="rt-transcript" id="rtTranscript">` element + `#rtTranscriptClear` button are all gone. The merged `#aiChatTranscript` is the single source of truth for both voice + typed turns. JS lookups for `rtTranscript` and `rtTranscriptClear` were null-guarded throughout (`rtClearTranscriptPlaceholder`, `rtGetOrCreateTurn`, `rtAppendTurnText`, `snapshotTranscript`, the `rtTranscriptClear.onclick = ...` binding) so the dormant rt-helpers no-op cleanly if invoked. Revival path: drop `data-dormant` wrappers + restore the rt-transcript block + the rt-helper paths re-attach automatically.
    - **JS — EL `onMessage` rewritten.** The `rtAppendTurnText(id, role, message, true)` call was retired. Voice messages now flow only into `AICHAT.history` with `source:'voice'` and trigger `aichatRender()` + `aichatSave()`. The merged transcript renders both voice (Hope) and typed (Claude) turns from a single source.
    - **JS — `snapshotTranscript()` rewritten.** Primary path now reads from `AICHAT.history` filtered by `source:'voice'` so end-of-call profile extraction (`maybeExtractProfile`) keeps working post-3b. The rt-transcript DOM walk stays as the back-pocket fallback for any revived OpenAI Realtime call. Don't reorder `maybeExtractProfile()` relative to `elCleanup()` — `AICHAT.history` persists, but the cleanup window matters for the rt-transcript fallback.
    - **JS — Read aloud button retired from `aichatRender`.** The per-message `<button>Read aloud</button>` markup was replaced with a comment block. `aichatSpeak`, `TTS` state machine, `TTS_RATES`, `TTS_MAX_CHARS` etc. all stay — back pocket for revival. The TTS dropdowns + audio element live in the `data-dormant="aichat-readaloud"` wrapper so the dormant code path still finds its DOM.
    - **JS — Dictation branches dormant-tagged.** The `if (activeTabId() === 'aichat')` and `if (tab === 'aichat')` branches in float-mic mousedown / mouseup / mouseleave / touchstart / touchend handlers + spacebar keydown handler stay verbatim. They're naturally unreachable now (the 'aichat' tab key is gone), but kept as the back pocket. Comments above the float-mic + spacebar handlers explain the dormancy. Revival path: re-add the AI Chat tab nav button + drop the `data-dormant="aichat-dictation"` wrapper + the branches re-fire.
    - **JS — Tool-handling boundary documented.** Added a comment block above `aichatSend` clarifying which path runs which tools: voice turns route through the EL SDK's `clientTools` map (registered in `elStart`), typed turns run the Anthropic `tool_use` loop (web_search + add_symptom_tile / delete_symptom_tile / list_symptom_tiles). Voice messages land in `AICHAT.history` purely for transcript rendering — they do NOT trigger the Anthropic tool-use loop. Don't merge the loops.
    - **JS — Diagnose-tab handoff repointed.** The "create troubleshooting tile" handler in `renderRecipes` previously switched to the AI Chat tab. Post-3b it switches to the Voice Chat tab where `#aiChatInput` now lives. The `data-tab="aichat"` / `getElementById('aichat')` fallback lookups stay (return null harmlessly) for any future revival.
    - **Focus modes status.** `RT.focusMode`, `FOCUS_TAB_SCOPES`, the system-prompt addenda blocks inside `rtStart` — all live in the dormant OpenAI Realtime path only. `elStart`'s `pendingContext` does not build any per-tab focus addendum, so the Batch 3b spec's "drop addenda from active use" was already true post-Batch-1; nothing changed here.
    - **Untouched but noted:** the OpenAI cost card (`#costCardOpenAI`, `oaSession`/`oaBalance`/etc.) still sits to the left of START CALL. Batch 4's cost-panel rewire repurposes it for ElevenLabs spend. Until then it shows OpenAI Realtime metrics that no longer accumulate (RT path is dormant).

14. **Batch 4 — Cost panel rewire.** Shipped 2026-05-05. The OpenAI cost card on the Voice Chat tab is now an ElevenLabs cost card. Specifics:

    - **HTML — card repurposed.** `<div class="rt-cost-card openai" id="costCardOpenAI">` → `<div class="rt-cost-card elevenlabs" id="costCardEleven">`. Header text `OpenAI · Realtime` → `ElevenLabs · Conversational AI`. Indigo `#818cf8` accent (border-left + dot), distinct from OpenAI green `#10a37f` and Anthropic orange `#d97757`. New CSS rules in the `.rt-cost-card.elevenlabs` / `.elevenlabs-dot` selectors mirror the existing colour-variant pattern.
    - **HTML — IDs renamed.** `oaSession` / `oaBalance` / `oaSpent` / `oaLeft` / `oaTopup` / `oaUpdate` / `oaUsageLink` → `elSession` / `elBalance` / `elSpent` / `elLeft` / `elTopup` / `elUpdate` / `elUsageLink`. The Usage-dashboards tile in the Session-tools panel had its `oaUsageLink` button → `elUsageLink` too. Top-up URL = `https://elevenlabs.io/app/subscription`. Usage URL = `https://elevenlabs.io/app/usage`.
    - **HTML — Session breakdown collapsed.** 4 OpenAI-flavoured rows (audioIn/audioOut/text/research) → 2 active rows: `#brEl` (Voice — EL minutes) + `#brResearch` (Research — Anthropic). The audioIn/audioOut/text rows are dormant-wrapped (`<div class="br-line" hidden data-dormant="openai-realtime">`) so any back-pocket revival of `rtRenderCost` doesn't crash on null lookups.
    - **JS — `EL_CONVAI_RATE_PER_MIN`** constant added near the SPEND_KEY definitions. Currently `22 / 250 ≈ $0.088/min` (Creator plan). Tweak when ElevenLabs changes plan structure.
    - **JS — `elRenderLiveCost()`** new function. Computes `(Date.now() - EL.startedAt) / 60000 * EL_CONVAI_RATE_PER_MIN` once per second, writes to `#elSession`, mirrors into `#brEl`, paints the `cpmValue` cost-per-minute tile (amber > $0.10/min, red > $0.20/min), and watches the soft-budget cap. Caches the figure on `EL.lastLiveCostEstimate` so the post-disconnect reconcile can diff against it. Hooked from `elStart`'s onConnect: `EL.timer = setInterval(() => { rtTickTimer(); elRenderLiveCost(); }, 1000)`.
    - **JS — `elFetchConversationCost(conversationId)`** new function. Hits `GET /v1/convai/conversations/{conversationId}` with `xi-api-key`. Tries multiple plausible response paths to find the exact minutes used: `metadata.charging.minutes_used`, `metadata.charging.duration_minutes`, `metadata.duration_minutes`, `charging.minutes_used`, `minutes_used`, `duration_seconds/60`, `metadata.duration_seconds/60`. First valid finite-positive number wins. Multiplies by `EL_CONVAI_RATE_PER_MIN`, diffs against `EL.lastLiveCostEstimate`. Top-up via `addSpend('el', delta)` when exact > estimate; logs only when under (no refund / double-credit). Hook in EL `onDisconnect`: capture `EL.conversationId` to a local **before** `elCleanup()` wipes it, then fire-and-forget independent of `maybeExtractProfile()` so neither blocks the other.
    - **JS — `updateElBalance()`** new function. Hits `GET /v1/user/subscription` with `xi-api-key`. Maps `data.tier` to monthly $ budget via `TIER_BUDGETS = { free: 0, starter: 5, creator: 22, pro: 99, scale: 330, business: 1320 }`. Falls back to manual prompt for unknown tiers or no key. Toast message includes character-budget headroom (`character_limit - character_count`) when available. `updateBalance('el')` routes through here; `updateBalance('oai' | 'an' | 'ant')` keeps the manual-prompt flow.
    - **JS — `renderCostPanels` rewired.** Reads `SPEND_KEY_EL` (was OAI). Writes to `el*` IDs. Anthropic side untouched. `renderHistoryBars` similarly switched (function still no-ops because the Last-7-days tile is removed; future re-enable will use the EL bucket as primary feeder).
    - **JS — `rtRenderCost`'s oaSession write guarded.** `const oaSessEl = document.getElementById('oaSession'); if (oaSessEl) ...` — the function is dormant after Batch 1 but if the OpenAI Realtime path is ever revived, it won't throw on the renamed DOM. The new EL session value is owned by `elRenderLiveCost`, not by this dormant function.
    - **JS — `EL` state additions.** `lastLiveCostEstimate: 0` and `budgetWarned: false` fields on the `EL` object, both reset by `elCleanup()`. `SESSION_BREAKDOWN` gained `el: 0`. Budget-cap dropdown change handler now resets `EL.budgetWarned` alongside `RT.budgetWarned` so a new cap allows a fresh warning.
    - **`SPEND_KEY_OAI` legacy archive.** Stays defined. `addSpend('oai', delta)` still routes there if any back-pocket revival of the OpenAI Realtime path fires it. `renderCostPanels` no longer reads from it. The 30-day localStorage history is preserved untouched.

15. **Batch 5 — Settings tab split.** Shipped 2026-05-06. Voice Chat panel is now purely the Conversation surface; configuration plumbing lives in a dedicated rightmost Settings tab. Specifics:

    - **HTML — new tab + panel.** New `<button class="tab" data-tab="settings">` (line-art gear SVG matching the project's icon family) added at the rightmost end of `.tabs`, after Plugin Library. New `<div class="panel" id="settings">` placed after the Plugin Library panel, with five `<div class="settings-section">` blocks: API keys, Models, Costs, Session safety, Notes. Each section has an `<h3>` heading + the relocated content.
    - **HTML — moves with IDs preserved.** Anthropic key (`#rtAntKey` + show/save/clear), ElevenLabs key (`#elKey` + show/save/clear), ElevenLabs Agent ID (`#elAgentId` + save/clear), and the dormant OpenAI key (`#rtApiKey` under `<div hidden data-dormant="openai-realtime">`) → API keys section. Research brain (`#rtClaudeModel`) + dormant `#rtModel`, `#rtVoice`, `#voiceProvider` (all `hidden data-dormant`) → Models section. Both cost cards (`#costCardEleven` + `#costCardAnthropic`) → Costs section, wrapped in `.settings-cost-row` 2-col grid. The whole `.rt-tools-panel` (cost/min, soft cap, breakdown, auto-pause, usage links) → Session safety section. `#browserWarn` + the How-it-works tip-box → Notes section. Every DOM ID survived the move so handlers (key save/load, prefs, cost rendering, click handlers) didn't need rewiring.
    - **HTML — Voice Chat panel cleanup.** Old `<div class="rt-call-row">` (3-child grid sandwiching START CALL between the two cost cards) was removed entirely; the inner `rt-main` with the call button + status row now sits directly inside the panel as a flex-column centered. The session-tools panel, the How-it-works tip-box, and the browserWarn banner are gone from Voice Chat — the audio element (`#rtAudio`) stays as the call's audio sink.
    - **HTML — new live cost chip on Conversation tab.** `<span class="rt-live-cost-chip" id="elLiveCostChip" hidden>` added to the rt-status-row (after `#rtCost`). Hidden by default; populated by `elRenderLiveCost` once per second while `EL.active`. Format: `Live · 0:42 · $0.06`. CSS `.rt-live-cost-chip` styled as a small monospace pill matching the row aesthetic; toggles `.amber` over $1, `.red` over $2 for cost-rage glance feedback. `elCleanup` hides it on call end (sets `hidden=true`, clears textContent, removes amber/red classes).
    - **CSS additions.** Around the `.section-head` rule: `.settings-section{margin:18px 0 28px}`, `.settings-section h3{font-size:13px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;color:#cbd5e1;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid #1f2937}`, `.settings-cost-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}` with a `@media (max-width:720px)` collapse to `1fr`. Live cost chip styling `.rt-live-cost-chip` near the dormant-wrap CSS fix.
    - **JS — elRenderLiveCost gained chip-write block.** Inside the function, after the existing brEl write: `const chip = document.getElementById('elLiveCostChip'); if (chip){...}`. Format string `Live · ${elapsed} · $${cost.toFixed(2)}` where `elapsed = rtFmtTime(Date.now() - EL.startedAt)`. Hidden when `!EL.active || !EL.startedAt`.
    - **JS — elCleanup added chip teardown.** After the existing `if (fm) fm.classList.remove('in-call')` line: hide chip + clear text + remove amber/red classes.
    - **No JS handler changes** — every relocated element kept its ID, so `rtSaveAntKey`, `elSaveKey`, `elSaveAgentId`, `rtSavePrefs`, `renderCostPanels`, `rtRenderCost`, `updateBalance`, `elFetchConversationCost`, the `#budgetCap` change listener, the `#autoPause` listener, and every other handler all find their targets unchanged.

### Localstorage keys added by the migration

- `aiMixMastersElevenKey_v1` — ElevenLabs API key
- `aiMixMastersElevenAgent_v1` — Agent ID (validated to start with `agent_`)
- `aiMixMastersVoiceProvider_v1` — `'openai'` or `'elevenlabs'` (the dormant dropdown on the Voice Chat tab — Batch 1 hid the UI; key stays for back-pocket use)
- `aiMixMastersSpendEleven_v1` — EL cumulative spend bucket (Batch 2 starts feeding it from Scribe; Batch 4 reads it for the cost panel)

### Files / sections to read before touching the EL code

In `index.html` (line numbers approximate — file is ~9100 lines):

- **`const EL_SDK_URL`** — the SDK pin and the rationale comment. Read the comment before changing.
- **`const EL = {...}`** — the state object. Mirrors `RT` in spirit.
- **`elLoadKey / elSaveKey / elLoadAgentId / elSaveAgentId / loadVoiceProvider`** — persistence helpers. `loadVoiceProvider` becomes vestigial after Batch 1.
- **`async function elStart()`** — the main connect path. Two key blocks: (a) the `clientTools` dict built programmatically from `TOOL_DEFS` just above the `Conversation.startSession({...})` call (each tool becomes an async wrapper around `handleToolCall` that JSON.stringifies its return), and (b) the `EL.pendingContext` flow that injects workbench state via `sendContextualUpdate` from `onConnect`. `pendingContext` already includes `buildLibraryDigest()`, `buildResearchDigest()`, AND `buildProfileDigest()` — append the focus-mode addendum here too if Batch 1 wants to fold the focus-tab system prompts into EL.
- **`async function elEnd() / function elCleanup()`** — disconnect + state reset.
- **`document.getElementById('rtCallBtn').addEventListener('click', ...)`** — the START CALL button. Currently branches by `getVoiceProvider()` and ends-anything-active; after Batch 1, drop the branch and just route to elStart/elEnd.
- **`function micStartFromFloat()`** — the float-mic click entry point. Currently branches by provider; Batch 1 simplifies to EL-only.
- **Spacebar handler `window.addEventListener('keydown', ...)`** — same provider branching, same simplification.
- **`async function maybeExtractProfile()` + `extractProfile()` + `snapshotTranscript()`** — profile extraction pipeline. Hooked from both `rtEnd` AND EL `onDisconnect` BEFORE cleanup wipes `RT.transcriptIndex`. Don't move the hook order or the transcript snapshot returns empty.
- **`function updateCallButtonState()`** (Batch 1) — gates `#rtCallBtn` on EL key + Agent ID. Called from every EL key/agent setter and at init. Early-returns during RT/EL active/connecting so it doesn't stomp `setVoiceState` paint. Search this name to find the function.
- **DICTATION (DICT) module** — search `// DICTATION (DICT)`. Post Batch-2: PTT path hits Scribe v2; the `SCRIBE_KEYTERMS` array near the top of the module is the editable plugin/producer dictionary. Always-on still uses Web Speech. Post Batch-3b: dictation-as-a-feature is dormant — the AI Chat tab is gone, so `activeTabId() === 'aichat'` branches in the float-mic + spacebar handlers never fire.
- **`function addSpend(provider, delta)`** — accepts `'oai'` / `'an' | 'ant'` / `'el'` (Batch 2 added the third bucket). Routes to `SPEND_KEY_OAI` / `SPEND_KEY_ANT` / `SPEND_KEY_EL`. The render functions only know about OAI + ANT until Batch 4.
- **AI Chat TTS** — search `aichatSpeak`. Dormant post Batch-3b: Read-aloud was retired in favour of Hope speaking every voice reply via the EL WebSocket. The TTS state machine + audio element live behind a `data-dormant="aichat-readaloud"` wrapper.
- **Merged Conversation surface** — search `<!-- CONVERSATION` in `index.html`. The single `<div class="aichat-layout">` block in `<div class="panel" id="voice">` holds the toolbar + transcript + compose area + foot row. `#aiChatTranscript` is the only transcript element — voice + typed turns share it.
- **`function snapshotTranscript()`** (Batch 3b) — primary path reads from `AICHAT.history` filtered by `source:'voice'`; rt-transcript DOM walk is the back-pocket fallback. Used by `maybeExtractProfile` for end-of-call profile extraction.
- **EL `onMessage`** — search `onMessage:` inside `elStart`. Post Batch-3b: pushes only to `AICHAT.history`, calls `aichatRender()` + `aichatSave()`. The `rtAppendTurnText` call into `#rtTranscript` was retired.

### Known good user flow

1. `python3 -m http.server 8000` from the repo root → open <http://localhost:8000>.
2. **Settings tab** (rightmost) → ElevenLabs API key + Agent ID saved + Anthropic key saved (loaded from localStorage on subsequent loads).
3. **Voice Chat tab** → click **START CALL** → Hope greets him in her voice with Claude Sonnet 4.6 brain. Live cost chip on the status row ticks `Live · 0:42 · $0.06` once per second during the call.
4. Try voice tool calls: "what's on my master bus?", "add Maag EQ4 to the master", "switch genre to trap" — workbench updates in real time, DevTools console logs `[EL tool] <name> <args> → <result>` for every call.
5. End the call → Haiku extracts profile updates (if Anthropic key saved + transcript >200 chars). The `#profileText` panel updates with new lines. Next call she remembers. Behind the scenes, `elFetchConversationCost` reconciles the live estimate against ElevenLabs' exact minute figure and tops up the spend bucket if needed.

### Open follow-ups

The OpenAI removal is **complete** — all five batches shipped (Batch 1 / 2 on 2026-05-03, Batches 3a / 3b on 2026-05-04, Batch 4 on 2026-05-05, Batch 5 on 2026-05-06). No active scope. Possible future polish (not committed):

- **Slow / slurry voice from Hope (Kev flagged 2026-05-06).** v3 conversational TTS occasionally sounds dragged-out. Voice settings sliders are not customizable on v3 models — pacing comes from the model's interpretation of the text, the Expressive Mode toggle in the dashboard, and the system-prompt + contextual-update content. Suspected cause: the auto-extracted profile blob contains language that the model reads as a "speak slowly" cue. Kev punted: "We'll come back to it if it persists." Diagnostic path if revisited: clear `STATE.profile`, refresh, test a call. If she perks up → it was the profile content. If still slow → toggle Expressive Mode off in the agent dashboard and Publish.
- **EL TTS character budget.** The `updateElBalance` toast surfaces `character_limit - character_count` from the subscription endpoint as supplementary info. It's not a separately-tracked spend bucket because TTS-per-character spend was retired in Batch 3b. If you ever revive a separate Read-aloud feature, this is where character-spend would re-enter.
- **`/v1/convai/conversations/{id}` field-name verification.** `elFetchConversationCost` tries seven plausible response paths because the exact field name has shifted over ElevenLabs API versions. Worth confirming the canonical path with a real call + simplifying the helper once the schema is locked in.
- **Live history bars tile.** The `historyBars` DOM is null right now (the tile was removed pre-EL-migration). If you ever re-add it, `renderHistoryBars` is already EL-aware — just drop the early-return null check on `wrap`.
- **Voice provider toggle revive.** The dormant-wrapped `#voiceProvider` dropdown is still in the DOM. If ElevenLabs ever has an extended outage and you need to fall back to OpenAI Realtime, drop the `hidden` attr on the dormant wrapper and the dual-provider plumbing comes back to life. Not free — `rtStart` would need a fresh OpenAI key paste — but the bones are there.

### Non-obvious gotchas

- **`.git/index.lock` permission issue** — Kev runs git commands in his real Terminal, not via the agent. Don't try to commit/push from inside Claude — generate the commands and have him paste them.
- **Free tier** — Conversational AI requires Creator plan ($22/mo). Kev is now on Creator. Don't suggest free tier for testing — it'll silently fail.
- **Mic permission** — never call `navigator.mediaDevices.getUserMedia()` before `Conversation.startSession()`. The SDK acquires the mic itself; pre-acquiring it causes the SDK to fail silently and you get a 30s "Successful, 0 messages" timeout pattern in the Conversations log. We learned this the hard way.
- **System prompt override** — toggle in the agent's Security → Overrides is ON, but the server still rejects the override. Don't waste time re-debugging this; we use `sendContextualUpdate` instead.
- **Drafts vs Live** — agent dashboard changes show as "Draft" until you click **Publish** in the top-right corner of the agent page. Without publishing, the live agent still uses the previous config. Burned an hour on this when Hope wasn't applying. Note: the `register_elevenlabs_tools.py` script's PATCH appears to auto-publish (Publish button stays greyed after running it).
- **Tool schema strictness** — ElevenLabs' tool-create endpoint requires every leaf parameter to declare a `description` (or `dynamic_variable` / `is_system_provided` / `constant_value`). This applies to enum-only fields, primitives like `{type:"integer"}`, AND array `items` schemas. Our `TOOL_DEFS` in `index.html` omits descriptions on those because OpenAI doesn't need them, so the Python register script normalises before POSTing — see `ensure_param_descriptions`.
- **Tool registration is per-workspace, not per-agent** — `POST /v1/convai/tools` creates tools in the workspace; the agent then references them by ID via `prompt.tool_ids`. Re-running the register script creates fresh tool entries; old ones become orphans that need manual cleanup from the dashboard's Tools list. Don't run the script casually.
- **Dormant-wrap pattern (Batch 1)** — when a UI section needs to disappear but its JS DOM lookups should keep working without null guards, wrap the block in `<div hidden data-dormant="<reason>">` and add a comment. The `hidden` HTML attribute hides the element CSS-side but leaves it in the DOM. To revive, drop the `hidden` attribute. Used in four places on the Voice Chat tab (`#rtApiKey` block, `#rtModel`, `#rtVoice`, `#voiceProvider`). Subsequent batches should follow this convention.
- **Updating the START CALL button label.** Don't add new ad-hoc `getElementById('rtCallLabel').textContent = '...'` calls outside the existing call-state machine. Idle/disabled paint is owned by `updateCallButtonState()`; mid-call paint is owned by `setVoiceState`/`rtStart`/`elStart`. New gating conditions (e.g. Batch 4 plan-quota warnings) should plug into `updateCallButtonState`.
- **Scribe keyterms surcharge (Batch 2).** Sending `keyterms` to `/v1/speech-to-text` adds +20% to base transcription cost, and crossing 100 keyterms triggers a 20-second minimum-billing rule per request. The `SCRIBE_KEYTERMS` array stays well under 100 (currently ~50). If you grow it past 100, either (a) split by domain and pick a subset per request, or (b) accept the 20s minimum and revise `SCRIBE_RATE_PER_MIN` accordingly. Don't blindly extend.
- **`tag_audio_events` defaults to true.** Without `tag_audio_events=false` Scribe will inject `(laughter)`, `(footsteps)` etc. into the transcript text — those land verbatim in `#aiChatInput` and look ridiculous. Always send `false` for typed-out chat input. (For meeting-style transcription where event tags are useful, leave it on.)
- **Batch 3b dormancy convention.** When Batch 3b retired AI Chat as a tab, the `activeTabId() === 'aichat'` and `tab === 'aichat'` checks in float-mic + spacebar handlers stayed VERBATIM (didn't get wrapped in `if (false &&`). The branches are unreachable because the tab key 'aichat' is no longer in the DOM, so they short-circuit naturally. If you ever need to verify a future change can't accidentally re-fire one of these, search for `activeTabId() === 'aichat'` and confirm the calling site doesn't set the tab.
- **`snapshotTranscript()` source-of-truth.** Post Batch-3b the function reads from `AICHAT.history` (filtered to `source:'voice'`) instead of `#rtTranscript` DOM children. Profile extraction depends on this — if you ever clear `AICHAT.history` aggressively (e.g. add a Clear-chat button that wipes it before `maybeExtractProfile()` runs), the profile dossier won't update from voice calls. Order matters: `maybeExtractProfile()` is hooked from EL `onDisconnect` BEFORE `elCleanup()`. Don't reorder.
- **Merged transcript renders both kinds of turns.** Voice (Hope) turns from EL `onMessage` and typed (Claude) turns from `aichatSend` both land in `AICHAT.history` and render through `aichatRender()` into `#aiChatTranscript`. Voice items are tagged `source:'voice'`; typed items are not. Future styling (a small mic glyph next to voice turns, a different background tint, etc.) can branch on `m.source === 'voice'` in `aichatRender`.

- Live: <https://begb0037admin.github.io/trap-master-reference/>
- Repo: <https://github.com/begb0037admin/trap-master-reference> (branch `main` is what GitHub Pages serves)
- Local source: `~/Documents/Claude/Artifacts/trap-master-reference/`

## File layout

```
trap-master-reference/
├── index.html                       ← THE app. Single-file: HTML + CSS + vanilla JS, all inline.
├── README.md                        ← User-facing readme (setup, voice chat keys, what's in it).
├── CLAUDE.md                        ← This file.
├── elevenlabs-client-tools.json     ← (voice-elevenlabs branch) 25 tool schemas extracted from TOOL_DEFS.
├── register_elevenlabs_tools.py     ← (voice-elevenlabs branch) bulk-register script — POST tools + PATCH agent.
├── .gitignore                       ← Ignores macOS junk, editor folders, secrets, versions/, __pycache__.
├── versions/                        ← Cowork's local artifact history. Gitignored — do NOT commit, do NOT touch.
└── .git/                            ← Standard git repo, remote `origin` → GitHub above.
```

**Rule of thumb:** every change is an edit to `index.html`. There is no build step, no bundler, no framework. No CSS or JS files to import.

## How `index.html` is organized

The JS is broken up by `// ========== SECTION ==========` banners. Use them to navigate. Roughly in order:

| Approx. line | Section |
| --- | --- |
| 1–537 | `<head>` + CSS |
| 538–1061 | HTML body (tabs, modals, toolbar) |
| 1062 | PUBLISHERS — alias map for plugin vendor names |
| 1124 | STAGES — signal-chain stage taxonomy |
| 1147 | BUILT-IN PLUGINS — the seed library |
| 1256 | GENRE TOP PICKS — the ⭐ map |
| 1268 | BUSES — master / vocal / 808 / drums / fx |
| 1275 | STATE — the in-memory STATE object |
| 1295 | PERSISTENCE — `saveState`/`loadState` (key: `trapMasterState_v1`) |
| 1400 | CHAIN BUILDER |
| 1448 | PICKER (add-plugin modal) |
| 1471 | LIBRARY RENDER |
| 1602 | GENRE PICKER + per-bus preset picker |
| 1752 | CHAIN PRESETS — 808, vocal, drums, master, FX |
| 2079 | PRESET MODAL |
| 2144 | SESSION JOURNAL |
| 2227 | METER + TROUBLESHOOTER |
| 2293 | TABS |
| 2297 | SNAPSHOT EXPORT |
| 2399 | REALTIME VOICE (OpenAI WebRTC) |
| 2709 | TOOLS exposed to the model — 13 function-calling tools |
| 2812 | KNOWLEDGE BASE |
| 3131 | PLUGIN IMPORT (paste/screenshot → Claude → preview → commit) |
| 3580 | RESEARCH (Claude API + web search) |
| 3661 | AI CHAT (text-only Claude conversation) |
| 4670 | SESSION INSTRUCTIONS (system prompt for the voice model) |
| 4757 | WEBRTC + SESSION wiring |
| 4950 | COST PANEL |
| 4982 | INIT |
| 5002 | TILE PICKERS (genre + platform) |

If you're hunting for a UI element, grep its emoji/label in the HTML body block first, then jump to the matching `render*` / handler in the JS.

## State + localStorage

All user state lives in `localStorage` on the user's machine — nothing is sent to a server we control. Keys:

- `trapMasterState_v1` — chain, genre, target, favorites, custom plugins, journal, knowledge notes, user-saved chain presets, etc. (versioned suffix — bump to `_v2` only with a migration).
- `LIB_PUB_FILTER_KEY` — library publisher multi-select.
- `RT_KEY_STORAGE` — OpenAI API key (voice).
- `RT_ANT_KEY_STORAGE` — Anthropic API key (optional research/chat).
- `RT_PREFS_STORAGE` — voice tab prefs (model, voice, budget cap, etc.).
- `AICHAT_HISTORY_KEY` — text chat history (last 50 messages).
- `trapMaster_eqLayouts_v2` — Mastering Reference card order + custom user-added tiles (see Sortable section below). The `_v1` key, if present, was an earlier GridStack pilot — safe to ignore/clear.
- `trapMaster_troubleLayout_v1` — Troubleshooter (Diagnose tab) symptom pills: order + hidden built-ins + custom user-added symptoms.
- `trapMaster_voiceToolsLayout_v1` — Voice Chat Session tools cards: order + hidden built-ins + custom note tiles.
- Spend-tracker keys for OpenAI / Anthropic session + balance.

**Never** introduce server-side persistence without flagging it — the privacy promise in `README.md` is "browser only."

## Local dev

```bash
cd ~/Documents/Claude/Artifacts/trap-master-reference
python3 -m http.server 8000
# open http://localhost:8000
```

Voice chat needs a secure context — `file://` will not let Chrome touch the mic. Use `localhost`, the GitHub Pages URL, or open the artifact through the Cowork sidebar.

## Deploy flow

GitHub Pages serves `main` from this repo at the live URL above. To ship a change:

```bash
cd ~/Documents/Claude/Artifacts/trap-master-reference
git add index.html               # plus README.md / CLAUDE.md if touched
git commit -m "<short feature-focused title>"
git push origin main
```

GitHub Pages typically updates within ~1 minute. There is no staging environment.

## Commit style (from existing history)

One short imperative-ish title that names the user-visible change. Optional parenthetical with the implementation gist. Examples already in the log:

- `Voice panels breathing room + publisher alias normalisation (alias map, custom-label promotion, one-time migration, sharper Claude prompt)`
- `AI Chat: 📷 Attach screenshot on compose — drag/drop/paste, vision-aware send, inline transcript display`
- `Add Tidal -14 LUFS as 6th master target`

Don't generate verbose multi-paragraph bodies unless the change really warrants it.

## Voice tools surface (function-calling)

The Realtime model can read and mutate the workbench through these tools (defined ~line 2709):

`get_context`, `set_genre`, `set_platform`, `add_plugin_to_bus`, `remove_plugin_from_bus`, `move_plugin`, `clear_bus`, `toggle_symptom`, `list_symptoms`, `toggle_favorite`, `record_meter`, `list_plugins`, `get_library`, `clear_plugin_settings`, plus `pin_plugin_settings` / `claude_research`.

If you add UI state that should be voice-controllable, add a tool here and wire its handler in the WEBRTC + SESSION block.

## Mastering Reference (Sortable pilot — drag-to-reorder + custom tiles)

The cards on the **Mastering Reference** tab (`#eq` panel) can be dragged to reorder, and users can add their own custom tiles per section. Powered by [Sortable.js v1](https://sortablejs.github.io/Sortable/) loaded from jsdelivr — ~30 KB, no deps. This is a *pilot* — no other tabs use it yet. If it earns its keep here, the same pattern extends to other card-heavy sections (e.g. Voice Chat session tools, Plugin Library stage columns).

Deliberately scoped: **no resize, no scroll-inside-tile.** Cards size themselves to their content like normal CSS-grid items. An earlier GridStack-based attempt added resize and scroll-inside-tile and Kev didn't want either — see git history for that branch if you ever need to revisit.

How it's wired:

- Each `<div class="row-grid">` in `#eq` carries a `data-section` attribute (`freqMap`, `loudness`, `truePeak`, `stereoWidth`). One Sortable instance per section.
- The `EQGRID` namespace in the main script handles init, persistence, toggle, custom-tile add/delete, and reset.
- Init is *lazy* — fires on the first click of the Mastering Reference tab.
- Per-card IDs: built-in cards get a slug of their `<h3>` text (`Sub-bass` → `sub-bass`); custom cards get `custom-<random>` and carry a `data-tile-id` attribute.
- The `.eq-toolbar` at the top of `#eq` exposes "Customise layout" (toggles `.editing` class on each section + enables Sortable) and "Reset layouts" (clears `localStorage`, drops custom tiles, restores original order).
- In edit mode each section gains a `.eq-add-tile` placeholder at the end. Clicking it expands an inline title + body form; saving creates a new custom card.

Storage layout (`trapMaster_eqLayouts_v2`):

```json
{
  "freqMap":     {"order": ["sub-bass", "bass-body", "custom-…"], "customs": [{"id": "custom-…", "title": "230 Hz trick", "body": "Kick punch sweet spot"}]},
  "loudness":    {...},
  "truePeak":    {...},
  "stereoWidth": {...}
}
```

Fallbacks:

- If Sortable's CDN fails to load, `eqGridInit()` retries up to 20× at 250ms then logs a warning. The tab still renders — cards just stay static.
- `forceFallback: true` is on in the Sortable options — works more cleanly with the CSS-grid `.row-grid` than HTML5 native drag.

When changing the Mastering Reference HTML:

- New section → add `data-section="<key>"` to the new `.row-grid` and the key to `EQGRID.SECTIONS`.
- Renaming an existing card's `<h3>` → either update the saved order key in `localStorage` or accept that the saved order for that card resets.

## Other customisable tile sections (Troubleshooter + Voice Tools)

After the Mastering Reference pilot proved out, the same drag/hide/add pattern was extended to two more places using a generic `makeTileSection(opts)` helper in the main script. Each section registers itself once and rerenders through a callback the helper invokes.

**Troubleshooter (Diagnose tab, `#symptomGrid`):**

- Pills can be reordered, built-in pills can be hidden, custom pills can be added (label only — no body).
- Custom pill IDs are `custom-<random>` and they participate in `STATE.symptoms` exactly like built-ins (toggle on/off, included in snapshot context for Claude). The Voice AI's `list_symptoms` / `toggle_symptom` tools currently see only built-ins — extending those is a separate task.
- `renderSymptoms` was refactored to honour saved order, hidden built-ins, and custom symptoms via `getDisplaySymptoms()` / `getAllSymptomsList()`.
- Toolbar buttons: `#troubleCustomiseBtn`, `#troubleResetBtn`. Edit hint: `#troubleEditHint`.

**Voice Chat Session tools (`#voice .rt-tools-panel .rt-tools-grid`):**

- Built-in cards (Cost/min, Soft budget cap, Session breakdown, Auto-pause, Usage dashboards, History bars) can be reordered or hidden. Custom title+body note tiles can be added.
- Built-in cards are annotated with `data-tile-id` derived from their `.label` text on first init. The annotation is idempotent.
- Toolbar buttons: `#voiceToolsCustomiseBtn`, `#voiceToolsResetBtn`. Edit hint: `#voiceToolsEditHint`.

Both sections eager-init at page load (right after `renderLibrary`) so saved customs are available before the Snapshot button is clicked. The helper retries with backoff if Sortable hasn't responded yet.

## Conventions / gotchas

- **Single-file rule.** No splitting into separate JS/CSS files unless we're explicitly doing that refactor — it would change the deploy story. (The GridStack CDN is the one external dependency, intentional.)
- **Inline event handlers** (`onclick="..."`) are used heavily. Match the existing style; don't introduce a framework.
- **`escapeHtml` / `escapeJs`** helpers exist (~line 1287). Use them when injecting any string into HTML or `onclick` attributes.
- **`STATE.favorites` is a `Set`** — serialization to `localStorage` converts to/from an array; check `saveState`/`loadState` if you add new state fields.
- **`versions/`** is Cowork's auto-snapshot folder. Gitignored. Ignore for diffs and edits.
- **Storage version (`_v1`).** Adding/removing top-level state fields is fine if defaults are handled in `loadState`. Renaming or restructuring should bump the suffix and write a migration.
- **Mobile** is not a target — the layout assumes a desktop-ish width. Don't sink time into mobile polish unless asked.

## Picking up next session — quick checklist

1. `git status` and `git log --oneline -5` to see where we left off.
2. Skim recent commits for the last user-facing change in flight.
3. Check the Cowork chat transcript / session notes for the open thread.
4. If Kevin describes a UI tweak: grep the visible label in `index.html`, jump to the nearest `// ==========` banner, edit in place.
5. Always test locally with `python3 -m http.server 8000` before pushing — there's no CI.
