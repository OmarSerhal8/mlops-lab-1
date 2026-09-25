import io
import os

import mlflow
import torch
from fastapi import FastAPI, File, UploadFile
from PIL import Image
from torchvision import transforms


# ============================================================
# 1. MLFLOW CONFIGURATION
# ============================================================

# Read the MLflow server address from an environment variable.
#
# If MLFLOW_TRACKING_URI does not exist, use the local default:
# http://127.0.0.1:5000
#
# Locally:
#   FastAPI -> 127.0.0.1:5000 -> MLflow
#
# Later in Docker:
#   FastAPI container -> host.docker.internal:5000 -> MLflow on Windows
MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)


# ============================================================
# 2. LOAD MODEL FROM MLFLOW MODEL REGISTRY
# ============================================================

# Ask MLflow to load:
#
# registered model = food11
# alias            = champion
#
# Right now:
# champion -> Version 1
loaded_model = mlflow.pyfunc.load_model(
    "models:/food11@champion"
)

# loaded_model is an MLflow PyFuncModel wrapper.
#
# Because the model was originally logged using:
#
# mlflow.pytorch.log_model(...)
#
# get_raw_model() gives us the actual native PyTorch model:
# ResNet18.
pytorch_model = loaded_model.get_raw_model()

# Put the neural network into inference/evaluation mode.
pytorch_model.eval()


# ============================================================
# 3. CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI()


# ============================================================
# 4. IMAGE PREPROCESSING
# ============================================================

# These are the SAME transformations used during training.
#
# Original image
#     ->
# resize to 224 x 224
#     ->
# convert to PyTorch Tensor
#     ->
# ImageNet normalization
transform = transforms.Compose([
    transforms.Resize((224, 224)),

    transforms.ToTensor(),

    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


# ============================================================
# 5. CLASS NAMES
# ============================================================

# This order matches ImageFolder's class_to_idx mapping
# from the training dataset.
CLASS_NAMES = [
    "Bread",
    "Dairy product",
    "Dessert",
    "Egg",
    "Fried food",
    "Meat",
    "Noodles-Pasta",
    "Rice",
    "Seafood",
    "Soup",
    "Vegetable-Fruit",
]


# ============================================================
# 6. HEALTH ENDPOINT
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ============================================================
# 7. PREDICTION ENDPOINT
# ============================================================

@app.post("/predict")
async def predict(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # Read uploaded file
    # --------------------------------------------------------

    contents = await file.read()

    # Convert the uploaded bytes into a PIL image.
    image = Image.open(
        io.BytesIO(contents)
    ).convert("RGB")


    # --------------------------------------------------------
    # Apply the same preprocessing used during training
    # --------------------------------------------------------

    image_tensor = transform(image)

    # Before:
    # [3, 224, 224]
    #
    # ResNet expects a batch:
    # [batch_size, channels, height, width]
    #
    # After:
    # [1, 3, 224, 224]
    image_tensor = image_tensor.unsqueeze(0)


    # --------------------------------------------------------
    # Run inference
    # --------------------------------------------------------

    # No gradients are needed because we are predicting,
    # not training.
    with torch.no_grad():

        # Pass image through ResNet18.
        #
        # Output shape:
        # [1, 11]
        outputs = pytorch_model(
            image_tensor
        )

        # Convert raw model scores (logits)
        # into probabilities.
        probabilities = torch.softmax(
            outputs,
            dim=1,
        )

        # Find:
        # 1. largest probability
        # 2. index of that class
        confidence, predicted_class = torch.max(
            probabilities,
            dim=1,
        )


    # --------------------------------------------------------
    # Convert class index into class name
    # --------------------------------------------------------

    class_index = predicted_class.item()

    category = CLASS_NAMES[
        class_index
    ]


    # --------------------------------------------------------
    # Return JSON response
    # --------------------------------------------------------

    return {
        "category": category,
        "confidence": confidence.item(),
    }