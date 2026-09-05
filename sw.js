const CACHE = 'groq-chat-v5';
const FILES = ['./', 'index.html', 'style.css', 'main.py', 'call_llm.py', 'output.py', 'manifest.json', 'icon-192.png', 'icon-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.url.includes('api.groq.com')) return;
  if (e.request.url.includes('cdn.jsdelivr.net')) return;

  // index.html はネットワーク優先。失敗時のみキャッシュへフォールバック。
  if (e.request.mode === 'navigate' || e.request.url.endsWith('index.html')) {
    e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    return;
  }

  e.respondWith(caches.match(e.request).then(res => res || fetch(e.request)));
});
