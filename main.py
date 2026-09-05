import asyncio
import json
import time
from js import document, localStorage, window, console
from pyodide.ffi import create_proxy
from call_llm import stream_groq_reply
from output import render_messages

DEFAULT_MODEL = "llama-3.3-70b-versatile"


def async_handler(coro_func):
    def wrapper(*args):
        asyncio.ensure_future(coro_func(*args))
    return create_proxy(wrapper)


def on(elt, event, handler):
    elt.addEventListener(event, handler)


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

chats = json.loads(localStorage.getItem("chats") or "[]")
current_id = localStorage.getItem("currentId")
sending = False


def save_chats():
    localStorage.setItem("chats", json.dumps(chats, ensure_ascii=False))


def get_current():
    return next((c for c in chats if c["id"] == current_id), None)


def do_render_messages():
    render_messages(messages_el, chat_title_el, get_current())


def new_chat(*_):
    global current_id
    chat = {"id": str(int(time.time() * 1000)), "title": "新規チャット", "messages": []}
    chats.insert(0, chat)
    current_id = chat["id"]
    localStorage.setItem("currentId", current_id)
    save_chats()
    render_chat_list()
    do_render_messages()
    sidebar.classList.remove("show")


def delete_chat(chat_id, event):
    global current_id, chats
    event.stopPropagation()
    if not window.confirm("このチャットを削除しますか？"):
        return
    chats = [c for c in chats if c["id"] != chat_id]
    current_id = chats[0]["id"] if (current_id == chat_id and chats) else current_id
    save_chats()
    localStorage.setItem("currentId", current_id or "")
    render_chat_list()
    do_render_messages()


def select_chat(chat_id, *_):
    global current_id
    current_id = chat_id
    localStorage.setItem("currentId", current_id)
    render_chat_list()
    do_render_messages()
    sidebar.classList.remove("show")


def render_chat_list():
    chat_list_el.innerHTML = ""
    for c in chats:
        div = document.createElement("div")
        div.className = "chatItem" + (" active" if c["id"] == current_id else "")
        div.innerHTML = "<span></span><button>×</button>"
        div.querySelector("span").textContent = c["title"]
        on(div, "click", create_proxy(lambda e, cid=c["id"]: select_chat(cid, e)))
        on(div.querySelector("button"), "click", create_proxy(lambda e, cid=c["id"]: delete_chat(cid, e)))
        chat_list_el.appendChild(div)


def auto_resize(*_):
    input_el.style.height = "auto"
    input_el.style.height = f"{min(input_el.scrollHeight, 150)}px"


def on_input_keydown(event):
    if event.key == "Enter" and not event.shiftKey:
        event.preventDefault()
        input_form.requestSubmit()


def open_settings(*_):
    api_key_input.value = localStorage.getItem("apiKey") or ""
    model_input.value = localStorage.getItem("model") or DEFAULT_MODEL
    settings_modal.classList.remove("hidden")


def close_settings(*_):
    settings_modal.classList.add("hidden")


def save_settings(*_):
    localStorage.setItem("apiKey", api_key_input.value.strip())
    localStorage.setItem("model", model_input.value.strip() or DEFAULT_MODEL)
    settings_modal.classList.add("hidden")


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

    chat = get_current() or (new_chat(), get_current())[1]
    chat["messages"].append({"role": "user", "content": text})
    if chat["title"] == "新規チャット":
        chat["title"] = text[:20]

    input_el.value = ""
    auto_resize()
    render_chat_list()
    do_render_messages()
    save_chats()

    sending = True
    send_btn.disabled = True
    assistant_msg = {"role": "assistant", "content": ""}
    chat["messages"].append(assistant_msg)
    model = localStorage.getItem("model") or DEFAULT_MODEL

    try:
        await stream_groq_reply(chat, assistant_msg, api_key, model, do_render_messages)
    except Exception as err:
        assistant_msg["content"] = "エラー: " + str(err)
        do_render_messages()
        console.error(str(err))

    sending = False
    send_btn.disabled = False
    save_chats()


on(input_el, "input", create_proxy(auto_resize))
on(input_el, "keydown", create_proxy(on_input_keydown))
on(q("newChatBtn"), "click", create_proxy(new_chat))
on(q("menuBtn"), "click", create_proxy(lambda *_: sidebar.classList.toggle("show")))
on(q("settingsBtn"), "click", create_proxy(open_settings))
on(q("closeSettingsBtn"), "click", create_proxy(close_settings))
on(q("saveSettingsBtn"), "click", create_proxy(save_settings))
on(input_form, "submit", async_handler(on_submit))

render_chat_list()
do_render_messages()
