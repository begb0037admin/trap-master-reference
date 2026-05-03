# CLAUDE.md — AI Mix Masters

Project context for future Claude (or Cowork) sessions. Read this first when picking the project back up.

> **Naming history:** the project was renamed in May 2026 from *Master Mix Workbench* (and earlier *Trap Master Reference*) to **AI Mix Masters**. The GitHub repo slug `trap-master-reference` and its live URL stay unchanged for now — the rename is user-facing only.

## What this is

**AI Mix Masters** — a single-page, browser-only mixing/mastering assistant for Kevin's iLok + Waves + Native Access + Plugin Alliance library. Genre-aware plugin picks, per-bus chain builder, platform loudness targets, troubleshooter, snapshot journal, and a voice/text co-pilot powered by the OpenAI Realtime API plus (optionally) Claude with web search for niche-knowledge lookups.

> **Voice migration in flight:** the project is being migrated from OpenAI Realtime to ElevenLabs Conversational AI (Claude Sonnet 4.6 brain, Hope voice, Expressive Mode on). Work happens on the `voice-elevenlabs` branch. The OpenAI path on `main` stays as the production fallback until the new path is solid.

## ⚠️ HANDOVER POINT — read this first if you're picking up the voice-elevenlabs branch

**Last working state (as of session ending May 2026):** ElevenLabs Conversational AI is fully working end-to-end. All 25 client tools registered + wired, profile system (cross-conversation memory) landed, dual-provider overlap bug fixed. Hope can read his chain, change genre, add/remove plugins, edit knowledge notes, etc. live during a call. Tools fire, workbench updates in real time, and the profile blob auto-extracts via Haiku at end-of-call so she remembers his preferences across sessions.

**Where to resume — full single-vendor consolidation (OpenAI → ElevenLabs).**

Kev decided he doesn't want to use OpenAI any more. The Voice Chat tab still has the dual-provider plumbing from the migration phase (provider dropdown, OpenAI Realtime path, OpenAI cost card). He wants ALL of that ripped out and replaced with ElevenLabs equivalents. We confirmed via web research that:

- **STT:** ElevenLabs Scribe v2 batch transcription is $0.22/hr ≈ $0.0037/min — about 40% cheaper than OpenAI Whisper ($0.36/hr). Same use case (POST audio, get text back). Perfect for the AI Chat dictation flow that currently uses Whisper.
- **TTS:** ElevenLabs has their own TTS API (it's their core product). Replaces the OpenAI TTS dropdown on the AI Chat "Read aloud" feature.
- **LLM-side voice:** Already on ElevenLabs Conversational AI with Claude Sonnet 4.6 brain. Done.

This is staged into **four batches** so each can ship + test independently. Important: don't delete the OpenAI code paths (rtStart, RT state, MIC_SVG_FLOAT, etc.) — Kev wants them dormant in the file as a "back pocket" if he ever needs to re-enable. Just unwire from the UI.

#### Batch 1 — UI sweep on Voice Chat tab

- Remove the **provider dropdown** (`#voiceProvider`) and its label / help text. Voice Chat is ElevenLabs-only now.
- Remove the **OpenAI API key field + Save / Show / Clear buttons** from the Voice Chat tab. The `RT_KEY_STORAGE` localStorage key can stay (legacy data), but the UI is gone.
- Remove the **voice model dropdown** (`#rtModel`) and **OpenAI Voice dropdown** (`#rtVoice`) — both are OpenAI Realtime concerns.
- The Anthropic API key field STAYS — it powers Claude research, profile extraction, AI Chat itself. Move/relabel as needed but keep it functional.
- The Mic-mode toggle (PTT / Always-on) on the Voice Chat tab can stay or go — EL's SDK runs always-on so PTT is a no-op for it. Suggest hiding it on Voice Chat (chain/library/eq/knowledge tabs still use it for the OpenAI path which won't run any more anyway, so the chain-toolbar pill becomes vestigial too — hide everywhere).
- Update the rtCallBtn click handler: drop the provider check, just call `elStart` / `elEnd`. Same for `micStartFromFloat`, the float-mic mouse handlers, and the spacebar handler — drop all the `getVoiceProvider()` branching, route everything to EL.
- Update the title-bar "How it works" tip-box copy on the Voice Chat tab — currently mentions "your API key talks to OpenAI's Realtime API directly". Rewrite for EL (mentions Hope, Claude Sonnet 4.6 brain, etc.).

