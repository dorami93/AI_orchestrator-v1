# app.py
# Groq Chat PWA のロジック本体。Pyodide上で実行され、
# DOM操作・localStorage・fetch はすべて js モジュール経由でブラウザAPIを直接呼び出す。

import asyncio
import json
import re
import time

from js import document, localStorage, window, fetch, console
from pyodide.ffi import create_proxy, to_js


def async_handler(coro_func):
    """async def のイベントハンドラを addEventListener に渡せる形にする。
    Pyodide はコルーチン関数をそのままイベントハンドラとして呼んでも
    自動では await/スケジュールしないため、同期関数でラップして
    asyncio.ensure_future に積む。
    """

    def wrapper(*args):
        asyncio.ensure_future(coro_func(*args))

    return create_proxy(wrapper)


def add_event_listener(elt, event, handler):
    """pyodide.ffi.wrappers.add_event_listener はリスナー登録の管理に
    JsProxy をハッシュキーとして使うため 'unhashable type' で失敗することがある。
    ここでは create_proxy したハンドラを素の addEventListener に渡すだけの
    シンプルな版を使う（このアプリでは個別のremoveは不要なため問題ない）。
    """
    elt.addEventListener(event, handler)


DEFAULT_MODEL = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------------------
# DOM ヘルパー
# ---------------------------------------------------------------------------

def q(id_):
    return document.getElementById(id_)


sidebar = q("sidebar")
chat_list_el = q("chatList")
messages_el = q("messages")
input_form = q("inputForm")
input_el = q("input")
send_btn = q("sendBtn")
chat_title_el = q("chatTitle")
settings_modal = q("settingsModal")
api_key_input = q("apiKeyInput")
model_input = q("modelInput")


# ---------------------------------------------------------------------------
# 状態管理 (localStorage)
# ---------------------------------------------------------------------------

def load_chats():
    raw = localStorage.getItem("chats")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def save_chats():
    localStorage.setItem("chats", json.dumps(chats, ensure_ascii=False))


def get_current():
    for c in chats:
        if c["id"] == current_id:
            return c
    return None


chats = load_chats()
current_id = localStorage.getItem("currentId")
sending = False


# ---------------------------------------------------------------------------
# チャット操作
# ---------------------------------------------------------------------------

def new_chat(*_args):
    global current_id
    chat = {"id": str(int(time.time() * 1000)), "title": "新規チャット", "messages": []}
    chats.insert(0, chat)
    current_id = chat["id"]
    localStorage.setItem("currentId", current_id)
    save_chats()
    render_chat_list()
    render_messages()
    sidebar.classList.remove("show")


def delete_chat(chat_id, event):
    global current_id, chats
    event.stopPropagation()
    if not window.confirm("このチャットを削除しますか？"):
        return
    chats = [c for c in chats if c["id"] != chat_id]
    if current_id == chat_id:
        current_id = chats[0]["id"] if chats else None
    save_chats()
    localStorage.setItem("currentId", current_id or "")
    render_chat_list()
    render_messages()


def select_chat(chat_id, *_args):
    global current_id
    current_id = chat_id
    localStorage.setItem("currentId", current_id)
    render_chat_list()
    render_messages()
    sidebar.classList.remove("show")


# ---------------------------------------------------------------------------
# レンダリング
# ---------------------------------------------------------------------------

def render_chat_list():
    chat_list_el.innerHTML = ""
    for c in chats:
        div = document.createElement("div")
        div.className = "chatItem" + (" active" if c["id"] == current_id else "")
        div.innerHTML = "<span></span><button>×</button>"
        div.querySelector("span").textContent = c["title"]

        select_proxy = create_proxy(lambda e, cid=c["id"]: select_chat(cid, e))
        add_event_listener(div, "click", select_proxy)

        delete_proxy = create_proxy(lambda e, cid=c["id"]: delete_chat(cid, e))
        add_event_listener(div.querySelector("button"), "click", delete_proxy)

        chat_list_el.appendChild(div)


def escape_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


CODE_BLOCK_RE = re.compile(r"```(\w*)\n([\s\S]*?)```")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def render_markdown(text):
    html = escape_html(text)

    def code_block_sub(m):
        code = m.group(2)
        return (
            f'<pre><code>{code}</code>'
            f'<button class="copyBtn" onclick="window.copyCode(this)">コピー</button></pre>'
        )

    html = CODE_BLOCK_RE.sub(code_block_sub, html)
    html = INLINE_CODE_RE.sub(r"<code>\1</code>", html)
    html = BOLD_RE.sub(r"<b>\1</b>", html)
    return html


def copy_code(btn):
    code_el = btn.previousElementSibling
    code = code_el.textContent
    window.navigator.clipboard.writeText(code)
    btn.textContent = "コピー済"

    def restore(*_a):
        btn.textContent = "コピー"

    window.setTimeout(create_proxy(restore), 1500)


