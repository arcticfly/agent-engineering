from __future__ import annotations

from typing import List, Literal, Optional
import json

from project_types import SyntheticQuery
from rich import print


def load_synthetic_queries(
    path: str,
    *,
    split: Optional[Literal["train", "test"]] = None,
    max_entries: int | None = None,
) -> List[SyntheticQuery]:
    """Load a list of ``SyntheticQuery`` objects from a JSON-Lines file.

    Parameters
    ----------
    path:
        Path to the ``.jsonl`` file produced by ``generate_synthetic_question_data``.
    split:
        If provided, only keep entries whose ``split`` attribute matches this
        value ("train" or "test").
    max_entries:
        If provided, stop after loading *at most* this many matching entries.

    Returns
    -------
    list[SyntheticQuery]
        A list of parsed and (optionally) filtered ``SyntheticQuery`` objects.
    """

    queries: List[SyntheticQuery] = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue  # Skip blank lines

            try:
                sq = SyntheticQuery.model_validate_json(line)
            except Exception:
                # Fallback: if the line isn't valid JSON for Pydantic parsing
                try:
                    data = json.loads(line)
                    sq = SyntheticQuery.model_validate(data)
                except Exception as e:
                    raise ValueError(
                        f"Failed to parse line as SyntheticQuery: {e}\nLine: {line[:100]}..."
                    ) from e

            if split is not None and sq.split != split:
                continue  # Skip unwanted split

            queries.append(sq)

            if max_entries is not None and len(queries) >= max_entries:
                break

    return queries


if __name__ == "__main__":
    queries = load_synthetic_queries(
        "data/synthetic_qa_dataset.jsonl",
        split="test",
        max_entries=2,
    )
    print(f"Loaded {len(queries)} queries")
    print(queries)


def benchmark_one_model(model: str, queries: List[SyntheticQuery]) -> float:
    for query in queries:
        