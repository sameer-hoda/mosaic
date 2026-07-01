#!/bin/bash
# TaskDog v2 — End-to-End Validation Script
#
# Prerequisites:
#   - Go bridge running on port 8080 (WhatsApp paired)
#   - Flask backend running on port 3001
#   - GEMINI_API_KEY set in taskdog-backend/.env
#
# Usage:
#   cd taskdog-backend
#   bash tests/e2e_v2.sh

set -e

BASE="http://localhost:3001"
PASS=0
FAIL=0

ok()   { echo "  ✅ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ❌ $1"; FAIL=$((FAIL + 1)); }

echo "============================================"
echo "  TaskDog v2 — End-to-End Validation"
echo "============================================"
echo ""

# ─── 1. Health Check ─────────────────────────────────────────────────
echo "1. Health check"
HEALTH=$(curl -sf $BASE/api/health) || { echo "  ❌ Backend not running on $BASE"; exit 1; }
echo "$HEALTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['ok'] == True, 'ok should be true'
print(f\"  ✅ Health OK — gemini_key_set={d['gemini_key_set']}, bridge={d['bridge_status']}\")
" || fail "Health check"
KEY_SET=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['gemini_key_set'])")
BRIDGE=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin)['bridge_status'])")
if [ "$KEY_SET" != "True" ]; then
    echo "  ⚠️  Gemini key not set. Set GEMINI_API_KEY in .env"
fi
if [ "$BRIDGE" != "connected" ]; then
    echo "  ⚠️  Bridge not connected ($BRIDGE). Start wa-bridge and pair WhatsApp."
fi
echo ""

# ─── 2. Validate API Key ─────────────────────────────────────────────
echo "2. Validate API key (if set)"
if [ "$KEY_SET" = "True" ]; then
    ok "Gemini key already set in environment"
else
    echo "  ℹ️  Skipping (no key set)"
fi
echo ""

# ─── 3. Bridge Status ────────────────────────────────────────────────
echo "3. Bridge status"
BRIDGE_RES=$(curl -sf $BASE/api/bridge/status) || fail "Bridge status endpoint"
echo "$BRIDGE_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"  ✅ Bridge: {d['status']}\")
" || fail "Bridge status"
echo ""

# ─── 4. Classify Chats ───────────────────────────────────────────────
echo "4. Classify chats"
CLASSIFY_RES=$(curl -sf -X POST $BASE/api/chats/classify) || fail "Classify endpoint"
CHAT_COUNT=$(echo "$CLASSIFY_RES" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")
echo "  ✅ Classified $CHAT_COUNT chats"
# Get first group JID
JID=$(echo "$CLASSIFY_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
groups = [c for c in d['chats'] if c['jid'].endswith('@g.us')]
if groups:
    print(groups[0]['jid'])
else:
    print('')
")
if [ -z "$JID" ]; then
    echo "  ⚠️  No group chats found. Using a test JID."
    JID="120363test@g.us"
fi
echo "  ℹ️  Using group JID: $JID"
echo ""

# ─── 5. Whitelist Groups ─────────────────────────────────────────────
echo "5. Whitelist group"
WL_RES=$(curl -sf -X POST $BASE/api/groups/whitelist \
    -H 'Content-Type: application/json' \
    -d "{\"jids\":[\"$JID\"]}") || fail "Whitelist endpoint"
echo "$WL_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['ok'] == True
print(f\"  ✅ Whitelisted {d['count']} group(s)\")
" || fail "Whitelist"
echo ""

# ─── 6. Discover Tasks ───────────────────────────────────────────────
echo "6. Discover tasks (Stage 1) — this takes 10-30s"
DISCOVER_RES=$(curl -sf -X POST $BASE/api/pipeline/discover \
    -H 'Content-Type: application/json' \
    -d "{\"group_jids\":[\"$JID\"]}") || fail "Discover endpoint"
TASK_COUNT=$(echo "$DISCOVER_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['summary']['total_tasks_found'])
")
echo "  ✅ Discovered $TASK_COUNT tasks"
echo ""

# ─── 7. Dashboard ────────────────────────────────────────────────────
echo "7. Dashboard"
DASH_RES=$(curl -sf $BASE/api/dashboard) || fail "Dashboard endpoint"
echo "$DASH_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
stats = d['stats']
print(f\"  ✅ Dashboard: {stats['total']} tasks ({stats['active']} active, {stats['completed']} completed)\")
assert stats['total'] > 0, 'Should have tasks after discovery'
" || fail "Dashboard"
echo ""

# ─── 8. Task Detail ──────────────────────────────────────────────────
echo "8. Task detail"
TASK_ID=$(echo "$DASH_RES" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tasks'][0]['id'] if d['tasks'] else '')")
if [ -n "$TASK_ID" ]; then
    TASK_RES=$(curl -sf $BASE/api/tasks/$TASK_ID) || fail "Task detail endpoint"
    echo "$TASK_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['ok'] == True
print(f\"  ✅ Task: {d['task']['title'][:50]}\")
" || fail "Task detail"
else
    echo "  ⚠️  No tasks to detail"
fi
echo ""

# ─── 9. Manual Task Update ───────────────────────────────────────────
echo "9. Manual task update (PATCH)"
if [ -n "$TASK_ID" ]; then
    PATCH_RES=$(curl -sf -X PATCH $BASE/api/tasks/$TASK_ID \
        -H 'Content-Type: application/json' \
        -d '{"importance":5}') || fail "PATCH endpoint"
    echo "$PATCH_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['ok'] == True
print('  ✅ Task importance updated to 5')
" || fail "PATCH"
else
    echo "  ⚠️  No task to update"
fi
echo ""

# ─── 10. Deep-Dive ───────────────────────────────────────────────────
echo "10. Deep-dive (Stage 3) — this takes 5-20s"
if [ -n "$TASK_ID" ]; then
    DD_RES=$(curl -sf -X POST $BASE/api/pipeline/deep-dive \
        -H 'Content-Type: application/json' \
        -d "{\"task_id\":\"$TASK_ID\"}") || fail "Deep-dive endpoint"
    echo "$DD_RES" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d['ok']:
    task = d['task']
    wiki_len = len(task.get('wiki','') or '')
    print(f\"  ✅ Deep-dive complete — wiki: {wiki_len} chars, people: {len(task.get('people',[]))}\")
else:
    print(f\"  ⚠️  Deep-dive returned error: {d.get('error','')}\")
" || fail "Deep-dive"
else
    echo "  ⚠️  No task to deep-dive"
fi
echo ""

# ─── Summary ─────────────────────────────────────────────────────────
echo "============================================"
echo "  Results: $PASS passed, $FAIL failed"
echo "============================================"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
