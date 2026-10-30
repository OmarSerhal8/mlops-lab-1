from PIL import Image

from src.food11.data import CLASSES, category_from_filename, resize_image


def test_category_from_filename():
    assert category_from_filename("0_12.jpg") == "Bread"
    assert category_from_filename("10_3.jpg") == "Vegetable-Fruit"


def test_resize_image_shape_and_mode():
    image = Image.new("L", (512, 384))
    output = resize_image(image)
    assert output.size == (128, 128)
    assert output.mode == "RGB"


def test_eleven_classes():
    assert len(CLASSES) == 11
