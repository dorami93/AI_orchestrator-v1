import re

from js import document, window
from pyodide.ffi import create_proxy


CODE_BLOCK_RE = re.compile(r"```(\w*)\n([\s\S]*?)```")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def escape_html(text):
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_markdown(text):
    html = escape_html(text)

    html = CODE_BLOCK_RE.sub(
        lambda m:
            f'<pre><code>{m.group(2)}</code>'
            f'<button class="copyBtn" '
            f'onclick="window.copyCode(this)">コピー</button></pre>',
        html
    )

    html = INLINE_CODE_RE.sub(r"<code>\1</code>", html)
    html = BOLD_RE.sub(r"<b>\1</b>", html)

    return html


def copy_code(btn):
    window.navigator.clipboard.writeText(
        btn.previousElementSibling.textContent
    )
    btn.textContent = "コピー済"

    window.setTimeout(
        create_proxy(lambda *_: setattr(btn, "textContent", "コピー")),
        1500
    )


window.copyCode = create_proxy(copy_code)


def render_messages(messages_el, chat):
    messages_el.innerHTML = ""

    for message in chat["messages"]:
        div = document.createElement("div")
        div.className = "msg " + message["role"]
        div.innerHTML = render_markdown(message["content"])
        messages_el.appendChild(div)

    messages_el.scrollTop = messages_el.scrollHeight
