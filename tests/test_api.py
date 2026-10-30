import torch
from fastapi.testclient import TestClient

from src.food11 import serve


class FakeModel:
    def __call__(self, _image_tensor):
        return torch.tensor([[5.0] + [0.0] * 10])


def test_health_without_model(monkeypatch):
    monkeypatch.setenv("SKIP_MODEL", "1")
    with TestClient(serve.app) as client:
        assert client.get("/health").status_code == 200
        assert client.post("/predict", files={"file": ("x.jpg", b"x", "image/jpeg")}).status_code == 503


def test_predict_returns_valid_json(monkeypatch):
    monkeypatch.setenv("SKIP_MODEL", "1")
    with TestClient(serve.app) as client:
        monkeypatch.setattr(serve, "model", FakeModel())
        with open("tests/fixtures/bread.jpg", "rb") as image:
            response = client.post("/predict", files={"file": ("bread.jpg", image, "image/jpeg")})

    assert response.status_code == 200
    body = response.json()
    assert body["category"] == "Bread"
    assert 0.0 <= body["confidence"] <= 1.0
