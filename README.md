# Groq Chat PWA

Groq APIを使ったフロントエンドのみのチャットPWA。GitHub Pagesにそのまま置くだけで動作します。

## 公開方法

1. このフォルダの中身をGitHubリポジトリのルート（またはdocs/）に置く
2. リポジトリの Settings > Pages で公開ブランチ・フォルダを設定
3. 公開されたURLにアクセス

## 使い方

1. 初回アクセス時、右下の「設定」からGroqのAPIキーを入力（https://console.groq.com で取得）
2. 使用するモデル名を入力（例: `llama-3.3-70b-versatile`）
3. 「保存」して、そのままチャット開始

## iPhoneでアプリ化

1. Safariで公開URLを開く
2. 共有ボタン → 「ホーム画面に追加」
3. ホーム画面のアイコンから起動すると全画面のアプリとして使えます

## データについて

- APIキー、モデル名、チャット履歴はすべて端末内のlocalStorageに保存されます
- サーバーへの保存やアカウント登録は一切ありません
- 別端末・別ブラウザとはデータは共有されません

## ファイル構成

- `index.html` - 画面構造
- `style.css` - スタイル
- `app.js` - アプリロジック（チャット送受信・履歴管理・Markdown表示）
- `manifest.json` - PWAマニフェスト
- `sw.js` - Service Worker（オフラインキャッシュ）
- `icon-192.png` / `icon-512.png` - アプリアイコン
