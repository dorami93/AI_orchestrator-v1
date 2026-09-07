import asyncio
import json
from js import document, localStorage

from call_llm import call_groq
from output import render_messages


DEFAULT_MODEL = "openai/gpt-oss-120b"

input_el = document.getElementById("input")
send_btn = document.getElementById("sendBtn")
messages_el = document.getElementById("messages")

api_key_input = document.getElementById("apiKeyInput")
model_input = document.getElementById("modelInput")
temperature_input = document.getElementById("temperatureInput")
tokens_input = document.getElementById("tokensInput")
json_input = document.getElementById("jsonInput")
settings = document.getElementById("settingsModal")

messages = []
schema = None


def open_settings(*_):
    api_key_input.value = localStorage.getItem("apiKey") or ""
    model_input.value = localStorage.getItem("model") or DEFAULT_MODEL
    temperature_input.value = localStorage.getItem("temperature") or "0"
    tokens_input.value = localStorage.getItem("tokens") or "2000"
    settings.classList.remove("hidden")


def save_settings(*_):
    localStorage.setItem("apiKey", api_key_input.value.strip())
    localStorage.setItem("model", model_input.value.strip() or DEFAULT_MODEL)
    localStorage.setItem("temperature", temperature_input.value or "0")
    localStorage.setItem("tokens", tokens_input.value or "2000")
    settings.classList.add("hidden")


def close_settings(*_):
    settings.classList.add("hidden")


async def select_json(event):
    global schema
    file = event.target.files.item(0)
    if file:
        schema = json.loads(await file.text())


async def edit_message(*_):
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
            float(localStorage.getItem("temperature") or 0),
            int(localStorage.getItem("tokens") or 2000),
            schema
        )
        messages.append({"role": "assistant", "content": result})
    except Exception as e:
        messages.append({"role": "assistant", "content": "エラー: " + str(e)})

    render_messages(messages_el, messages)


send_btn.onclick = lambda *_: asyncio.ensure_future(edit_message())
document.getElementById("settingsBtn").onclick = open_settings
document.getElementById("saveSettingsBtn").onclick = save_settings
document.getElementById("closeSettingsBtn").onclick = close_settings
json_input.onchange = lambda e: asyncio.ensure_future(select_json(e))
