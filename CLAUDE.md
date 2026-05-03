# CLAUDE.md — AI Mix Masters

Project context for future Claude (or Cowork) sessions. Read this first when picking the project back up.

> **Naming history:** the project was renamed in May 2026 from *Master Mix Workbench* (and earlier *Trap Master Reference*) to **AI Mix Masters**. The GitHub repo slug `trap-master-reference` and its live URL stay unchanged for now — the rename is user-facing only.

## What this is

**AI Mix Masters** — a single-page, browser-only mixing/mastering assistant for Kevin's iLok + Waves + Native Access + Plugin Alliance library. Genre-aware plugin picks, per-bus chain builder, platform loudness targets, troubleshooter, snapshot journal, and a voice/text co-pilot powered by the OpenAI Realtime API plus (optionally) Claude with web search for niche-knowledge lookups.

> **Voice migration in flight:** the project is being migrated from OpenAI Realtime to ElevenLabs Conversational AI (Claude Sonnet 4.6 brain, Hope voice, Expressive Mode on). Work happens on the `voice-elevenlabs` branch. The OpenAI path on `main` stays as the production fallback until the new path is solid.

## ⚠️ HANDOVER POINT — read this first if you're picking up the voice-elevenlabs branch

**Last working state:** ElevenLabs Conversational AI is **working end-to-end**. Hope greets Kev in-character, voice flows both ways, system prompt is set + published in the dashboard. The basic conversation loop works.

**Where to resume:** wiring **client tools** so Hope can actually modify Kev's workbench when asked ("add Maag EQ4 to the master bus", "switch genre to drill", etc.). This is the next task. Voice without tools is just a chat — voice WITH tools is the workbench actually transformed. See the "Next task" section at the very bottom of this file for the exact step-by-step.

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

### Localstorage keys added by the migration

- `aiMixMastersElevenKey_v1` — ElevenLabs API key
- `aiMixMastersElevenAgent_v1` — Agent ID (validated to start with `agent_`)
- `aiMixMastersVoiceProvider_v1` — `'openai'` or `'elevenlabs'` (the dropdown on the Voice Chat tab)

### Files / sections to read before touching the EL code

In `index.html`:
- **`const EL_SDK_URL`** — ~line 3955. The SDK pin and the rationale comment for it. Read the comment before changing.
- **`const EL = {...}`** — the state object. Mirrors `RT` in spirit.
- **`elLoadKey / elSaveKey / elLoadAgentId / elSaveAgentId / loadVoiceProvider`** — persistence helpers.
- **`async function elStart()`** — the main connect path. Note the `EL.pendingContext` flow that injects workbench state via `sendContextualUpdate` in `onConnect`.
- **`async function elEnd() / function elCleanup()`** — disconnect + state reset.
- **`document.getElementById('rtCallBtn').addEventListener('click', ...)`** — the START CALL button now branches by `getVoiceProvider()` to pick OpenAI or ElevenLabs.

### Known good user flow

1. Kev opens `localhost:8000` (or the Cowork-served folder)
2. Voice Chat tab → Voice provider dropdown set to **ElevenLabs**
3. ElevenLabs API key + Agent ID saved (loaded from localStorage on subsequent loads)
4. Click **START CALL** → Hope greets him in her voice with Claude Sonnet 4.6 brain
5. He talks, she replies. Tools haven't been wired yet so she can't change the chain — that's the next task.

### Next task — wire client tools

ElevenLabs' SDK supports a `clientTools` parameter in `Conversation.startSession()`. It's a dict of `{ tool_name: handler_function }`. When the agent decides to call a tool, our handler runs locally in the browser and the return value goes back to the agent.

Two-part wiring:

**Part A — Register tools in the ElevenLabs agent dashboard.** Each tool needs a JSON schema describing its name, description, and parameters. The 13+ tool definitions are already written for OpenAI in the existing code (search `TOOL_DEFS` in `index.html`). They translate cleanly to ElevenLabs' format — same name, same parameter schema, slightly different wrapper.

