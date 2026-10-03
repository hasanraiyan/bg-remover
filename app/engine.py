from abc import ABC, abstractmethod
import io
import logging
from PIL import Image
import rembg

logger = logging.getLogger(__name__)

class BaseBackgroundRemovalEngine(ABC):
    """Abstract base class for background removal engines."""

    @abstractmethod
    def remove_background(self, image_bytes: bytes) -> bytes:
        """Processes raw image bytes and returns PNG bytes with transparent background."""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Returns True if the engine/model is ready to process images."""
        pass


class RembgEngine(BaseBackgroundRemovalEngine):
    """Engine implementation using rembg (u2net / ONNX runtime locally)."""

    def __init__(self, model_name: str = "u2net"):
        self.model_name = model_name
        self._session = None

    def _get_session(self):
        if self._session is None:
            logger.info(f"Initializing rembg session with model: {self.model_name}")
            self._session = rembg.new_session(self.model_name)
        return self._session

    def is_ready(self) -> bool:
        try:
            _ = self._get_session()
            return True
        except Exception as e:
            logger.error(f"Error initializing rembg session: {e}")
            return False

    def remove_background(self, image_bytes: bytes) -> bytes:
        """
        Removes background from image_bytes and returns PNG byte stream.
        """
        session = self._get_session()
        # Process image with rembg
        output_bytes = rembg.remove(image_bytes, session=session)

        # Ensure output is valid PNG with RGBA mode
        out_img = Image.open(io.BytesIO(output_bytes))
        if out_img.mode != "RGBA":
            out_img = out_img.convert("RGBA")

        buffer = io.BytesIO()
        out_img.save(buffer, format="PNG")
        return buffer.getvalue()
