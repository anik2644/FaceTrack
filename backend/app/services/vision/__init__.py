"""Vision subsystem: detection, encoding, matching and live streaming."""
from app.services.vision.manager import StreamManager, get_stream_manager
from app.services.vision.pipeline import RecognitionPipeline

__all__ = ["StreamManager", "get_stream_manager", "RecognitionPipeline"]
