"""
De-escalation Agent Implementation
Generates real-time audio safety guidance based on perception agent output
"""

import os
import json
from google import genai
from google.genai import types
from pathlib import Path
from deescalation_prompt import DEESCALATION_SYSTEM_PROMPT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DeescalationAgent:
    """
    Generates calm, actionable audio guidance for road rage situations
    based on perception agent threat assessments.
    """
    
    def __init__(
        self, 
        api_key: str = None, 
        voice_name: str = "Puck",
        speaking_rate: float = 1.0,
        pitch: float = 0.0
    ):
        """
        Initialize the de-escalation agent with Gemini audio model.
        
        Args:
            api_key: Google API key. If None, will use GEMINI_API_KEY from environment.
            voice_name: Voice to use for audio generation. 
                       Recommended: "Puck" (clear male), "Aoede" (clear female)
                       Other options: "Charon" (deep male), "Kore" (professional female)
            speaking_rate: Speech speed (0.25-4.0). Default 1.0. Try 0.9 for clearer speech.
            pitch: Voice pitch adjustment (-20.0 to 20.0). Default 0.0.
        """
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Google API key is required. Set GEMINI_API_KEY environment variable.")
        
        # Initialize client with new API
        self.client = genai.Client(api_key=api_key)
        
        # Model configuration
        self.text_model = "gemini-2.5-flash"  # For text generation
        self.audio_model = "gemini-2.5-flash-preview-tts"  # For audio only
        self.voice_name = voice_name
        self.speaking_rate = max(0.25, min(4.0, speaking_rate))  # Clamp to valid range
        self.pitch = max(-20.0, min(20.0, pitch))  # Clamp to valid range
        
        # System prompt for guidance generation
        self.system_prompt = DEESCALATION_SYSTEM_PROMPT
        
        # Generation configuration optimized for calm, consistent responses
        self.temperature = 0.3      # Lower for consistent, measured responses
        self.top_p = 0.8
        self.top_k = 40
        self.max_output_tokens = 200  # Keep audio instructions short and actionable
    
    def generate_guidance(
        self, 
        perception_output: dict,
        focus_incident: int = None,
        return_audio: bool = True,
        return_text: bool = True
    ) -> dict:
        """
        Generate de-escalation audio guidance based on perception analysis.
        
        Args:
            perception_output: JSON output from perception agent
            focus_incident: Optional specific incident ID to focus on. If None, 
                          addresses overall situation and highest threats.
            return_audio: If True, generates audio output
            return_text: If True, returns text transcript
        
        Returns:
            Dictionary with 'audio' (bytes), 'text' (str), and 'audio_mime_type' keys
        """
        # Construct the user prompt
        if focus_incident is not None:
            # Focus on specific incident
            incident = next(
                (inc for inc in perception_output["incidents"] if inc["incident_id"] == focus_incident),
                None
            )
            if not incident:
                raise ValueError(f"Incident ID {focus_incident} not found")
            
            user_prompt = f"""Immediate situation requiring guidance:

Threat Level: {incident['threat_level']}
Threat Type: {incident['threat_type']}
Time: {incident['start_time']} to {incident['end_time']}

Visual: {incident['visual_observations']['description']}

Audio Indicators: {json.dumps(incident.get('audio_observations', {}), indent=2)}

Recommended Action: {incident['recommended_action']}

Provide immediate, calm audio safety instructions for the driver RIGHT NOW."""
        
        else:
            # Address overall situation
            user_prompt = f"""Road rage threat assessment requiring immediate guidance:

Overall Threat Level: {perception_output['analysis_metadata']['overall_threat_level']}
Total Incidents: {perception_output['summary']['total_incidents']}
Primary Threats: {', '.join(perception_output['summary']['primary_threats'])}

Incidents:
{json.dumps(perception_output['incidents'], indent=2)}

Provide immediate, calm audio safety instructions for the driver RIGHT NOW. Focus on the most critical threats first."""
        
        result = {}
        
        # First, generate text transcript with system prompt using text model
        if return_text or return_audio:
            text_response = self.client.models.generate_content(
                model=self.text_model,  # Use text model for text generation
                contents=f"{self.system_prompt}\n\n{user_prompt}",
                config=types.GenerateContentConfig(
                    temperature=self.temperature,
                    top_p=self.top_p,
                    top_k=self.top_k,
                    max_output_tokens=self.max_output_tokens
                )
            )
            transcript = text_response.text
            
            if return_text:
                result['text'] = transcript
        
        # Generate audio output if requested
        if return_audio:
            # Generate audio from transcript using audio model with quality settings
            audio_response = self.client.models.generate_content(
                model=self.audio_model,  # Use audio model for audio synthesis
                contents=transcript,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],  # TTS model only accepts AUDIO
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.voice_name
                            )
                        )
                        # Note: speaking_rate and pitch may not be supported yet
                        # The API is in preview and parameters are limited
                    )
                )
            )
            
            # Extract audio data
            if audio_response.candidates:
                for part in audio_response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        result['audio'] = part.inline_data.data
                        result['audio_mime_type'] = part.inline_data.mime_type
                        break
        
        return result
    
    def generate_continuous_guidance(
        self,
        perception_output: dict,
        interval_seconds: int = 10
    ):
        """
        Generate guidance for each incident in sequence, simulating real-time updates.
        
        Args:
            perception_output: JSON output from perception agent
            interval_seconds: Time between guidance updates (for simulation)
        
        Yields:
            Tuple of (incident_id, guidance_dict)
        """
        incidents = sorted(
            perception_output["incidents"], 
            key=lambda x: x["start_time"]
        )
        
        for incident in incidents:
            guidance = self.generate_guidance(
                perception_output,
                focus_incident=incident["incident_id"]
            )
            yield (incident["incident_id"], guidance)
    
    def save_guidance_audio(
        self,
        guidance: dict,
        output_path: str
    ) -> str:
        """
        Save generated audio guidance to file.
        
        Args:
            guidance: Output from generate_guidance()
            output_path: Path to save audio file (should end with appropriate extension)
        
        Returns:
            Path to saved audio file
        """
        if 'audio' not in guidance:
            raise ValueError("No audio data in guidance to save")
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Auto-detect extension based on mime type if not provided
        if not output_file.suffix and 'audio_mime_type' in guidance:
            mime_to_ext = {
                'audio/wav': '.wav',
                'audio/mp3': '.mp3',
                'audio/mpeg': '.mp3',
                'audio/ogg': '.ogg'
            }
            ext = mime_to_ext.get(guidance['audio_mime_type'], '.wav')
            output_path = str(output_file) + ext
        
        # Save audio to file
        with open(output_path, 'wb') as f:
            f.write(guidance['audio'])
        
        print(f"Audio guidance saved to: {output_path}")
        return output_path


