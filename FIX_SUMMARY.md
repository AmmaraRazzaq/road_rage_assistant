# Fix Summary - TTS Model AUDIO-Only Issue

**Date**: February 9, 2026  
**Issue**: `400 INVALID_ARGUMENT - models/gemini-2.5-flash-preview-tts accepts AUDIO modality only`

## Problem

The `gemini-2.5-flash-preview-tts` model **only accepts AUDIO response modality**, not TEXT. When we tried to generate text output from this model, it returned an error.

## Root Cause

We were using the TTS (text-to-speech) model for both text generation AND audio synthesis. However, the TTS model is designed ONLY for audio output.

## Solution

Use **two separate models**:

1. **`gemini-2.5-flash`** - For text generation (supports TEXT modality)
2. **`gemini-2.5-flash-preview-tts`** - For audio synthesis only (AUDIO modality)

### Updated Code Flow

```python
# Step 1: Generate text guidance (use standard flash model)
text_response = client.models.generate_content(
    model="gemini-2.5-flash",  # ← Changed from TTS model
    contents=f"{SYSTEM_PROMPT}\n\n{prompt}",
    config=types.GenerateContentConfig(temperature=0.3)
)

transcript = text_response.text

# Step 2: Convert text to audio (use TTS model)
audio_response = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",  # ← TTS model
    contents=transcript,
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"]  # ← AUDIO only
    )
)
```

## Files Updated

### Core Code
- ✅ `src/deescalation_agent.py` - Uses two separate models
- ✅ `src/deescalation_prompt.py` - Updated usage example

### Documentation
- ✅ `docs/API_MIGRATION.md` - Clarified two-step process
- ✅ `API_QUICK_REFERENCE.md` - Updated model table and examples
- ✅ `examples/test_new_api.py` - Uses correct models

### New File
- ✅ `FIX_SUMMARY.md` - This document

## Key Changes in `deescalation_agent.py`

### Before (Broken)
```python
self.model_name = "gemini-2.5-flash-preview-tts"

# Tried to get text from TTS model
text_response = client.models.generate_content(
    model=self.model_name,  # ← TTS model
    contents=prompt
)
# ❌ ERROR: TTS model doesn't support TEXT modality
```

### After (Fixed)
```python
self.text_model = "gemini-2.5-flash"        # For text
self.audio_model = "gemini-2.5-flash-preview-tts"  # For audio

# Generate text with text model
text_response = client.models.generate_content(
    model=self.text_model,  # ← Standard flash model
    contents=prompt
)

# Generate audio with TTS model
audio_response = client.models.generate_content(
    model=self.audio_model,  # ← TTS model
    contents=text_response.text,
    config=types.GenerateContentConfig(
        response_modalities=["AUDIO"]  # ✅ AUDIO only
    )
)
```

## Model Comparison

| Model | Use For | Modalities | Notes |
|-------|---------|------------|-------|
| `gemini-2.5-flash` | Text generation | TEXT | Fast, standard model |
| `gemini-2.5-flash-preview-tts` | Audio synthesis | AUDIO only | Cannot generate text |
| `gemini-2.5-pro` | Advanced text | TEXT | Slower, more capable |

## Testing the Fix

```bash
# Activate environment
conda activate zutec

# Run the fixed agent
python src/deescalation_agent.py
```

Expected output:
```
[GENERATING OVERALL SAFETY GUIDANCE]

Audio Transcript:
------------------------------------------------------------
Lock your doors now. Stay inside your vehicle and keep your
hands visible. Do not engage with the person blocking you.
------------------------------------------------------------

[INCIDENT 1]
Time: 00:00:03 - 00:00:13
Threat: approaching_person (High)

Audio Guidance:
------------------------------------------------------------
Lock your doors immediately. Stay calm and remain in your
vehicle. Do not engage. Call 911 if the threat persists.
------------------------------------------------------------
✓ Audio saved: results/audio/incident_1_guidance.wav
```

## Why Two Models?

1. **Text Model** (`gemini-2.5-flash`)
   - Generates the safety guidance text
   - Processes system prompt
   - Fast and efficient

2. **TTS Model** (`gemini-2.5-flash-preview-tts`)
   - Converts text to speech
   - Applies voice characteristics
   - Produces natural audio output

This separation is by design in Google's API:
- Text generation models focus on content quality
- TTS models focus on natural speech synthesis

## Error Prevention

The updated code:
- ✅ Always uses text model for text generation
- ✅ Only uses TTS model with AUDIO modality
- ✅ Gracefully handles audio generation failures
- ✅ Falls back to text-only if audio unavailable

## Quick Reference

### Generate Text Only
```python
agent = DeescalationAgent()
guidance = agent.generate_guidance(
    perception_output,
    return_text=True,
    return_audio=False  # Skip audio
)
print(guidance['text'])
```

### Generate Text + Audio
```python
agent = DeescalationAgent()
guidance = agent.generate_guidance(
    perception_output,
    return_text=True,
    return_audio=True  # Include audio
)

print(guidance['text'])
agent.save_guidance_audio(guidance, "output.wav")
```

## Troubleshooting

### Still getting INVALID_ARGUMENT error?
- Check you're using the updated `deescalation_agent.py`
- Verify you're not calling TTS model for text generation
- Ensure `response_modalities=["AUDIO"]` when using TTS model

### No audio in output?
- This is OK - audio generation may not be available to all API users
- The agent will always return text guidance
- Check API access level for TTS features

## Summary

✅ **Fixed**: TTS model AUDIO-only limitation  
✅ **Solution**: Use two separate models (text + audio)  
✅ **Benefit**: Proper separation of concerns  
✅ **Status**: Working correctly

---

**Quick Start**: `python src/deescalation_agent.py`  
**Test Script**: `python examples/test_new_api.py`  
**Documentation**: See `docs/API_MIGRATION.md` for details
