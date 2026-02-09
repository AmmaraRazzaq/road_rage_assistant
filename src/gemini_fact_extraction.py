from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv
import os
import time
import subprocess
from pydantic import BaseModel, Field
from typing import List
from prompts import perception_prompt
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Pydantic models for Road Rage Detection
class AnalysisMetadata(BaseModel):
    video_duration: str = Field(description="Duration in seconds")
    analysis_timestamp: str = Field(description="ISO 8601 timestamp")
    overall_threat_level: str = Field(description="Low/Moderate/High/Critical")

class ApproachingPersons(BaseModel):
    detected: bool = Field(description="Whether persons are approaching")
    count: int = Field(description="Number of persons approaching")
    proximity: str = Field(description="Distance in meters or description")
    behavior: str = Field(description="Description of behavior and posture")

class BlockingBehavior(BaseModel):
    detected: bool = Field(description="Whether blocking behavior detected")
    type: str = Field(description="vehicle/pedestrian/multiple")
    duration: str = Field(description="Duration in seconds")
    description: str = Field(description="Specific blocking details")

class VisualObservations(BaseModel):
    description: str = Field(description="Detailed description of what is visible")
    approaching_persons: ApproachingPersons
    blocking_behavior: BlockingBehavior
    other_visual_indicators: str = Field(description="Additional threatening visual cues")

class AggressiveHonking(BaseModel):
    detected: bool = Field(description="Whether aggressive honking detected")
    pattern: str = Field(description="single/multiple/sustained/rhythmic")
    duration: str = Field(description="Duration in seconds")
    intensity: str = Field(description="mild/moderate/severe")

class VerbalThreats(BaseModel):
    detected: bool = Field(description="Whether verbal threats detected")
    tone: str = Field(description="Description of vocal tone")
    content_summary: str = Field(description="Summary without explicit language")
    threat_level: str = Field(description="implicit/explicit")

class AudioObservations(BaseModel):
    aggressive_honking: AggressiveHonking
    verbal_threats: VerbalThreats
    other_audio_indicators: str = Field(description="Additional relevant sounds")

class ContextualFactors(BaseModel):
    traffic_condition: str = Field(description="stopped/slow_moving/normal_flow")
    location_context: str = Field(description="intersection/highway/parking_lot/residential")
    time_of_day: str = Field(description="If determinable from video")
    weather_visibility: str = Field(description="If determinable")

class Incident(BaseModel):
    incident_id: int = Field(description="Unique incident identifier")
    start_time: str = Field(description="Start timestamp HH:MM:SS")
    end_time: str = Field(description="End timestamp HH:MM:SS")
    threat_type: str = Field(description="aggressive_honking/approaching_person/verbal_threat/blocking_behavior")
    threat_level: str = Field(description="Low/Moderate/High/Critical")
    visual_observations: VisualObservations
    audio_observations: AudioObservations
    contextual_factors: ContextualFactors
    escalation_indicators: str = Field(description="Signs of escalation or de-escalation")
    recommended_action: str = Field(description="Suggested driver response")

class Summary(BaseModel):
    total_incidents: int = Field(description="Total number of incidents detected")
    primary_threats: List[str] = Field(description="List of main threat types detected")
    timeline_overview: str = Field(description="Brief narrative of events")
    safety_recommendations: str = Field(description="Overall recommendations for driver")

class RoadRageAnalysis(BaseModel):
    analysis_metadata: AnalysisMetadata
    incidents: List[Incident] = Field(description="List of detected incidents")
    summary: Summary


# Configuration
VIDEO_FILE = "data/videos/road_rage_3.mp4"  # Path to dashcam video
CHUNK_DURATION_MINUTES = 2  # Split into 2-minute chunks
CHUNKS_DIR = "data/chunks"
MAX_RETRIES = 3
PROCESSING_TIMEOUT = 600  # 10 minutes max wait for processing
VIDEO_FPS = 1  # Frames per second for video analysis (1 FPS for dashcam is sufficient)
MAX_INLINE_SIZE_MB = 20  # Maximum file size for inline upload
MIN_CHUNK_SIZE_MB = 0.1  # Minimum chunk size to process (skip corrupted/empty chunks)
MODEL = "gemini-2.5-flash"  # Using gemini-2.0-flash-exp for multimodal analysis
OUTPUT_FILE = f"results/{MODEL}_road_rage_analysis_fps{VIDEO_FPS}.json"


