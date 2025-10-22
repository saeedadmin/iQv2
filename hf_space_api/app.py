from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import whisper
import torch
import tempfile
import os
from pathlib import Path
import logging
from TTS.api import TTS
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Persian STT/TTS API",
    description="Free Persian Speech-to-Text and Text-to-Speech API using Whisper and Coqui TTS",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for models
whisper_model = None
tts_model = None

@app.on_event("startup")
async def load_models():
    """Load models on startup"""
    global whisper_model, tts_model
    
    try:
        logger.info("🔄 Loading Whisper model...")
        # Use small model for good balance between speed and accuracy
        whisper_model = whisper.load_model("small")
        logger.info("✅ Whisper model loaded successfully")
        
        logger.info("🔄 Loading Coqui TTS model...")
        # Use Persian VITS model from Hugging Face
        tts_model = TTS(
            model_path="https://huggingface.co/Kamtera/persian-tts-female-glow_tts/resolve/main/best_model.pth",
            config_path="https://huggingface.co/Kamtera/persian-tts-female-glow_tts/resolve/main/config.json"
        )
        logger.info("✅ Coqui TTS model loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Error loading models: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Persian STT/TTS API is running",
        "whisper_loaded": whisper_model is not None,
        "tts_loaded": tts_model is not None
    }

@app.get("/health")
async def health():
    """Health check for keeping the space alive"""
    return {"status": "ok"}

@app.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    Convert Persian speech to text using Whisper
    
    Parameters:
    - audio: Audio file (ogg, mp3, wav, etc.)
    
    Returns:
    - text: Transcribed Persian text
    """
    if whisper_model is None:
        raise HTTPException(status_code=503, detail="Whisper model not loaded")
    
    temp_audio = None
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_audio = temp_file.name
        
        logger.info(f"🎤 Transcribing audio file: {audio.filename}")
        
        # Transcribe
        result = whisper_model.transcribe(
            temp_audio,
            language="fa",  # Persian
            task="transcribe"
        )
        
        text = result["text"].strip()
        logger.info(f"✅ Transcription successful: {text[:50]}...")
        
        return {
            "success": True,
            "text": text,
            "language": "fa"
        }
        
    except Exception as e:
        logger.error(f"❌ STT Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temp file
        if temp_audio and os.path.exists(temp_audio):
            os.unlink(temp_audio)

@app.post("/tts")
async def text_to_speech(text: str):
    """
    Convert Persian text to speech using Coqui TTS
    
    Parameters:
    - text: Persian text to convert
    
    Returns:
    - Audio file (wav)
    """
    if tts_model is None:
        raise HTTPException(status_code=503, detail="TTS model not loaded")
    
    output_path = None
    try:
        if not text or len(text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        logger.info(f"🔊 Generating speech for text: {text[:50]}...")
        
        # Create temp output file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            output_path = temp_file.name
        
        # Generate speech
        tts_model.tts_to_file(
            text=text,
            file_path=output_path
        )
        
        logger.info(f"✅ Speech generated successfully")
        
        # Return audio file
        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename="output.wav",
            background=None  # Keep file until response is sent
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ TTS Error: {e}")
        if output_path and os.path.exists(output_path):
            os.unlink(output_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)