#!/usr/bin/env node
// register-elevenlabs-tools.mjs
//
// One-shot script to bulk-register every client tool from
// elevenlabs-client-tools.json with the ElevenLabs Convai API and attach the
// resulting tool IDs to the AI Mix Masters agent's prompt.tool_ids list.
//
// Why: pasting 25 tools one by one in the dashboard form is brutal.
//
// What it does:
//   1. Reads elevenlabs-client-tools.json (sibling file in this folder)
//   2. POSTs each entry to https://api.elevenlabs.io/v1/convai/tools as a
//      `client` tool with `expects_response: true` and a 20s timeout
//   3. Collects the returned tool IDs
//   4. PATCHes the agent (via /v1/convai/agents/{agentId}) so its
//      conversation_config.agent.prompt.tool_ids contains the full list
//
// After running it, open the agent in the dashboard and click PUBLISH
// (drafts don't go live — see CLAUDE.md gotchas).
//
// Usage:
//   EL_API_KEY=sk_xxx EL_AGENT_ID=agent_xxx node register-elevenlabs-tools.mjs
//
// Or pass them inline:
//   node register-elevenlabs-tools.mjs <api_key> <agent_id>
//
// Defaults: agent ID falls back to the AI Mix Masters production agent
// (agent_2601kqm4g7txfsvv0pkvpe02389p) if EL_AGENT_ID isn't set.
//
// Idempotency: this script CREATES tools every run. If you re-run it, you'll
// get a new set of IDs and the agent will be patched to use those instead —
// the old tool entries are left orphaned in your workspace. Clean those up
// from the dashboard's Tools list if it bothers you.

import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

const apiKey = process.env.EL_API_KEY || process.argv[2];
const agentId = process.env.EL_AGENT_ID || process.argv[3] || 'agent_2601kqm4g7txfsvv0pkvpe02389p';

if (!apiKey){
  console.error('Missing API key. Set EL_API_KEY=sk_... or pass it as the first arg.');
  console.error('Usage: EL_API_KEY=sk_xxx node register-elevenlabs-tools.mjs');
  process.exit(1);
}

const jsonPath = resolve(__dirname, 'elevenlabs-client-tools.json');
if (!existsSync(jsonPath)){
  console.error('elevenlabs-client-tools.json not found alongside this script.');
  console.error('Path checked:', jsonPath);
  process.exit(1);
}

const tools = JSON.parse(readFileSync(jsonPath, 'utf8'));
console.log(`Loaded ${tools.length} tools from elevenlabs-client-tools.json`);
console.log(`Target agent: ${agentId}`);
console.log('');

const headers = {
  'xi-api-key': apiKey,
  'Content-Type': 'application/json'
};
const base = 'https://api.elevenlabs.io/v1/convai';

// 1. Create each tool and collect the returned ID.
const toolIds = [];
for (let i = 0; i < tools.length; i++){
  const t = tools[i];
  const body = {
    tool_config: {
      type: 'client',
      name: t.name,
      description: t.description,
      // Client-tool variant: parameters is the JSON Schema describing args.
      // expects_response = true so Hope waits for our handler to return and
      // appends the result to the conversation context (per ElevenLabs docs).
      parameters: t.parameters,
      expects_response: true,
      response_timeout_secs: 20
    }
  };
  process.stdout.write(`  [${(i+1).toString().padStart(2)}/${tools.length}] ${t.name.padEnd(28)} → `);
  let res;
  try {
    res = await fetch(`${base}/tools`, {method:'POST', headers, body: JSON.stringify(body)});
  } catch (e){
    console.error(`network error: ${e.message}`);
    process.exit(1);
  }
  if (!res.ok){
    const txt = await res.text().catch(()=>'(no body)');
    console.error(`FAILED ${res.status}`);
    console.error('  body:', txt.slice(0, 500));
    console.error('');
    console.error('If the error mentions an unexpected field, the API schema may have moved.');
    console.error('Last sent payload:', JSON.stringify(body, null, 2).slice(0, 800));
    process.exit(1);
  }
  const j = await res.json();
  if (!j.id){
    console.error(`response missing id:`, JSON.stringify(j).slice(0,300));
    process.exit(1);
  }
  console.log(`id ${j.id}`);
  toolIds.push(j.id);
}

console.log('');
console.log(`Attaching ${toolIds.length} tool IDs to agent ${agentId} …`);

// 2. Patch the agent. Per the API migration docs, we set
// conversation_config.agent.prompt.tool_ids (the legacy `tools` field has
// been removed since July 2025).
const patchBody = {
  conversation_config: {
    agent: {
      prompt: {
        tool_ids: toolIds
      }
    }
  }
};
let pr;
try {
  pr = await fetch(`${base}/agents/${agentId}`, {method:'PATCH', headers, body: JSON.stringify(patchBody)});
} catch (e){
  console.error(`network error patching agent: ${e.message}`);
  process.exit(1);
}
if (!pr.ok){
  const txt = await pr.text().catch(()=>'(no body)');
  console.error(`PATCH agent FAILED ${pr.status}`);
  console.error('  body:', txt.slice(0, 800));
  console.error('  payload:', JSON.stringify(patchBody, null, 2).slice(0, 800));
  process.exit(1);
}

console.log('');
console.log('✓ Done. Open the agent dashboard and click PUBLISH (top-right) to make these tools live.');
console.log(`  https://elevenlabs.io/app/agents/agents/${agentId}`);
