import os
import logging
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)

# Optional dependencies for OCR
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Optional dependencies for Audio
try:
    import whisper
    WHISPER_AVAILABLE = True
    # We delay loading the model until it's actually used to save memory/startup time
    _whisper_model = None
except ImportError:
    WHISPER_AVAILABLE = False


def extract_image_text(image_path: str) -> str:
    """
    Extracts visible text from an image using OCR (Tesseract).
    Gracefully falls back to returning an empty string if dependencies or the image are missing.
    """
    if not OCR_AVAILABLE:
        logger.debug("OCR dependencies (pytesseract, PIL) not available.")
        return ""
        
    if not image_path or not os.path.exists(image_path):
        logger.debug(f"Image path does not exist or is empty: {image_path}")
        return ""
        
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        logger.warning(f"Failed to extract text from image {image_path}: {e}")
        return ""


def extract_voice_text(audio_path: str) -> str:
    """
    Extracts transcript from an audio file using Whisper.
    Gracefully falls back to returning an empty string if dependencies or the audio are missing.
    """
    global _whisper_model
    
    if not WHISPER_AVAILABLE:
        logger.debug("Whisper dependency not available.")
        return ""
        
    if not audio_path or not os.path.exists(audio_path):
        logger.debug(f"Audio path does not exist or is empty: {audio_path}")
        return ""
        
    try:
        # Lazy load model to avoid heavy init if not needed
        if _whisper_model is None:
            # Using 'tiny' or 'base' model by default for speed
            _whisper_model = whisper.load_model("tiny")
            
        result = _whisper_model.transcribe(audio_path)
        return str(result.get("text", "")).strip()
    except Exception as e:
        logger.warning(f"Failed to extract text from audio {audio_path}: {e}")
        return ""


def process_media(message_row: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """
    Processes a message row to extract text from attached media (image or audio).
    
    Args:
        message_row: A dictionary or pandas Series representing a message.
                     Expected to contain 'media_type' and 'media_path'.
                     
    Returns:
        A dictionary containing the media type and extracted texts.
    """
    # Safely extract fields whether it's a dict or an object
    if isinstance(message_row, dict):
        raw_media_type = message_row.get('media_type', 'none')
        media_path = str(message_row.get('media_path', message_row.get('media_id', '')))
    else:
        raw_media_type = getattr(message_row, 'media_type', 'none')
        media_path = str(getattr(message_row, 'media_path', getattr(message_row, 'media_id', '')))
    
    # Safely handle NaN / None / float values from pandas
    if raw_media_type is None or (isinstance(raw_media_type, float)) or str(raw_media_type).lower() == 'nan':
        media_type = 'none'
    else:
        media_type = str(raw_media_type).lower()
    
    if media_path == 'nan':
        media_path = ''
        
    ocr_text = ""
    voice_text = ""
    
    if media_type == 'image' and media_path:
        ocr_text = extract_image_text(media_path)
    elif media_type in ['audio', 'voice'] and media_path:
        voice_text = extract_voice_text(media_path)
        
    combined_text = f"{ocr_text} {voice_text}".strip()
    
    return {
        "media_type": media_type,
        "ocr_text": ocr_text,
        "voice_text": voice_text,
        "combined_text": combined_text
    }
