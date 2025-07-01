import art
from art.local import LocalBackend
import asyncio
from dotenv import load_dotenv
from typing import List, cast
from local_email_db import generate_database
from load_scenarios import load_scenarios
from art.utils import iterate_dataset


load_dotenv()


async def train():
    generate_database()

    model = art.TrainableModel(
        base_model="Qwen/Qwen2.5-14B-Instruct",
        project="agent-class-art",
        name="model_1",
    )

    with LocalBackend() as backend:
        await model.register(backend)

        print("Loading training data...")
        train_scenarios = load_scenarios(split="train", limit=1000)
        print("Loading validation data...")
        val_scenarios = load_scenarios(split="test", limit=100)

        print(f"Training data size: {len(train_scenarios)}")
        print(f"Validation data size: {len(val_scenarios)}")

        train_iterator = iterate_dataset(
            train_scenarios,
            groups_per_step=12,
            num_epochs=3,
            initial_step=await model.get_step(),
        )

        for batch, epoch, global_step, epoch_step in train_iterator:
            if global_step % 10 == 0:
                print(f"\n--- Evaluating at Iteration {global_step} ---")
                await benchmark_model(model, step=global_step)

            groups = await art.gather_trajectory_groups(
                (
                    art.TrajectoryGroup(
                        (
                            rollout(model, scenario)
                            for _ in range(
                                model.config.training_config.trajectories_per_group
                            )
                        )
                    )
                    for scenario in batch
                )
            )

            # Optionally rescore each trajectory group with the LLM-judge before training.
            training_cfg = model.config.training_config
            if training_cfg.use_judge_group_variant is not None:
                judge_tasks = [
                    group_judge.judge(
                        cast(list[ProjectTrajectory], g.trajectories),
                    )
                    for g in groups
                ]

                results = await asyncio.gather(*judge_tasks, return_exceptions=True)

                # Determine which groups succeeded.
                successful_groups = []
                for grp_idx, (g, res) in enumerate(zip(groups, results)):
                    if isinstance(res, Exception):
                        print(
                            f"WARNING:JUDGE_GROUP_FAILED group={grp_idx} step={global_step}: {res!r}",
                            flush=True,
                        )
                    else:
                        successful_groups.append(g)

                # Replace `groups` with the subset that passed judgement so
                # that training only uses trajectories with judge rewards.
                groups = successful_groups

                for g in groups:
                    for t in g.trajectories:
                        report_trajectory(model, t, global_step)

                # If every group failed, skip this training step entirely.
                if not groups:
                    print(
                        f"WARNING:ALL_JUDGE_GROUPS_FAILED step={global_step}; skipping training step",
                        flush=True,
                    )
                    continue  # Proceed to next batch/epoch without training.

            # Drop groups with reward standard deviation below threshold
            if (
                training_cfg.minimum_reward_std_dev is not None
                and training_cfg.minimum_reward_std_dev > 0
            ):
                filtered_groups = []
                for grp_idx, g in enumerate(groups):
                    rewards = [t.reward for t in g.trajectories]
                    if len(rewards) < 2:
                        std_dev = 0.0
                    else:
                        std_dev = statistics.pstdev(rewards)
                    if std_dev < training_cfg.minimum_reward_std_dev:
                        print(
                            f"WARNING:REWARD_STD_DEV_TOO_LOW group={grp_idx} step={global_step} stddev={std_dev:.4f}; dropping group",
                            flush=True,
                        )
                        continue
                    filtered_groups.append(g)

                # Replace groups with only those meeting the std dev threshold
                groups = filtered_groups

                # If every group failed the std dev filter, skip this training step
                if not groups:
                    print(
                        f"WARNING:ALL_GROUPS_DROPPED_LOW_STD_DEV step={global_step}; skipping training step",
                        flush=True,
                    )
                    continue  # Proceed to next batch/epoch without training.

            await model.train(
                groups,
                config=art.TrainConfig(
                    learning_rate=model.config.training_config.learning_rate
                ),
            )

        await benchmark_model(model, step=global_step)
        await backend._experimental_push_to_s3(
            model,
            s3_bucket=os.environ["BACKUP_BUCKET"],
        )
        print("Training finished.")


if __name__ == "__main__":
    asyncio.run(train())
