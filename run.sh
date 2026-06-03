#!/bin/bash
# GRIP Dashboard — Start / Restart (with Cloudflare tunnel for sharing)
# Usage: bash run.sh

DASHBOARD_DIR="/Users/xuli/.openclaw/workspace-yanqing/grip-dashboard"
PORT=8510

# Kill existing
lsof -ti:$PORT | xargs kill -9 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 1

# Export API key
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-sk-001dccd5ee38475eb85956188e45f7d9}"

# Start Streamlit
cd "$DASHBOARD_DIR"
nohup python3 -m streamlit run app.py --server.port $PORT --server.headless true > /tmp/grip_dashboard.log 2>&1 &
sleep 3

# Verify Streamlit
HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/)
if [ "$HTTP" != "200" ]; then
    echo "❌ Dashboard failed to start (HTTP $HTTP)"
    cat /tmp/grip_dashboard.log | tail -20
    exit 1
fi
echo "✅ Dashboard running on port $PORT"

# Start Cloudflare tunnel
nohup cloudflared tunnel --url http://localhost:$PORT > /tmp/cloudflared.log 2>&1 &
sleep 6
TUNNEL_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cloudflared.log | head -1)

if [ -n "$TUNNEL_URL" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔗 Share this link:"
    echo "   $TUNNEL_URL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "⚠️  Tunnel URL not found — check /tmp/cloudflared.log"
fi