def main():
    """
    Example usage: Process perception agent output and generate guidance
    """
    # Initialize agent with clearer voice
    print("Initializing De-escalation Agent...")
    print("Using voice: Puck (clear male voice)")
    print("TIP: Run 'python examples/test_voices.py' to test different voices\n")
    
    agent = DeescalationAgent(voice_name="Puck")  # Puck is generally clearer than Kore
    
    # Load perception agent output
    perception_file = Path(__file__).parent.parent / "results" / "gemini-2.5-flash_road_rage_analysis_fps1.json"
    
    with open(perception_file, 'r') as f:
        perception_output = json.load(f)
    
    print("=" * 60)
    print("DE-ESCALATION AGENT - Real-time Safety Guidance")
    print("=" * 60)
    print(f"\nAnalyzing perception output from: {perception_file.name}")
    print(f"Overall Threat Level: {perception_output['analysis_metadata']['overall_threat_level']}")
    print(f"Total Incidents: {perception_output['summary']['total_incidents']}")
    print("\n" + "=" * 60)
    
    # Generate overall guidance
    print("\n[GENERATING OVERALL SAFETY GUIDANCE]\n")
    try:
        overall_guidance = agent.generate_guidance(
            perception_output,
            return_audio=False,  # Skip audio for faster demo
            return_text=True     # Get text guidance
        )
        
        if 'text' in overall_guidance:
            print("Audio Transcript:")
            print("-" * 60)
            print(overall_guidance['text'])
            print("-" * 60)
    except Exception as e:
        print(f"Error generating guidance: {e}")
        print("Note: Audio generation requires proper API access and model availability")
    
    # Generate incident-specific guidance
    print("\n" + "=" * 60)
    print("INCIDENT-SPECIFIC GUIDANCE")
    print("=" * 60)
    
    for incident in perception_output["incidents"]:
        incident_id = incident["incident_id"]
        
        print(f"\n[INCIDENT {incident_id}]")
        print(f"Time: {incident['start_time']} - {incident['end_time']}")
        print(f"Threat: {incident['threat_type']} ({incident['threat_level']})")
        
        try:
            guidance = agent.generate_guidance(
                perception_output,
                focus_incident=incident_id,
                return_audio=True,  # Try to get audio
                return_text=True
            )
            
            if 'text' in guidance:
                print("\nAudio Guidance:")
                print("-" * 60)
                print(guidance['text'])
                print("-" * 60)
            
            # Save audio if available
            if 'audio' in guidance:
                output_dir = Path(__file__).parent.parent / "results" / "audio"
                output_dir.mkdir(parents=True, exist_ok=True)
                audio_path = output_dir / f"incident_{incident_id}_guidance"
                saved_path = agent.save_guidance_audio(guidance, str(audio_path))
                print(f"✓ Audio saved: {saved_path}")
        
        except Exception as e:
            print(f"Error generating guidance for incident {incident_id}: {e}")
    
    print("\n" + "=" * 60)
    print("De-escalation guidance generation complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
