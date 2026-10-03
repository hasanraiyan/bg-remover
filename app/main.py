import io
import logging
import os
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Header, Security, status
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import Response, JSONResponse
from PIL import Image, UnidentifiedImageError

from app.config import settings
from app.engine import RembgEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("background_removal_api")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Local Background Removal API using Python and FastAPI."
)

# Initialize engine instance
engine = RembgEngine(model_name=settings.REMBG_MODEL)

# Optional API Key Authentication Security Scheme
api_key_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(
    x_api_key: Optional[str] = Security(api_key_header_scheme),
    authorization: Optional[str] = Header(None)
):
    """
    Validates API key if settings.API_KEY is configured.
    Supports either X-API-Key header or Authorization: Bearer <key>.
    """
    if settings.API_KEY is None:
        return True  # Auth not enabled

    provided_key = x_api_key
    if not provided_key and authorization:
        if authorization.startswith("Bearer "):
            provided_key = authorization.split("Bearer ")[1].strip()

    if provided_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized", "message": "Invalid or missing API key."}
        )
    return True


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Health endpoint returning basic API operational status."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/ready", tags=["Monitoring"])
async def readiness_check():
    """Readiness endpoint verifying if background removal model/engine is loaded and ready."""
    is_engine_ready = engine.is_ready()
    if is_engine_ready:
        return {
            "status": "ready",
            "engine": engine.__class__.__name__,
            "model": settings.REMBG_MODEL
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "error": "Background removal engine is not ready."}
        )


async def process_image_upload(file: UploadFile) -> bytes:
    """Helper function to validate upload file and process background removal."""
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Bad Request", "message": "No file uploaded."}
        )

    # 1. Validate Extension
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Unsupported Media Type",
                "message": f"File extension '{ext}' is not supported. Allowed extensions: {settings.ALLOWED_EXTENSIONS}"
            }
        )

    # 2. Read File Content & Check File Size
    contents = await file.read()
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(contents) > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail={
                "error": "Payload Too Large",
                "message": f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
            }
        )

    # 3. Validate Content Type / Header via Pillow
    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()  # Verify image integrity
    except (UnidentifiedImageError, Exception) as e:
        logger.warning(f"Invalid image uploaded: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Bad Request", "message": "Uploaded file is not a valid or readable image."}
        )

    # 4. Perform Background Removal
    try:
        output_bytes = engine.remove_background(contents)
        return output_bytes
    except Exception as e:
        logger.error(f"Error processing background removal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Processing Error", "message": "Failed to remove image background."}
        )


@app.post(
    "/remove-background",
    tags=["Background Removal"],
    response_class=Response,
    responses={
        200: {"content": {"image/png": {}}, "description": "Processed PNG image with transparent background."},
        400: {"description": "Invalid input image or unsupported format."},
        413: {"description": "File size exceeds limit."},
        401: {"description": "Unauthorized API key."},
        500: {"description": "Internal image processing error."}
    }
)
@app.post(
    "/api/v1/remove-background",
    tags=["Background Removal"],
    response_class=Response,
    include_in_schema=False
)
async def remove_background_endpoint(
    file: UploadFile = File(...),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Endpoint accepting an uploaded image, processing background removal locally,
    and returning a transparent-background PNG image.
    """
    output_png_bytes = await process_image_upload(file)
    return Response(content=output_png_bytes, media_type="image/png")
