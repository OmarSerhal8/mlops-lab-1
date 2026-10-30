"""Prepare Food-11 images for training and validation."""

from pathlib import Path

from PIL import Image

CLASSES = [
    "Bread", "Dairy product", "Dessert", "Egg", "Fried food", "Meat",
    "Noodles-Pasta", "Rice", "Seafood", "Soup", "Vegetable-Fruit",
]
CLASS_NAMES = {str(index): name for index, name in enumerate(CLASSES)}

RAW_DIR = Path("data/food11_raw")
PROCESSED_DIR = Path("data/food11_processed")
MINI_DIR = Path("data/food11_processed_mini")
IMAGE_SIZE = (128, 128)
MINI_LIMIT = 100


def category_from_filename(filename: str) -> str:
    """Return the Food-11 category encoded by a filename such as ``3_120.jpg``."""
    class_id = Path(filename).stem.split("_", 1)[0]
    if class_id not in CLASS_NAMES:
        raise ValueError(f"Unknown Food-11 class in filename: {filename}")
    return CLASS_NAMES[class_id]


def resize_image(img: Image.Image, size: int = 128) -> Image.Image:
    """Return an RGB square image of ``size`` pixels per side."""
    return img.convert("RGB").resize((size, size))


def process_split(split: str) -> None:
    input_dir = RAW_DIR / split
    counts = {class_name: 0 for class_name in CLASSES}

    for image_path in input_dir.glob("*.jpg"):
        class_name = category_from_filename(image_path.name)
        output_dir = PROCESSED_DIR / split / class_name
        mini_output_dir = MINI_DIR / split / class_name
        output_dir.mkdir(parents=True, exist_ok=True)
        mini_output_dir.mkdir(parents=True, exist_ok=True)

        with Image.open(image_path) as image:
            resized = resize_image(image)
            resized.save(output_dir / image_path.name)
            if counts[class_name] < MINI_LIMIT:
                resized.save(mini_output_dir / image_path.name)
                counts[class_name] += 1


def main() -> None:
    for split in ("training", "evaluation", "validation"):
        print(f"Processing {split}...")
        process_split(split)
    print("Processing complete.")


if __name__ == "__main__":
    main()
