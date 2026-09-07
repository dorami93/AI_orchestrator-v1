import asyncio
import json
from js import document, localStorage, fetch

from call_llm import call_groq
from output import render_messages


DEFAULT_MODEL = "openai/gpt-oss-120b"

input_el = document.getElementById("input")
messages_el = document.getElementById("messages")
settings = document.getElementById("settingsModal")

api_key = document.getElementById("apiKeyInput")
model = document.getElementById("modelInput")
temperature = document.getElementById("temperatureInput")
tokens = document.getElementById("tokensInput")
json_input = document.getElementById("jsonInput")

messages = []
schema = None


async def load_models():
    key = api_key.value.strip()
    model.innerHTML = ""

    if not key:
        placeholder = document.createElement("option")
        placeholder.value = ""
        placeholder.textContent = "先にAPI Keyを入力してください"
        model.appendChild(placeholder)
        return

    try:
        response = await fetch(
            "https://api.groq.com/openai/v1/models",
            {"headers": {"Authorization": f"Bearer {key}"}}
        )
    except Exception as e:
        placeholder = document.createElement("option")
        placeholder.value = ""
        placeholder.textContent = "通信エラー: モデル一覧を取得できません"
        model.appendChild(placeholder)
        print(f"[load_models] fetch failed: {e}")
        return

    if not response.ok:
        placeholder = document.createElement("option")
        placeholder.value = ""
        text = await response.text()
        placeholder.textContent = f"API Keyが無効か権限がありません ({response.status})"
        model.appendChild(placeholder)
        print(f"[load_models] response not ok: {response.status} {text}")
        return

    data = json.loads(await response.text())

    # 音声専用モデル(whisper系)やガード用の小型モデルなど、
    # チャット補完(chat/completions)で使えないモデルは選択肢から除外する。
    excluded_prefixes = ("whisper", "canopylabs", "meta-llama/llama-prompt-guard", "llama-prompt-guard")
    chat_models = [
        item for item in data.get("data", [])
        if not item["id"].lower().startswith(excluded_prefixes)
    ]

    if not chat_models:
        placeholder = document.createElement("option")
        placeholder.value = ""
        placeholder.textContent = "利用可能なチャットモデルが見つかりません"
        model.appendChild(placeholder)
        return

    for item in chat_models:
        option = document.createElement("option")
        option.value = item["id"]
        option.textContent = item["id"]
        model.appendChild(option)

    saved = localStorage.getItem("model") or DEFAULT_MODEL

    if any(item["id"] == saved for item in chat_models):
        model.value = saved
    else:
        model.value = chat_models[0]["id"]


def open_settings(*_):
    api_key.value = localStorage.getItem("apiKey") or ""
    temperature.value = localStorage.getItem("temperature") or "0"
    tokens.value = localStorage.getItem("tokens") or "2000"

    settings.classList.remove("hidden")
    asyncio.ensure_future(load_models())


def on_api_key_change(*_):
    # APIキーを入力し終えたタイミングでモデル一覧を再取得する。
    # 保存ボタンを押すまで待つ必要がないようにする。
    asyncio.ensure_future(load_models())


def save_settings(*_):
    localStorage.setItem("apiKey", api_key.value.strip())
    localStorage.setItem("model", model.value)
    localStorage.setItem("temperature", temperature.value or "0")
    localStorage.setItem("tokens", tokens.value or "2000")
    settings.classList.add("hidden")


def close_settings(*_):
    settings.classList.add("hidden")


async def select_json(event):
    global schema

    file = event.target.files.item(0)

    if not file:
        schema = None
        return

    try:
        schema = json.loads(await file.text())
    except Exception:
        schema = None


async def edit_message():
    text = input_el.value.strip()
    key = localStorage.getItem("apiKey")

    if not text or not key:
        return

    input_el.value = ""
    messages.append({"role": "user", "content": text})
    render_messages(messages_el, messages)

    try:
        result = await call_groq(
            messages,
            key,
            localStorage.getItem("model") or DEFAULT_MODEL,
            float(localStorage.getItem("temperature") or "0"),
            int(localStorage.getItem("tokens") or "2000"),
            schema
        )

        messages.append({"role": "assistant", "content": result})

    except Exception as e:
        messages.append({"role": "assistant", "content": "エラー: " + str(e)})

    render_messages(messages_el, messages)


def submit(event):
    event.preventDefault()
    asyncio.ensure_future(edit_message())


def bind(el_id, el, attr, handler):
    # キャッシュされた古いHTMLなどでDOM要素が見つからない場合に
    # AttributeError で全体がクラッシュするのを防ぐ
    if el is None:
        print(f"[warn] element #{el_id} not found; skipping binding")
        return
    setattr(el, attr, handler)


bind("inputForm", document.getElementById("inputForm"), "onsubmit", submit)
bind("settingsBtn", document.getElementById("settingsBtn"), "onclick", open_settings)
bind("saveSettingsBtn", document.getElementById("saveSettingsBtn"), "onclick", save_settings)
bind("closeSettingsBtn", document.getElementById("closeSettingsBtn"), "onclick", close_settings)
bind("jsonInput", json_input, "onchange", lambda e: asyncio.ensure_future(select_json(e)))
bind("apiKeyInput", api_key, "onchange", on_api_key_change)
