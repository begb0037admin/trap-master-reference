#!/usr/bin/env python3
"""
register_elevenlabs_tools.py

One-shot script to bulk-register every client tool from
elevenlabs-client-tools.json with the ElevenLabs Convai API and attach the
resulting tool IDs to the AI Mix Masters agent's prompt.tool_ids list.

Why: pasting 25 tools one by one in the dashboard form is brutal.

Pure Python, stdlib only — runs on macOS's built-in python3 with no install.

Usage:
    EL_API_KEY=sk_xxx python3 register_elevenlabs_tools.py

Or pass them inline:
    python3 register_elevenlabs_tools.py <api_key> [agent_id]

The agent ID defaults to the AI Mix Masters production agent
(agent_2601kqm4g7txfsvv0pkvpe02389p) if EL_AGENT_ID isn't set.

After running, open the agent dashboard and click PUBLISH (top-right) — drafts
do not go live until published. (CLAUDE.md gotcha — burned an hour on this.)

Idempotency: this script CREATES tools every run. Re-running gets a fresh set
of IDs and the agent is patched to use the new ones; the old tool entries are
left orphaned in your workspace and can be cleaned up from the dashboard's
Tools list.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

API_KEY = os.environ.get('EL_API_KEY') or (sys.argv[1] if len(sys.argv) > 1 else None)
AGENT_ID = (
    os.environ.get('EL_AGENT_ID')
    or (sys.argv[2] if len(sys.argv) > 2 else None)
    or 'agent_2601kqm4g7txfsvv0pkvpe02389p'
)

if not API_KEY:
    print('Missing API key. Set EL_API_KEY=sk_... or pass it as the first arg.')
    print('Get one at https://elevenlabs.io/app/settings/api-keys')
    sys.exit(1)

if API_KEY == 'sk_your_key_here':
    print('"sk_your_key_here" is the placeholder text — replace it with your real key.')
    print('Get yours at https://elevenlabs.io/app/settings/api-keys')
    sys.exit(1)

here = Path(__file__).resolve().parent
json_path = here / 'elevenlabs-client-tools.json'
if not json_path.exists():
    print(f'elevenlabs-client-tools.json not found at {json_path}')
    sys.exit(1)

tools = json.loads(json_path.read_text())
print(f'Loaded {len(tools)} tools from elevenlabs-client-tools.json')
print(f'Target agent: {AGENT_ID}')
print()

BASE = 'https://api.elevenlabs.io/v1/convai'
HEADERS = {
    'xi-api-key': API_KEY,
    'Content-Type': 'application/json'
}


def call(method, url, body):
    """POST/PATCH JSON, return (status_code, body_as_dict_or_text)."""
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = r.read().decode('utf-8')
            try:
                return r.status, json.loads(txt)
            except json.JSONDecodeError:
                return r.status, txt
    except urllib.error.HTTPError as e:
        txt = e.read().decode('utf-8', errors='replace')
        return e.code, txt
    except urllib.error.URLError as e:
        return 0, f'network error: {e.reason}'


def ensure_param_descriptions(schema, name_hint=None):
    """ElevenLabs requires every leaf parameter (string/number/integer/boolean
    properties AND array items) to set one of: description, dynamic_variable,
    is_system_provided, or constant_value. Our TOOL_DEFS in index.html omit
    description on enum-only fields and array-item types, so we inject a
    sensible fallback before POSTing. Mutates in place."""
    if not isinstance(schema, dict):
        return schema
    typ = schema.get('type')
    # The root parameters object (type=object) is a container — only leaf
    # schemas (string/number/integer/boolean/array) need descriptions.
    if typ and typ != 'object':
        has_description_field = any(
            k in schema for k in ('description', 'dynamic_variable',
                                  'is_system_provided', 'constant_value')
        )
        if not has_description_field:
            schema['description'] = name_hint or typ
    # Recurse into properties.
    props = schema.get('properties')
    if isinstance(props, dict):
        for name, p in props.items():
            ensure_param_descriptions(p, name.replace('_', ' ').strip())
    # Recurse into array items.
    items = schema.get('items')
    if isinstance(items, dict):
        item_hint = (name_hint + ' item') if name_hint else 'item'
        ensure_param_descriptions(items, item_hint)
    return schema


# 1. Create each tool, collect returned IDs.
tool_ids = []
for i, t in enumerate(tools):
    # Deep-copy params before mutating (ensure_param_descriptions adds defaults).
    params = json.loads(json.dumps(t['parameters']))
    ensure_param_descriptions(params)
    body = {
        'tool_config': {
            'type': 'client',
            'name': t['name'],
            'description': t['description'],
            # Client-tool variant: parameters is the JSON Schema describing args.
            # expects_response = True so Hope waits for our handler to return
            # and appends the result to the conversation context.
            'parameters': params,
            'expects_response': True,
            'response_timeout_secs': 20,
        }
    }
    label = f'  [{i+1:2d}/{len(tools)}] {t["name"]:<28} -> '
    print(label, end='', flush=True)
    status, resp = call('POST', f'{BASE}/tools', body)
    if status >= 400 or status == 0:
        print(f'FAILED {status}')
        if isinstance(resp, str):
            print(f'  body: {resp[:600]}')
        else:
            print(f'  body: {json.dumps(resp)[:600]}')
        print()
        print('If the error mentions an unexpected field, the API schema may have shifted.')
        print('Last sent payload:')
        print(json.dumps(body, indent=2)[:1200])
        sys.exit(1)
    if not isinstance(resp, dict) or 'id' not in resp:
        print(f'response missing id: {str(resp)[:300]}')
        sys.exit(1)
    print(f'id {resp["id"]}')
    tool_ids.append(resp['id'])

print()
print(f'Attaching {len(tool_ids)} tool IDs to agent {AGENT_ID} ...')

# 2. Patch the agent. Per the API migration docs, set
# conversation_config.agent.prompt.tool_ids — the legacy `tools` field has
# been removed since July 2025.
patch_body = {
    'conversation_config': {
        'agent': {
            'prompt': {
                'tool_ids': tool_ids
            }
        }
    }
}
status, resp = call('PATCH', f'{BASE}/agents/{AGENT_ID}', patch_body)
if status >= 400 or status == 0:
    print(f'PATCH agent FAILED {status}')
    if isinstance(resp, str):
        print(f'  body: {resp[:800]}')
    else:
        print(f'  body: {json.dumps(resp)[:800]}')
    sys.exit(1)

print()
print('Done. Open the agent dashboard and click PUBLISH (top-right) to make the tools live:')
print(f'  https://elevenlabs.io/app/agents/agents/{AGENT_ID}')
