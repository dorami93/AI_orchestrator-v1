import json

from js import window, fetch
from pyodide.ffi import to_js


GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


async def stream_groq_reply(
    chat,
    assistant_msg,
    api_key,
    model,
    temperature,
    max_tokens,
    response_schema,
    on_update
):
    body = {
        "model": model,
        "messages": [
            {"role": m["role"], "content": m["content"]}
            for m in chat["messages"][:-1]
        ],
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
        "stream": True
    }

    if response_schema:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "strict": True,
                "schema": response_schema
            }
        }
    options = to_js(
        {
            "method": "POST",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key
            },
            "body": json.dumps(body)
        },
        dict_converter=window.Object.fromEntries
    )
    response = await fetch(GROQ_ENDPOINT, options)
    if not response.ok:
        raise Exception(
            f"API error {response.status}: {await response.text()}"
        )
    reader = response.body.getReader()
    decoder = window.TextDecoder.new()
    buffer = ""
    while True:
        chunk = await reader.read()
        if chunk.done:
            break
        buffer += decoder.decode(
            chunk.value,
            to_js(
                {"stream": True},
                dict_converter=window.Object.fromEntries
            )
        )
        *lines, buffer = buffer.split("\n")
        for line in lines:
            if not line.startswith("data: ") or line[6:] == "[DONE]":
                continue

            data = json.loads(line[6:])
            delta = data["choices"][0]["delta"].get("content")

            if delta:
                assistant_msg["content"] += delta
                on_update()
