# API Quick Reference - New Google Genai

## Installation

```bash
pip install google-genai python-dotenv
```

## Basic Setup

```python
from google import genai
from google.genai import types
import os

# Initialize client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
```

## Text Generation

```python
# Use gemini-2.5-flash for text generation
response = client.models.generate_content(
    model="gemini-2.5-flash",  # Standard flash model
    contents="Your prompt here",
    config=types.GenerateContentConfig(
        temperature=0.3,
        top_p=0.8,
        top_k=40,
        max_output_tokens=200
    )
)

text = response.text
```

## Audio Generation

```python
# Step 1: Generate transcript (use standard flash model)
text_response = client.models.generate_content(
    model="gemini-2.5-flash",  # NOT the TTS model
    contents="Generate safety guidance for road rage incident",
    config=types.GenerateContentConfig(temperature=0.3)
)

# Step 2: Convert to audio (use TTS model with AUDIO modality)
audio_response = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",  # TTS model
    contents=text_response.text,
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],  # TTS model ONLY accepts AUDIO
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name='Kore'  # or Puck, Charon, Aoede
                )
            )
        )
    )
)

# Step 3: Extract audio
for part in audio_response.candidates[0].content.parts:
    if hasattr(part, 'inline_data') and part.inline_data:
        audio_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type
        
        # Save to file
        with open('output.wav', 'wb') as f:
            f.write(audio_bytes)
        break
```

## De-escalation Agent Usage

```python
from deescalation_agent import DeescalationAgent
import json

# Initialize with voice selection
agent = DeescalationAgent(voice_name="Kore")

# Load perception data
with open("perception_output.json") as f:
    data = json.load(f)

# Generate guidance
guidance = agent.generate_guidance(
    data,
    return_audio=True,
    return_text=True
)

# Access results
print(guidance['text'])          # Text transcript
audio = guidance['audio']         # Audio bytes
mime = guidance['audio_mime_type'] # e.g., 'audio/wav'

# Save audio
agent.save_guidance_audio(guidance, "output/guidance.wav")
```

## Available Voices

| Voice | Description | Best For |
|-------|-------------|----------|
| **Kore** | Calm, professional female | Emergency guidance (default) |
| **Puck** | Male voice | Alternative option |
| **Charon** | Deep male voice | Authoritative tone |
| **Aoede** | Soft female voice | Gentle guidance |

## Configuration Options

### GenerateContentConfig

```python
config = types.GenerateContentConfig(
    # Text generation
    temperature=0.3,          # 0.0-1.0, lower = more consistent
    top_p=0.8,               # 0.0-1.0, nucleus sampling
    top_k=40,                # Top-k sampling
    max_output_tokens=200,   # Max response length
    
    # Audio generation
    response_modalities=["AUDIO"],  # Request audio output
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name='Kore'
            )
        )
    )
)
```

## Model Names

| Model | Purpose | Modalities |
|-------|---------|------------|
| `gemini-2.5-flash` | Text generation | TEXT only |
| `gemini-2.5-flash-preview-tts` | Audio synthesis | AUDIO only (no text output) |
| `gemini-2.5-pro` | Advanced text generation | TEXT only |

**Important**: The TTS model (`gemini-2.5-flash-preview-tts`) only supports AUDIO output. Always use `gemini-2.5-flash` for text generation first.

## Error Handling

```python
try:
    response = client.models.generate_content(...)
    text = response.text
except Exception as e:
    print(f"Generation failed: {e}")
    # Fallback or retry logic
```

## Common Patterns

### Pattern 1: System Prompt + User Input

```python
system_prompt = "You are a calm safety assistant..."
user_input = "Person approaching vehicle aggressively"

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents=f"{system_prompt}\n\n{user_input}",
    config=config
)
```

### Pattern 2: Generate Multiple Responses

```python
for incident in incidents:
    guidance = agent.generate_guidance(
        perception_data,
        focus_incident=incident['id']
    )
    print(guidance['text'])
```

### Pattern 3: Text First, Audio Optional

```python
# Always get text
guidance = agent.generate_guidance(
    data,
    return_text=True,
    return_audio=True  # Try audio, fallback to text
)

if 'audio' in guidance:
    play_audio(guidance['audio'])
else:
    speak_text(guidance['text'])  # TTS fallback
```

## Testing

```bash
# Test API connectivity
python examples/test_new_api.py

# Run de-escalation agent
python src/deescalation_agent.py

# Test complete pipeline
python examples/complete_pipeline.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import error | `pip install google-genai` |
| No GOOGLE_API_KEY | Set in `.env` file |
| Model not found | Check API access permissions |
| No audio in response | Verify TTS access, try text-only |
| Rate limit | Add retry logic with exponential backoff |

## Quick Start Commands

```bash
# Setup
conda activate zutec
pip install google-genai python-dotenv

# Configure
echo "GOOGLE_API_KEY=your_key_here" > .env

# Test
python examples/test_new_api.py

# Run
python src/deescalation_agent.py
```

## More Information

- **Full Documentation**: `docs/DEESCALATION_AGENT.md`
- **Migration Guide**: `docs/API_MIGRATION.md`
- **System Prompt**: `src/deescalation_prompt.py`
- **Examples**: `examples/`

---

**Current API Version**: `google-genai>=1.0.0`  
**Model**: `gemini-2.5-flash-preview-tts`  
**Last Updated**: February 9, 2026
