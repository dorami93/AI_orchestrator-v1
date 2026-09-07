import asyncio
import json
from js import document, localStorage, fetch

from call_llm import call_groq
from output import render_messages


DEFAULT_MODEL = "openai/gpt-oss-120b"

input_el = document.getElementById("input")
send_btn = document.getElementById("sendBtn")
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
    if not key:
        return

    response = await fetch(
        "https://api.groq.com/openai/v1/models",
        {"headers": {"Authorization": f"Bearer {key}"}}
    )

    if not response.ok:
        return

    data = json.loads(await response.text())
    model.innerHTML = ""

    for item in data["data"]:
        option = document.createElement("option")
        option.value = item["id"]
        option.textContent = item["id"]
        model.appendChild(option)

    saved = localStorage.getItem("model") or DEFAULT_MODEL
    if any(x["id"] == saved for x in data["data"]):
        model.value = saved


def open_settings(*_):
    api_key.value = localStorage.getItem("apiKey") or ""
    temperature.value = localStorage.getItem("temperature") or "0"
    tokens.value = localStorage.getItem("tokens") or "2000"
    settings.classList.remove("hidden")
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

    if file:
        try:
            schema = json.loads(await file.text())
        except Exception:
            schema = None


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
            float(localStorage.getItem("temperature") or "0"),
            int(localStorage.getItem("tokens") or "2000"),
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