def split_video_into_chunks(video_path: str, chunk_duration_min: int, output_dir: str) -> List[str]:
    """Split video into smaller chunks using ffmpeg."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Get video duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
         "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True
    )
    total_duration = float(result.stdout.strip())
    print(f"Total video duration: {total_duration/60:.1f} minutes")
    
    chunk_duration_sec = chunk_duration_min * 60
    chunk_files = []
    
    # Split video
    num_chunks = int(total_duration // chunk_duration_sec) + 1
    print(f"Splitting into {num_chunks} chunks of ~{chunk_duration_min} minutes each...")
    
    for i in range(num_chunks):
        start_time = i * chunk_duration_sec
        output_file = os.path.join(output_dir, f"chunk_{i:03d}.webm")
        
        if not os.path.exists(output_file):
            print(f"Creating chunk {i+1}/{num_chunks}...")
            subprocess.run([
                "ffmpeg", "-y", "-i", video_path,
                "-ss", str(start_time), "-t", str(chunk_duration_sec),
                "-c", "copy", output_file
            ], capture_output=True)
        else:
            print(f"Chunk {i+1}/{num_chunks} already exists, skipping...")
        
        chunk_files.append(output_file)
    
    return chunk_files


def upload_and_wait(file_path: str, timeout: int = PROCESSING_TIMEOUT) -> object:
    """Upload file and wait for processing with timeout."""
    myfile = client.files.upload(file=file_path)
    print(f"Uploaded: {file_path} -> {myfile.name}, state: {myfile.state}")
    
    start_time = time.time()
    while myfile.state == "PROCESSING":
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise TimeoutError(f"Processing timeout for {file_path} after {timeout}s")
        
        print(f"  Processing... ({elapsed:.0f}s elapsed)")
        time.sleep(10)
        myfile = client.files.get(name=myfile.name)
    
    if myfile.state == "FAILED":
        raise ValueError(f"File processing failed: {myfile.name}")
    
    print(f"  File ready: {myfile.state}")
    return myfile


def get_mime_type(file_path: str) -> str:
    """Get MIME type based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.webm': 'video/webm',
        '.mp4': 'video/mp4',
        '.avi': 'video/avi',
        '.mov': 'video/quicktime',
        '.mkv': 'video/x-matroska',
    }
    return mime_types.get(ext, 'video/mp4')


