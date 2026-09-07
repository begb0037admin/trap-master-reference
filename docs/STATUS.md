# STATUS.md — AIMM

**2026-09-07 update, corridor-comparison architectural fix (Cat) — Backlog 22 (Multi-stem Mix
Check) requirement 3 refinement.** Kevin found a real architectural gap: dropping a solo bass stem
into Mix Check compared it against the FULL-MIX genre corridor, producing meaningless numbers
("your low end is forty one dB over") since a bass-only signal has no highs by design — the
corridor didn't know it was looking at an isolated stem rather than a full mix. Went with Kevin's
explicitly chosen simpler option (of the two he offered): when a multi-stem session has been
narrowed to exactly one currently-audible stem, SUPPRESS the corridor comparison and say so
honestly, rather than inventing a stem-specific reference target (a fabricated "what a solo bass
stem should look like" target would be just as misleading as the wrong-target comparison it
replaces). `index.html` untouched — `docs/mockups/multistem-mixcheck-final.html` only, build bumped
to `2026-09-07.4`.

**Exact detection condition** — a new shared accessor `window.__mcSingleStemIsolated()` (added
inside the existing multi-stem IIFE, exported as `window.mcCorridorSuppressed()` for external
callers) returns true only when BOTH: (a) more than one stem was EVER loaded into the session
(`stems.length > 1` — counts every stem dropped in, including ones later excluded for a
sample-rate/length mismatch, so a 2-stem session where one failed validation still counts as
"attempted multi-stem", not an ordinary single-file load — a real edge case Codex's TP1 review
caught, see below), AND (b) exactly one of the non-mismatched stems is currently audible
(`eligibleStems().filter(s=>!effectiveMuted(s)).length === 1`, using the SAME
`eligibleStems()`/`effectiveMuted()` logic `runAnalysisSync()` itself uses, so "suppressed here" can
never disagree with "audible for analysis"). Deliberately returns **false** (corridor stays
meaningful, unaffected) for: an ordinary single-file load (no stems array populated at all) and a
degenerate one-stem-total session (nothing was ever loaded alongside it) — matching Kevin's own
framing that a single loaded "stem" IS the full file the corridor was designed for. Mute-down-to-one
and solo-one are treated identically (both produce `audible.length === 1`), confirmed by direct
test.

