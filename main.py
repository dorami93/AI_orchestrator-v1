import asyncio
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

chat = {"messages": []}
sending = False


def async_handler(func):
    def wrapper(*args):
        asyncio.ensure_future(func(*args))
    return create_proxy(wrapper)


def open_settings(*_):
    api_key_input.value = localStorage.getItem("apiKey") or ""
    model_input.value = localStorage.getItem("model") or DEFAULT_MODEL
    settings_modal.classList.remove("hidden")


def save_settings(*_):
    localStorage.setItem("apiKey", api_key_input.value.strip())
    localStorage.setItem("model", model_input.value.strip() or DEFAULT_MODEL)
    settings_modal.classList.add("hidden")


def close_settings(*_):
    settings_modal.classList.add("hidden")


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
    chat["messages"].append({"role": "user", "content": text})
    render_messages(messages_el, chat)

    assistant = {"role": "assistant", "content": ""}
    chat["messages"].append(assistant)

    sending = True
    send_btn.disabled = True

    try:
        await stream_groq_reply(
            chat,
            assistant,
            api_key,
            localStorage.getItem("model") or DEFAULT_MODEL,
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
