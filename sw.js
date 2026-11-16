// NameEmAll service worker: makes the site installable and playable offline.
//
// - Same-origin files (the page, pokemon.json, translations...): network first, so a new
//   deploy shows up on the next load; the cached copy is used only when offline.
// - Pokémon sprites and other pinned CDN files: cache first (they never change), capped.
// - Analytics, the stats API and PeerJS signalling are never cached.
//
// Bump CACHE_VERSION only to force-clear old caches; normal deploys don't need it.
const CACHE_VERSION = 'v1';
const APP_CACHE = 'nea-app-' + CACHE_VERSION;
const CDN_CACHE = 'nea-cdn-' + CACHE_VERSION;
const CDN_MAX_ENTRIES = 1500;

const PRECACHE = [
  '/',
  '/pokemon.json',
  '/families.json',
  '/pokemon_forms.json',
  '/pokemon_details.json',
  '/manifest.webmanifest',
  '/img/icons/icon-192.png',
];
const CDN_HOSTS = ['cdn.jsdelivr.net', 'raw.githubusercontent.com', 'unpkg.com'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(APP_CACHE)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys
        .filter((k) => k.startsWith('nea-') && k !== APP_CACHE && k !== CDN_CACHE)
        .map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

async function networkFirst(request) {
  const cache = await caches.open(APP_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (err) {
    const cached = await cache.match(request, { ignoreSearch: true });
    if (cached) return cached;
    // Offline on a page we never cached (e.g. /?gens=3 or a landing page): open the game
    if (request.mode === 'navigate') {
      const home = await cache.match('/');
      if (home) return home;
    }
    throw err;
  }
}

async function trimCache(cache) {
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - CDN_MAX_ENTRIES; i++) await cache.delete(keys[i]);
}

async function cacheFirst(request) {
  const cache = await caches.open(CDN_CACHE);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  // Opaque (no-cors) image responses have status 0 but are still usable
  if (response.ok || response.type === 'opaque') {
    cache.put(request, response.clone()).then(() => trimCache(cache));
  }
  return response;
}

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);

  if (url.origin === self.location.origin) {
    // version.txt is the "is there an update?" check, so it must always be fresh
    if (url.pathname === '/version.txt') return;
    event.respondWith(networkFirst(request));
    return;
  }
  if (CDN_HOSTS.includes(url.hostname)) {
    event.respondWith(cacheFirst(request));
  }
  // Everything else (Google Analytics, api.nameemall.com, PeerJS servers) goes straight to the network
});
