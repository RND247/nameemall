// NameEmAll Daily stats API (Cloudflare Worker + D1).
//
//   POST /v1/daily/result   submit a ranked Daily result, returns the day's stats for that player
//   GET  /v1/daily/stats    ?day=N&mode=mini|midi[&player=ID]  day stats (+ percentile for player)
//   GET  /v1/daily/counts   ?day=N  players per mode (lobby)
//   POST /v1/transfer       store an encrypted progress snapshot for 24h (body {id, data})
//   GET  /v1/transfer/:id   fetch it on another device
//   GET  /health
//
// Everything is anonymous: the browser sends a random player ID. Raw IPs are never stored;
// a salted, per-day hash is kept only to rate-limit abuse.

const EPOCH_MS = Date.UTC(2026, 3, 30); // Daily #1 = 2026-04-30
const MODES = { mini: 5, midi: 30 };
const MAX_PER_IP_PER_DAY = 40;          // submissions (all modes) from one network per daily
const MAX_ROWS_FOR_RATES = 20000;       // cap rows scanned for per-Pokémon found rates
const PLAYER_RE = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const cors = corsHeaders(request, env);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });

    try {
      if (url.pathname === '/health') return json({ ok: true }, 200, cors);
      if (url.pathname === '/v1/daily/result' && request.method === 'POST') return await submitResult(request, env, cors);
      if (url.pathname === '/v1/daily/stats' && request.method === 'GET') return await getStats(url, env, cors);
      if (url.pathname === '/v1/daily/counts' && request.method === 'GET') return await getCounts(url, env, cors);
      if (url.pathname === '/v1/transfer' && request.method === 'POST') return await putTransfer(request, env, cors);
      if (url.pathname.startsWith('/v1/transfer/') && request.method === 'GET') return await getTransfer(url, request, env, cors);
      return json({ error: 'not_found' }, 404, cors);
    } catch (err) {
      console.error(err && err.stack || err);
      return json({ error: 'server_error' }, 500, cors);
    }
  }
};

// ── Helpers ──

function json(body, status, headers, extra) {
  return new Response(JSON.stringify(body), {
    status,
    headers: Object.assign({ 'Content-Type': 'application/json; charset=utf-8' }, headers, extra || {})
  });
}

function corsHeaders(request, env) {
  const origin = request.headers.get('Origin') || '';
  const allowed = String(env.ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
  const h = { 'Vary': 'Origin' };
  if (allowed.includes(origin)) {
    h['Access-Control-Allow-Origin'] = origin;
    h['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS';
    h['Access-Control-Allow-Headers'] = 'Content-Type';
    h['Access-Control-Max-Age'] = '86400';
  }
  return h;
}

function currentDay(now) {
  return Math.floor((now - EPOCH_MS) / 86400000) + 1;
}

// Players see "today" in their own time zone, so accept yesterday..tomorrow (UTC-12 .. UTC+14).
function dayAccepted(day, now) {
  const d = currentDay(now);
  return Number.isInteger(day) && day >= Math.max(1, d - 1) && day <= d + 1;
}

async function ipHash(request, env, day) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const data = new TextEncoder().encode(`${env.IP_SALT || 'dev-salt'}|${day}|${ip}`);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(digest)].slice(0, 12).map(b => b.toString(16).padStart(2, '0')).join('');
}

function parseDayMode(url) {
  const day = Number(url.searchParams.get('day'));
  const mode = url.searchParams.get('mode');
  return { day, mode };
}

// ── POST /v1/daily/result ──

