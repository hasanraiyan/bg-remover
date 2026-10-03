# Background Removal API

A high-performance, privacy-focused REST API for automatic image background removal built with Python 3.12, FastAPI, and local background removal ML models (`rembg` / `u2net`).

The service runs processing entirely locally without sending user images to external third-party services.

---

## Architecture

```
┌──────────────┐      HTTP POST      ┌──────────────┐
│  Client App  │ ──────────────────> │ FastAPI App  │
└──────────────┘                     └──────┬───────┘
                                            │
                                            ▼
                                     ┌──────────────┐
                                     │ Validation   │
                                     └──────┬───────┘
                                            │
                                            ▼
                                     ┌──────────────┐
                                     │ Local Model  │
                                     │   (rembg)    │
                                     └──────┬───────┘
                                            │
                                            ▼
                                     ┌──────────────┐
                                     │  RGBA / PNG  │
                                     └──────────────┘
```

The architecture decouples the core API routes from the underlying ML background removal engine (`app/engine.py`), enabling seamless swapping or upgrading of background removal models without breaking API contracts.

---

## Features

- **Local Image Processing:** Full privacy — no image data leaves the server.
- **FastAPI Core:** Interactive Swagger UI documentation and high performance.
- **Flexible Image Support:** Accepts JPEG, PNG, and WebP image uploads.
- **Output:** Transparent PNG image with alpha channel.
- **Configurable Limits:** Customizable file size limits and supported extensions.
- **Authentication:** Optional API Key or Bearer token authentication.
- **Container Ready:** Includes `Dockerfile` and `docker-compose.yml`.

---

## API Reference

### 1. Health Check
- **Endpoint:** `GET /health`
- **Response:**
  ```json
  {
    "status": "healthy",
    "service": "Background Removal API",
    "version": "1.0.0"
  }
  ```

### 2. Readiness Check
- **Endpoint:** `GET /ready`
- **Response:**
  ```json
  {
    "status": "ready",
    "engine": "RembgEngine",
    "model": "u2net"
  }
  ```

### 3. Background Removal
- **Endpoints:** `POST /remove-background` or `POST /api/v1/remove-background`
- **Headers:** `Content-Type: multipart/form-data`
- **Body:** `file` (Image file)
- **Optional Auth Header:** `X-API-Key: <key>` or `Authorization: Bearer <key>`
- **Response:** `200 OK` (`image/png` binary stream)

---

## Installation & Running Locally

### Prerequisites
- Python 3.11+

### Setup
```bash
# Clone the repository and navigate to root directory
cd /path/to/repo

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API documentation will be available at `http://localhost:8000/docs`.

---

## Docker Deployment

### Using Docker Compose
```bash
docker-compose up -d
```

### Using Docker CLI
```bash
docker build -t background-removal-api .
docker run -d -p 8000:8000 background-removal-api
```

---

## Running Tests

Execute tests with pytest:
```bash
PYTHONPATH=. pytest -v
```