def adjust_timestamps(incidents: list, offset_minutes: int) -> list:
    """
    Adjust timestamps in incidents by adding an offset.
    Handles timestamp format: "HH:MM:SS"
    """
    def parse_time_to_seconds(time_str: str) -> int:
        """Convert time string to seconds."""
        time_str = time_str.strip()
        parts = time_str.split(':')
        
        if len(parts) == 2:  # MM:SS or M:SS
            minutes = int(parts[0])
            seconds = int(float(parts[1]))
            return minutes * 60 + seconds
        elif len(parts) == 3:  # HH:MM:SS
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(float(parts[2]))
            return hours * 3600 + minutes * 60 + seconds
        else:
            return 0
    
    def seconds_to_time_str(seconds: int) -> str:
        """Convert seconds to time string in HH:MM:SS format."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    offset_seconds = offset_minutes * 60
    adjusted_incidents = []
    
    for incident in incidents:
        adjusted_incident = incident.copy()
        if 'start_time' in adjusted_incident:
            start_seconds = parse_time_to_seconds(adjusted_incident['start_time'])
            adjusted_incident['start_time'] = seconds_to_time_str(start_seconds + offset_seconds)
        if 'end_time' in adjusted_incident:
            end_seconds = parse_time_to_seconds(adjusted_incident['end_time'])
            adjusted_incident['end_time'] = seconds_to_time_str(end_seconds + offset_seconds)
        adjusted_incidents.append(adjusted_incident)
    
    return adjusted_incidents


def process_chunk_inline(file_path: str, chunk_index: int, start_minutes: int) -> dict:
    """Process a single video chunk with Gemini using inline data with FPS metadata."""
    # Modify prompt to include chunk context
    chunk_prompt = f"""This is chunk {chunk_index + 1} of the dashcam footage, starting at approximately {start_minutes} minutes into the full recording.
    
    {perception_prompt}
    
    Note: Provide timestamps relative to the start of this chunk (starting from 00:00:00)."""

    # Read video bytes
    video_bytes = open(file_path, 'rb').read()
    mime_type = get_mime_type(file_path)
    
    # Create content with FPS metadata
    content = types.Content(
        parts=[
            types.Part(
                inline_data=types.Blob(
                    data=video_bytes,
                    mime_type=mime_type
                ),
                video_metadata=types.VideoMetadata(fps=VIDEO_FPS)
            ),
            types.Part(text=chunk_prompt)
        ]
    )

    response = client.models.generate_content(
        model=MODEL, 
        contents=content,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": RoadRageAnalysis.model_json_schema(),
        }, 
    )
    
    print(f"  Tokens used: {response.usage_metadata}")
    result = json.loads(response.text)
    
    # Adjust timestamps to reflect absolute time in original video
    if 'incidents' in result:
        result['incidents'] = adjust_timestamps(result['incidents'], start_minutes)
    
    return result


def process_chunk_uploaded(myfile, chunk_index: int, start_minutes: int) -> dict:
    """Process a single video chunk with Gemini using uploaded file (for files > 20MB)."""
    # Modify prompt to include chunk context
    chunk_prompt = f"""This is chunk {chunk_index + 1} of the dashcam footage, starting at approximately {start_minutes} minutes into the full recording.
    
    {perception_prompt}
    
    Note: Provide timestamps relative to the start of this chunk (starting from 00:00:00)."""

    response = client.models.generate_content(
            model=MODEL, 
            contents=[myfile, chunk_prompt],
            config={
                "response_mime_type": "application/json",
                "response_json_schema": RoadRageAnalysis.model_json_schema(),
            }, 
        )
    
    print(f"  Tokens used: {response.usage_metadata}")
    result = json.loads(response.text)
    
    # Adjust timestamps to reflect absolute time in original video
    if 'incidents' in result:
        result['incidents'] = adjust_timestamps(result['incidents'], start_minutes)
    
    return result


def main():
    all_incidents = []
    analysis_metadata = None
    all_summaries = []
    
    # Check if we should split the video
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
         "-of", "default=noprint_wrappers=1:nokey=1", VIDEO_FILE],
        capture_output=True, text=True
    )
    total_duration_min = float(result.stdout.strip()) / 60
    total_duration_sec = int(float(result.stdout.strip()))
    
    if total_duration_min > 15:  # Split videos longer than 15 minutes
        print(f"Video is {total_duration_min:.1f} minutes - splitting into chunks...")
        chunk_files = split_video_into_chunks(VIDEO_FILE, CHUNK_DURATION_MINUTES, CHUNKS_DIR)
        
        for i, chunk_file in enumerate(chunk_files):
            print(f"\n--- Processing chunk {i+1}/{len(chunk_files)} ---")
            start_minutes = i * CHUNK_DURATION_MINUTES
            
            # Check file size to decide between inline and upload
            file_size_mb = os.path.getsize(chunk_file) / (1024 * 1024)
            
            # Skip empty/corrupted chunks
            if file_size_mb < MIN_CHUNK_SIZE_MB:
                print(f"  Skipping chunk (file size {file_size_mb:.3f}MB < {MIN_CHUNK_SIZE_MB}MB - likely empty/corrupted)")
                continue
            
            use_inline = file_size_mb < MAX_INLINE_SIZE_MB
            
            for attempt in range(MAX_RETRIES):
                try:
                    if use_inline:
                        print(f"  Using inline upload with FPS={VIDEO_FPS} (file size: {file_size_mb:.1f}MB)")
                        chunk_result = process_chunk_inline(chunk_file, i, start_minutes)
                    else:
                        print(f"  Using file upload (file size: {file_size_mb:.1f}MB > {MAX_INLINE_SIZE_MB}MB)")
                        myfile = upload_and_wait(chunk_file)
                        chunk_result = process_chunk_uploaded(myfile, i, start_minutes)
                        # Clean up uploaded file
                        try:
                            client.files.delete(name=myfile.name)
                        except:
                            pass
                    
                    # Collect incidents from this chunk
                    all_incidents.extend(chunk_result.get("incidents", []))
                    
                    # Store metadata from first chunk
                    if analysis_metadata is None and "analysis_metadata" in chunk_result:
                        analysis_metadata = chunk_result["analysis_metadata"]
                    
                    # Collect summaries for later aggregation
                    if "summary" in chunk_result:
                        all_summaries.append(chunk_result["summary"])
                    
                    break
                    
                except (TimeoutError, ValueError, APIError) as e:
                    print(f"  Attempt {attempt+1} failed: {e}")
                    if attempt == MAX_RETRIES - 1:
                        print(f"  Skipping chunk {i+1} after {MAX_RETRIES} failures")
                    else:
                        time.sleep(30)  # Wait before retry
    else:
        # Process single file for shorter videos
        print(f"Video is {total_duration_min:.1f} minutes - processing as single file...")
        
        file_size_mb = os.path.getsize(VIDEO_FILE) / (1024 * 1024)
        
        if file_size_mb < MAX_INLINE_SIZE_MB:
            # Use inline upload with FPS metadata
            print(f"Using inline upload with FPS={VIDEO_FPS} (file size: {file_size_mb:.1f}MB)")
            video_bytes = open(VIDEO_FILE, 'rb').read()
            mime_type = get_mime_type(VIDEO_FILE)
            
            content = types.Content(
                parts=[
                    types.Part(
                        inline_data=types.Blob(
                            data=video_bytes,
                            mime_type=mime_type
                        ),
                        video_metadata=types.VideoMetadata(fps=VIDEO_FPS)
                    ),
                    types.Part(text=perception_prompt)
                ]
            )
            
            response = client.models.generate_content(
                model=MODEL, 
                contents=content,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": RoadRageAnalysis.model_json_schema(),
                }, 
            )
            result_data = json.loads(response.text)
            all_incidents = result_data.get("incidents", [])
            analysis_metadata = result_data.get("analysis_metadata")
            all_summaries = [result_data.get("summary")] if "summary" in result_data else []
            print(response.usage_metadata)
        else:
            # Use file upload for larger files
            print(f"Using file upload (file size: {file_size_mb:.1f}MB > {MAX_INLINE_SIZE_MB}MB)")
            myfile = upload_and_wait(VIDEO_FILE)
            
            tokens = client.models.count_tokens(
                model=MODEL, contents=[perception_prompt, myfile]
            )
            print(f"TotalTokens: {tokens}")
            
            response = client.models.generate_content(
                model=MODEL, 
                contents=[myfile, perception_prompt],
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": RoadRageAnalysis.model_json_schema(),
                }, 
            )
            result_data = json.loads(response.text)
            all_incidents = result_data.get("incidents", [])
            analysis_metadata = result_data.get("analysis_metadata")
            all_summaries = [result_data.get("summary")] if "summary" in result_data else []
            print(response.usage_metadata)
    
    # Aggregate summaries from multiple chunks
    all_threat_types = []
    for summary in all_summaries:
        if summary and "primary_threats" in summary:
            all_threat_types.extend(summary["primary_threats"])
    unique_threats = list(set(all_threat_types))
    
    # Determine overall threat level
    threat_levels = [incident.get("threat_level", "Low") for incident in all_incidents]
    if "Critical" in threat_levels:
        overall_threat = "Critical"
    elif "High" in threat_levels:
        overall_threat = "High"
    elif "Moderate" in threat_levels:
        overall_threat = "Moderate"
    else:
        overall_threat = "Low"
    
    # Create aggregated analysis
    final_result = {
        "analysis_metadata": {
            "video_duration": str(total_duration_sec),
            "analysis_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "overall_threat_level": overall_threat
        },
        "incidents": all_incidents,
        "summary": {
            "total_incidents": len(all_incidents),
            "primary_threats": unique_threats,
            "timeline_overview": f"Analyzed {total_duration_min:.1f} minutes of dashcam footage. Detected {len(all_incidents)} potential road rage incidents.",
            "safety_recommendations": "Review all incidents and consider reporting high/critical threats to authorities."
        }
    }
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Save combined response to json file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(final_result, f, indent=2)
    
    print(f"\n=== Complete ===")
    print(f"Total incidents detected: {len(all_incidents)}")
    print(f"Overall threat level: {overall_threat}")
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
