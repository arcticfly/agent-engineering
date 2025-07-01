from project_types import Scenario
from typing import List, Optional, Literal
from datasets import load_dataset, Dataset
import random

# Define the Hugging Face repository ID
HF_REPO_ID = "corbt/enron_emails_sample_questions"


def load_scenarios(
    split: Literal["train", "test"] = "train",
    limit: Optional[int] = None,
    max_messages: Optional[int] = 1,
    shuffle: bool = False,
    seed: Optional[int] = None,
) -> List[Scenario]:
    dataset: Dataset = load_dataset(HF_REPO_ID, split=split)  # type: ignore

    if max_messages is not None:
        dataset = dataset.filter(lambda x: len(x["message_ids"]) <= max_messages)

    if shuffle or seed is not None:
        if seed is not None:
            dataset = dataset.shuffle(seed=seed)
        else:
            dataset = dataset.shuffle()

    # Convert each row (dict) in the dataset to a Scenario object
    scenarios = [
        Scenario(**row, split=split)  # type: ignore
        for row in dataset  # type: ignore
    ]

    if max_messages is not None:
        scenarios = [
            scenario
            for scenario in scenarios
            if len(scenario.message_ids) <= max_messages
        ]

    if shuffle:
        if seed is not None:
            rng = random.Random(seed)
            rng.shuffle(scenarios)
        else:
            random.shuffle(scenarios)

    if limit is not None:
        return scenarios[:limit]
    else:
        return scenarios


if __name__ == "__main__":
    from rich import print

    scenarios = load_scenarios(limit=10)
    print(scenarios)
