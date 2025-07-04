import sky
import textwrap
from dotenv import dotenv_values
from sky import ClusterStatus
from all_experiments import models

print("Launching on SkyPilot…")


def run_training(model_name: str):
    setup_script = textwrap.dedent(
        """
            echo 'Setting up environment...'
            apt install -y nvtop
            curl -LsSf https://astral.sh/uv/install.sh | sh
            source $HOME/.local/bin/env

            uv sync
        """
    )

    run_command = f"uv run train.py --model {model_name}"

    # Create a SkyPilot Task
    task = sky.Task(
        name=f"train-{model_name}",
        setup=setup_script,
        run=run_command,
        workdir=".",  # Sync the project directory
        envs=dict(dotenv_values()),  # type: ignore
    )
    task.set_resources(sky.Resources(accelerators="H100-SXM:1"))

    # Generate cluster name
    cluster_name = f"class-email-assistant-{model_name}"
    print(f"Launching task on cluster: {cluster_name}")

    print("Checking for existing cluster and jobs…")
    cluster_status = sky.get(sky.status(cluster_names=[cluster_name]))
    if len(cluster_status) > 0 and cluster_status[0]["status"] == ClusterStatus.UP:
        print(f"Cluster {cluster_name} is UP. Canceling any active jobs…")
        sky.stream_and_get(sky.cancel(cluster_name, all=True))

    # Launch the task; stream_and_get blocks until the task starts running, but
    # running this in its own thread means all models run in parallel.
    job_id, _ = sky.stream_and_get(
        sky.launch(
            task,
            cluster_name=cluster_name,
            retry_until_up=True,
            idle_minutes_to_autostop=20,
            down=True,
            fast=True,
        )
    )

    print(f"Job submitted for {cluster_name} (ID: {job_id}). Streaming logs…")
    exit_code = sky.tail_logs(cluster_name=cluster_name, job_id=job_id, follow=True)
    print(f"Job {job_id} for {cluster_name} finished with exit code {exit_code}.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Launch a SkyPilot training job for a specific model defined in all_experiments.py"
    )
    parser.add_argument(
        "--model",
        required=True,
        help="The key of the model to train as defined in all_experiments.py (e.g. 'run_1')",
    )

    args = parser.parse_args()

    if args.model not in models:
        available = ", ".join(models.keys())
        raise ValueError(f"Unknown model '{args.model}'. Available models: {available}")

    run_training(args.model)
