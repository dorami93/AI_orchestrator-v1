import json
from js import window, fetch
from pyodide.ffi import to_js

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


async def stream_groq_reply(chat, assistant_msg, api_key, model, on_update):
    body = {
        "model": model,
        "messages": [{"role": m["role"], "content": m["content"]} for m in chat["messages"][:-1]],
        "stream": True,
    }
    opts = to_js(
        {"method": "POST", "headers": {"Content-Type": "application/json", "Authorization": "Bearer " + api_key}, "body": json.dumps(body)},
        dict_converter=window.Object.fromEntries,
    )
    response = await fetch(GROQ_ENDPOINT, opts)
    if not response.ok:
        detail = await response.text()
        raise Exception(f"API error {response.status}: {detail}")

    reader = response.body.getReader()
    decoder = window.TextDecoder.new()
    buffer = ""
    while True:
        chunk = await reader.read()
        if chunk.done:
            break
        buffer += decoder.decode(chunk.value, to_js({"stream": True}, dict_converter=window.Object.fromEntries))
        *lines, buffer = buffer.split("\n")
        for line in lines:
            if not line.startswith("data: ") or line[6:] == "[DONE]":
                continue
            delta = json.loads(line[6:])["choices"][0]["delta"].get("content")
            if delta:
                assistant_msg["content"] += delta
                on_update()
