import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def create_sample_image(format="JPEG", size=(100, 100), color="red"):
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf.getvalue()

def test_remove_background_success():
    img_bytes = create_sample_image(format="JPEG")
    response = client.post(
        "/remove-background",
        files={"file": ("sample.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # Verify returning image can be opened by Pillow and has RGBA mode
    out_img = Image.open(io.BytesIO(response.content))
    assert out_img.format == "PNG"
    assert out_img.mode == "RGBA"

def test_remove_background_versioned_endpoint():
    img_bytes = create_sample_image(format="PNG")
    response = client.post(
        "/api/v1/remove-background",
        files={"file": ("sample.png", img_bytes, "image/png")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

def test_unsupported_file_extension():
    response = client.post(
        "/remove-background",
        files={"file": ("test.txt", b"hello world", "text/plain")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "Unsupported Media Type"

def test_corrupted_image_file():
    response = client.post(
        "/remove-background",
        files={"file": ("test.jpg", b"invalid byte stream", "image/jpeg")}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "Bad Request"

def test_file_size_exceeded(monkeypatch):
    monkeypatch.setattr(settings, "MAX_FILE_SIZE_MB", 0.0001)  # tiny limit ~ 100 bytes
    img_bytes = create_sample_image(size=(300, 300))
    response = client.post(
        "/remove-background",
        files={"file": ("large.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 413
    data = response.json()
    assert data["detail"]["error"] == "Payload Too Large"
