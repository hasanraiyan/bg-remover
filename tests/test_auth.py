import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def create_sample_image():
    img = Image.new("RGB", (50, 50), color="green")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()

def test_authentication_disabled(monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", None)
    img_bytes = create_sample_image()
    response = client.post(
        "/remove-background",
        files={"file": ("sample.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200

def test_authentication_enabled_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "secret-key-123")
    img_bytes = create_sample_image()
    response = client.post(
        "/remove-background",
        files={"file": ("sample.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "Unauthorized"

def test_authentication_enabled_valid_header_key(monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "secret-key-123")
    img_bytes = create_sample_image()
    response = client.post(
        "/remove-background",
        files={"file": ("sample.jpg", img_bytes, "image/jpeg")},
        headers={"X-API-Key": "secret-key-123"}
    )
    assert response.status_code == 200

def test_authentication_enabled_valid_bearer_token(monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "secret-key-123")
    img_bytes = create_sample_image()
    response = client.post(
        "/remove-background",
        files={"file": ("sample.jpg", img_bytes, "image/jpeg")},
        headers={"Authorization": "Bearer secret-key-123"}
    )
    assert response.status_code == 200

def test_authentication_enabled_invalid_key(monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "secret-key-123")
    img_bytes = create_sample_image()
    response = client.post(
        "/remove-background",
        files={"file": ("sample.jpg", img_bytes, "image/jpeg")},
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 401
