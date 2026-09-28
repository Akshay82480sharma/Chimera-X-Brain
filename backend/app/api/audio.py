from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
import os
import shutil
import uuid
import structlog
from typing import Any
from pydantic import BaseModel

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/v1/audio", tags=["audio"])

# Lazy loaded whisper model to prevent slow startup times
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            # Suppress the annoying Windows symlink warning from huggingface_hub
            os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
            
            from faster_whisper import WhisperModel
            # Load the base model. Options: tiny, base, small, medium, large-v3
            logger.info("Initializing faster-whisper model (small) for better multilingual support...")
            _whisper_model = WhisperModel("small", device="cpu", compute_type="default")
            logger.info("faster-whisper model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize faster-whisper: {e}")
            raise HTTPException(status_code=500, detail="Speech-to-text model failed to load.")
    return _whisper_model

class TranscriptionResponse(BaseModel):
    text: str

@router.post("/transcriptions", response_model=TranscriptionResponse)
async def create_transcription(file: UploadFile = File(...)) -> Any:
    """
    Transcribes audio to text using faster-whisper.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    import tempfile
    
    try:
        # Save the uploaded file to the OS temp directory
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_file_path = tmp.name

        # Get the lazy-loaded model
        model = get_whisper_model()

        # Perform transcription
        # beam_size=5 is standard for good quality.
        logger.info(f"Transcribing {temp_file_path}...")
        segments, info = model.transcribe(temp_file_path, beam_size=5)

        # Combine segments into a single text
        transcription_text = " ".join([segment.text for segment in segments]).strip()

        logger.info(f"Transcription complete: {transcription_text[:50]}...")
        return TranscriptionResponse(text=transcription_text)

    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to remove temporary audio file {temp_file_path}: {e}")
