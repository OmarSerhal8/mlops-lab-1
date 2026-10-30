"""Promote a registered Food-11 model only when it clears a statistical gate."""

import argparse
import math
import os
from pathlib import Path

from mlflow.tracking import MlflowClient

import mlflow


def test_size_for_run(run, data_root: Path) -> int:
    dataset = run.data.params.get("dataset")
    if dataset not in ("mini", "processed"):
        raise ValueError("Champion run has no recognized dataset parameter; pass --test-size")
    folder = data_root / ("food11_processed_mini" if dataset == "mini" else "food11_processed") / "evaluation"
    if not folder.is_dir():
        raise ValueError(f"Missing test split at {folder}; pass --test-size")
    size = sum(1 for path in folder.rglob("*") if path.is_file())
    if size == 0:
        raise ValueError(f"Test split is empty at {folder}")
    return size


def promote(client: MlflowClient, name: str, version: str, test_size: int | None, data_root: Path) -> str:
    candidate = client.get_model_version(name, version)
    champion = client.get_model_version_by_alias(name, "champion")
    candidate_run = client.get_run(candidate.run_id)
    champion_run = client.get_run(champion.run_id)

    metric = "test_accuracy"
    if metric not in candidate_run.data.metrics or metric not in champion_run.data.metrics:
        raise ValueError(f"Both runs must have the {metric} metric")
    candidate_accuracy = candidate_run.data.metrics[metric]
    champion_accuracy = champion_run.data.metrics[metric]
    if not 0 <= candidate_accuracy <= 1 or not 0 <= champion_accuracy <= 1:
        raise ValueError("Test accuracies must be between 0 and 1")

    n = test_size if test_size is not None else test_size_for_run(champion_run, data_root)
    if n <= 0:
        raise ValueError("Test size must be positive")
    standard_error = math.sqrt(champion_accuracy * (1 - champion_accuracy) / n)
    threshold = champion_accuracy + 2 * standard_error
    decision = "champion" if candidate_accuracy >= threshold else "challenger"

    client.set_registered_model_alias(name, decision, candidate.version)
    for key, value in {
        "promotion_decision": decision,
        "candidate_accuracy": candidate_accuracy,
        "champion_accuracy": champion_accuracy,
        "required_accuracy": threshold,
        "test_size": n,
    }.items():
        client.set_model_version_tag(name, candidate.version, key, str(value))

    print(
        f"version {candidate.version}: {decision}; candidate={candidate_accuracy:.4f}, "
        f"champion={champion_accuracy:.4f}, 2*SE={2 * standard_error:.4f}, "
        f"required={threshold:.4f}, n={n}"
    )
    return decision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--model-name", default="food11")
    parser.add_argument("--test-size", type=int, help="Override the test split size")
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    args = parser.parse_args()

    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000"))
    promote(MlflowClient(), args.model_name, args.version, args.test_size, args.data_root)


if __name__ == "__main__":
    main()
