---
title: Persian STT TTS API
emoji: 🎙️
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Persian Speech-to-Text and Text-to-Speech API

This API provides free Persian (Farsi) speech recognition and text-to-speech capabilities using:

- **STT (Speech-to-Text):** OpenAI Whisper (small model)
- **TTS (Text-to-Speech):** Coqui TTS with Persian GlowTTS model

## API Endpoints

### Health Check
```bash
GET /
GET /health
```

### Speech to Text
```bash
POST /stt
Content-Type: multipart/form-data

Parameters:
- audio: Audio file (ogg, mp3, wav, etc.)

Response:
{
  "success": true,
  "text": "متن فارسی تبدیل شده",
  "language": "fa"
}
```

### Text to Speech
```bash
POST /tts?text=سلام دنیا

Response:
Audio file (wav)
```

## Usage Example

### Python
```python
import requests

# Speech to Text
with open('audio.ogg', 'rb') as f:
    response = requests.post(
        'https://YOUR-SPACE-NAME.hf.space/stt',
        files={'audio': f}
    )
    print(response.json()['text'])

# Text to Speech
response = requests.post(
    'https://YOUR-SPACE-NAME.hf.space/tts',
    params={'text': 'سلام دنیا'}
)
with open('output.wav', 'wb') as f:
    f.write(response.content)
```

## Models

- **Whisper Small:** 472 MB, 2.5 GB RAM
- **Coqui GlowTTS:** 344 MB, ~1 GB RAM
- **Total:** ~3.5 GB RAM (fits in HF Spaces free tier: 16 GB)

## License

MIT License