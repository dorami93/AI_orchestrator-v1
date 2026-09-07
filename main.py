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


# https://console.groq.com/docs/models#production-models のモデルIDをmodels.jsonに記載
async def load_models():
    response = await fetch("models.json")
    model_ids = json.loads(await response.text())

    model.innerHTML = ""
    for model_id in model_ids:
        option = document.createElement("option")
        option.value = model_id
        option.textContent = model_id
        model.appendChild(option)

    model.value = localStorage.getItem("model") or DEFAULT_MODEL


def open_settings(*_):
    api_key.value = localStorage.getItem("apiKey") or ""
    temperature.value = localStorage.getItem("temperature") or "0"
    tokens.value = localStorage.getItem("tokens") or "2000"
    asyncio.ensure_future(load_models())
    settings.classList.remove("hidden")


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
