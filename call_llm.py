import json
from pyodide.http import pyfetch

URL = "https://api.groq.com/openai/v1/chat/completions"


async def call_groq(messages, key, model, temperature, tokens, schema):
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": tokens
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

    response = await pyfetch(
        URL,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        },
        body=json.dumps(body)
    )

    if not response.ok:
        raise Exception(await response.string())

    data = json.loads(await response.string())
    return data["choices"][0]["message"]["content"]
