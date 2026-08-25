import json
import urllib.error
import urllib.request


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi4-mini"


def ask_ollama(
    prompt,
    *,
    temperature=0.2,
    num_predict=120,
    timeout=120,
):
    """
    Send a prompt to the local Ollama engine.

    Designed for Zyron:
        - local Ollama
        - concise voice responses
        - deterministic behavior
        - controlled output length
        - model kept loaded temporarily
    """

    prompt = str(prompt).strip()

    if not prompt:
        return ""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,

        # Keep the model available for a while after use.
        "keep_alive": "10m",

        # More predictable responses.
        "options": {
            "temperature": temperature,

            # Limit unnecessary long responses.
            "num_predict": num_predict,
        },
    }

    data = json.dumps(
        payload,
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST",
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        return str(
            result.get(
                "response",
                "",
            )
        ).strip()

    except urllib.error.URLError:

        return (
            "I cannot connect to the local AI engine. "
            "Please make sure Ollama is running."
        )

    except TimeoutError:

        return (
            "The local AI engine took too long "
            "to respond."
        )

    except Exception as error:

        return f"AI error: {error}"