**What's suppressed vs. shown when isolated** — three surfaces gated on the same flag: (1) the
visible Spectral Balance Low/Mid/High corridor-deviation cards (`ozPopulateBands()`) show `N/A ·
isolated stem` instead of a computed dB delta, plus a new visible banner
(`#mcCorridorNote`, "Corridor comparison needs the full mix (or multiple stems) — showing raw
spectrum only") — the raw spectral CURVE canvas itself is left completely untouched, still drawing
the real measured curve; (2) the Fix Queue's per-band corridor-delta signal group
(`MC_FIXQUEUE.build()`, titled e.g. "Low end +X dB vs corridor") is skipped entirely — zero
corridor-based items generated; (3) Hope's context feed (`breakdownData().tonalBalanceDeltas`
nulled + new `tonalBalanceSuppressed` flag, consumed by both `buildMixCheckContextBlock()`'s "MIX
CHECK — LIVE STATE" block and the real Claude-API prompt that generates Hope's spoken "read") says
the comparison isn't meaningful right now instead of reciting fabricated or blank numbers.
Deliberately UNCHANGED: LUFS/true peak/PLR/correlation/crest (Audio Specs) — all computed directly
from the combined audible buffer with zero corridor involvement — and the Fix Queue's other signal
groups (true peak/PLR/correlation/loudness direct-measure signals, plus the ratio-based sub/air-band
heuristics like "muddy"/"808"/"harsh", which use fixed thresholds rather than a corridor
comparison) — the brief scoped suppression strictly to "corridor-comparison claims", and these
remain valid measurements of whatever's currently audible.

**Codex three-touchpoint review, mandatory per agent-commons policy:**
- **TP1 (plan)** — reviewed the exact detection condition + what gets suppressed before writing
  code. Flagged one real edge case (see (a) above — using `eligibleStems().length` instead of
  `stems.length` would have misclassified a multi-stem session where all-but-one stem failed
  validation as an ordinary single-file load); confirmed leaving the ratio-based Fix Queue signals
  untouched was the correct scope boundary per the brief.
- **TP2 (diff)** — found and fixed one real bug: the "N/A — isolated stem" tag text was written into
  `#ozBand*Tag`, an element permanently `display:none` in this redesign (status is conveyed via the
  fill bar, not the tag) — so the explanation was silently invisible, leaving only a bare dash on
  screen. Fixed by moving the explanation into `.oz-band-val` itself (genuinely visible). Also
  flagged a defensive-consistency nit (two call sites used `window.__mcSingleStemIsolated()`
  directly instead of the guarded `mcCorridorSuppressed()` wrapper) — fixed for consistency across
  all three gated surfaces.
- **TP3 (real headless-Chrome, Playwright)** — synthetic 3-stem session (60/90 Hz "Bass", 150/3000 Hz
  "Drums", 300/700 Hz "Vocals") driven via `window.mcHandleFiles()` + real solo/mute button clicks.
  Confirmed: full mix shows real corridor numbers + corridor Fix Queue items, note hidden; soloing
  Bass suppresses corridor cards (now visibly "N/A · isolated stem"), shows the banner, drops
  corridor Fix Queue items while keeping LUFS/PLR items, and LUFS/true peak read real numbers for the
  isolated stem (-16.2 LUFS / -10.9 dBTP, distinct from the full-mix numbers); un-soloing back to
  full mix resumes corridor comparison with the exact same numbers as before; mute-down-to-one
  (no solo) produces identical suppression to solo-one, confirming the two are treated the same;
  all-muted (unrelated pre-existing edge case, zero stems audible) correctly does NOT trigger
  suppression — out of scope either way; the ordinary single-file-loaded case (`stemCount:0`, never
  entered stem mode at all — `mcHandleFiles` degenerate-case path) was explicitly re-tested and
  confirmed corridor comparison still works completely normally, unaffected by this fix.

**2026-09-07 update, second correctness-bug pass (Cat) — Backlog 22 (Multi-stem Mix Check):
five issues found and fixed on `docs/mockups/multistem-mixcheck-final.html`, routed by Jules.**
Kevin re-tested with 6 real WAV files after the stem-classifier fix (below) and reported two
concrete bugs from a screenshot; Jules folded in three more real gaps mid-pass (immediate-draw
timing, the colour scheme never actually being applied, and Hope having zero stem awareness).
`index.html` untouched throughout — mockup-only. Full Codex three-touchpoint review on all five.

1. **Per-stem waveforms were completely blank.** Root cause, confirmed with real headless-Chrome
   instrumentation (temporary console.log probes in `smDraw()`/`mcDrawStemRows()`, real synthetic
   stereo WAV stems loaded via `#refFileInput`, live DOM ancestor-chain dump at the exact moment
   the draw call returned early): the whole `#mcStemStack` tree lives inside `#refDzLoaded`, which
   is `display:none` until something adds `.visible` to it. That reveal only ever happened inside
   `window.refLoadFile()` (the single-file path), and for the multi-stem path `refLoadFile()` is
   only invoked ASYNCHRONOUSLY and LATER — via `scheduleAnalysisSync() -> runAnalysisSync() ->
   await window.refLoadFile(wavFile)` (the synthesized down-mixed analysis file). `mcEnterStemMode()`
   calls `mcRenderStemRows()` (which draws every stem canvas) synchronously and immediately, well
   before that async reveal — so every canvas measured 0×0 at draw time, `smDraw()`'s
   `if(!cw||!ch) return;` guard silently fired, and nothing ever re-triggered a redraw until a
   later transport action (play/pause/seek) happened to fire after the reveal had finally landed.
   Measured directly: initial draw call logged `cw=0,ch=0` with `#refDzLoaded` computed
   `display:none`; a later draw call (post-reveal) produced non-blank canvas pixel data.
   **Fix:** added `window.__mcRevealTransport()` — the same three DOM writes `refLoadFile()` always
   did, now shared and called SYNCHRONOUSLY at the top of `mcEnterStemMode()`, before any row is
   rendered/drawn — plus a defensive extra `mcDrawStemRows()` call at the end of
   `runAnalysisSync()`'s success branch as a cheap, idempotent second-chance repaint. This also
   satisfies Kevin's separate, previously-missed requirement that waveforms render immediately once
   stems are decoded, not wait for Play.

2. **Stem rows with the same guessed category were visually identical.** Root cause, confirmed by
   reading the code: `mcHandleFiles()`'s `stems.push({..., label: stemBaseName(f.name), ...})`
   initially stored the real filename in `label`, but the immediately-following classification loop
   unconditionally overwrote it (`s.label=guess.label`), permanently discarding it — nothing else on
   the stem object retained it, and the row template only ever rendered `label` + a "guessed" badge.
   With 3 stems guessed "Other" and 2 "Bass" (Kevin's screenshot), those rows became text-for-text
   identical. **Fix:** added an immutable `fileName` field captured once at push time (never touched
   by classification or rename), rendered in the row head ahead of the existing editable
   content-guessed label + badge, reusing the app's existing muted small-mono `.tp-file` filename
   styling (used for the single main loaded file's name) with a row-local override
   (`.mc-stem-file{min-width:0;flex-shrink:1;max-width:130px}`) so long names still fit.

3. **Colour scheme was never actually applied.** Kevin's words: "I want the waves in our colour...
   complete wave and as played they turn Orange." `smDraw()` previously stroked the WHOLE unplayed
   span in flat grey and only the played span in the app's blue->purple `--send-blue` gradient — the
   opposite of what was asked, and never implemented at all despite being in the original brief.
   **Fix:** inverted for these NEW per-stem rows only (the real locked `#mcWave` transport canvas is
   untouched — `smDraw()` is a fully separate function from `MC_WAVE.draw()`): the full/unplayed
   span now renders in the blue->purple gradient (`#2fa1e6`->`#a557f4`, spanning the whole canvas
   width) and the played span (behind the playhead) switches to the app's existing faded-orange
   gradient (`#fdba74`->`#f97316`, reused verbatim from `.aichat-msg.fixaction .fa-mini i`).
   Verified with real per-pixel colour sampling across the canvas width, before and during playback.

4. **Hope had zero stem awareness.** Kevin tested it and Hope answered "bounce a stem down and drop
   it in separately" as if only a single rendered mix file was loaded — a dropped requirement from
   the original brief (req 4: "Hope must be aware of stem state at all times... never ask, she
   already knows"). Root cause: the Hope rail's text chat (`aichatSend()`, a REAL Claude API call,
   not scripted text) builds its system-prompt context via `buildMixCheckContextBlock()`, which only
   ever described `buildMixCheckState()`'s single `file_name` — nothing in it ever asked the
   multi-stem module (whose `stems` array is private to its own IIFE closure) whether stems were
   loaded at all. **Fix:** added `window.__mcStemsForHope()`, a real (non-debug) accessor bridging
   the closure, and wove its output into `buildMixCheckContextBlock()` — stem list, guessed/renamed
   labels, and accurate mute/solo/audible state, woven in ahead of the existing Fix Queue section.
   Scoped as content/context-string changes only — explicitly not new ElevenLabs/RT_INSTRUCTIONS/
   TOOL_DEFS wiring, so this stayed with Cat rather than routing to Markey.
   **Codex TP2 caught two real follow-on bugs, both fixed and re-verified:** (a) a stale-analysis
   exposure — muting/soloing/adding/removing a stem bumps the async re-analysis but the OLD Fix
   Queue/loudness numbers stayed visible with no indication they didn't match the new stem
   combination yet; fixed with `window.__mcAnalysisStale()` (an `analysisSeq` vs
   `lastCompletedAnalysisSeq` tracker) which now suppresses stale numbers behind an explicit
   "re-running after a stem change" note. (b) a soloed-AND-muted stem displayed as `[SOLO, muted]`
   even though solo overrides mute and the stem is actually audible; fixed to read
   "mute requested but overridden by solo — still audible", based on the same `effectiveMuted()`
   logic already used for playback.

Codex three-touchpoint summary for this pass: TP1 (plan, before code) confirmed the bug-1 root
cause against the actual `mcEnterStemMode()`/`refLoadFile()`/`runAnalysisSync()` code and the fix
location, flagged an existing-but-separate async race (stems cleared mid-analysis) as a hardening
note (not required for this scope), and confirmed bug-2 + the colour plan. TP2 (diff review) found
the two real follow-on bugs described above (stale analysis exposure, solo/mute display) — both
fixed before TP3. TP3 (real headless Chrome, Playwright + a real Chrome binary, 6 real synthetic
stereo WAV stems — kick/bass/vocal/guitar/pad/fx, deliberately producing 3 "Bass" + 3 "Vocals"
duplicate-category guesses to reproduce the original "3 identical Other rows" scenario): confirmed
all 6 rows show real non-blank waveform pixel content the instant stems finish decoding (before any
Play click); confirmed all 6 rows show a distinguishing filename alongside the guessed-category
badge, with same-category rows fully distinguishable; confirmed real per-pixel colour sampling
matches the blue->purple (unplayed) / orange (played) split exactly, both before playback (100%
blue->purple) and mid-playback (orange up to the playhead, blue->purple after it); confirmed
`buildMixCheckContextBlock()` (the actual string fed into both the elStart voice path and the
aichatSend text-chat path) correctly lists all 6 stems with accurate labels and updates mute/solo
state live, including the stale-analysis and solo-overrides-mute corrections. Zero console
`pageerror`s across the full run.

---

**2026-09-07 update, correctness-bug pass (Cat) — Backlog 22 (Multi-stem Mix Check): real
stem-classifier bug found and fixed, routed by Jules.** Kevin tested the final-brief build
(commit `755e68b`) and reported: "vocals appear as drums - we need to fix this - every track is
completely off." Real DSP debugging, not a threshold re-tune — full Codex three-touchpoint review.

**Root cause, proven with real headless-Chrome numbers, not self-report.** `classifyStem()`'s
stereo-to-mono downmix (`mono()`) fed a signal into the FFT whose every sample's magnitude came
from the correct energy formula `sqrt((L^2+R^2)/2)` but whose SIGN was an arbitrary global choice
based on `(l+r)`'s sign — the code's own comment claimed this was "harmless… magnitude-only," which
was false. Whenever L and R aren't in phase (true of nearly every real stereo stem — reverb, delay,
chorus, stereo width, all normal on a vocal stem exported from a DAW), this produces a
rectification-like artifact that fabricates broadband harmonic content not present in either
channel, inflating spectral flatness specifically. Measured directly: a formant-shaped, sung-melody
synthetic "vocals" test signal (mono) measured flatness ≈0.066 (correctly reads as tonal, well under
the 0.30 Vocals ceiling); the identical vocal content, unchanged, with a realistic 3-tap reverb tail
added to the right channel only, measured flatness 0.33–0.43 through the old downmix — enough to
cross out of the Vocals bucket entirely and, depending on the exact reverb/onset shape, all the way
past the 0.35 Drums floor too, even with `midRatio` still ≈0.6–0.86 (clearly vocal-formant-dominant).
This directly reproduces "vocals reads as drums / every track is completely off" — since almost
every real-world stereo stem carries some width/reverb, this wasn't an edge case.

**Fix:** `classifyStem()` no longer downmixes time-domain samples before the FFT. It now FFTs each
channel separately (same Hann window) and sums squared magnitude per bin across channels — a
phase-safe combination that can neither fabricate harmonics (the bug) nor destructively cancel
out-of-phase content (the original, valid concern the old sign-hack was trying, incorrectly, to
solve). `mono()` was renamed `monoEnergy()` and kept only for the RMS/onset envelope, where sign is
provably irrelevant (RMS squares the sample). Mono-file behaviour is unchanged. Real headless-Chrome
verification (Playwright + a real Chrome binary, same 4 realistic stereo synthetic stems, before
`git HEAD` vs after the fix): Drums/Bass/Other all still correctly classified both before and after;
Vocals went from misclassified (`Other`, flatness 0.356) to correctly `Vocals` (flatness 0.066),
`midRatio` unchanged (≈0.87, always clearly vocal) proving the fix touched only the fabricated
metric, not the real signal content. Codex TP1 (plan, before code) flagged the `mono()` sign bug on
inspection before any instrumentation ran; Codex TP2 (diff review) approved with two minor
follow-ups applied (`Float64Array` for the power-spectrum accumulator to preserve the original
double-precision accuracy; `channels` debug field now reads `buf.numberOfChannels` directly).

**Also confirmed, not fixed (honest limitation, not a bug):** an extreme synthetic test where a
"vocal" signal's energy was deliberately ~80% broadband noise (a far heavier sibilant/consonant
ratio than any real singing voice) still reads as Drums even post-fix (`flatness` 0.43,
`transientsPerSec` 3.5) — a stem that's mostly noise-transient energy genuinely does resemble
percussive content on this feature set. This matches the classifier's existing disclosed limitation
in the section below (tonal-vs-percussive ambiguity is a real heuristic ceiling, not a coding error)
and is not something this fix should chase further — badged "guessed," click-to-rename remains the
correction path.

Instrumentation added (all additive, no decision-logic change): `classifyStem()`'s return now also
carries `activeWindows`, `framesCounted`, `onsets` (split into `silenceOnsets`/`jumpOnsets`),
`analyzedSec`, `sampleRate`, `channels`; `window.__mcDebug.classifyStem` exposes the real function
for future headless-Chrome verification without needing file drag/drop. `AIMM_BUILD` bumped to
`2026-09-07.3`.

---

**2026-09-07 update, final pass (Jules) — Backlog 22 (Multi-stem Mix Check): final agreed brief,
SUPERSEDES `multistem-mixcheck.html`, `multistem-mixcheck-in-context.html`, and
`multistem-mixcheck-minimal.html` for review purposes.** After an extensive live design discussion,
Kevin gave a complete final brief covering all remaining open questions on this feature (the exact
continuous-sync-while-muted playback model, content-based stem labelling instead of filenames,
Snapshot integration, and a hard "never concatenate filenames in the header" rule after the earlier
concatenated-header bug). One-line reason each prior mockup is superseded: `multistem-mixcheck.html`
— wrong drop-target structure (a separate stem-slot panel instead of extending the real shared
drop zone); `multistem-mixcheck-in-context.html` — hidden real components + a duplicate Hope panel;
`multistem-mixcheck-minimal.html` — wrong interaction model (one single-buffer engine reused for
both playback and analysis, so mute/solo had to interrupt the mix, and filename-based labels, which
is what produced the concatenated-header bug).

**Flagged, not silently resolved:** a fourth prior mockup, `multistem-mixcheck-v2.html` (per-stem
drop slots, built after Kevin rejected the minimal pass's shared picker), was NOT named in this
final brief's explicit supersession list. This pass's shared-drop-zone requirement is the opposite
structural direction from v2's slots. Very likely also superseded given the rest of the brief
(content classification + rename removes the labelling problem slots partly existed to solve), but
logged as an open question for Kevin to confirm rather than assumed — see the full reasoning in
`docs/ROADMAP.md`'s Multi-stem Mix Check section. `multistem-mixcheck-v2.html` stays live,
unchanged; its DASHBOARD.html badge is not removed.

**Delivered:** `docs/mockups/multistem-mixcheck-final.html`, pushed to `main`. Live at
`https://begb0037admin.github.io/aimm/docs/mockups/multistem-mixcheck-final.html`. Base = a fresh
fetch of `main` `index.html`, edited in place; `index.html` itself untouched throughout.

**The core correction, verified not just built:** every loaded stem's `AudioBufferSourceNode` now
runs continuously for the whole playback duration regardless of mute state — mute/solo ramps ONLY
that stem's own persistent `GainNode`, never stops/restarts/reschedules a source. Verified via a
debug hook (`window.__mcDebug`) instrumenting real `AudioContext.prototype.createBufferSource`
calls: 3 full rounds of mute-toggling every stem + a solo/un-solo cycle, while genuinely playing,
produced zero new source-node creations, with `AudioContext.state` staying `"running"` and
`currentTime`/elapsed-time continuing to advance throughout. Isolating one stem changed measured
loudness from -70.0 LUFS (all muted) to -14.7 LUFS (real signal) — live-reactive Audio Specs/Fix
Queue/Spectral Balance confirmed functionally correct, not just visually plausible, reusing the
same summed-buffer-through-`refLoadFile()` technique the minimal pass proved, now serialized via a
latest-wins queue. Stem labels come from real content-based classification (concrete FFT/threshold
constants, honestly badged "guessed," click-to-rename), classified all 4 correctly on
spectrally-distinguishable synthetic demo stems after a TP3-found onset-detection fix. A Snapshot
extends the existing `STATE.journal`/`createWorkbenchBackupPill()` pattern (fingerprint-keyed,
settings-only) — confirmed via headless-Chrome save/reload that labels (including a manual rename)
restore automatically without re-classifying. Header never concatenates (`#mcSub` = "N stems loaded
— duration"). No EQ, exactly one real `#hopeRail`. Codex three-touchpoint review — TP1 materially
reshaped the playback engine, analysis-serialization, classification constants, and Snapshot
fingerprint design before code was written; TP2 (diff review) confirmed the mute/solo path never
touches a source node and found+fixed 6 more real bugs (an analysis-reset race, a solo+mute
audible-set inconsistency between playback and analysis, an unstable Fix-Queue signature across
reloads, a Snapshot-restore duplicate-matching gap, a stem added mid-playback staying silent, a
mismatch-reference edge case); TP3 (real headless-Chrome click-through) found+fixed 2 more (a
`[hidden]` CSS bug, the onset-detection logic bug) then re-ran the full suite clean. Full
design-decision + Codex-findings write-up in `docs/ROADMAP.md`'s Multi-stem Mix Check section.
Not build authorization; Option A vs B remains Kevin's open call.

**2026-09-07 update, later same day again (Jules) — Backlog 22 (Multi-stem Mix Check) v2:
per-stem drop slots, SUPERSEDES the minimal pass below after Kevin tested it and found a real
bug plus a wrong interaction model.** Kevin tested `docs/mockups/multistem-mixcheck-minimal.html`
(the "minimal pass" write-up immediately below this one) and reported two problems: (1) a real
bug — dropping files produced 7 identical duplicate stem rows all named the same thing, with a
"mismatched stem(s) excluded" warning; (2) the interaction model itself was wrong — he sent a
screenshot of the ORIGINAL standalone mockup's "Input — Stems" panel (fixed Drums/Bass/Vocals/
Other rows, each its own independent drop target reading "Drop WAV here or click to browse", plus
a "+ Add stem" row) and said "they should look like this," explicitly rejecting the minimal
pass's single shared multi-file `Drop / browse WAV` picker. He also asked "where are the multiple
wave files" — expecting each stem to show its own waveform preview inline, not just the shared
combined waveform.

**Root cause of the duplicate-stem bug, confirmed by live headless-Chrome reproduction (Playwright
against the actual built minimal-pass file, not guessed):** a single synthetic drop with one file
correctly produced exactly one stem — event bubbling/`stopPropagation()` were NOT the problem.
Re-dispatching the SAME file at the SAME shared drop target 7 times in a row produced exactly 7
identical `window.mcStems` entries, an exact match for Kevin's report. The minimal pass's shared
multi-file picker had no dedupe check against an already-loaded identical stem, AND gave ZERO
visible feedback below 2 stems (`mcRenderStemRow()` hides the stem row entirely until there are
2+ stems, by design, to keep the single-file case pixel-identical to today) — so a user who drops
once, sees no visible "stem added" acknowledgement, and reasonably re-drops the same file
expecting it to register, silently accumulates duplicate stems. This is a UX/interaction-model
bug, not a stray double-event-firing bug — and it is exactly the kind of failure the per-stem-slot
redesign structurally prevents (each slot holds at most one stem and REPLACES, not appends, on
every drop).

**Delivered: `docs/mockups/multistem-mixcheck-v2.html`**, pushed to `main`. Live at
`https://begb0037admin.github.io/aimm/docs/mockups/multistem-mixcheck-v2.html`. `index.html`
read-only reference throughout, fetched fresh — never edited. Kevin should review THIS one now;
the minimal pass and both earlier mockups stay live at their own URLs, unchanged, for reference
only.

**What changed vs the minimal pass:**
- **Per-stem drop slots, not a shared picker.** Four default slots (Drums/Bass/Vocals/Other) plus
  a "+ Add stem" row for open-ended generic slots, matching the structure in Kevin's screenshot.
  Each slot is independently droppable/clickable; dropping into an already-filled slot REPLACES
  its stem in place (no remove-then-reload needed), closing the duplicate-drop failure mode
  structurally, not just by coincidence of the new layout.
- **Restyled to the real app's own visual language**, not the standalone mockup's separate dark
  card system Kevin had already flagged as inconsistent in an earlier round — reuses the real
  page's own `--card`/`--card-bd`/`--inset2`/`--grad`/`--mono` tokens and the exact `.ref-t-btn`
  button class already used by the real transport's play/prev/loop/stop buttons.
- **Each stem shows its own inline waveform preview** — a small per-slot `<canvas>` peak-render of
  that individual stem's decoded audio, standalone/decoupled from the real combined-waveform
  engine (no shared mutable state) — in addition to, not instead of, the existing shared combined
  waveform below the transport (which still shows the combined currently-audible mix).
- **Generation-token guarded loads** — a rapid second drop onto the same slot before the first
  decode resolves always lets the newer one win, never a stale race (a Codex TP1 plan-review
  catch, verified in TP3 with two back-to-back drops onto one slot).
- **The legacy shared "Drop / browse WAV" control is hidden (via CSS, not deleted)**, not
  re-purposed into the slot system — its pristine drop/click handlers call `refLoadFile()`
  directly and bypass `window.mcSlots` entirely, so wiring it into the new model would let it
  silently fight the slot system for control of the transport (a real risk Codex's TP2 diff review
  caught and this pass closed with a capture-phase guard on `#eq` that blocks any drop landing
  outside a stem slot, rather than letting it silently diverge state). `#refDropZone`/
  `#refFileInput`/`#mcInput` keep their exact ids/DOM position so the real page's own uncapped
  DOM-retry init loops (`wireDropZone()`/`wireMcInput()`) still resolve on the first pass, per the
  standing lesson from the earlier in-context mockup pass.
- Mute(M)/Solo(S) per stem still reuse the real `.ref-t-btn` styling. **No EQ anywhere** — still
  explicitly out of scope, confirmed via a zero-match grep for real `BiquadFilterNode` usage (the
  one text hit in the file is this pass's own code comment saying EQ is out of scope).
- Sync/mismatch validation (requirement 1), the combine-buffer-through-`refLoadFile()` reuse for
  live-reactive Audio Specs/Spectral Balance/Fix Queue (requirement 3), the single-file degenerate
  case, and the single real `#hopeRail` are all unchanged in behaviour from the minimal pass,
  just re-plumbed onto a slot-keyed data model instead of a flat push-only array.

**Codex three-touchpoint review — all three touchpoints found real, concrete issues, all fixed
and re-verified via live headless-Chrome (Playwright) execution, not self-report:**
- **TP1 (plan):** confirmed the root-cause diagnosis and that per-slot replace-not-append
  semantics close the duplicate-drop bug, but flagged: add a generation token per slot to guard
  against a race between two in-flight loads targeting the same slot (built in from the start);
  keep the per-slot waveform renderer fully decoupled from the real combined-waveform engine's
  state (built in from the start — a standalone pure function, no shared globals); and account
  for the real page's uncapped DOM-retry init functions when replacing the shared drop zone's
  markup (addressed by leaving `#refDropZone`/`#refFileInput`/`#mcInput` untouched and only hiding
  their empty-state children via CSS, never deleting/moving them).
- **TP2 (diff, against the actual built file):** found 3 real issues, all fixed and re-verified:
  (1) the legacy `#refDropZone`/`#eq`/`#mcTransport` background area could still silently diverge
  `window.mcSlots` from the visible transport via a stray drop outside any stem slot — closed
  with a capture-phase guard on `#eq`; (2) `mcClearAllStems()` cleared the internal slot array but
  never called `scheduleSync()`, leaving the real transport showing a stale combined file — fixed;
  (3) replacing an already-loaded slot required remove-then-reload since the drop target was only
  the empty-state markup — fixed by delegating drag/drop off the whole `.mc-stem-slot` row instead
  of just its empty-state child, so a direct drop-to-replace works.
- **TP3 (real headless-Chrome click-through, Playwright, not a self-report):** re-verified the
  original bug fix (a single drop into one slot → exactly 1 stem; the SAME file re-dropped 7 times
  onto the SAME slot → still exactly 1 stem, replaced not accumulated — the literal regression
  test for what Kevin hit); 4 different stems loaded into their own slots with correct names; each
  loaded slot's own waveform canvas has real non-empty drawn pixels, confirmed via `getImageData`,
  alongside the still-present shared combined waveform; solo/mute correctly re-drives the combined
  buffer and Audio Specs/Spectral Balance; a genuine mismatch (very different real duration, not
  just a re-decode of the same file) is correctly flagged/excluded; a race — two drops onto one
  slot with no await between them — the later one always wins; dynamically added "+ Add stem"
  slots load, render their own waveform, and can be fully removed (this surfaced and fixed a real
  bug during iteration: a loaded dynamic slot initially had no way to remove the SLOT itself, only
  its stem, since the remove control only rendered in the empty state — fixed by unifying the
  remove button's behaviour on `slot.fixed`); a stray drop outside any stem slot is blocked
  entirely, never appearing in `window.mcSlots`; a replacement file dropped directly onto an
  already-loaded slot replaces it in place; `mcClearAllStems()` now genuinely clears the real
  transport (`#refDzLoaded` loses its `.visible` class, `#mcTitle` resets to "Mix Check"); zero EQ
  UI/`BiquadFilterNode`; exactly one `#hopeRail`; single-file load into one slot unchanged from
  today's behaviour.

**Disclosed, carried forward unchanged from the already-Codex-reviewed minimal pass, not a new
v2 issue:** the combined buffer is hard-clamped to `[-1,1]` rather than normalized, so multiple
simultaneous full-scale stems can clip the combined analysis — an accepted product-acceptance
question for Kevin, not a bug in this pass.

Still backlog capture only, still not build authorization; Option A vs B in `docs/ROADMAP.md`
remains Kevin's open call, unaffected by this or any of the other mockups.

**2026-09-07 update, later same day (Jules) — Backlog 22 (Multi-stem Mix Check): a fresh, MUCH
NARROWER mockup after a live design discussion with Kevin, superseding both prior mockups for
review purposes.** Kevin's explicit framing after seeing the all-7-requirements and in-context
mockups below: "we already have this, just add the tracks." The two prior mockups (built earlier
today) were both too elaborate and built the wrong shape — a separate stem-rack panel, a real
per-stem EQ, a scripted duplicate Hope surface. **New scope, nothing more:** the real Mix Check
transport bar (play/prev/loop/stop, volume, time readout, `Drop / browse WAV ▾`) stays completely
unchanged mechanically; the ONLY new capability is that the drop control now accepts MULTIPLE named
stems (filename = stem label, no fixed Kick/Bass/Vocals/Other taxonomy) with a minimal inline
mute(M)/solo(S)/remove(×) toggle per stem, styled with the exact same `.ref-t-btn` class as the
existing play/prev/loop/stop buttons. **EQ (requirement 7) is explicitly OUT OF SCOPE this pass —
Kevin: "remove EQ — this is not working."** Nothing from either prior mockup's EQ code was carried
into this one.

**Kevin should review `docs/mockups/multistem-mixcheck-minimal.html`** — this is the one to look
at now, not `multistem-mixcheck.html` or `multistem-mixcheck-in-context.html` (both still live at
their own URLs, unchanged, kept for reference — this minimal pass supersedes them for review
purposes only, it doesn't delete or replace them). Live at
`https://begb0037admin.github.io/aimm/docs/mockups/multistem-mixcheck-minimal.html`.

**Build approach — genuinely minimal, reuses the real pipeline as a black box.** Base: a fresh
`index.html` fetched straight from `main` (byte-identical), edited surgically in place —
`index.html` itself was never touched, it's read-only reference. The diff against it is small and
literal: `#refFileInput` gains a `multiple` attribute; the existing `wireDropZone` drop/change
handlers (on `#refDropZone`, and the shared `#eq`/`#mcTransport` drop targets) now collect ALL
dropped/selected files into `window.mcHandleFiles()` instead of only `files[0]`; a new hidden
`<div id="mcStemRow">` sits inside the real `#refDzLoaded`, between the existing `.ref-transport`
row and the existing `.mc-wave-box` — hidden until 2+ stems are loaded, so the single-file
workflow (requirement 8) is pixel-identical to today. All the real analysis machinery (Audio
Specs, Spectral Balance, Fix Queue, `#mcWave`, the transport) is reused UNMODIFIED: a stem store
(`window.mcStems`) decodes and validates each stem (requirement 1 — sample rate/channel
count/length checked against the first stem; a mismatch is flagged with a visible ⚠ + a toast and
excluded from the combined sum, never silently misaligned), and on every add/remove/mute/solo
change, `mcSync()` sums the currently-audible stems' PCM into one combined `AudioBuffer`, encodes
it as a small in-memory WAV, and feeds it through the SAME unmodified `window.refLoadFile()` the
app already uses for a single file — so there's only ever one playback/analysis buffer (no
separate multi-source clock-sync engine needed) and Audio Specs/Spectral Balance/Fix Queue update
live via the app's own existing repopulate functions (requirement 3), exactly as they would for
any normal file load. The degenerate 1-unmuted-stem case routes the ORIGINAL file straight through
`refLoadFile()`, unchanged from today's exact single-file path.

**Codex three-touchpoint review — real issues found and fixed at TP1 and TP2, not just a clean
pass-through.** TP1 (plan, before code) confirmed the `refLoadFile()`-reuse approach was sound and
the scope was clean, but flagged 7 concrete implementation risks: drop-event bubbling could
double-load files (three nested elements all bound `drop` without `stopPropagation`), an
async-race guard was needed, mismatch validation needed to check channel count too (not just
sample rate/length) and exclude mismatched stems from the sum rather than including them
misaligned, a "byte-for-byte" framing claim was slightly inaccurate, PCM16 encoding needed an
explicit clipping policy, the synthetic file's identity needed to be fresh every time so the Fix
Queue never inherits a stale applied/dismissed entry from a different mute/solo state, and the
1-stem-remaining and 0-stems-remaining removal paths both needed explicit handling. All 7 were
fixed before TP2. **TP2 (diff review) then reproduced two REAL bugs live**, not just scope-audited:
(1) a drop landing on `#mcTransport` (inside `#eq`) still bubbled to `#eq`'s own copy of the same
handler and double-loaded every file — reproduced with an actual `DragEvent`/`DataTransfer` drop;
fixed by adding `stopPropagation()` to that shared handler too. (2) the first draft's "revision
counter" race guard was ineffective because it only checked staleness AFTER `refLoadFile()` had
already mutated the shared UI state — replaced with a strictly-serialized promise-chain queue
(`scheduleSync()`) where every mutating action reads `window.mcStems` fresh at execution time, so
no matter how many rapid clicks queue up, the run that actually executes last always reflects the
truly-current state. TP2 also caught that reducing to exactly 1 stem always reloaded the original
file regardless of that stem's own mute state — a muted lone stem would have silently un-muted
itself; fixed so the single-file shortcut only applies when that stem is actually unmuted, muted
routes through the general (silence-capable) combine path instead. TP3 (real headless-Chrome
click-through, not a self-report) then specifically re-tested both TP2 findings as regression
cases — a real `DragEvent` dropped directly on `#mcTransport` added exactly one stem, not two; a
stem muted via the UI then reduced down to the last remaining one stayed muted (measured loudness
read near-silence, ~−70 LUFS, not the plain unmuted tone) — plus the full original checklist:
exactly one `#hopeRail` on the page, zero `BiquadFilterNode`/EQ UI anywhere (the only "EQ" text
matches on the page are the pre-existing plugin-library names like "Neutron 5 EQ", unrelated to
this feature), single-file load unchanged (stem row stays hidden), 3 demo stems loading + chip
names correct, mute/solo verifiably changing the measured loudness and the `#mcWave` pixel output,
a sample-rate/length-mismatched stem correctly flagged and excluded, and clean removal all the way
back down to zero stems (which correctly calls the real `refClearFile()` and restores the empty
drop-zone state). Console was clean of errors introduced by this diff (the only console noise —
`docs/knowledge/*.json` fetch failures and an Anthropic-proxy CORS block — is pre-existing app
behaviour when run outside its normal hosted origin, reproducible identically on vanilla
`index.html`, unrelated to this change).

**Requirements 4-6 (Hope-awareness, tool-calling control, demonstrate-vs-instruct) were NOT built
this pass** — the brief flagged them as lower priority than 1-3 for this minimal pass, and time
went to getting 1-3 genuinely robust (including the TP1/TP2 fixes above) rather than a shallow pass
at all seven. Logged here as explicitly deferred, not silently dropped — a future pass extending
`buildMixCheckState()`/`buildMixCheckContextBlock()` with stem/mute/solo state, feeding the ONE
real `#hopeRail`, is the next piece if Kevin wants to continue down this path after reviewing the
minimal version.

**Not build authorization.** This is still a mockup for Kevin's review, on `main` alongside (not
replacing) the two prior mockups; Option A vs B (multi-stem upload vs auto stem-split) in
`docs/ROADMAP.md`'s "Multi-stem Mix Check" section remains Kevin's open call, unaffected by any of
the three mockups existing.

**2026-09-07 update (Jules) — Backlog 22 (Multi-stem Mix Check) mockup now shown IN THE REAL APP
FRAME, alongside the original standalone mockup:** Per Kevin's explicit ask after reviewing the
standalone mockup ("I want to see it in context of the entire page"), built a second mockup file,
`docs/mockups/multistem-mixcheck-in-context.html`, that wraps the exact same multi-stem Mix Check
feature (all 7 requirements, unchanged) inside the REAL, freshly-fetched `main` `index.html`'s own
chrome — real header, real 8-tab strip (Mix Check/Workbench/Library/Insight/Snapshots/Settings/
Marketing/Community, Mix Check active by default), and the real `#hopeRail` dock, so Kevin can
judge the new stem-slot UI sitting in the actual app rather than as an isolated single-tab demo.
Live at
`https://begb0037admin.github.io/aimm/docs/mockups/multistem-mixcheck-in-context.html` — the
original standalone mockup (`docs/mockups/multistem-mixcheck.html`) is unchanged and still live at
its own URL below; this is an additional view, not a replacement. `index.html` itself is
read-only reference for this pass — never edited.

**Build approach:** the real `index.html` is carried over byte-for-byte; only `#eq`'s (Mix
Check's) inner content changed. The REAL `.mc-head` title row (which also receives the real
Genre/Target/Settings header-actions cluster, exactly as it does live) was kept fully visible and
untouched. Everything else that used to be inside `#eq` — the real banner/transport/meter-rail/
analyser/actions markup — was wrapped in a hidden (`display:none`), NOT deleted, wrapper
(`#eqLegacyHidden`), matching this codebase's existing hide-via-CSS-don't-delete pattern, so the
real page's own init code (`wireDropZone`/`wireMcBanner`/`wireMcInput`/`wireScrub`/`wireMcVol`/
`ozSpecInit`, the transport/header-actions relocation shims, `eqGridInit`/`refTargetChanged`) keeps
finding every element it looks for instead of retrying forever against missing nodes — this exact
retry-loop risk was one of Codex's TP1 catches, before any code was written. The new multi-stem
content itself was carried over verbatim from the standalone mockup into a new `#msmcRoot`
container, with its `<style>` block re-scoped so every selector is prefixed `#msmcRoot` (nothing
in it can bleed into, or be shadowed by, the real page's own extensive CSS).

**Codex three-touchpoint review, all three touchpoints found real issues, all fixed:**
- **TP1 (plan):** verified the tab strip's actual click-handler logic, the `.panel`/`.panel.active`
  CSS, and that the one function known to reach into `#eq`'s specific descendants (`eqGridInit`)
  already null-guards cleanly — but flagged that verbatim page-copying is only safe if the OTHER
  real Mix-Check-specific relocation/init hooks are checked too, not just that one. Follow-up
  investigation (still pre-build) found several more — `wireDropZone`/`wireMcBanner`/`wireMcInput`/
  `wireScrub`/`wireMcVol`/`ozSpecInit`, plus the transport and header-actions relocation shims —
  which retry forever (uncapped `setTimeout`) against missing DOM nodes, which directly shaped the
  hide-don't-delete decision above instead of deleting `#eq`'s original content outright. Also
  flagged real global `@keyframes` names in the standalone mockup's CSS as a zero-cost thing to
  namespace before merging (renamed `hopePulse`/`ringPulse2`/`fadeIn`/`blinkDot` to an `msmc-`
  prefix — no actual collision existed, but cheap to rule out for good).
- **TP2 (diff, against the actual built file):** found a genuine event-bubbling bug — dropping a
  WAV onto a stem row also bubbles up to the real page's own `#eq` drop listener (wired by the
  hidden `wireDropZone()`), which would silently call the real single-file `refLoadFile()` and
  overwrite the real, still-visible `.mc-head` title with the dropped filename. Fixed with
  `stopPropagation()` on the stem-row handler, plus a catch-all `dragover`/`drop` guard on
  `#msmcRoot` itself for anywhere else in the new content. TP2 also found that several transport
  class names (`tp-file`, `tp-row`, `tp-btns`, `ref-t-btn`, `ref-play-pause`, `tp-vol`,
  `tp-vol-ico`, `tp-vol-range`, `tp-time`, `mc-wave-box`) were intentionally named to match the
  real component's own styling in the original standalone mockup, but because both now live under
  the same `#eq` subtree, the real page's `#eq.oz-mixcheck .tp-file`-style rules (higher
  specificity than `#msmcRoot`'s scoped rules) would win and visibly clip/re-style the transport's
  file label — renamed all ten to an `msmc-` prefix to remove the whole class of risk rather than
  patch it rule-by-rule; re-screenshotted afterward to confirm no visual regression (values had
  been intentionally matched anyway, so the fix is style-neutral). Confirmed the carried-over
  multi-stem markup/script otherwise matches the standalone mockup exactly (ids and interaction
  functions intact), and confirmed the `#eq.oz-mixcheck.active{display:block}` override is
  guaranteed to win over the real page's own `display:grid` rule for this file (later in source
  order, identical specificity, nothing downstream re-asserts `display:grid`).
