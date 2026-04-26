# CLAUDE.md — Trap Master Reference

Project context for future Claude (or Cowork) sessions. Read this first when picking the project back up.

## What this is

**Master Mix Workbench** — a single-page, browser-only mixing/mastering assistant for Kevin's iLok + Waves + Native Access + Plugin Alliance library. Genre-aware plugin picks, per-bus chain builder, platform loudness targets, troubleshooter, snapshot journal, and a voice/text co-pilot powered by the OpenAI Realtime API plus (optionally) Claude with web search for niche-knowledge lookups.

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

- `trapMasterState_v1` — chain, genre, target, favorites, custom plugins, journal, knowledge notes, etc. (versioned suffix — bump to `_v2` only with a migration).
- `LIB_PUB_FILTER_KEY` — library publisher multi-select.
- `RT_KEY_STORAGE` — OpenAI API key (voice).
- `RT_ANT_KEY_STORAGE` — Anthropic API key (optional research/chat).
- `RT_PREFS_STORAGE` — voice tab prefs (model, voice, budget cap, etc.).
- `AICHAT_HISTORY_KEY` — text chat history (last 50 messages).
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

## Conventions / gotchas

- **Single-file rule.** No splitting into separate JS/CSS files unless we're explicitly doing that refactor — it would change the deploy story.
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