The tools to register (names + brief purpose):
- `get_context` — read current chain, genre, target, meters, flags
- `set_genre` — switch active genre (hiphop, trap, drill, etc.)
- `set_platform` — switch loudness target (Spotify, YouTube, Tidal, etc.)
- `add_plugin_to_bus` — add a plugin to a specific bus (master / vocal / 808 / drums / fx)
- `remove_plugin_from_bus` — remove by index
- `move_plugin` — reorder
- `clear_bus` — wipe a bus
- `set_plugin_settings` — pin settings text under a plugin in the chain
- `clear_plugin_settings` — wipe pinned settings
- `toggle_symptom` / `list_symptoms` — flag/unflag mix issues from the Diagnose tab
- `toggle_favorite` — heart a plugin in the library
- `record_meter` — capture a meter reading (LUFS / TP / etc.)
- `list_plugins` / `get_library` — list / digest the plugin library
- `claude_research` — call Anthropic with web search for niche-knowledge lookups (requires Anthropic API key in the workbench)

**Part B — Wire client-side handlers in `elStart()`.** Add a `clientTools` field to the `Conversation.startSession()` call:

```js
clientTools: {
  get_context: () => buildContextSummary(),
  set_genre: ({genre}) => handleToolCall('set_genre', {genre}),
  add_plugin_to_bus: ({bus, name, position}) => handleToolCall('add_plugin_to_bus', {bus, name, position}),
  // ... and so on for every tool
}
```

The existing `handleToolCall(name, args)` function already routes to the right local handler — same one OpenAI uses. Reuse it. Most handlers return a JSON string; ElevenLabs' SDK expects either a string, number, or void return.

**Important:** the OpenAI path in `onRtEvent` parses tool-call argument JSON manually (because OpenAI streams them). ElevenLabs already passes parsed args directly to the handler. So our handler signatures might need wrapping — check `handleToolCall` to see if it expects already-parsed objects (it does — the parsing happens in `onRtEvent` before calling).

### Other in-flight work (not yet started)

- **Profile system (Task #89).** Cross-conversation memory. STATE.profile blob in localStorage, Haiku-extracts learnings at call end, injected via sendContextualUpdate at session start, visible editor UI in Voice Chat tab, JSON synced to repo for cross-machine portability. Build AFTER tools are working.
- **Cost tracking (Task #91).** Pull minute-cost from `/v1/convai/conversations/{conversation_id}` after disconnect, stream into the spend panel.

### Non-obvious gotchas

- **`.git/index.lock` permission issue** — Kev runs git commands in his real Terminal, not via the agent. Don't try to commit/push from inside Claude — generate the commands and have him paste them.
- **Free tier** — Conversational AI requires Creator plan ($22/mo). Kev is now on Creator. Don't suggest free tier for testing — it'll silently fail.
- **Mic permission** — never call `navigator.mediaDevices.getUserMedia()` before `Conversation.startSession()`. The SDK acquires the mic itself; pre-acquiring it causes the SDK to fail silently and you get a 30s "Successful, 0 messages" timeout pattern in the Conversations log. We learned this the hard way.
- **System prompt override** — toggle in the agent's Security → Overrides is ON, but the server still rejects the override. Don't waste time re-debugging this; we use `sendContextualUpdate` instead.
- **Drafts vs Live** — agent dashboard changes show as "Draft" until you click **Publish** in the top-right corner of the agent page. Without publishing, the live agent still uses the previous config. Burned an hour on this when Hope wasn't applying.

- Live: <https://begb0037admin.github.io/trap-master-reference/>
- Repo: <https://github.com/begb0037admin/trap-master-reference> (branch `main` is what GitHub Pages serves)
- Local source: `~/Documents/Claude/Artifacts/trap-master-reference/`

## File layout

```
trap-master-reference/
├── index.html      ← THE app. ~5,100 lines, ~312 KB. Single-file: HTML + CSS + vanilla JS, all inline.
├── README.md       ← User-facing readme (setup, voice chat keys, what's in it).
├── CLAUDE.md       ← This file.
├── .gitignore      ← Ignores macOS junk, editor folders, secrets, and versions/.
├── versions/       ← Cowork's local artifact history. Gitignored — do NOT commit, do NOT touch.
└── .git/           ← Standard git repo, remote `origin` → GitHub above.
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