- **TP3 (end-to-end, real headless-Chrome click-through):** confirmed Mix Check loads by default
  showing the new content; clicked through all 8 tabs in sequence and back to Mix Check, confirming
  `.tab.active`/`.panel.active` matched the clicked tab every time and that returning to Mix Check
  preserved live in-progress state (stem still soloed, playback still running, live analysis panel
  still updating) with the new UI fully intact; loaded demo stems, confirmed Solo/Play/EQ-panel-
  open/Hope-suggestion-card/"Let me show you" (tool-call audit line + Undo link) all worked exactly
  as in the standalone mockup; ran `node --check` on every real `<script>` block (clean; one
  pre-existing non-JS `<script type="application/json">` block correctly fails, same as in
  unmodified `index.html`); confirmed the only 2 console messages seen
  (`docs/knowledge/*.json` fetch failures) are byte-identical when loading the unmodified real
  `index.html` directly — a `file://`-vs-`https://` testing artifact, not something this change
  introduced; and specifically re-tested the TP2 drop-bubbling fix with a dispatched native `drop`
  event on a stem row, confirming the real `.mc-head` title text is unchanged afterward.

**2026-09-07 update (Jules) — Backlog 22 (Multi-stem Mix Check) mockup now covers all 7
requirements, pushed to `main`, awaiting Kevin's review:** Per Kevin's 2026-09-06 priority bump
and his explicit authorization to proceed to the mockup stage overnight, extended the existing
requirement-1/2 stem-upload mockup (`docs/mockups/multistem-mixcheck.html`, built 2026-09-04) to
also cover requirements 3-7 — the full requirement set from `docs/ROADMAP.md`'s "Multi-stem Mix
Check" section. Reqs 1-2 (stem drop/upload, sync-mismatch validation, one shared sample-accurate
transport) are unchanged from the earlier pass. New in this pass: a deterministic in-browser
demo-stem generator ("Load demo stems") so the whole mockup is reviewable without Kevin supplying
his own files; a real reactive live-analysis panel (req 3) — an `AnalyserNode` tapped BEFORE the
monitor-volume gain (so playback volume never affects the reading), redrawing on every
mute/solo/EQ change, explicitly labelled "relative FFT magnitude, demo only" rather than claiming
production BS.1770-4/corridor numbers; a scripted, state-grounded Hope rail (req 4); Hope
suggestion cards with two real interaction modes (reqs 5-6, the emphasis area per Kevin) — "Let
me show you" genuinely calls the same `toggleSolo()`/`play()` functions the UI buttons call
(exclusive isolate, a visible tool-call audit line, and a full-state Undo restoring every stem's
solo state + transport position), while "Talk me through it" changes nothing and instead rings
the real controls Kevin should click; and a genuinely-wired per-stem 3-band EQ (req 7) via real
`BiquadFilterNode`s, so a demonstrated move is audibly real, not just pictured. Codex
three-touchpoint review run in full — TP1 (plan) surfaced 9 gaps (deterministic fixture, a
correctly-separated analysis/monitor audio graph, no fabricated dB claims, broader req-5
coverage, protecting the two Hope modes from ambiguity, layout) all addressed before building;
TP2 (diff, against the actual built file) surfaced further honesty/robustness gaps (paused
analysis reading stale "Live" values, `Math.random()` non-determinism, an unsupported "Low is
reading hot" diagnostic claim, several async races around stale `decodeAudioData` callbacks and
delayed Hope timers surviving a Reset, non-real `<button>` elements) — all fixed and independently
re-verified via a real headless-Chrome click-through (load demo → sync OK → play → live analysis
→ pause correctly drops to Idle, not stale → solo → exactly 1 stem isolated → suggestion card →
demonstrate → both tool-call audit lines + Undo correctly restores solo state → reset clears
everything); TP3 (end-to-end) found 4 further concrete issues (Undo not keyboard-accessible,
Undo not restoring transport position, `play()` never resuming a suspended `AudioContext`, Hope
directly mutating state instead of calling the same `toggleSolo()` the UI uses) — all fixed and
re-verified. `index.html` untouched throughout — this is a docs/mockups-only pass, no build
authorization. Pushed directly to `main` (mockups are design artifacts per `docs/CLAUDE.md`'s
standing process, not a branch this time) at commit `24e491e`. Review at
`https://begb0037admin.github.io/aimm/docs/mockups/multistem-mixcheck.html` — Kevin reviews live
and gives explicit sign-off/redirect before any real build starts; Option A vs B (multi-stem
upload vs auto stem-split) also remains Kevin's call, unchanged by this mockup.

