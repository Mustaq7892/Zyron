from ..ai.ollama_client import ask_ollama
from .web_search import search_web


SYSTEM_PROMPT = """You are Zyron, a personal AI assistant.

Rules:
- Be helpful, clear, and concise.
- Answer in simple English.
- Use conversation history when useful.
- You are running locally through Ollama using phi4-mini.

WEB SEARCH RULES:
- When WEB SEARCH RESULTS are provided, they are the primary source of truth for the current question.
- Use the information from the WEB SEARCH RESULTS directly.
- Do NOT rely on your old built-in knowledge when web results are available.
- NEVER mention your knowledge cutoff.
- NEVER say "as of early 2023".
- NEVER say "as of my knowledge cutoff".
- NEVER discuss your training data or knowledge cutoff unless the user specifically asks about it.
- If the web results show a current version, date, price, release, event, or other fact, use that information in your answer.
- If the web results do not contain enough information, say that the search results do not provide enough information.
"""


def needs_web_search(command):
    """Check whether the question needs current internet information."""

    keywords = [
        "latest",
        "current",
        "today",
        "recent",
        "news",
        "weather",
        "price",
        "stock",
        "version",
        "release",
        "2026",
        "search the web",
        "search online",
    ]

    command_lower = command.lower()

    return any(keyword in command_lower for keyword in keywords)


def handle_ai_command(command, name, memory):

    history = memory.get_context()

    web_context = ""

    if needs_web_search(command):

        print("\n[Zyron is searching the web...]\n")

        search_results = search_web(command, 5)

        web_context = f"""
WEB SEARCH RESULTS:

{search_results}

END WEB SEARCH RESULTS.
"""

    prompt = f"""
{SYSTEM_PROMPT}

User's name: {name}

CONVERSATION HISTORY:
{history if history else "No previous conversation."}

{web_context}

CURRENT USER QUESTION:
{command}

IMPORTANT:
WEB SEARCH RESULTS HAVE PRIORITY OVER YOUR BUILT-IN KNOWLEDGE.

If the user asks for the latest, current, recent, today's, or other
time-sensitive information, use the WEB SEARCH RESULTS.

Do not mention your knowledge cutoff.

Do not say:
- "as of early 2023"
- "as of my knowledge cutoff"
- "according to my training data"

Give the answer directly using the information found in the
WEB SEARCH RESULTS.

Zyron's response:
"""

    response = ask_ollama(prompt)

    memory.add("user", command)
    memory.add("assistant", response)

    return response