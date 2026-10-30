"""Replace cross-split duplicates in the mini dataset using the full processed split."""

import hashlib
import shutil
from pathlib import Path

MINI = Path("data/food11_processed_mini")
FULL = Path("data/food11_processed")
SPLITS = ("training", "validation", "evaluation")


def digest(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def main() -> None:
    seen: dict[str, str] = {}
    duplicates: list[Path] = []
    used_hashes: set[str] = set()

    for split in SPLITS:
        for path in sorted((MINI / split).rglob("*")):
            if not path.is_file():
                continue
            key = digest(path)
            used_hashes.add(key)
            if key in seen and seen[key] != split:
                duplicates.append(path)
            else:
                seen[key] = split

    replacements: list[tuple[Path, Path]] = []
    for duplicate in duplicates:
        relative = duplicate.relative_to(MINI)
        full_class_dir = FULL / relative.parent
        mini_class_dir = duplicate.parent
        for candidate in sorted(full_class_dir.iterdir()):
            if not candidate.is_file() or (mini_class_dir / candidate.name).exists():
                continue
            key = digest(candidate)
            if key not in used_hashes:
                replacements.append((duplicate, candidate))
                used_hashes.add(key)
                break
        else:
            raise RuntimeError(f"No unique replacement for {duplicate}")

    for duplicate, candidate in replacements:
        shutil.copy2(candidate, duplicate.parent / candidate.name)
        duplicate.unlink()
        print(f"{duplicate} -> {candidate.name}")
    print(f"Replaced {len(replacements)} cross-split duplicate(s)")


if __name__ == "__main__":
    main()
