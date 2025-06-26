MAX_TURNS = 10

from pydantic import BaseModel
from litellm import acompletion
from litellm.utils import function_to_dict
from textwrap import dedent
from pydantic import ValidationError, validate_call
from email_search_tools import (
    search_emails,
    read_email as read_email_tool,
    SearchResult,
)
from langchain_core.utils.function_calling import convert_to_openai_tool
import litellm
from litellm.caching.caching import LiteLLMCacheType, Cache
import json
import weave
from rich import print
import logging
from panza import limit_concurrency

litellm.cache = Cache(type=LiteLLMCacheType.DISK)
logging.getLogger("weave.trace.op").setLevel(logging.WARNING)
logging.getLogger("LiteLLM").setLevel(logging.WARNING)


class Scenario(BaseModel):
    question: str
    inbox: str


weave.init(project_name="agent-class-art")


class RolloutResult(BaseModel):
    final_answer: str | None = None
    matches_expected_answer: bool | None = None
    tool_calls: list[dict] = []


@limit_concurrency(5)
async def check_answer(response: str, expected_answer: str) -> bool:
    """Return True if *response* is semantically equivalent to *expected_answer*.

    The judgment is delegated to the "openrouter/gemini/gemini-2.5-flash" model via
    LiteLLM. The model is prompted to output **only** a single token indicating the
    match (``TRUE`` or ``FALSE``) so we can reliably parse the result as a boolean.
    """

    judge_system_prompt = dedent(
        """
        You are an strict evaluator for question-answering tasks. Your job is to
        decide whether a *candidate* answer conveys the **same information** as the
        *reference* answer. The wording can differ – focus only on the meaning. If
        the answers are semantically identical, reply with the single word
        "TRUE". Otherwise reply with the single word "FALSE". Do **not** output
        anything else.
        """
    )

    messages = [
        {"role": "system", "content": judge_system_prompt},
        {
            "role": "user",
            "content": (
                "Reference answer:\n"
                + expected_answer
                + "\n\nCandidate answer:\n"
                + response
                + "\n\nAre these answers semantically identical?"
            ),
        },
    ]

    # Ask Gemini-Flash to grade the answer
    completion = await acompletion(
        model="openrouter/gemini/gemini-2.5-flash",
        messages=messages,
        caching=True,
    )

    # Extract model output (may come back as a dict or a LiteLLM wrapper)
    try:
        content: str = completion["choices"][0]["message"]["content"].strip().lower()  # type: ignore[index]
    except Exception:
        # Fallback: best-effort stringification
        content = str(completion).strip().lower()

    # Accept a few reasonable variants of a positive/negative response
    if content.startswith(("true", "yes", "1")):
        return True
    if content.startswith(("false", "no", "0")):
        return False

    # If the output is unrecognisable, be conservative and treat as non-match
    return False


# @weave.op()
async def rollout(scenario: Scenario) -> RolloutResult | None:
    system_prompt = dedent(
        """
        You are an agent that can search my inbox for information. You will be given a question by the user, and you must search the inbox to find the answer.
        """
    )

    async def search_inbox(keywords: list[str]) -> list[SearchResult]:
        """
        Search the inbox for emails that match the given keywords.
        """
        return search_emails(keywords=keywords, inbox=scenario.inbox)

    async def read_email(message_id: str) -> dict:
        """
        Read an email from the inbox.
        """
        result = read_email_tool(message_id=message_id)
        if result is None:
            return {"error": "Email not found"}
        return result.model_dump()

    tools = [search_inbox, read_email]

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": scenario.question},
    ]

    # Keep track of every tool call issued during the dialogue so we can
    # surface them to the caller in the RolloutResult object.
    executed_tool_calls: list[dict] = []

    # Placeholder that will hold the agent's final answer once we receive it.
    final_response: str | None = None

    for turn in range(MAX_TURNS):
        print(f"Turn {turn}")
        response = await acompletion(
            model="openrouter/qwen/qwen3-32b",
            messages=messages,
            tools=[convert_to_openai_tool(t) for t in tools],
            tool_choice="required",
            caching=True,
        )

        tool_calls = response["choices"][0]["message"].get("tool_calls", None)
        if tool_calls is None:
            # The model did not request any subsequent tool calls, so we treat
            # the current content as the final answer and exit the loop.
            final_response = response["choices"][0]["message"]["content"]
            print(f"Final response: {final_response}")
            break

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            print(f"Tool {tool_name} called with args: {tool_args}")

            for tool_fn in tools:
                if tool_fn.__name__ == tool_call.function.name:
                    try:
                        validated_fn = validate_call(tool_fn)
                        tool_result = await validated_fn(**tool_args)

                        # Remember this tool invocation so we can surface it in
                        # the RolloutResult returned to the caller.
                        executed_tool_calls.append(
                            {
                                "name": tool_fn.__name__,
                                "arguments": tool_args,
                                "result": tool_result,
                            }
                        )

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(tool_result),
                            }
                        )
                    except ValidationError as e:
                        print(f"Invalid args for {tool_call.function.name}: {e}")
                        break

    # After exhausting the dialogue turns, decide what to return.
    if final_response is None:
        # We never obtained a conclusive answer from the agent.
        return None

    # Construct the RolloutResult payload. matches_expected_answer cannot be
    # filled here because the expected answer is unknown to this function.
    return RolloutResult(
        final_answer=final_response,
        matches_expected_answer=None,
        tool_calls=executed_tool_calls,
    )


if __name__ == "__main__":
    import asyncio

    scenario = Scenario(
        question="What time is my flight on Friday?", inbox="kyle@openpipe.ai"
    )
    asyncio.run(rollout(scenario))
