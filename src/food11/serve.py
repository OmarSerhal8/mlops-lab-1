"""FastAPI service that loads the current Food-11 champion at startup."""

import io
import os
from typing import Annotated

import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from torchvision import transforms

import mlflow
from src.food11.data import CLASSES

app = FastAPI()
model = None

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


@app.on_event("startup")
def load_model() -> None:
    global model
    if os.environ.get("SKIP_MODEL"):
        model = None
        return
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000"))
    model = mlflow.pyfunc.load_model("models:/food11@champion").get_raw_model()
    model.eval()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: Annotated[UploadFile, File()]) -> dict[str, str | float]:
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    try:
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail="Invalid image") from exc

    image_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(image_tensor)
        probabilities = torch.softmax(logits, dim=1)
        confidence, predicted_class = torch.max(probabilities, dim=1)

    return {
        "category": CLASSES[predicted_class.item()],
        "confidence": confidence.item(),
    }