# JS側の onclick="window.copyCode(this)" から呼べるように公開
window.copyCode = create_proxy(copy_code)


def render_messages():
    chat = get_current()
    messages_el.innerHTML = ""
    chat_title_el.textContent = chat["title"] if chat else "Groq Chat"
    if not chat:
        return
    for m in chat["messages"]:
        div = document.createElement("div")
        div.className = "msg " + m["role"]
        div.innerHTML = render_markdown(m["content"])
        messages_el.appendChild(div)
    messages_el.scrollTop = messages_el.scrollHeight


# ---------------------------------------------------------------------------
# 入力欄の自動リサイズ / Enter送信
# ---------------------------------------------------------------------------

def auto_resize(*_args):
    input_el.style.height = "auto"
    input_el.style.height = f"{min(input_el.scrollHeight, 150)}px"


def on_input_keydown(event):
    if event.key == "Enter" and not event.shiftKey:
        event.preventDefault()
        input_form.requestSubmit()


add_event_listener(input_el, "input", create_proxy(auto_resize))
add_event_listener(input_el, "keydown", create_proxy(on_input_keydown))


# ---------------------------------------------------------------------------
# 設定モーダル
# ---------------------------------------------------------------------------

def open_settings(*_args):
    api_key_input.value = localStorage.getItem("apiKey") or ""
    model_input.value = localStorage.getItem("model") or DEFAULT_MODEL
    settings_modal.classList.remove("hidden")


def close_settings(*_args):
    settings_modal.classList.add("hidden")


def save_settings(*_args):
    localStorage.setItem("apiKey", api_key_input.value.strip())
    localStorage.setItem("model", model_input.value.strip() or DEFAULT_MODEL)
    settings_modal.classList.add("hidden")


add_event_listener(q("newChatBtn"), "click", create_proxy(new_chat))
add_event_listener(q("menuBtn"), "click", create_proxy(lambda *_: sidebar.classList.toggle("show")))
add_event_listener(q("settingsBtn"), "click", create_proxy(open_settings))
add_event_listener(q("closeSettingsBtn"), "click", create_proxy(close_settings))
add_event_listener(q("saveSettingsBtn"), "click", create_proxy(save_settings))


# ---------------------------------------------------------------------------
# Groq API 通信 (ストリーミング)
# ---------------------------------------------------------------------------

async def stream_groq_reply(chat, assistant_msg, api_key, model):
    body = {
        "model": model,
        "messages": [
            {"role": m["role"], "content": m["content"]}
            for m in chat["messages"][:-1]
        ],
        "stream": True,
    }

    response = await fetch(
        "https://api.groq.com/openai/v1/chat/completions",
        to_js(
            {
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + api_key,
                },
                "body": json.dumps(body),
            },
            dict_converter=window.Object.fromEntries,
        ),
    )

    if not response.ok:
        raise Exception(f"API error: {response.status}")

    reader = response.body.getReader()
    decoder = window.TextDecoder.new()
    buffer = ""

    while True:
        chunk = await reader.read()
        if chunk.done:
            break
        buffer += decoder.decode(chunk.value, to_js({"stream": True}, dict_converter=window.Object.fromEntries))
        lines = buffer.split("\n")
        buffer = lines.pop()
        for line in lines:
            if not line.startswith("data: "):
                continue
            data = line[6:]
            if data == "[DONE]":
                continue
            try:
                obj = json.loads(data)
                delta = obj["choices"][0]["delta"].get("content")
                if delta:
                    assistant_msg["content"] += delta
                    render_messages()
            except Exception:
                pass


async def on_submit(event):
    global sending
    event.preventDefault()
    if sending:
        return

    text = input_el.value.strip()
    if not text:
        return

    api_key = localStorage.getItem("apiKey")
    if not api_key:
        open_settings()
        return

    if not get_current():
        new_chat()
    chat = get_current()

    chat["messages"].append({"role": "user", "content": text})
    if chat["title"] == "新規チャット":
        chat["title"] = text[:20]

    input_el.value = ""
    auto_resize()
    render_chat_list()
    render_messages()
    save_chats()

    sending = True
    send_btn.disabled = True
    assistant_msg = {"role": "assistant", "content": ""}
    chat["messages"].append(assistant_msg)

    model = localStorage.getItem("model") or DEFAULT_MODEL

    try:
        await stream_groq_reply(chat, assistant_msg, api_key, model)
    except Exception as err:
        assistant_msg["content"] = "エラー: " + str(err)
        render_messages()
        console.error(str(err))

    sending = False
    send_btn.disabled = False
    save_chats()


add_event_listener(input_form, "submit", async_handler(on_submit))


# ---------------------------------------------------------------------------
# 初期描画
# ---------------------------------------------------------------------------

render_chat_list()
render_messages()
