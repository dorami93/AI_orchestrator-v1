import re
from js import document, window
from pyodide.ffi import create_proxy


def markdown(text):
    text = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    text = re.sub(
        r"```(\w*)\n([\s\S]*?)```",
        r'<pre><code>\2</code><button onclick="window.copyCode(this)">コピー</button></pre>',
        text
    )

    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def copy_code(button):
    window.navigator.clipboard.writeText(
        button.previousElementSibling.textContent
    )
    button.textContent = "コピー済"


window.copyCode = create_proxy(copy_code)


def render_messages(element, chat):
    element.innerHTML = ""

    for message in chat["messages"]:
        div = document.createElement("div")
        div.className = "msg " + message["role"]
        div.innerHTML = markdown(message["content"])
        element.appendChild(div)

    element.scrollTop = element.scrollHeight
