import asyncio
import json

from js import document, localStorage
from pyodide.ffi import create_proxy

from call_llm import stream_groq_reply
from output import render_messages


DEFAULT_MODEL = "llama-3.3-70b-versatile"

input_el = document.getElementById("input")
send_btn = document.getElementById("sendBtn")
messages_el = document.getElementById("messages")

settings_modal = document.getElementById("settingsModal")
api_key_input = document.getElementById("apiKeyInput")
model_input = document.getElementById("modelInput")
temperature_input = document.getElementById("temperatureInput")
tokens_input = document.getElementById("tokensInput")
json_input = document.getElementById("jsonInput")

chat = {"messages": []}
response_schema = None
sending = False


def async_handler(func):
    def wrapper(*args):
        asyncio.ensure_future(func(*args))
    return create_proxy(wrapper)


def open_settings(*_):
    api_key_input.value = localStorage.getItem("apiKey") or ""
    model_input.value = localStorage.getItem("model") or DEFAULT_MODEL
    temperature_input.value = localStorage.getItem("temperature") or "1"
    tokens_input.value = localStorage.getItem("maxTokens") or "1024"
    settings_modal.classList.remove("hidden")


def save_settings(*_):
    localStorage.setItem("apiKey", api_key_input.value.strip())
    localStorage.setItem("model", model_input.value.strip() or DEFAULT_MODEL)
    localStorage.setItem("temperature", temperature_input.value or "1")
    localStorage.setItem("maxTokens", tokens_input.value or "1024")
    settings_modal.classList.add("hidden")


def close_settings(*_):
    settings_modal.classList.add("hidden")


async def select_json(event):
    global response_schema

    files = event.target.files
    if not files.length:
        return

    try:
        response_schema = json.loads(await files.item(0).text())
    except Exception:
        response_schema = None


async def edit_message(*_):
    global sending

    if sending:
        return

    text = input_el.value.strip()
    if not text:
        return

    api_key = localStorage.getItem("apiKey")
    if not api_key:
        open_settings()
        return

    input_el.value = ""

    chat["messages"].append({
        "role": "user",
        "content": text
    })

    assistant = {
        "role": "assistant",
        "content": ""
    }

    chat["messages"].append(assistant)
    render_messages(messages_el, chat)

    sending = True
    send_btn.disabled = True

    try:
        await stream_groq_reply(
            chat,
            assistant,
            api_key,
            localStorage.getItem("model") or DEFAULT_MODEL,
            float(localStorage.getItem("temperature") or "1"),
            int(localStorage.getItem("maxTokens") or "1024"),
            response_schema,
            lambda: render_messages(messages_el, chat)
        )
    except Exception as e:
        assistant["content"] = "エラー: " + str(e)
        render_messages(messages_el, chat)

    sending = False
    send_btn.disabled = False


send_btn.addEventListener("click", async_handler(edit_message))

document.getElementById("settingsBtn").addEventListener(
    "click", create_proxy(open_settings)
)

document.getElementById("saveSettingsBtn").addEventListener(
    "click", create_proxy(save_settings)
)

document.getElementById("closeSettingsBtn").addEventListener(
    "click", create_proxy(close_settings)
)

json_input.addEventListener(
    "change", create_proxy(select_json)
)
