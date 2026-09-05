const CACHE = 'groq-chat-v3';
const FILES = ['./', 'index.html', 'style.css', 'app.py', 'manifest.json', 'icon-192.png', 'icon-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))));
});

self.addEventListener('fetch', (e) => {
  // Groq API と Pyodide CDN はキャッシュせず常にネットワーク経由で取得する
  if (e.request.url.includes('api.groq.com')) return;
  if (e.request.url.includes('cdn.jsdelivr.net')) return;
  e.respondWith(caches.match(e.request).then(res => res || fetch(e.request)));
});
