import re
from js import document


def markdown(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"```(\w*)\n([\s\S]*?)```", r"<pre><code>\2</code></pre>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


def render_messages(element, messages):
    element.innerHTML = ""

    for message in messages:
        div = document.createElement("div")
        div.className = "msg " + message["role"]
        div.innerHTML = markdown(message["content"])
        element.appendChild(div)

    element.scrollTop = element.scrollHeight
