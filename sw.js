// キャッシュ名はデプロイの度に必ず変更する（例: 日付やコミットハッシュ）。
// これを更新し忘れると、ユーザーのブラウザに古いHTML/PYファイルが残り続け、
// 新しいコードとの不整合（例: 要素IDのズレによるエラー）が発生する。
const CACHE = "groq-chat-v6";

const ASSETS = [
  "./",
  "./index.html",
  "./style.css",
  "./main.py",
  "./call_llm.py",
  "./output.py",
  "./manifest.json",
  "./models.json"
];

self.addEventListener("install", e => {
  // 新しいSWをインストール後すぐ有効化candidateにする
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS))
  );
});

self.addEventListener("activate", e => {
  // 現バージョン以外の古いキャッシュを全て削除
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE).map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  // ネットワーク優先: 常に最新ファイルを取りに行き、
  // オフライン時のみキャッシュにフォールバックする。
  e.respondWith(
    fetch(e.request)
      .then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(cache => cache.put(e.request, copy));
        return res;
      })
      .catch(() => caches.match(e.request))
  );
});
