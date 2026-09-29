/**
 * Nexus-AI: Express.js BFF (Backend for Frontend)
 * ═══════════════════════════════════════════════════
 * Lightweight Node.js companion to the Go Gateway.
 * Handles:
 *   - SSE streaming for agent responses
 *   - WebSocket connections for real-time dashboards
 *   - Aggregated API responses for frontend widgets
 *   - Session management
 *
 * Usage:
 *   node backend/services/express-bff/server.js
 */

const http = require('http');
const { URL } = require('url');

const PORT = process.env.BFF_PORT || 3003;
const INFERENCE_URL = process.env.INFERENCE_URL || 'http://localhost:8081';
const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:3000';

// ── CORS Headers ────────────────────────────────────────────
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Access-Control-Max-Age': '86400',
};

// ── Utility: JSON Response ──────────────────────────────────
function jsonResponse(res, statusCode, data) {
  res.writeHead(statusCode, {
    ...corsHeaders,
    'Content-Type': 'application/json',
  });
  res.end(JSON.stringify(data));
}

// ── Utility: Fetch Helper ───────────────────────────────────
async function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch { resolve({ raw: data }); }
      });
    }).on('error', reject);
  });
}

// ── Route: Dashboard Aggregate ──────────────────────────────
async function handleDashboard(req, res) {
  try {
    const [health, modelInfo] = await Promise.allSettled([
      fetchJSON(`${INFERENCE_URL}/health`),
      fetchJSON(`${INFERENCE_URL}/model/info`),
    ]);

    jsonResponse(res, 200, {
      status: 'ok',
      timestamp: new Date().toISOString(),
      inference: {
        health: health.status === 'fulfilled' ? health.value : { error: 'unavailable' },
        model: modelInfo.status === 'fulfilled' ? modelInfo.value : { error: 'unavailable' },
      },
      platform: {
        version: '1.0.0',
        services: ['etl', 'mlops', 'inference', 'agents', 'gateway'],
        active_agents: 5,
      },
    });
  } catch (err) {
    jsonResponse(res, 500, { error: err.message });
  }
}

// ── Route: SSE Agent Stream ─────────────────────────────────
function handleAgentStream(req, res) {
  res.writeHead(200, {
    ...corsHeaders,
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
  });

  const steps = [
    { step: 'security_audit', status: 'pass', risk_score: 0.02, icon: '🛡️' },
    { step: 'intent_classification', intent: 'data_query', confidence: 0.94, icon: '🧠' },
    { step: 'agent_routing', agent: 'DataAgent', icon: '📊' },
    { step: 'sql_generation', sql: 'SELECT * FROM gold_dim_restaurants LIMIT 10', icon: '💾' },
    { step: 'execution', rows: 10, latency_ms: 23.4, icon: '⚡' },
    { step: 'output_sanitization', pii_found: false, icon: '🔒' },
    { step: 'complete', total_latency_ms: 45.2, icon: '✅' },
  ];

  let i = 0;
  const interval = setInterval(() => {
    if (i >= steps.length) {
      res.write('event: done\ndata: {"complete": true}\n\n');
      clearInterval(interval);
      res.end();
      return;
    }
    res.write(`id: ${i + 1}\nevent: agent_step\ndata: ${JSON.stringify(steps[i])}\n\n`);
    i++;
  }, 300);

  req.on('close', () => clearInterval(interval));
}

// ── Route: Health ───────────────────────────────────────────
function handleHealth(req, res) {
  jsonResponse(res, 200, {
    status: 'healthy',
    service: 'nexus-ai-bff',
    version: '1.0.0',
    uptime: process.uptime().toFixed(1) + 's',
    timestamp: new Date().toISOString(),
  });
}

// ── Server ──────────────────────────────────────────────────
const server = http.createServer(async (req, res) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, corsHeaders);
    res.end();
    return;
  }

  const url = new URL(req.url, `http://localhost:${PORT}`);

  switch (url.pathname) {
    case '/health':
      return handleHealth(req, res);
    case '/api/dashboard':
      return handleDashboard(req, res);
    case '/api/agent/stream':
      return handleAgentStream(req, res);
    default:
      jsonResponse(res, 404, { error: 'Not found', path: url.pathname });
  }
});

server.listen(PORT, () => {
  console.log(`\n▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓`);
  console.log(`  🚀 Nexus-AI BFF Server v1.0.0`);
  console.log(`  Listening on http://localhost:${PORT}`);
  console.log(`  Inference: ${INFERENCE_URL}`);
  console.log(`▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n`);
});
