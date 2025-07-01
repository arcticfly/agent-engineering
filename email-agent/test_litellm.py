# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "litellm[caching]==1.73.6",
#     "python-dotenv",
#     "langchain-core",
#     "datasets",
# ]
# ///
from textwrap import dedent
from litellm import acompletion
import litellm
from dotenv import load_dotenv
import json
from dataclasses import asdict

from litellm.caching.caching import LiteLLMCacheType, Cache

from email_search_tools import search_emails, read_email, SearchResult

# from langchain_core.utils.function_calling import convert_to_openai_tool
import asyncio
from importlib.metadata import version as pkg_version

litellm.cache = Cache(type=LiteLLMCacheType.DISK)

load_dotenv()

MAX_TURNS = 10


# async def main() -> str | None:
#     print(f"LITTELM VERSION: {pkg_version('litellm')}")
#     response = await acompletion(
#         model="openai/gpt-4.1-mini",
#         messages=[
#             {
#                 "role": "system",
#                 "content": "count to 3",
#             },
#         ],
#     )
#     print("finished!")


# asyncio.run(main())


async def run_agent(question: str, inbox: str) -> str | None:
    system_prompt = dedent(
        """
        Use the tools provided to answer the user's question.
        """
    )

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    response = await acompletion(
        model="openrouter/Qwen/Qwen3-32B", messages=messages, max_tokens=1
    )

    response_message = response.choices[0].message
    messages.append(response_message.model_dump(exclude_none=True))


if __name__ == "__main__":
    import asyncio

    answer = asyncio.run(
        run_agent("What time is my meeting on Friday?", "louise.kitchen@enron.com")
    )
    # print("ANSWER:")
    # print(answer)