Files to touch: `index.html` only. No external deps to add.

#### Batch 2 — AI Chat dictation: Whisper → Scribe v2

The DICT module (search `// DICTATION (DICT)` in index.html) currently calls `https://api.openai.com/v1/audio/transcriptions` with `model: 'whisper-1'`. Migrate to `https://api.elevenlabs.io/v1/speech-to-text` with the appropriate Scribe model id (web-fetch the docs to confirm — last known: `scribe_v1` or `scribe_v2`, multipart form-data with `file` and `model_id`, returns JSON with `.text`).

- Same MediaRecorder capture path; just swap the fetch target + auth header (`xi-api-key` instead of `Authorization: Bearer`).
- Use the existing `aiMixMastersElevenKey_v1` key (already saved on every call setup). Drop the `RT_KEY_STORAGE` check.
- Web Speech API stays as the no-key fallback. PTT vs always-on logic on the AI Chat tab is unchanged.
- Roll the cost into a new `addSpend('elevenlabs', cost)` bucket — see Batch 4.
- Update the prompt-priming context (the "Pultec, FabFilter, Soothe2..." plugin-name dictionary) — Scribe likely takes this as a `language_code` or `prompt` field; check the API.

#### Batch 3 — AI Chat "Read aloud": OpenAI TTS → ElevenLabs TTS

The TTS module (search `aichatSpeak` / `aichatTtsAudioEl` in index.html) currently posts to `https://api.openai.com/v1/audio/speech` with `model: 'tts-1' | 'tts-1-hd' | 'gpt-4o-mini-tts'` and a `voice` from the OpenAI voice list (alloy, ash, ballad, etc.). Migrate to:

- Endpoint: `https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` (or the streaming variant if word-level highlighting needs it)
- Auth: `xi-api-key` header
- Body: `{text, model_id, voice_settings}` — model probably `eleven_multilingual_v2` or `eleven_turbo_v2_5` for cheaper
- Replace the voice dropdown options on the AI Chat toolbar with ElevenLabs voice IDs. Suggest defaulting to Hope (`WAhoMTNdLdMoq1j3wf3I`) so Read aloud sounds like Hope mid-conversation. Add a few other ElevenLabs library voices for variety.
- Word-level TTS highlight (`aichatTtsHighlightTick`, `aichatInstallWordSpans`) currently sweeps through tokenised words at audio playback time — this should still work as long as the new audio source plays in the same `<audio>` element. The highlight algorithm doesn't depend on per-word timestamps.
- Roll cost into the EL spend bucket.

#### Batch 4 — Cost panel rewire (the originally-deferred follow-up)

Replace the OpenAI cost card on the Voice Chat tab with an ElevenLabs cost card. Three sources of EL spend now:

1. **Conversational AI minutes** — pull from `GET /v1/convai/conversations/{conversationId}` after each `onDisconnect` fires. Response includes `metadata.charging.minutes_used` (or similar — verify with a real call). Kev's on Creator plan: $22/mo / 250 min ≈ $0.088/min. Live during the call: estimate from `EL.startedAt` * rate; reconcile after disconnect with the API's exact number.
2. **Scribe v2 dictation** — count duration of each MediaRecorder capture, multiply by $0.0037/min.
3. **TTS** — ElevenLabs bills per character; each Read-aloud call multiplies the text length × rate (~$0.30/1000 chars on Creator plan; verify).

UI side:
- Rename the `oaSession` / `oaBalance` / `oaSpent` / `oaLeft` element IDs and all references to neutral / EL names. Keep `aiMixMastersSpendOpenAI_v1` legacy key for archive purposes but use a fresh `aiMixMastersSpendEleven_v1` for new spend.
- The `cpmValue` "cost / minute" tile — point at the EL minute rate.
- The Anthropic side of the panel stays exactly as-is.
- Add a small "Update balance" button that pulls the user's remaining ElevenLabs subscription minutes via `GET /v1/user/subscription` so Kev can see plan headroom.

