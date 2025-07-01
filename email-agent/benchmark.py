from load_scenarios import load_scenarios
from run_agent import run_and_score_agent
from rich import print
from tqdm.asyncio import tqdm

scenarios = load_scenarios(limit=10)

MODELS_TO_BENCHMARK = [
    "openai/gpt-4.1",
    "openai/gpt-4o",
]

# for scenario in scenarios:
#     answer, accept = await run_and_score_agent(scenario)
#     print(f"Scenario {scenario.id}: {accept}")
#     print(f"Answer: {answer.answer}")
#     print(f"Source IDs: {answer.source_ids}")
#     print()


async def benchmark_model(model: str, max_scenarios: int = 10) -> float:
    scenarios = load_scenarios(limit=max_scenarios, split="test")
    scores = []
    results = await tqdm.gather(
        *[run_and_score_agent(scenario) for scenario in scenarios]
    )
    for result in results:
        scores.append(result[1])
    return sum(scores) / len(scores)


async def benchmark_models(
    models: list[str], max_scenarios: int = 10
) -> dict[str, float]:
    results = await tqdm.gather(
        *[benchmark_model(model, max_scenarios) for model in models]
    )
    return {model: score for model, score in zip(models, results)}


if __name__ == "__main__":
    import asyncio

    results = asyncio.run(benchmark_models(MODELS_TO_BENCHMARK))
    print(results)