**2026-09-06 update — Hope-rail waveform saga CLOSED (build 2026-09-06.8), Kevin: "better - it will do for now":**
Final state after 4 rounds (3 blind, 1 source-verified) on the same live-call feedback thread
("no headroom, constantly large, no dynamics" → fixed for speaking; then "this should not happen
in an active chat" → the "listening" state needed its own fix too). What actually closed it:
cloned `begb0037admin/windows-mac-dictation` (PTT) directly and read its real `ui/app.js` instead
of continuing to guess from screenshots — PTT has NO separate "listening" state at all; its
"recording" state is ONE continuous state, always fed real mic RMS through the full-size aurora
rendering (idle shimmer even uses the SAME `paintBar(60,4)` size as active, per an explicit
historical Kevin PTT instruction: "use the active as the default in terms of size and bars" — the
AIMM port had drifted to a smaller `26px` idle without that being noticed until now). Also
confirmed directly in the pinned `@elevenlabs/client@0.1.7` SDK source that it exposes
`getInputVolume()` (identical `calculateVolume()` math to `getOutputVolume()`, reading the input
analyser instead) — nobody had checked for this in 3 prior rounds. Final fix: `HOPE_VOICE`'s
`currentMode` now switches `tick()` between sampling `getOutputVolume()` (speaking) and
`getInputVolume()` (listening — Kevin's own real mic input), both routed through the SAME
`feed()`/`feedReal()`/aurora-colour pipeline at the same `ACTIVE_BAR_MAX=60`, so listening shows
real audio, at full size, in the same colour spectrum as speaking — matching PTT's actual source
instead of three successive invented approximations (single fixed hue → full aurora sweep with a
synthetic breathing pattern → this). True pre/post-call standby (`IDLE_BAR_MAX=26`, mono chrome
shimmer) is UNTOUCHED throughout — confirmed fine as-is by Kevin. New standing lesson captured:
[[feedback_port_from_real_source_not_screenshots]] — clone the actual reference repo before
inventing a fix next time a similar "make it like X" report comes in. Commits `6a649fd` (diagnostic
logging, interim AGC target drop), `125ff25` (distinct listening state v1, single fixed hue),
`6aeb598` (v2, full aurora sweep), `dc4e1a2` (v3, real getInputVolume()-driven — the one that
stuck). All on `main`, pushed and live.

**2026-09-06 update — Markey: Hope-rail waveform AGC round 1 (`2026-09-06.3`, merged to `main`) did NOT work live, round 2 fix pushed:** Kevin live-tested the merged round-1 fix and reported "no change." Confirmed not a deploy/cache issue. Actual root cause: a conceptual flaw, not a code bug — `feedReal()`'s reference (`realRef`) was a same-signal EMA lagging `rms` by only 550ms, so `gain = target/realRef` self-cancelled within roughly a word, making output converge to a constant `target` regardless of absolute loudness (a compressor, not a VU meter). Round 2 replaces the single 550ms symmetric tau with an asymmetric attack (1500ms, rising toward louder) / release (4000ms, falling toward quieter) follower — both far slower than speech-level dynamics, so real loud/quiet contrast survives display instead of being normalized away, while still auto-leveling overall loudness across calls/turns. Hand-worked numerical example (quiet→LOUD→quiet) Codex-verified at both TP1 (plan) and TP2 (diff): LOUD reads `0.885-1.000`, QUIET-after-LOUD reads `0.613-0.698`, for the FULL duration of each segment. Merged to `main` this pass (was branch `markey-hopewave-gain-tune-2-work`) — Kevin's live listen is the remaining step, same as round 1. Full detail in the "R3 Mix Check full-layout" section below.

**2026-09-06 update — Fix Queue "Analysing…" stuck-placeholder bug FIXED, pushed pending merge:**
Confirmed Kevin's diagnosis was correct, with the exact root cause pinned down.
`MC_FIXMOVES.generate()` (the silent background call to Anthropic's API that populates the Fix
Queue card's "Recommended move" text) has an early-return guard for "no Anthropic key configured
/ nothing queued yet" that returned immediately WITHOUT ever applying the honest fallback text
("Ask Hope to talk through the move — she has it grounded in your reference library.") that the
same function's own `finally` block already used on a failed/unparseable API call — so
`movesById` stayed permanently empty for that path and the card patched with nothing, forever,
regardless of what Hope had already told Kevin verbally via her own separate `propose_mix_move`
tool. Fix: the early-return branch now applies that same fallback before returning. The deeper
gap — feeding Hope's live answer INTO the Fix Queue card directly — was investigated and found to
have no clean 1:1 mapping (`propose_mix_move`'s `bus` argument and the Fix Queue's `key`/
`focusBand` taxonomy don't correspond, and `propose_mix_move` has no `fix_id` unlike
`mark_fix_applied`); flagged as a follow-up UX/tooling decision for Kevin rather than guessed at.
Codex three-touchpoint review (TP1 plan / TP2 diff / TP3 end-to-end) all clean. Pushed to branch
`cat-fixqueue-stuck-placeholder-safety-net` off `main` @ `2c98bfd` (main has since moved on —
`markey-hopewave-gain-tune-2` merged after this branch was cut; rebasing/merging is the
coordinating session's call), build `2026-09-06.4`, NOT merged. Logged as ROADMAP.md item 33 /
DASHBOARD.html Now card 33. Per the priority reorder below, this correctly drops to low priority
relative to Backlog 22 now that it's shipped-to-branch.

**2026-09-06 update — Priority reorder (Kevin, explicit):** Backlog 22 (Multi-stem Mix Check)
bumped up — it's now the next thing to pick up. The Fix Queue "Analysing…" stuck-placeholder bug
fix (Cat was already mid-fix on it when this reorder came in — let to finish rather than stopped,
per Kevin's own call, since it was already running) is correspondingly dropped to low priority
once it lands; it's a real confirmed bug, just no longer urgent relative to Backlog 22.

**2026-09-06 update — Docs-only backlog capture, Glossary/Reference tab:** Kevin referenced
[iZotope's glossary of common and confusing mixing
terms](https://www.izotope.com/community/blog/a-glossary-of-common-and-confusing-mixing-terms) as
scope/structure inspiration — checked directly (WebFetch), roughly 30 "confusing" + 50 "common"
terms with short practical definitions; AIMM needs its own written content, not a copy. Captured as
new **Backlog 32**: a visible Glossary/Reference tab Kevin can browse (taking the nav slot freed up
when the Conversation tab was retired, not a literal revival), plus Hope drawing on the same
glossary in conversation ("Hope can use this when explaining e.g. muddy," grounding terms in real
definitions instead of using them loosely). Explicit cross-reference to Backlog 31 (logged in the
same pass, below): 31's term-to-frequency vocabulary map IS 32's audio-diagnostic subset — not
duplicated, 31 seeds it. Implementation consideration flagged for later, not decided now: Hope's
side could reuse whatever compact-digest mechanism Markey builds for the YouTube KB (Backlog 24).
Not prioritized ahead of Backlog 24/25 or 22. `index.html` untouched — docs-only, no build
authorization. Codex three-touchpoint review clean. Same branch as the frequency-solo capture below:
`docs-roadmap-capture-freq-solo-2026-09-06`.

**2026-09-06 update — Docs-only backlog capture, frequency-range solo / ear-training mode:**
Kevin called this "a must-have feature for stems," inspired by [Carve Audio's "Mixing Cheat
Sheet"](https://www.audioloom.com/carve-audio/mixing-cheat-sheet) (free plugin — direct
inspiration for the solo-to-hear mechanic only, not something to copy exactly). Captured as new
**Backlog 31**: let the user (or Hope, once her control tools exist) solo/isolate a specific
frequency range of the loaded audio — or, once stems exist, a specific stem's frequency range — so
it's audible in isolation, not just shown as a number/chart, paired with a vocabulary layer mapping
frequency ranges to named mix problems (muddy, boxy, harsh, sibilant, boomy, thin, nasal, hissy) so
Hope can name the actual problem and let the user hear it, not just report a delta number. Kevin's
framing: "the more Hope can point us to the issue... the better she can help to really improve a
mix." Explicit cross-reference: this is a direct extension of Backlog 22 (Multi-stem Mix Check) —
it's what Backlog 22's requirement 6 ("demonstrate and instruct" / "let me show you") would
actually demonstrate, and shares DSP work with requirement 7 (basic live EQ). **Not prioritized
ahead of Backlog 24/25 or Backlog 22** — sequenced as an extension of those once they exist, per
Kevin's explicit instruction. Verified before capture: re-checked `docs/ROADMAP.md` and
`DASHBOARD.html` directly against `main` to confirm 30 was the highest existing backlog ID (item 31
is next-free) and to confirm a pre-existing numbering mismatch — the "Multi-stem Mix Check" section
in `docs/ROADMAP.md` has no numeric prefix even though `DASHBOARD.html` labels it Backlog 22; noted
inline rather than silently assumed. `index.html` untouched — docs-only capture, no build
authorization. Codex three-touchpoint review clean. Branch:
`docs-roadmap-capture-freq-solo-2026-09-06`.

**2026-09-05 update — Docs-only backlog capture, loudness/reference-track investigation:**
Investigated Kevin's report that Mix Check's Audio Specs "Classified Genre" reading seemed stuck on
Trap. Found three separate, confusingly-similar loudness/genre-target controls in the live
`index.html` (Genre pill — works correctly; Target pill — confirmed broken/dormant hardcode; Spectral
Balance's own "Target" dropdown — works but synthetic-corridor only, not a real reference track). Full
finding recorded as a standing note in `docs/ROADMAP.md` (not an action item) so it isn't re-explored
as unknown territory. Kevin then referenced loudnesspenalty.com and iZotope's reference-track mixing
guidance, reframing two backlog items: **Backlog 29** (revive + expand the dormant Platform Loudness
Comparison table to show every platform at once, fix the underlying hardcode — awaiting a Jules
mockup, not "not started") and **Backlog 30** (real reference-track A/B comparison for Spectral
Balance — updates the existing P-B/B-P2 "A/B Ref tab" item, not a duplicate). Both explicitly queued
by Kevin behind Hope's intelligence work (Backlog 24/25) — captured now so the insight isn't lost, not
prioritized ahead of it. `index.html` untouched — docs-only capture, no build authorization.
Codex three-touchpoint review clean. Branch: `docs-roadmap-capture-loudness-refab-2026-09-05`.

**2026-09-05 update — KB ingestion, "That Logic Pro Guy" (20 videos):** Following `docs/INGEST.md`
Path B, curated the top 20 videos from `@thatlogicproguy` (6.53k subs, 145 videos, concrete
Logic Pro workflow/UI/mixing-technique content) for trap/hip-hop relevance and general production
technique — Kevin approved the curated list before ingestion. Ran the batch `ingest` command
directly (VPN on, Kevin confirmed). **Caught and fixed two real bugs during this run, not just
ingested blindly:** (1) `youtube-transcript-api` wasn't installed for the Python `ingest_yt.py`
actually runs under — installed, all 20 transcripts then fetched cleanly. (2) `fetch_video_title()`
silently falls back to the video ID as the title when its `import yt_dlp` fails — that module
wasn't installed for the same interpreter either (only the separate `yt-dlp` CLI was), so all 20
entries were first written with the raw video ID as their title (e.g. `"GJclT90IhPM"` instead of
the real title). Installed `yt-dlp` for the correct interpreter, verified title-fetch works, then
re-fetched and patched the real titles into both `docs/knowledge/index.json` and the 20 markdown
files' frontmatter/heading (did not need to re-fetch transcripts, only titles). KB now at **353
videos** (was 333). `fetch_video_title()`'s bare `except Exception: return video_id` still silently
swallows errors going forward — worth hardening in a future pass so a broken title-fetch surfaces
loudly instead of silently degrading citations again, but not blocking on that now since the
underlying environment cause (missing module) is fixed. **Follow-up same day:** the other three
candidate channels were also curated and ingested with Kevin's approval — TheModernCreative (20
of 593, technique-focused subset, channel otherwise skews plugin-review/gear-comparison),
Make Your Music (20 of 91, strong finishing-discipline + Logic Pro mixing content), Radium
Records (13 of 20 curated — the other 7, a "Mixing Masterclass" series, are paywalled behind a
paid channel membership tier and not publicly scrapable, confirmed via a genuine
`VideoUnplayable` error, not a pipeline bug). **KB now at 406 videos** (was 333 at session start).

Last updated: 2026-09-06 (Cat, docs-only backlog capture — Backlog 31 and 32 added, see updates above). Current reality: the 2026-09-02 Mix Check feedback round — items
1–15 (16 folded into 15), 17, 18, 20 — is **SHIPPED & LIVE on `main` @ `e9bcd8a`, build
`2026-09-02.15`**. Docs were reconciled the same day in a docs-only commit, `main` @ `4424590`,
then a further docs-only pass added the DASHBOARD.html hard-sync rule to `docs/CLAUDE.md`,
bringing `main`'s HEAD to **`ced9e6cf1`** (still `index.html` build `2026-09-02.15` — that commit
was docs/CLAUDE.md only). The still-open queue from the 2026-09-02 round (Backlog 9–14 / feedback
#21, #22, #19, #3, #6 + a default-tab change) is tracked in `docs/ROADMAP.md` → "Mix Check redesign
— outstanding feedback queue" and mirrored as DASHBOARD.html Backlog cards 9–14 (owners: mostly
Markey, one Cat item — #13 default tab, one Cat-builds/Jules-specs item — #9).

**In flight (not yet merged):** branch `mixcheck-audiospecs-label-align` @ `05eb0362` off `main`
@ `ced9e6cf1` — fixes the Audio Specs card label-wrap misalignment ("LUFS short-term" / "Phase /
correlation" rows), build `2026-09-04.1`. Codex 3-touchpoint review clean (TP2 caught one CSS
comment accuracy issue, fixed and re-verified). Pushed for Kevin's review/merge — not on `main`
yet.

**New backlog capture 2026-09-04** (not started, no build authorization yet): "Multi-stem Mix
Check" — DASHBOARD.html Backlog card 22 / `docs/ROADMAP.md` → "Multi-stem Mix Check — stem upload
/ auto-split so Hope can see per-element measurements". Full requirement set (sync, UI, live
reactive analysis, Hope-awareness, transport/stem control tools, demonstrate-and-instruct, basic
live EQ) captured from a live conversation with Kevin; next step is a Jules interactive mockup, not
implementation.

DASHBOARD.html is Kevin's working source of truth for planning; its "Now" section's 4 legacy P1
cards (P-C/P-B/P-K2/P-E, carried over from the 2026-05/06 Session-6 priorities) were corrected in
place 2026-09-04 rather than removed: P-C (Retire Repair tab) was actually already shipped
2026-06-04 (`620f708`) and is now marked done there; P-B/P-K2/P-E are confirmed not started and not
currently in flight, marked accordingly — none of the four represent active work. See
`docs/HANDOVER.md` top entry for the full correction record.

**2026-09-05 update (Markey):** Backlog item 12 (feedback #3 — Hope tab-awareness verify +
persisted-history fix) is done and **pushed pending merge**, not backlog anymore. Root cause:
the 9797772 instruction fix (RETIRED SURFACES / "never ask" rule in `buildAppKnowledgeDigest`/
`RT_INSTRUCTIONS`) was correct, but a user's pre-fix persisted chat history under
`AICHAT_HISTORY_KEY` (`trapMasterAiChatHistory_v1`) could still replay old contaminated turns on
page load. Fixed by bumping the key to `_v2` (old key orphaned, not migrated) plus, as a
defense-in-depth fold-in from Codex review, bumping `EL_LAST_CALL_KEY`
(`aiMixMastersLastCall_v1 → _v2`, the 30-min voice-call continuity cache, same contamination
path). Live-verified headless against a real HTTP origin: old key seeded with contaminated
history is ignored on reload, new turns persist only under the new keys, the 9797772 instruction
text confirmed unregressed. Codex 3-touchpoint review (plan / diff / end-to-end) all clean. Not
independently verified: a live Anthropic/ElevenLabs round-trip (no API key available in the
review sandbox) — the mechanism-level fix is proven directly instead, per the card's own verify
steps. Branch `markey-hope-history-key-bump` @ `f8cb2b6`, off `main` @ `ced9e6cf1`,
`AIMM_BUILD 2026-09-05.1`, pushed, **NOT merged** (Kevin merges).

**New backlog capture 2026-09-05** (docs-only, no build authorization, no priority reordering
beyond what's explicitly noted below): six items captured from a live session with Kevin, mirrored
in `docs/ROADMAP.md` and DASHBOARD.html Backlog cards 23–28.

- **Competitive context (attached to Backlog 22, Multi-stem Mix Check, not a new item):** a live
  competitor already ships paid AI stem-splitting, a scored mix-history library with
  compare-versions, a "Tools" marketplace, and a locked Reference-track A/B feature. Kevin's read:
  their structure is generic/replicable — AIMM's differentiator has to be Hope actually being
  intelligent, not matching their feature checklist.
- **Backlog 23 — Library reorganization** (LOWER PRIORITY, explicitly deprioritized behind
  Hope-intelligence work below): sub-sections analogous to the competitor's — scored history (ties
  to Snapshots, needs reconciling), Tools (deferred, new scope — no processing-tools feature exists
  in AIMM today), Stems (ties to Backlog 22), References (ties to ROADMAP P-B / DASHBOARD B-P2).
- **Backlog 24 — Hope DAW-specific instruction quality** (achievable soon): Hope should name actual
  Logic Pro UI elements/steps, not generic mixing language — confirmed 33 of 333 ingested KB videos
  are Logic-Pro-specific. Gated on two existing DASHBOARD Now/P2 cards now **elevated to P1**:
  "Smoke test: YouTube KB hits" and "YouTube citation links" — neither confirmed working
  end-to-end yet.
- **Backlog 25 — Hope actually driving/controlling Logic Pro** (bigger, unscoped): ties to
  B-DAW1/2/3. Real caveat logged explicitly and folded into B-DAW1's own description: Logic Pro has
  no rich public scripting/automation API like some DAWs — needs a technical research spike
  (AppleScript hooks, MIDI/OSC control surfaces) before any build estimate.
- **Backlog 26 — Mix Check first-run onboarding, pending Kevin's decision** (design work exists,
  not "not started"): Jules built v1 (`jules-mixcheck-empty-state` — lightweight greeting + chips +
  1-2-3 strip) and v2 (`jules-mixcheck-firstrun-tour` — full 5-step guided tour) mockups. Kevin
  hasn't reviewed/chosen yet. **Separately, being built live right now by Markey (not on this
  backlog list, not "not started"):** the Hope-rail greeting-message piece specifically, extracted
  from v1 — Kevin's call, "there's nothing stopping us, it's a quick win."
- **Backlog 27 — "1-2-3 guide" onboarding strip** (deferred, separate future stage): the
  "① Drop → ② Measure → ③ Ask Hope" strip from v1, explicitly not bundled into whichever onboarding
  direction Backlog 26 resolves to.
- **Backlog 28 — Spectral Balance card, revisit** (deprioritized, vague placeholder): Kevin flagged
  interest, no specifics given; Hope-intelligence work (24/25) matters more right now.

**2026-09-05 correction round (Markey, same branch, commit `d492eb1`, `AIMM_BUILD 2026-09-05.2`):**
Kevin reviewed the above and gave three corrections:
1. Confirmed the Insight tab was never actually named in the RETIRED SURFACES list — only "an
   Insight note" (as a fix source) was disclaimed there, distinct from the Insight tab itself,
   which was always described elsewhere as a real, active tab. Nothing to remove; added an
   explicit "NOT retired" clarifier to prevent future ambiguity.
2. Retired the standalone **Conversation tab** for real, since Hope's chat is now a persistent
   rail docked on every tab: removed the nav button + default-active markup (Mix Check `#eq` is
   the new default-active tab+panel, which also resolves backlog item 13 as a forced side effect,
   including an on-load init fix — `eqGridInit()`/`window.refTargetChanged()` — so Mix Check is
   fully live without requiring a manual first click); updated Hope's own instructions
   (`buildAppKnowledgeDigest()` — both the tour list AND a second "full inventory" appendix
   section Codex TP1 found I'd missed — and `RT_INSTRUCTIONS`) so she never offers to switch
   there; removed `voice` from the `switch_tab` tool's enum and its case-handler VALID list;
   removed the now-dead `TAB_DISPLAY_NAMES.voice`/`TAB_PURPOSES.voice` entries; fixed a
   legacy-but-still-wired Troubleshooter handoff handler (Codex TP1 catch) that force-activated
   the retired panel directly; fixed several genuinely user-visible strings (tip-boxes, toasts,
   empty states, tooltips) referencing "the Conversation tab"/"the Hope tab" as a destination.
   **Investigated the mobile collapse-fallback mechanism FIRST, per Kevin's explicit caveat**,
   before removing anything: confirmed live (headless Chrome, 390×844 mobile viewport) that
   `#voice`'s DOM node (kept in place, just never `.active`/nav-reachable) is still the exact
   attachment point the rail re-parents `.aichat-layout` into when "closed" below the 1024px
   breakpoint, and that the floating `#railReopen` button (position:fixed, not scoped to any tab)
   already opens the chat overlay from any tab regardless of Conversation's existence — switched
   to the Workbench tab, tapped reopen, chat opened correctly; collapsed again, correctly
   re-parented back to `#voice` immediately before `#aichatHome`. No mobile regression.
3. Tab-strip must not shrink when Conversation is removed. Confirmed no CSS change needed:
   `.tabs.oz-tabstrip .tab.oz-tab{flex:1 1 0}` is already global (R3 round 15). Measured live
   before (pristine `main` @ `ced9e6cf1`) vs after: strip `left:16 right:1088 width:1072` in BOTH
   states — identical — 9 tabs @ ~115-117px each before, 8 tabs @ ~130-132px each after.
   Screenshots taken of both states for visual confirmation.

Codex 3-touchpoint review ran across both rounds; the correction round's TP1 (plan-confirmation)
found the real gaps listed above (all folded in, none dropped), TP2 (diff review) and TP3
(end-to-end incl. the live render results) both came back clean. One **pre-existing, unrelated**
issue flagged non-blocking by TP3: ~9 toast/status strings across the file already said "add a
key on the Hope tab" before this change, even though those keys live in Settings — not caused or
worsened by this correction, left untouched to avoid scope creep (candidate for a separate,
small follow-up ticket). Branch `markey-hope-history-key-bump` @ `d492eb1`, off `main` @
`ced9e6cf1` (confirmed unchanged throughout both rounds), `AIMM_BUILD 2026-09-05.2`, pushed,
**NOT merged** (Kevin merges).

## Workstream status

| Workstream | Status | Notes |
|---|---|---|
| Project OS setup | SHIPPED | Committed, pushed |
| GitHub repo rename | SHIPPED | github.com/begb0037admin/aimm live |
| Hope Knowledge Base — wiring | SHIPPED | Smoke tested, KB hitting correctly |
| Hope Knowledge Base — .nojekyll fix | SHIPPED | Transcript files now serve on GitHub Pages |
| Hope Knowledge Base — trigger fix | SHIPPED | buildResearchDigest early-exit fixed |
| Hope Knowledge Base — topic index | SHIPPED | 28 topics mapped to video_ids in RT_INSTRUCTIONS |
| Hope Knowledge Base — ingestion | IN PROGRESS | 333 videos ingested (+92 Mix With The Masters 2026-06-17: Jaycen Joshua, Leslie Brathwaite, Bainz, Illangelo, Teezio, Anthony Kilhoffer, Young Guru, Boi-1da, Rodney Jerkins, Timbaland, Stuart White, Ben Baptie, Tom Elmhirst, Josh Gudwin, Neal Pogue, Finneas, others; 17 failed — no transcript/age-restricted). Logic Pro & DAW Training tier next (14 channels). |
| YouTube citation links | PLANNED — **elevated to P1 2026-09-05** | Hope cites title/channel but no clickable URL yet; gates Backlog 24 (Hope DAW-specific instruction quality) |
| Ingest tooling | SHIPPED | ~/bin/ingest + Ingest Video.command + docs/INGEST.md |
| **Reference tab rebuild** | **SHIPPED** | WAV drop + transport + meter dashboard + spectral analyser + loudness tables. Committed 4be7200, live on GitHub Pages. |
| **Mix Check tab (P-A)** | **SHIPPED 2026-06-04** | Renamed Reference→Mix Check; threshold-driven troubleshooter pills from WAV analysis + manual input overrides. Commit a3d96ba. Superseded by the R3 Mix Check full-layout redesign (row below). |
| **R3 Mix Check full layout** | **PROMOTED & LIVE on `main` @ `dbc793d` (build 2026-09-01.9), 2026-09-01. Post-ship fix round CLOSED 2026-09-02 — feedback items 1–15 (16 folded into 15), 17, 18, 20 SHIPPED & LIVE on `main` @ `e9bcd8a` (build 2026-09-02.15). Docs reconciled `main` @ `4424590` (2026-09-04). Still-open queue (Backlog 9–14 / feedback #21, #22, #19, #3, #6 + default-tab) tracked in `docs/ROADMAP.md` — nothing currently mid-build.** | First R3 tab rebuilt mockup→live to Jules mockup `05-r3-mixcheck-full-layout.html` @ `8c2785e`. Grid shell + de-pinned transport; single `Drop / browse WAV ▾` input + brand wordmark; Audio Specs panel absorbing the 4 meter cards (RMS/Crest/LRA/noise-floor DSP, Tempo via web-audio-beat-detector, in-browser chroma Key, TEMPO/KEY headline tiles, stereo-width meter, SSL-style band deviation meters); context banner; Fix Queue with the `window.mcFixQueue` contract + `aimm:analysis-complete` event (replaces the 6 Mix Issues pills); transport waveform; `#hopeRail` full-height grid item with a speech-tied meter; Hope transcript mix-breakdown + live action-item cards + `mark_fix_applied` tool (Markey). Codex TP1 approve-with-notes (folded), per-step TP2 clean, TP3 end-to-end complete (no blockers). Gate 1 + Gate 2 Kevin-approved 2026-09-01; PROMOTED to `main` via Kevin's PowerShell ff-only merge 2026-09-01 (`main` @ `dbc793d`, live). Durable record: `docs/HANDOVER-r3-mixcheck.md`; post-ship fix round: `docs/HANDOVER.md`. Deferred/residual items listed below. **Post-fix follow-up (header re-layout, tab strip full-width + taller, Genre/Target/Settings → title row, WAV loader → transport bar) shipped as part of the 2026-09-02 feedback round above — no longer awaiting review.** |
| **A/B Ref tab (P-B)** | **PLANNED** | New tab: two drop zones, overlaid spectral curves, delta meters, Hope commentary. Spec in docs/ROADMAP.md. Mockup: docs/mockups/ab-ref.html |
| **Retire Repair tab (P-C)** | **PLANNED** | Remove Repair tab once P-A ships; slot freed for P-B. ~1 hr. |
| **Hope's sphere (P-D)** | **PLANNED** | Animated particle orb replaces floating mic button. Idle/listening/speaking/thinking states. Mockup: docs/mockups/hope-sphere.html |
| **Hope tools for Mix Check + A/B Ref (P-E)** | **PLANNED** | get_mix_check_state, set_meter_value, get_ab_ref_state client tools. Depends on P-A + P-B. |
| **Cloudflare Worker key relay** | **SHIPPED** | Merged PR #1 (`a533ed3`), live. Worker deployed at aimm-proxy.kevinlelitte.workers.dev, secrets set, `/health` verified green. Zero Settings entry on any device. |
| **Voice session stacking fix + spacebar-only** | **SHIPPED 2026-06-11** | Root cause: elEnd during connect orphaned the in-flight session. Session registry + endRequested + ending lock + 600ms space cooldown; mouse call control removed per 2026-06-04 brief. Sphere = drag only. |
| **open_dashboard + capture fixes** | **SHIPPED 2026-06-11** | Dashboard now opens in in-app overlay (popup blocker killed the old new-tab path); relative URL fixes localStorage origin; capture dedup reads docs/ROADMAP.md; captures toast on success. |
| **open_dashboard root cause (round 2)** | **SHIPPED 2026-06-11** | Tool was registered on EL side but MISSING from TOOL_DEFS → no client handler → 30s timeout → "isn't connecting". Added. Also: read_doc remaps to active docs (ROADMAP.md→docs/ROADMAP.md, CLAUDE.md→docs/HANDOVER.md); elEnd paints instant "Ending…" feedback. |
| **Build stamp + panic button** | **SHIPPED 2026-06-11** | `AIMM_BUILD` const + bottom-right badge (bump every index.html commit — hard rule in docs/CLAUDE.md); pagehide handler explicitly endSession()s every live Hope session so closing the tab always stops billing instantly. Build `2026-06-11.4`. |
| **Durable captures store** | **SHIPPED 2026-06-11** | `/captures` on aimm-proxy Worker (Workers KV, binding `AIMM_KV`); app + DASHBOARD sync with localStorage fallback. Kev one-time setup: KV namespace + binding + re-paste worker code (`worker/README.md`). |
| **Dashboard opens in new tab** | **SHIPPED 2026-06-11** | window.open first (needs one-time pop-up allow for the site), overlay only as fallback. Build 2026-06-11.5. |
| **Hope dashboard sight + inbox autonomy** | **SHIPPED 2026-06-11** | read_doc DASHBOARD.html → live digest (inbox + roadmap); new manage_roadmap_inbox tool (list/remove/promote/edit, live overlay refresh). Kev one-time: Settings → "Register dashboard-inbox tool", then fresh call. Build 2026-06-11.6. |
| **Double-tap orb call control (iPad)** | **SHIPPED 2026-06-11** | Double-tap (2 non-drag taps ≤450ms) toggles the call via the same guarded path as spacebar; first tap arms (orb flash). Build 2026-06-11.7. |
| **Mix Check meter accuracy (BS.1770-4)** | **SHIPPED 2026-06-11** | Real K-weighted gated LUFS + 4× oversampled true peak + PLR; validated vs reference signals (−18dBFS 997Hz → −18.00 LUFS exact). Was raw RMS/sample-peak. Build 2026-06-11.8. |
| **Live input metering** | **SHIPPED 2026-06-11** | "or meter live" bar: input device (BlackHole = DAW feed) or tab-audio capture; streaming BS.1770 + max-hold TP; Stop locks readings. Validated −18.00/−18.00 on simulated stream. Build 2026-06-11.9. |
| **Tonal Balance-style spectral display** | **SHIPPED 2026-06-11** | Genre target corridor + normalised smoothed 64-pt curve (8192 FFT) + whole-file average spectrum at load + graphite restyle. Target selector follows workbench genre. Build 2026-06-11.10. |
| **Mix Move cards (Mixio steal #1)** | **SHIPPED 2026-06-11** | propose_mix_move tool → structured card (plugin/move/why/confidence) + Apply button (adds plugin + pins settings). Kev: re-click the Settings register button, fresh call. Build 2026-06-11.11. |
| **Bus snapshot overlay (Mixio steal #2)** | **PLANNED** | Solo a bus → capture curve via live metering → overlay colours on the corridor display. Spec in docs/ROADMAP.md P-K2. |
| **Full-page redesign — R3 per-tab rollout** | **Mix Check tab PROMOTED & LIVE on `main` @ `dbc793d` (build 2026-09-01.9) 2026-09-01, plus the full 2026-09-02 feedback round on top (`main` @ `e9bcd8a`, build 2026-09-02.15); other tabs still to do** | The R3 Mix Check full-layout redesign (see the dedicated row above) is the first R3 tab taken mockup→live to a real working build against Jules mockup `05-r3-mixcheck-full-layout.html` @ `8c2785e`. Gate 1 + Gate 2 Kevin-approved 2026-09-01 @ `256cae8`; the PowerShell `git merge --ff-only` promote of `main` was run by Kevin 2026-09-01 (`main` @ `dbc793d`). The 2026 rounds 1–5 screenshot-rebuild history and the `r3-preview` branch (`https://raw.githack.com/begb0037admin/aimm/r3-preview/index.html`) are **superseded** by this build. Still to do: the rest of the R3 per-tab redesign — Workbench, Library, Insight, Snapshots, Settings, Marketing, Community, Conversation. Epic not fully settled (still blocks the Hope→Mia rename — see docs/ROADMAP.md). |
| **Hope chat rail (static on every page)** | **SHIPPED 2026-06-11** | #hopeRail docks .aichat-layout on the right of every tab (Mixio-style); collapse returns it to the Conversation tab; persisted. Build 2026-06-11.13. |
| DAW Bridge Epic | PLANNED | 3 phases scoped, not started |
| iPad PWA | PLANNED | Not started |
| Branch consolidation | PLANNED | Consolidate voice-elevenlabs into main only |
| **Platform Evolution Epic** | **PLANNED — decision locked 2026-06-23** | AIMM evolves from single-file to hosted, login-based web app. No install ever. 3 staged arches: ARCH-1 (Cloudflare Worker + R2 + auth), ARCH-2 (RoEx-style analysis via Python/Librosa microservice), ARCH-3 (HyFi-style AI online mastering). Spec in docs/ROADMAP.md. Cards in DASHBOARD.html. |

## R3 Mix Check full-layout — deferred & accepted residuals (as of build 2026-09-01.9)

**Deferred to the analyst phase (tracked, not bugs — logged as Backlog 6/7 in ROADMAP.md + DASHBOARD.html):**

- **Audio Specs "with full analysis" placeholders** — Subgenre / Production style / Energy / Mood / Dissonance render as placeholder rows with a neutral dot; real detected values need the deferred server-side analysis phase (Platform Evolution ARCH-2 territory). Placeholders by design.
- **Transport waveform INTRO / VERSE / BRIDGE / VERSE sections** are fixed cosmetic proportional layers, not detected from the audio. Real arrangement detection (SSM / novelty / energy segmentation) is an analyst-phase job, explicitly deferred in the build's locked decisions.
- **Markey's Hope-rail speaking-meter real-amplitude gain — round 1 (`markey-hopewave-gain-tune`, build 2026-09-06.3) DID NOT WORK LIVE; round 2 fix on `markey-hopewave-gain-tune-2-work` (build 2026-09-06.4), NOT YET MERGED, Kevin's live confirmation still pending.** Was originally a flat `getOutputVolume() * 18` (docs previously said `× 11` — that was stale; the live code was `× 18`) copied verbatim from PTT's mic-RMS curve. Kevin's live-call feedback confirmed the predicted symptom (constantly large, no headroom/dynamics). Root cause of the ORIGINAL bug confirmed by reading the pinned `@elevenlabs/client@0.1.7` dist source directly: `getOutputVolume()` is `calculateVolume(getOutputByteFrequencyData())`, structurally not the same signal domain as PTT's time-domain mic RMS. Round 1's fix (`feedReal()`/`resetRealPeak()` in `HOPE_WAVE`, merged to `main` at `20c9384`) replaced the flat multiplier with a `REAL_REF_TARGET=0.62` / `REAL_REF_TAU_MS=550` single-tau EMA reference, passed Codex TP2 round 5 approval on numerically-verified AGC behavior — **but Kevin live-tested it and reported "no change."** Confirmed NOT a deploy/caching issue (live site was serving `2026-09-06.3`'s actual code). Real root cause, found on re-reading the design itself: `realRef` was a same-signal EMA of `rms` lagging by only ~550ms — since word/sentence-level loudness changes happen on that timescale or slower, `gain = target/realRef` converged so `rms*gain -> target` almost immediately regardless of absolute loudness. That's a textbook compressor (removes dynamic range); a VU-meter-style visualization needs the opposite (reveal dynamic range). The code was doing exactly what an AGC/compressor is supposed to do — the wrong tool for this job, and a design-intent bug Codex's correctness-focused review didn't catch. **Round 2 fix (this update):** `realRef` is now an ASYMMETRIC attack/release follower — climbs toward a new LOUDER rms over `REAL_REF_ATTACK_TAU_MS=1500`ms, falls toward a new QUIETER rms over `REAL_REF_RELEASE_TAU_MS=4000`ms — both far slower than word/phrase-level speech dynamics (~0.3-1s), so within any single loud or quiet passage the reference does not catch up before the passage ends. Hand-worked and Codex-verified (TP1 + TP2, both PASS): a quiet(0.30)->LOUD(0.75) 2s->quiet(0.30) 3s sequence reads `0.885-1.000` throughout the LOUD segment and `0.613-0.698` throughout the following QUIET segment — a persistent ~0.2-0.4 gap for the FULL segment duration, not just a brief attack transition; even a single ~400ms loud word spikes to `1.000` against a ~0.73-0.75 quiet floor right after. Reasoned through with hand arithmetic + Codex review rather than a live console.log round-trip with Kevin, to avoid a third blind guess without first fixing the fundamental self-cancellation flaw — if this ALSO reads as "no change" live, the next step is the console.log-behind-a-dev-flag capture this round skipped. **Still open:** Kevin's own live listen is the confirmation step, same as round 1 — this round has NOT been live-tested yet.

**Accepted Gate-2 residuals (Kevin signed off 2026-09-01 with these known — logged as Backlog 8):**

- A. Empty (no-WAV) state — Audio Specs column runs well below the shorter empty analyser card before the columns bottom-align; matching the empty analyser height is a separate grid tweak.
- B. Very hot bands peg at the ±6 dB edge of the deviation meter (e.g. LOW +11 shows at the edge); the signed value above carries the true number.
- C. Stereo-width meter is a 1:1 %→track map; typical masters (~25–40%) sit left of centre; could switch to a compressed scale.
- D. RESOLVED 2026-09-06, build `2026-09-06.8` (`dc4e1a2`) — Kevin: "better - it will do for now." Took 4 rounds; the one that stuck came from reading PTT's actual source directly rather than guessing further. See the top-of-file entry for full detail.
- E. Speaker button in the composer has no effect with no call live (arms the mute preference); could show a disabled state.
- F. PRE-EXISTING: empty-state analyser hint text overlaps the "Low / Low-Mid / High-Mid / High" axis labels — long-standing, not introduced by R3, still present.

## Last known good state

- index.html on `main`: v4 redesign live — build 2026-06-18.3 (3-column layout, canvas orb, ribbon waveform). **Unchanged this round — confirmed `git diff main r3-preview -- index.html` before push.**
- index.html on `r3-preview` (branch, NOT merged): round-5 MixCheck rebuild, build 2026-08-17.1, commit `433888d`. **Superseded by `r3-mixcheck-codex` below — do not use for sign-off.**
- index.html on `main` @ `dbc793d`: R3 Mix Check full-layout redesign, build 2026-09-01.9 (merged ff-only from `r3-mixcheck-codev` @ `256cae8`). Gate 1 + Gate 2 Kevin-approved 2026-09-01; Codex TP3 end-to-end clean; PROMOTED & LIVE 2026-09-01. Durable record: `docs/HANDOVER-r3-mixcheck.md`; post-ship fixes: `docs/HANDOVER.md`.
- index.html on `main` @ `e9bcd8a` (build 2026-09-02.15): the 2026-09-02 Mix Check feedback round fully shipped on top of `dbc793d` — header re-layout, Hope-rail pass, Fix Queue + transport batch, transcript layout, `#hopeWave` PTT port, viewport-fit density, page gutter, Fix Queue "production line" (queue side + Hope side). **This is the current live index.html on `main`.**
- `main` HEAD as of 2026-09-04 is `4424590` — one docs-only commit on top of `e9bcd8a` (DASHBOARD.html + docs/ROADMAP.md, no index.html/build change) reconciling the feedback round into Recently Shipped and queuing Backlog 9–14.
- `main` HEAD confirmed live 2026-09-05 (Markey, at dispatch time) is `ced9e6cf1`, unchanged when this branch was pushed.
- index.html on branch `markey-hope-history-key-bump` @ `f8cb2b6` (off `main` @ `ced9e6cf1`): item 12 fix (`AICHAT_HISTORY_KEY`/`EL_LAST_CALL_KEY` → `_v2`), build `2026-09-05.1`. Pushed, **NOT merged**.
- Tag pre-v4-redesign: full pre-v4 app preserved for instant revert
- docs/knowledge/index.json: 333 videos (+92 Mix With The Masters, 2026-06-17)
- ~/bin/ingest: installed and smoke tested
- Both branches: 4be7200 (voice-elevenlabs and main both at this commit)
- GitHub Pages: live — https://begb0037admin.github.io/aimm/ (still serving `main`, untouched)
- Round 3/4 screenshot-only review pages (mixcheck-r3-review.html / -v2.html / -v3.html) are superseded by the round-5 live build above — don't use them for sign-off.

## Session 6 start priorities (2026-05-26)

P-A → P-C → P-B → P-D → P-E (in that order, each depends on prior)
Effort total: ~12.5 hours across all five items.
Start with P-A (Mix Check) — smallest risk, highest immediate value.