Files to touch: `index.html`. New helper: `elFetchConversationCost(conversationId)`. Hook into `onDisconnect` after `maybeExtractProfile()` (don't block one on the other).

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

10. **Dual-provider overlap fix.** Earlier the float mic and spacebar always called `rtStart` regardless of the provider dropdown — so pressing PTT while Hope was running started a parallel OpenAI session and both providers played audio into the shared `#rtAudio` element. Five surgical fixes landed: `micStartFromFloat` branches by provider, `rtStart` and `elStart` defensively cross-end any other-provider session at top, the rtCallBtn handler ends ANY active session (not just the matching-provider one), and the float-mic + spacebar handlers became EL-aware (mousedown is a no-op when EL is active; mouseup ends the call; spacebar tap toggles EL start/end since it has no PTT semantics). All this is moot once Batch 1 above ships and removes the dropdown — but the cross-end guards in `rtStart`/`elStart` should stay as belt-and-braces.

### Localstorage keys added by the migration

- `aiMixMastersElevenKey_v1` — ElevenLabs API key
- `aiMixMastersElevenAgent_v1` — Agent ID (validated to start with `agent_`)
- `aiMixMastersVoiceProvider_v1` — `'openai'` or `'elevenlabs'` (the dropdown on the Voice Chat tab)

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
- **DICTATION (DICT) module** — search `// DICTATION (DICT)`. Currently uses Whisper. Batch 2 swaps to Scribe.
- **AI Chat TTS** — search `aichatSpeak`. Currently OpenAI TTS. Batch 3 swaps to ElevenLabs TTS.

### Known good user flow

1. `python3 -m http.server 8000` from the repo root → open <http://localhost:8000>.
2. Voice Chat tab → ElevenLabs API key + Agent ID saved (loaded from localStorage on subsequent loads). The provider dropdown still exists (until Batch 1 lands) and should be set to **ElevenLabs** — but the agent will refuse to call OpenAI Realtime now anyway since we're not maintaining that path.
3. Click **START CALL** → Hope greets him in her voice with Claude Sonnet 4.6 brain.
4. Try voice tool calls: "what's on my master bus?", "add Maag EQ4 to the master", "switch genre to trap" — workbench updates in real time, DevTools console logs `[EL tool] <name> <args> → <result>` for every call.
5. End the call → Haiku extracts profile updates (if Anthropic key saved + transcript >200 chars). The `#profileText` panel updates with new lines. Next call she remembers.

### Open follow-ups

The OpenAI removal is the active scope (4 batches in the HANDOVER POINT section above). Beyond that, no other open threads.

### Non-obvious gotchas

- **`.git/index.lock` permission issue** — Kev runs git commands in his real Terminal, not via the agent. Don't try to commit/push from inside Claude — generate the commands and have him paste them.
- **Free tier** — Conversational AI requires Creator plan ($22/mo). Kev is now on Creator. Don't suggest free tier for testing — it'll silently fail.
- **Mic permission** — never call `navigator.mediaDevices.getUserMedia()` before `Conversation.startSession()`. The SDK acquires the mic itself; pre-acquiring it causes the SDK to fail silently and you get a 30s "Successful, 0 messages" timeout pattern in the Conversations log. We learned this the hard way.
- **System prompt override** — toggle in the agent's Security → Overrides is ON, but the server still rejects the override. Don't waste time re-debugging this; we use `sendContextualUpdate` instead.
- **Drafts vs Live** — agent dashboard changes show as "Draft" until you click **Publish** in the top-right corner of the agent page. Without publishing, the live agent still uses the previous config. Burned an hour on this when Hope wasn't applying. Note: the `register_elevenlabs_tools.py` script's PATCH appears to auto-publish (Publish button stays greyed after running it).
- **Tool schema strictness** — ElevenLabs' tool-create endpoint requires every leaf parameter to declare a `description` (or `dynamic_variable` / `is_system_provided` / `constant_value`). This applies to enum-only fields, primitives like `{type:"integer"}`, AND array `items` schemas. Our `TOOL_DEFS` in `index.html` omits descriptions on those because OpenAI doesn't need them, so the Python register script normalises before POSTing — see `ensure_param_descriptions`.
- **Tool registration is per-workspace, not per-agent** — `POST /v1/convai/tools` creates tools in the workspace; the agent then references them by ID via `prompt.tool_ids`. Re-running the register script creates fresh tool entries; old ones become orphans that need manual cleanup from the dashboard's Tools list. Don't run the script casually.

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