async function submitResult(request, env, cors) {
  let body;
  try { body = await request.json(); } catch (e) { return json({ error: 'bad_json' }, 400, cors); }
  const now = Date.now();
  const { player, day, mode, score, total, time_ms, gave_up, found, lang } = body || {};

  if (typeof player !== 'string' || !PLAYER_RE.test(player)) return json({ error: 'bad_player' }, 400, cors);
  if (!MODES[mode]) return json({ error: 'bad_mode' }, 400, cors);
  if (!dayAccepted(day, now)) return json({ error: 'bad_day' }, 400, cors);
  if (total !== MODES[mode]) return json({ error: 'bad_total' }, 400, cors);
  if (!Number.isInteger(score) || score < 0 || score > total) return json({ error: 'bad_score' }, 400, cors);
  if (!Number.isInteger(time_ms) || time_ms < 0 || time_ms > 86400000) return json({ error: 'bad_time' }, 400, cors);
  if (typeof found !== 'string' || found.length !== total || !/^[01]+$/.test(found)) return json({ error: 'bad_found' }, 400, cors);
  if ((found.match(/1/g) || []).length !== score) return json({ error: 'found_mismatch' }, 400, cors);
  // Nobody types a Pokémon name in under ~0.25s; rejects obviously scripted results
  if (score > 0 && time_ms < score * 250) return json({ error: 'too_fast' }, 400, cors);
  const safeLang = typeof lang === 'string' && /^[A-Za-z-]{2,10}$/.test(lang) ? lang : null;

  const hash = await ipHash(request, env, day);
  const recent = await env.DB.prepare('SELECT COUNT(*) AS n FROM daily_results WHERE day = ? AND ip_hash = ?')
    .bind(day, hash).first();
  if (recent && recent.n >= MAX_PER_IP_PER_DAY) return json({ error: 'rate_limited' }, 429, cors);

  // First ranked result per player/day/mode wins; later submissions are ignored
  await env.DB.prepare(
    'INSERT OR IGNORE INTO daily_results (day, mode, player_id, score, total, time_ms, gave_up, found, lang, ip_hash, created_at) ' +
    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
  ).bind(day, mode, player, score, total, time_ms, gave_up ? 1 : 0, found, safeLang, hash, now).run();

  return json(await buildStats(env, day, mode, player), 200, cors);
}

// ── GET /v1/daily/stats ──

async function getStats(url, env, cors) {
  const { day, mode } = parseDayMode(url);
  if (!MODES[mode] || !Number.isInteger(day) || day < 1 || day > currentDay(Date.now()) + 1) return json({ error: 'bad_request' }, 400, cors);
  const player = url.searchParams.get('player');
  const stats = await buildStats(env, day, mode, player && PLAYER_RE.test(player) ? player : null);
  return json(stats, 200, cors, { 'Cache-Control': player ? 'no-store' : 'public, max-age=30' });
}

async function buildStats(env, day, mode, player) {
  const total = MODES[mode];
  const agg = await env.DB.prepare(
    'SELECT COUNT(*) AS players, SUM(CASE WHEN score = total THEN 1 ELSE 0 END) AS perfect, ' +
    'SUM(gave_up) AS gave_up, AVG(score) AS avg_score, ' +
    'AVG(CASE WHEN score = total THEN time_ms END) AS avg_perfect_ms ' +
    'FROM daily_results WHERE day = ? AND mode = ?'
  ).bind(day, mode).first();
  const players = (agg && agg.players) || 0;

  const dist = await env.DB.prepare('SELECT score, COUNT(*) AS n FROM daily_results WHERE day = ? AND mode = ? GROUP BY score')
    .bind(day, mode).all();
  const distribution = new Array(total + 1).fill(0);
  for (const r of dist.results || []) if (r.score >= 0 && r.score <= total) distribution[r.score] = r.n;

  // How many players named each Pokémon (by position in the daily's fixed order)
  const counts = new Array(total).fill(0);
  let scanned = 0;
  if (players > 0) {
    const rows = await env.DB.prepare('SELECT found FROM daily_results WHERE day = ? AND mode = ? LIMIT ?')
      .bind(day, mode, MAX_ROWS_FOR_RATES).all();
    for (const r of rows.results || []) {
      scanned++;
      for (let i = 0; i < total && i < r.found.length; i++) if (r.found.charCodeAt(i) === 49) counts[i]++;
    }
  }
  const foundRates = counts.map(c => scanned ? Math.round(c * 100 / scanned) : null);

  const out = {
    day, mode, total, players,
    perfect: (agg && agg.perfect) || 0,
    gave_up: (agg && agg.gave_up) || 0,
    avg_score: agg && agg.avg_score != null ? Math.round(agg.avg_score * 10) / 10 : null,
    avg_perfect_ms: agg && agg.avg_perfect_ms != null ? Math.round(agg.avg_perfect_ms) : null,
    distribution,
    found_rates: foundRates
  };

  if (player) {
    const me = await env.DB.prepare('SELECT score, time_ms FROM daily_results WHERE day = ? AND mode = ? AND player_id = ?')
      .bind(day, mode, player).first();
    if (me) {
      // "You beat X%": players with fewer Pokémon named, or the same count but slower
      const beaten = await env.DB.prepare(
        'SELECT COUNT(*) AS n FROM daily_results WHERE day = ? AND mode = ? AND (score < ? OR (score = ? AND time_ms > ?))'
      ).bind(day, mode, me.score, me.score, me.time_ms).first();
      out.you = {
        score: me.score,
        time_ms: me.time_ms,
        beat: beaten ? beaten.n : 0,
        beat_pct: players > 1 ? Math.round(((beaten ? beaten.n : 0) * 100) / (players - 1)) : null
      };
    }
  }
  return out;
}

