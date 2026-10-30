from pathlib import Path

from PIL import Image

from src.food11.data import CLASSES
from src.food11.validate_data import validate


def make_dataset(root: Path) -> None:
    for split_index, split in enumerate(("training", "validation", "evaluation")):
        for class_index, class_name in enumerate(CLASSES):
            folder = root / split / class_name
            folder.mkdir(parents=True)
            Image.new("RGB", (128, 128), (30 + split_index * 80, class_index * 20, 0)).save(folder / "image.jpg")


def test_valid_dataset_and_cross_split_duplicate(tmp_path):
    make_dataset(tmp_path)
    assert validate(tmp_path, min_per_class=1)

    source = tmp_path / "training" / "Bread" / "image.jpg"
    target = tmp_path / "evaluation" / "Bread" / "duplicate.jpg"
    target.write_bytes(source.read_bytes())
    assert not validate(tmp_path, min_per_class=1)
