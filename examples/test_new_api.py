"""
Test script for new Google Genai API
Demonstrates the updated de-escalation agent with the latest API
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test 1: Import the new API
print("=" * 70)
print("TEST 1: Import New Google Genai API")
print("=" * 70)

try:
    from google import genai
    from google.genai import types
    print("✓ Successfully imported google.genai")
    print("✓ Successfully imported google.genai.types")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("\nPlease install: pip install google-genai")
    sys.exit(1)

# Test 2: Initialize Client
print("\n" + "=" * 70)
print("TEST 2: Initialize Genai Client")
print("=" * 70)

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("✗ GOOGLE_API_KEY not found in environment")
    print("Please set it in your .env file")
    sys.exit(1)

try:
    client = genai.Client(api_key=api_key)
    print("✓ Client initialized successfully")
except Exception as e:
    print(f"✗ Client initialization failed: {e}")
    sys.exit(1)

# Test 3: Generate Text Response
print("\n" + "=" * 70)
print("TEST 3: Generate Text Content")
print("=" * 70)

try:
    test_prompt = """You are a calm, professional safety assistant. 
A driver is experiencing a road rage incident where someone is approaching their vehicle aggressively.
Provide 2-3 sentences of calm safety guidance."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",  # Use standard flash model for text
        contents=test_prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=100
        )
    )
    
    print("✓ Text generation successful")
    print("\nGenerated text:")
    print("-" * 70)
    print(response.text)
    print("-" * 70)
    
except Exception as e:
    print(f"✗ Text generation failed: {e}")
    print("\nThis might be due to:")
    print("- Model access permissions")
    print("- API quota limits")
    print("- Invalid API key")

# Test 4: Test De-escalation Agent
print("\n" + "=" * 70)
print("TEST 4: De-escalation Agent Integration")
print("=" * 70)

try:
    from deescalation_agent import DeescalationAgent
    
    agent = DeescalationAgent()
    print("✓ De-escalation Agent initialized")
    
    # Create a minimal test scenario
    test_scenario = {
        "analysis_metadata": {"overall_threat_level": "High"},
        "incidents": [{
            "incident_id": 1,
            "start_time": "00:00:05",
            "end_time": "00:00:15",
            "threat_level": "High",
            "threat_type": "approaching_person",
            "visual_observations": {
                "description": "Person approaching vehicle aggressively",
                "approaching_persons": {
                    "detected": True,
                    "proximity": "0-1 meter"
                }
            },
            "audio_observations": {
                "verbal_threats": {"detected": True}
            },
            "recommended_action": "lock_doors"
        }],
        "summary": {
            "total_incidents": 1,
            "primary_threats": ["approaching_person"]
        }
    }
    
    print("\nGenerating guidance for test scenario...")
    guidance = agent.generate_guidance(
        test_scenario,
        return_audio=False,  # Text only for testing
        return_text=True
    )
    
    if 'text' in guidance:
        print("✓ Guidance generated successfully")
        print("\nGenerated Safety Guidance:")
        print("-" * 70)
        print(guidance['text'])
        print("-" * 70)
    else:
        print("✗ No text in guidance response")
        
except Exception as e:
    print(f"✗ De-escalation Agent test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Audio Generation (Optional)
print("\n" + "=" * 70)
print("TEST 5: Audio Generation (Optional)")
print("=" * 70)

try:
    print("Attempting to generate audio output...")
    print("Note: Using TTS model with AUDIO modality (text-to-speech synthesis)")
    
    # TTS model only accepts AUDIO modality
    audio_response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",  # TTS model
        contents="Lock your doors now. Stay inside your vehicle. Do not engage.",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],  # TTS model ONLY accepts AUDIO
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Kore'
                    )
                )
            )
        )
    )
    
    # Check for audio data
    audio_found = False
    if audio_response.candidates:
        for part in audio_response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                audio_data = part.inline_data.data
                mime_type = part.inline_data.mime_type
                audio_found = True
                
                # Save audio to test file
                output_path = Path(__file__).parent.parent / "results" / "audio" / "test_audio.wav"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                
                print(f"✓ Audio generation successful")
                print(f"✓ Audio saved to: {output_path}")
                print(f"✓ MIME type: {mime_type}")
                print(f"✓ Audio size: {len(audio_data)} bytes")
                break
    
    if not audio_found:
        print("⚠ Audio generation returned but no audio data found")
        print("This might be expected depending on your API access level")
        
except Exception as e:
    print(f"⚠ Audio generation test failed: {e}")
    print("This is optional - text generation is the main requirement")

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("""
Key Takeaways:
- New API uses: from google import genai
- Client-based: client = genai.Client(api_key=...)
- Two models needed:
  * gemini-2.5-flash for text generation (TEXT modality)
  * gemini-2.5-flash-preview-tts for audio synthesis (AUDIO modality only)
- TTS model ONLY accepts response_modalities=["AUDIO"]
- Voice options: Kore, Puck, Charon, Aoede, etc.

If all tests passed, your de-escalation agent is ready to use!
""")
print("=" * 70)