// ── GET /v1/daily/counts ──

async function getCounts(url, env, cors) {
  const day = Number(url.searchParams.get('day'));
  if (!Number.isInteger(day) || day < 1 || day > currentDay(Date.now()) + 1) return json({ error: 'bad_request' }, 400, cors);
  const rows = await env.DB.prepare('SELECT mode, COUNT(*) AS n FROM daily_results WHERE day = ? GROUP BY mode').bind(day).all();
  const out = { day, mini: 0, midi: 0 };
  for (const r of rows.results || []) if (MODES[r.mode]) out[r.mode] = r.n;
  return json(out, 200, cors, { 'Cache-Control': 'public, max-age=60' });
}

// ── Device transfer ──
// The browser sends only a fingerprint of the code (id) and data it already encrypted with the code,
// so nothing stored here can be read without the code the player was shown.
const TRANSFER_TTL_MS = 24 * 3600 * 1000;
const TRANSFER_MAX_BYTES = 300000;
const TRANSFER_LIMITS = { put: 20, get: 60 };   // per network per day
const TRANSFER_ID_RE = /^[a-f0-9]{64}$/;

async function transferHit(request, env, kind) {
  const day = Math.floor(Date.now() / 86400000);
  const hash = await ipHash(request, env, day);
  const row = await env.DB.prepare('SELECT n FROM transfer_hits WHERE ip_hash = ? AND day = ? AND kind = ?').bind(hash, day, kind).first();
  if (row && row.n >= TRANSFER_LIMITS[kind]) return false;
  await env.DB.prepare('INSERT INTO transfer_hits (ip_hash, day, kind, n) VALUES (?, ?, ?, 1) ON CONFLICT(ip_hash, day, kind) DO UPDATE SET n = n + 1')
    .bind(hash, day, kind).run();
  return true;
}

async function putTransfer(request, env, cors) {
  let body;
  try { body = await request.json(); } catch (e) { return json({ error: 'bad_json' }, 400, cors); }
  const { id, data } = body || {};
  if (typeof id !== 'string' || !TRANSFER_ID_RE.test(id)) return json({ error: 'bad_id' }, 400, cors);
  if (typeof data !== 'string' || !data.length || data.length > TRANSFER_MAX_BYTES || !/^[A-Za-z0-9+/=]+$/.test(data)) return json({ error: 'bad_data' }, 400, cors);
  if (!(await transferHit(request, env, 'put'))) return json({ error: 'rate_limited' }, 429, cors);
  const now = Date.now();
  await env.DB.prepare('DELETE FROM transfers WHERE expires_at < ?').bind(now).run();
  await env.DB.prepare('INSERT OR REPLACE INTO transfers (id, data, created_at, expires_at) VALUES (?, ?, ?, ?)')
    .bind(id, data, now, now + TRANSFER_TTL_MS).run();
  return json({ ok: true, expires_at: now + TRANSFER_TTL_MS }, 200, cors);
}

async function getTransfer(url, request, env, cors) {
  const id = url.pathname.slice('/v1/transfer/'.length);
  if (!TRANSFER_ID_RE.test(id)) return json({ error: 'bad_id' }, 400, cors);
  if (!(await transferHit(request, env, 'get'))) return json({ error: 'rate_limited' }, 429, cors);
  const row = await env.DB.prepare('SELECT data, expires_at FROM transfers WHERE id = ?').bind(id).first();
  if (!row || row.expires_at < Date.now()) return json({ error: 'not_found' }, 404, cors, { 'Cache-Control': 'no-store' });
  return json({ data: row.data, expires_at: row.expires_at }, 200, cors, { 'Cache-Control': 'no-store' });
}
