import json
from js import window, fetch
from pyodide.ffi import to_js

URL = "https://api.groq.com/openai/v1/chat/completions"


async def stream_groq_reply(chat, assistant, key, model, temperature, tokens, schema, update):
    body = {
        "model": model,
        "messages": chat["messages"][:-1],
        "temperature": temperature,
        "max_completion_tokens": tokens,
        "stream": True
    }

    if schema:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "strict": True,
                "schema": schema
            }
        }

    options = to_js({
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        },
        "body": json.dumps(body)
    }, dict_converter=window.Object.fromEntries)

    response = await fetch(URL, options)

    if not response.ok:
        raise Exception(await response.text())

    reader = response.body.getReader()
    decoder = window.TextDecoder.new()
    buffer = ""

    while True:
        chunk = await reader.read()
        if chunk.done:
            break

        buffer += decoder.decode(chunk.value, {"stream": True})
        *lines, buffer = buffer.split("\n")

        for line in lines:
            if not line.startswith("data: ") or line[6:] == "[DONE]":
                continue

            delta = json.loads(line[6:])["choices"][0]["delta"].get("content")

            if delta:
                assistant["content"] += delta
                update()
