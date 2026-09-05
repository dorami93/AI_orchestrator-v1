# Groq Chat PWA (Pyodide版)

Groq APIを使ったフロントエンドのみのチャットPWA。
アプリのロジックは Python で書かれており、[Pyodide](https://pyodide.org/)（ブラウザ内で動くPythonランタイム）上で実行されます。
GitHub Pagesにそのまま置くだけで動作します。

公開URL: https://dorami93.github.io/AI_orchestrator-v1/

## 公開方法

1. このフォルダの中身をGitHubリポジトリのルート（またはdocs/）に置く
2. リポジトリの Settings > Pages で公開ブランチ・フォルダを設定
3. 公開されたURLにアクセス

## 使い方

1. 初回アクセス時、Pyodide（Pythonランタイム）の読み込みに数秒〜十数秒かかります
2. 右下の「設定」からGroqのAPIキーを入力（https://console.groq.com で取得）
3. 使用するモデル名を入力（例: `llama-3.3-70b-versatile`）
4. 「保存」して、そのままチャット開始

## iPhoneでアプリ化

1. Safariで公開URLを開く
2. 共有ボタン → 「ホーム画面に追加」
3. ホーム画面のアイコンから起動すると全画面のアプリとして使えます

## データについて

- APIキー、モデル名、チャット履歴はすべて端末内のlocalStorageに保存されます
- サーバーへの保存やアカウント登録は一切ありません
- 別端末・別ブラウザとはデータは共有されません

## 仕組み（Pyodideベース）

- `index.html` が CDN 経由で Pyodide を読み込み、`output.py` → `call_llm.py` → `main.py` の順に
  取得して Pyodide の仮想ファイルシステムに書き込んだ後、`import main` でアプリを起動します
- ロジックは役割ごとに3ファイルに分割しています
  - `main.py` — エントリーポイント。DOM取得、チャット状態管理（localStorage）、
    イベント登録、`call_llm`/`output`の呼び出しを行うオーケストレーション役
  - `call_llm.py` — Groq APIへのプロンプト送信とストリーミング応答の受信
  - `output.py` — 簡易Markdown→HTML変換と、メッセージ表示・コードコピー機能
- DOM操作やfetch、localStorageなどのブラウザAPIは、Pyodideの`js`モジュール経由でPythonから直接呼び出しています
- 画面構造（HTML）とスタイル（CSS）は従来のまま変更していません

## ファイル構成

- `index.html` - 画面構造 ＋ Pyodideの読み込み・起動処理
- `style.css` - スタイル（ローディング画面のスタイルを追加）
- `main.py` - エントリーポイント（状態管理・イベント登録）
- `call_llm.py` - Groq APIとのストリーミング通信
- `output.py` - Markdown変換・メッセージ表示
- `manifest.json` - PWAマニフェスト
- `sw.js` - Service Worker（オフラインキャッシュ、Pyodide CDNとGroq APIは対象外）
- `icon-192.png` / `icon-512.png` - アプリアイコン

## 注意点

- 初回起動時にPyodide本体（数十MB程度）をCDNからダウンロードするため、旧JS版よりも起動が遅くなります
- オフライン時は、初回にPyodideの読み込みが完了していないと利用できません
- Pyodideのバージョンは `index.html` 内のCDN URL（`https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js`）で固定しています
