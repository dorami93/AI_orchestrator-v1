# Groq Chat PWA

 Groq APIを使ったフロントエンドのみのチャットPWAです。

 Pythonで書かれたロジックを[Pyodide](<https://pyodide.org/>)上で実行します。

 公開URL: https://dorami93.github.io/AI_orchestrator-v1/

 ## 公開方法

 1. ファイルをGitHubリポジトリのルートまたは`docs/`に置く
2. GitHubのSettings \> Pagesから公開するブランチとフォルダを設定
3. 公開URLにアクセスする

 ## 使い方

 1. 公開URLを開く
2. 「設定」からGroq API Keyを入力
3. モデルを選択
4. Temperatureと最大出力トークン数を設定
5. 必要ならJSON Schemaを選択
6. メッセージを入力して「送信」

 JSON Schemaを指定しない場合は通常のMarkdown形式で出力します。

 ## iPhoneでアプリ化

 Safariで公開URLを開き、「共有」→「ホーム画面に追加」でPWAとして利用できます。

 ## データ

 API Key、モデル、Temperature、最大出力トークン数は端末の`localStorage`に保存されます。

 チャット内容はページを閉じると保持されません。

 ## 仕組み

 - `index.html` — 画面構造とPyodideの起動
- `main.py` — 入力、設定、モデル取得、送信処理
- `call_llm.py` — Groq APIとの通信
- `output.py` — Markdown変換とメッセージ表示
- `style.css` — スタイル
- `manifest.json` — PWA設定
- `sw.js` — Service Worker
- `icon-192.png` / `icon-512.png` — アプリアイコン

 `index.html`がPyodideを読み込み、`main.py`、`call_llm.py`、`output.py`をPyodide上で実行します。

 ## 注意

 初回起動時はPyodide本体の読み込みに時間がかかります。

 Groq APIを使用するため、チャットにはインターネット接続が必要です。

 Pyodideのバージョンは`index.html`内のCDN URLで固定しています。
 
