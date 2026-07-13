/**
 * Phase 16 added push notifications here. Phase 26 extends this to real
 * app-shell caching — the piece Phase 16's own comment explicitly said
 * this file did NOT do yet.
 *
 * This uses runtime ("cache-as-you-go") caching rather than a build-time
 * precache list: Vite's built JS/CSS filenames are content-hashed and
 * only known after a build, and adding a precache-manifest build step
 * (e.g. vite-plugin-pwa) is a bigger tooling change than this phase
 * needs. Instead, every same-origin GET response is cached the first
 * time it's actually fetched; on a later request, network is tried
 * first and a cache hit is served only if the network fails. Practically:
 * the app shell becomes available offline after the first successful
 * online visit, not before — an honest, standard trade-off for this
 * approach, not a limitation unique to this app.
 */

const APP_SHELL_CACHE = 'hifzai-app-shell-v1';

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((key) => key.startsWith('hifzai-app-shell') && key !== APP_SHELL_CACHE).map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  // Cross-origin requests (the API, the Quran text/audio CDN) have their
  // own caching (offlineSyncService's mutation queue, quranTextCacheDb,
  // audioCacheDb) — this cache is for the app shell itself only.
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api')) return;

  event.respondWith(
    caches.open(APP_SHELL_CACHE).then(async (cache) => {
      try {
        const response = await fetch(request);
        if (response.ok) cache.put(request, response.clone());
        return response;
      } catch (networkError) {
        const cached = await cache.match(request);
        if (cached) return cached;
        // A navigation (loading the app itself, e.g. a deep link while
        // offline) falls back to the cached shell so client-side routing
        // still works, rather than showing the browser's own offline page.
        if (request.mode === 'navigate') {
          const shell = await cache.match('/');
          if (shell) return shell;
        }
        throw networkError;
      }
    }),
  );
});

self.addEventListener('push', (event) => {
  let payload = { title: 'HifzAI', body: 'You have a new notification.' };
  try {
    if (event.data) payload = event.data.json();
  } catch {
    // Non-JSON push payload — fall back to the default text above.
  }

  event.waitUntil(self.registration.showNotification(payload.title, { body: payload.body }));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(self.clients.openWindow('/notifications'));
});
