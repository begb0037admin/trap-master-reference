# Trap Master Reference

A trap / hip-hop mixing and mastering workbench — live genre-aware plugin picks, meter targets, a troubleshooter, and a voice-chat mastering assistant powered by OpenAI's Realtime API and (optionally) Claude with live web search for niche knowledge lookups.

🔗 **Live demo**: <https://begb0037admin.github.io/trap-master-reference/>

Built as a single-file HTML app. No build step, no backend. Your state (chains, notes, favorites, API keys) lives in your browser's localStorage.

## Quick start (local)

```bash
python3 -m http.server 8000
```

then open <http://localhost:8000> in Chrome or Safari.

Or use the hosted version on GitHub Pages — link at the top of this repo's description once it's enabled.

## Voice chat setup

1. Sign up at <https://platform.openai.com> and add a few dollars of pay-as-you-go credit.
2. Create an API key at <https://platform.openai.com/api-keys> — starts with `sk-`.
3. In the app, open the **Voice Chat** tab, paste the key, hit **Save**.
4. Hit the big **Start call** button. The browser will ask for mic permission once.

The key is stored only in your browser. It's never uploaded anywhere except directly to OpenAI when you start a call.

Default model is `gpt-4o-mini-realtime-preview` (cheap but a bit dumb). Switch the Voice model dropdown to `gpt-4o-realtime-preview` for better accuracy — roughly 10× the cost per minute, still pennies for a short session.

### Optional: Anthropic key for the research tool

The voice model is fast and conversational but its knowledge of niche producer techniques (specific engineers, plugin parameters, current 2024–2026 trends) is shaky and it tends to bluff. To fix that, paste a Claude API key (`sk-ant-…`) into the second key field. When the voice AI is about to bluff on something niche, it'll instead call Claude with live web search, get a grounded answer with citations, and read it back to you. Adds ~2–4s of "hold on, let me check…" but kills the hallucinations.

Get a key at <https://console.anthropic.com> → Settings → API Keys → Create. ~$5 in credits is plenty to start. Pick the research model in the dropdown — Sonnet 4.6 is the balanced default; Opus 4.6 if you want maximum smart.

## What's in it

- **450+ plugin library**: Waves, iZotope, UA, Softube, SSL Native, Plugin Alliance, Native Instruments, Sonnox, Slate, Eiosis, oeksound, Soundtoys, Antares, Celemony, LiquidSonics, and more.
- **Genre presets**: trap, drill, UK drill, phonk, rage, cloud, Memphis, Jersey club, hyperpop, boom bap.
- **Per-bus chains** (master / vocal / 808 / drums / FX) with inline settings notes that stick to each plugin.
- **Platform loudness targets**: club-loud, Spotify, Apple Music, SoundCloud.
- **Troubleshooter**: flag symptoms (harsh hats, muddy 808, pumping, etc.), get recipe chains.
- **Voice AI** that can read your workbench state, add/remove plugins, switch genre, flag issues, and pin settings to plugins via function calling.
- **Deep research** (with an Anthropic key): voice model delegates niche / knowledge-heavy questions to Claude with live web search instead of bluffing.

## Collaboration

Every user has their own local state. To share work:

- **Snapshot** (top right) copies the whole workbench as markdown — paste into Slack, email, Notion.
- Import/export of session state is planned.

For live collaboration (multiple people on the same workbench at once) a small backend would be needed — not there yet.

## Privacy

- API key: browser localStorage only.
- Voice audio: browser ↔ OpenAI direct, via WebRTC.
- State: browser localStorage only.
- Nothing is sent to any server run by the repo author.

## Stack

- Single-file HTML + vanilla JS + CSS. No frameworks.
- OpenAI Realtime API (WebRTC + data channel) for voice.
- 13 function-calling tools expose workbench state to the model.

## License

Private / personal — add your own license if you fork it.
