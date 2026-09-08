from pathlib import Path
from PIL import Image

CLASS_NAMES = {
    "0": "Bread",
    "1": "Dairy product",
    "2": "Dessert",
    "3": "Egg",
    "4": "Fried food",
    "5": "Meat",
    "6": "Noodles-Pasta",
    "7": "Rice",
    "8": "Seafood",
    "9": "Soup",
    "10": "Vegetable-Fruit",
}

RAW_DIR = Path("data/food11_raw")
PROCESSED_DIR = Path("data/food11_processed")
MINI_DIR = Path("data/food11_processed_mini")

IMAGE_SIZE = (128, 128)
MINI_LIMIT = 100


def process_split(split):
    input_dir = RAW_DIR / split

    counts = {class_id: 0 for class_id in CLASS_NAMES}

    for image_path in input_dir.glob("*.jpg"):
        class_id = image_path.stem.split("_")[0]
        class_name = CLASS_NAMES[class_id]

        output_dir = PROCESSED_DIR / split / class_name
        mini_output_dir = MINI_DIR / split / class_name

        output_dir.mkdir(parents=True, exist_ok=True)
        mini_output_dir.mkdir(parents=True, exist_ok=True)

        with Image.open(image_path) as image:
            image = image.convert("RGB")
            image = image.resize(IMAGE_SIZE)

            output_path = output_dir / image_path.name
            image.save(output_path)

            if counts[class_id] < MINI_LIMIT:
                mini_output_path = mini_output_dir / image_path.name
                image.save(mini_output_path)
                counts[class_id] += 1


def main():
    splits = ["training", "evaluation", "validation"]

    for split in splits:
        print(f"Processing {split}...")
        process_split(split)

    print("Processing complete.")


if __name__ == "__main__":
    main()