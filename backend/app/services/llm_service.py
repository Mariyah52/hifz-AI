import json
from typing import Awaitable, Callable

import httpx

from app.config import settings

CHAT_API_URL = "https://api.openai.com/v1/chat/completions"
MAX_TOOL_ROUNDS = 4

ExecuteTool = Callable[[str, dict], Awaitable[dict]]


class LLMError(Exception):
    pass


async def run_chat_with_tools(
    messages: list[dict],
    tools: list[dict],
    execute_tool: ExecuteTool,
) -> tuple[str, list[str]]:
    """
    Runs the standard OpenAI tool-calling loop: send messages + tool
    definitions, and if the model asks to call a tool, run it (via
    `execute_tool`, real backend logic — see assistant_service.py) and
    feed the real result back, repeating until the model produces a plain
    text reply or MAX_TOOL_ROUNDS is hit. Returns (reply_text, tool_names_called).

    Deliberately raw httpx rather than the `openai` SDK — one more
    external dependency avoided, same choice Phase 14 made for Whisper.
    """
    if not settings.openai_api_key:
        raise LLMError("The assistant isn't configured on this server — OPENAI_API_KEY is unset.")

    conversation = list(messages)
    tools_called: list[str] = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        for _ in range(MAX_TOOL_ROUNDS):
            response = await client.post(
                CHAT_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.assistant_chat_model,
                    "messages": conversation,
                    "tools": tools,
                },
            )
            if response.status_code != 200:
                raise LLMError(f"Assistant request failed (HTTP {response.status_code}): {response.text[:300]}")

            body = response.json()
            choice = body["choices"][0]["message"]

            tool_calls = choice.get("tool_calls")
            if not tool_calls:
                return choice.get("content") or "", tools_called

            # The model wants to call one or more tools before replying —
            # append its request, execute each tool for real, and feed
            # the real results back as 'tool' messages.
            conversation.append(choice)
            for call in tool_calls:
                name = call["function"]["name"]
                tools_called.append(name)
                try:
                    args = json.loads(call["function"].get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = await execute_tool(name, args)
                conversation.append(
                    {"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)}
                )

    return (
        "I looked into that but couldn't finish putting together an answer — try asking again.",
        tools_called,
    )
