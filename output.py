from js import document


def render_messages(element, messages):
    element.innerHTML = ""

    for message in messages:
        div = document.createElement("div")
        div.className = "msg " + message["role"]
        div.textContent = message["content"]
        element.appendChild(div)

    element.scrollTop = element.scrollHeight
