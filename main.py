import asyncio, json
from js import document, localStorage
from pyodide.ffi import create_proxy
from call_llm import stream_groq_reply
from output import render_messages

DEFAULT_MODEL = "llama-3.3-70b-versatile"

input_el = document.getElementById("input")
send_btn = document.getElementById("sendBtn")
messages_el = document.getElementById("messages")
settings = document.getElementById("settingsModal")
api_key = document.getElementById("apiKeyInput")
model = document.getElementById("modelInput")
temperature = document.getElementById("temperatureInput")
tokens = document.getElementById("tokensInput")
json_input = document.getElementById("jsonInput")

chat = {"messages": []}
schema = None
sending = False


def proxy(func):
    def wrapper(*args):
        asyncio.ensure_future(func(*args))
    return create_proxy(wrapper)


def open_settings(*_):
    api_key.value = localStorage.getItem("apiKey") or ""
    model.value = localStorage.getItem("model") or DEFAULT_MODEL
    temperature.value = localStorage.getItem("temperature") or "1"
    tokens.value = localStorage.getItem("maxTokens") or "1024"
    settings.classList.remove("hidden")


def save_settings(*_):
    localStorage.setItem("apiKey", api_key.value.strip())
    localStorage.setItem("model", model.value.strip() or DEFAULT_MODEL)
    localStorage.setItem("temperature", temperature.value or "1")
    localStorage.setItem("maxTokens", tokens.value or "1024")
    settings.classList.add("hidden")


async def select_json(event):
    global schema
    try:
        schema = json.loads(await event.target.files.item(0).text())
    except Exception:
        schema = None


async def edit_message(*_):
    global sending
    if sending or not (text := input_el.value.strip()):
        return

    key = localStorage.getItem("apiKey")
    if not key:
        open_settings()
        return

    input_el.value = ""
    chat["messages"].append({"role": "user", "content": text})
    assistant = {"role": "assistant", "content": ""}
    chat["messages"].append(assistant)
    render_messages(messages_el, chat)

    sending = True
    send_btn.disabled = True

    try:
        await stream_groq_reply(
            chat, assistant, key,
            localStorage.getItem("model") or DEFAULT_MODEL,
            float(localStorage.getItem("temperature") or 1),
            int(localStorage.getItem("maxTokens") or 1024),
            schema,
            lambda: render_messages(messages_el, chat)
        )
    except Exception as e:
        assistant["content"] = "エラー: " + str(e)
        render_messages(messages_el, chat)

    sending = False
    send_btn.disabled = False


send_btn.addEventListener("click", proxy(edit_message))
document.getElementById("settingsBtn").addEventListener("click", create_proxy(open_settings))
document.getElementById("saveSettingsBtn").addEventListener("click", create_proxy(save_settings))
document.getElementById("closeSettingsBtn").addEventListener("click", create_proxy(lambda *_: settings.classList.add("hidden")))
json_input.addEventListener("change", proxy(select_json))
