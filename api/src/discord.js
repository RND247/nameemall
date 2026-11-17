// Daily Discord post (Cloudflare cron trigger, once a day at 12:00 UTC).
//
// At 12:00 UTC every time zone from UTC-12 to UTC+14 has finished the previous Daily, so
// yesterday's recap can't spoil a game someone is still playing (the hardest Pokémon is
// still wrapped in a Discord spoiler for anyone catching up on the archive).
//
// Needs the secret DISCORD_WEBHOOK (npx wrangler secret put DISCORD_WEBHOOK).
// Without it the cron does nothing.

const EPOCH_MS = Date.UTC(2026, 3, 30); // Daily #1 = 2026-04-30 (same as the game)
const SITE = 'https://nameemall.com/';
const PLAY_URL = SITE + '?utm_source=discord&utm_medium=social&utm_campaign=daily#daily';
const MODES = [
  { key: 'mini', label: 'Mini', icon: '⚡', size: 5 },
  { key: 'midi', label: 'Midi', icon: '🎯', size: 30 }
];
const MIN_PLAYERS_FOR_STATS = 5; // below this the numbers say more about the sample than the puzzle

export function dayNumberAt(now) {
  return Math.floor((now - EPOCH_MS) / 86400000) + 1;
}

export function dateForDay(n) {
  return new Date(EPOCH_MS + (n - 1) * 86400000).toISOString().slice(0, 10);
}

// ── Same picking as the game (index.html: dailySeedFor, mulberry32, dailyShuffle, dailyBuildItems) ──
function mulberry32(seed) {
  return function() {
    seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function dailySeedFor(dateStr, mode) {
  const str = dateStr + ':' + mode;
  let s = 0;
  for (let i = 0; i < str.length; i++) s = (s * 31 + str.charCodeAt(i)) | 0;
  return s >>> 0;
}
function dailyShuffle(arr, rng) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    const t = a[i]; a[i] = a[j]; a[j] = t;
  }
  return a;
}
// The Daily always draws from Gens 1-9 (ids 1-1025), in Pokédex order
export function dailyPokemon(pokemon, dateStr, mode, size) {
  const pool = pokemon.filter(p => p.id <= 1025);
  const rng = mulberry32(dailySeedFor(dateStr, mode));
  const picked = dailyShuffle(pool.map((_, i) => i), rng).slice(0, Math.min(size, pool.length)).sort((a, b) => a - b);
  return picked.map(i => pool[i]);
}

async function modeStats(env, day, mode, total) {
  const agg = await env.DB.prepare(
    'SELECT COUNT(*) AS players, SUM(CASE WHEN score = total THEN 1 ELSE 0 END) AS perfect, AVG(score) AS avg_score ' +
    'FROM daily_results WHERE day = ? AND mode = ?'
  ).bind(day, mode).first();
  const players = (agg && agg.players) || 0;
  const counts = new Array(total).fill(0);
  if (players > 0) {
    const rows = await env.DB.prepare('SELECT found FROM daily_results WHERE day = ? AND mode = ? LIMIT 20000').bind(day, mode).all();
    for (const r of rows.results || []) {
      for (let i = 0; i < total && i < r.found.length; i++) if (r.found.charCodeAt(i) === 49) counts[i]++;
    }
  }
  return {
    players,
    perfect: (agg && agg.perfect) || 0,
    avg: agg && agg.avg_score != null ? Math.round(agg.avg_score * 10) / 10 : null,
    counts
  };
}

// Builds the message text. `pokemon` is pokemon.json; `stats` maps mode key → modeStats() result.
export function buildDailyMessage(today, pokemon, stats) {
  const lines = [`🗓️ **Daily #${today} is live!** ⚡ Mini (5) and 🎯 Midi (30)`, `<${PLAY_URL}>`];
  const recap = [];
  const yDate = dateForDay(today - 1);
  for (const m of MODES) {
    const s = stats[m.key];
    if (!s || s.players < MIN_PLAYERS_FOR_STATS) continue;
    let line = `${m.icon} ${m.label}: ${s.players} players · average ${s.avg}/${m.size} · ${s.perfect} perfect`;
    if (pokemon) {
      const mons = dailyPokemon(pokemon, yDate, m.key, m.size);
      let hardest = -1;
      for (let i = 0; i < s.counts.length; i++) if (hardest < 0 || s.counts[i] < s.counts[hardest]) hardest = i;
      if (hardest >= 0 && mons[hardest] && s.counts[hardest] < s.players) {
        const pct = Math.round(s.counts[hardest] * 100 / s.players);
        line += ` · hardest: ||${mons[hardest].n}|| (${pct}% named it)`;
      }
    }
    recap.push(line);
  }
  if (recap.length) lines.push('', `**Yesterday (Daily #${today - 1})**`, ...recap);
  return lines.join('\n');
}

export async function postDaily(env, now) {
  if (!env.DISCORD_WEBHOOK) return { skipped: 'no_webhook' };
  const today = dayNumberAt(now);
  const stats = {};
  for (const m of MODES) stats[m.key] = await modeStats(env, today - 1, m.key, m.size);
  let pokemon = null;
  try {
    const r = await fetch(SITE + 'pokemon.json', { cf: { cacheTtl: 3600 } });
    if (r.ok) pokemon = await r.json();
  } catch (e) { /* recap still posts, just without the hardest Pokémon */ }
  const content = buildDailyMessage(today, pokemon, stats);
  const res = await fetch(env.DISCORD_WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    // allowed_mentions: never ping @everyone or anyone else from automated posts
    body: JSON.stringify({ content, allowed_mentions: { parse: [] } })
  });
  if (!res.ok) throw new Error('discord_webhook_' + res.status + ': ' + (await res.text()).slice(0, 200));
  return { posted: today };
}
