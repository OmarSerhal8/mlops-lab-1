"""Check the processed Food-11 data contract before training or release."""

import argparse
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

if __package__:
    from src.food11.data import CLASSES
else:
    from data import CLASSES

SPLITS = ("training", "validation", "evaluation")


def validate(root: Path, min_per_class: int = 50, tau: float = 0.05) -> bool:
    issues: dict[str, list[str]] = defaultdict(list)
    counts = {split: {class_name: 0 for class_name in CLASSES} for split in SPLITS}
    hashes: dict[str, tuple[str, Path]] = {}

    if not root.is_dir():
        print(f"FAIL dataset: {root} does not exist")
        return False

    for split in SPLITS:
        split_dir = root / split
        actual = {p.name for p in split_dir.iterdir() if p.is_dir()} if split_dir.is_dir() else set()
        expected = set(CLASSES)
        if actual != expected:
            issues["class folders"].append(
                f"{split}: missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
            )

        for class_name in CLASSES:
            class_dir = split_dir / class_name
            if not class_dir.is_dir():
                continue
            for path in class_dir.iterdir():
                if not path.is_file():
                    issues["images"].append(f"{path}: not a regular image file")
                    continue
                counts[split][class_name] += 1
                try:
                    with Image.open(path) as image:
                        image.load()
                        if image.mode != "RGB" or image.size != (128, 128):
                            issues["images"].append(
                                f"{path}: mode={image.mode}, size={image.size}"
                            )
                except (OSError, ValueError) as exc:
                    issues["images"].append(f"{path}: {exc}")

                digest = hashlib.md5(path.read_bytes()).hexdigest()
                previous = hashes.get(digest)
                if previous is not None and previous[0] != split:
                    issues["cross-split duplicates"].append(f"{previous[1]} == {path}")
                else:
                    hashes[digest] = (split, path)

            if counts[split][class_name] < min_per_class:
                issues["minimum count"].append(
                    f"{split}/{class_name}: {counts[split][class_name]} < {min_per_class}"
                )

    training_total = sum(counts["training"].values())
    validation_total = sum(counts["validation"].values())
    if training_total == 0 or validation_total == 0:
        issues["class balance"].append("training or validation split is empty")
    else:
        for class_name in CLASSES:
            train_share = counts["training"][class_name] / training_total
            val_share = counts["validation"][class_name] / validation_total
            if abs(train_share - val_share) > tau:
                issues["class balance"].append(
                    f"{class_name}: training={train_share:.3f}, validation={val_share:.3f}"
                )

    for check in ("class folders", "images", "minimum count", "cross-split duplicates", "class balance"):
        errors = issues[check]
        print(f"{'FAIL' if errors else 'PASS'} {check}" + (f": {len(errors)} issue(s); {errors[0]}" if errors else ""))
    return not any(issues.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--min-per-class", type=int, default=50)
    parser.add_argument("--tau", type=float, default=0.05)
    args = parser.parse_args()
    if args.min_per_class < 0 or not 0 <= args.tau <= 1:
        parser.error("--min-per-class must be nonnegative and --tau must be between 0 and 1")
    sys.exit(0 if validate(args.dataset, args.min_per_class, args.tau) else 1)


if __name__ == "__main__":
    main()
