# Road Rage Detection Pipeline - Complete System Overview

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ROAD RAGE DETECTION PIPELINE                │
│                         (src/pipeline.py)                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│   Dashcam Video     │
│  (.mp4, .webm)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: PERCEPTION AGENT (gemini_fact_extraction.py)           │
│  ─────────────────────────────────────────────────────────────  │
│  • Analyzes video frames and audio                              │
│  • Detects threats: approaching persons, aggressive honking,    │
│    verbal threats, blocking behavior                            │
│  • Classifies threat levels: Low/Moderate/High/Critical         │
│  • Model: gemini-2.5-flash                                      │
│  • Output: JSON threat assessment                               │
└──────────┬──────────────────────────────────────────────────────┘
           │
           │ perception_output.json
           │ {
           │   "overall_threat_level": "High",
           │   "incidents": [...]
           │ }
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: DE-ESCALATION AGENT (deescalation_agent.py)            │
│  ─────────────────────────────────────────────────────────────  │
│  • Processes threat assessment for each incident                │
│  • Generates calm, actionable safety instructions               │
│  • Converts text to natural-sounding speech                     │
│  • Model: gemini-2.5-flash (text) + gemini-2.5-flash-preview-  │
│    tts (audio)                                                  │
│  • Voice: Puck (clear professional male)                        │
│  • Output: WAV audio files + text transcripts                   │
└──────────┬──────────────────────────────────────────────────────┘
           │
           │ incident_1_guidance.wav
           │ incident_1_guidance.txt
           │ incident_2_guidance.wav
           │ incident_2_guidance.txt
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: POST-INCIDENT AGENT (post_incident_agent.py)           │
│  ─────────────────────────────────────────────────────────────  │
│  • Combines perception data + guidance transcripts              │
│  • Generates comprehensive incident report                      │
│  • Creates 3 report formats:                                    │
│    1. Incident Summary (brief overview)                         │
│    2. Detailed Timeline (chronological events)                  │
│    3. Police Report (neutral, factual format)                   │
│  • Model: gemini-2.5-flash                                      │
│  • Output: TXT reports + JSON                                   │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FINAL OUTPUTS                               │
│  ─────────────────────────────────────────────────────────────  │
│  results/                                                        │
│  ├── gemini-2.5-flash_road_rage_analysis_fps1.json             │
│  ├── audio/                                                      │
│  │   ├── incident_1_guidance.wav                                │
│  │   ├── incident_1_guidance.txt                                │
│  │   ├── incident_2_guidance.wav                                │
│  │   └── incident_2_guidance.txt                                │
│  └── reports/                                                    │
│      ├── incident_report.txt (full report)                      │
│      ├── incident_report.json (structured data)                 │
│      ├── incident_report_summary.txt                            │
│      ├── incident_report_timeline.txt                           │
│      └── incident_report_police_report.txt                      │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Pipeline Orchestrator (`src/pipeline.py`)

**Class:** `RoadRagePipeline`

Coordinates all three agents in sequence with error handling, progress tracking, and flexible execution modes.

**Key Features:**
- Automated workflow execution
- Two modes: full pipeline or from existing perception
- Configurable voice and output directories
- Comprehensive error handling and logging
- Individual agent access for custom workflows

### 2. Perception Agent (`src/gemini_fact_extraction.py`)

**Input:** Dashcam video file
**Output:** JSON threat assessment
**Processing:** 
- Splits long videos into chunks
- Analyzes at 1 FPS for efficiency
- Structured output with Pydantic schemas

**Detected Threats:**
- Approaching persons (proximity, behavior)
- Aggressive honking (pattern, intensity)
- Verbal threats (tone, content)
- Blocking behavior (duration, type)

### 3. De-escalation Agent (`src/deescalation_agent.py`)

**Class:** `DeescalationAgent`

**Input:** Perception JSON
**Output:** Audio guidance + text transcripts

**Features:**
- Incident-specific or overall guidance
- Professional, calm voice delivery
- Multiple voice options
- Low-temperature generation for consistency

**Example Output:**
> "Stay calm. Lock your doors immediately. Keep your hands visible on the steering wheel. Do not make eye contact with the approaching individual. Call 911 if you have not already done so."

### 4. Post-Incident Agent (`src/post_incident_agent.py`)

**Class:** `PostIncidentAgent`

**Input:** Perception JSON + guidance transcripts
**Output:** Comprehensive incident reports

**Report Sections:**

1. **Incident Summary**
   - Brief overview of events
   - Key findings
   - Overall assessment

2. **Detailed Timeline**
   - Chronological event sequence
   - Timestamps for each incident
   - Threat levels and actions

3. **Police Report**
   - Neutral, factual language
   - Suitable for law enforcement
   - Evidence documentation

## Usage Modes

### Mode 1: Full Pipeline (All Three Agents)

```bash
# Simple run
python run_pipeline.py

# Or with CLI options
python src/pipeline.py --mode full --voice Puck --output-dir results/
```

**When to use:**
- First-time analysis of a video
- Complete end-to-end processing needed
- Starting from raw dashcam footage

**Duration:** 5-15 minutes depending on video length

### Mode 2: From Existing Perception (Skip Video Analysis)

```bash
python src/pipeline.py --mode from-perception \
    --perception-file results/gemini-2.5-flash_road_rage_analysis_fps1.json
```

**When to use:**
- Re-running with different voice settings
- Regenerating reports after prompt changes
- Testing without reprocessing video

**Duration:** 1-3 minutes

### Mode 3: Individual Agents (Custom Workflow)

```python
from src.pipeline import RoadRagePipeline

pipeline = RoadRagePipeline()

# Run only perception
perception_data = pipeline.run_perception_agent()

# Custom logic here...

# Run only de-escalation
guidance = pipeline.run_deescalation_agent(perception_data)
```

**When to use:**
- Custom workflows
- Debugging specific components
- Integration with other systems

## Configuration Options

### Voice Selection
- `Puck` (default) - Clear professional male
- `Aoede` - Clear professional female  
- `Kore` - Authoritative female
- `Charon` - Deep authoritative male

### Output Directory
- Default: `results/`
- Custom: `--output-dir my_results/`

### API Configuration
- Via environment: `GEMINI_API_KEY` in `.env`
- Via parameter: `RoadRagePipeline(api_key="...")`

## File Structure

```
road_rage_poc/
├── src/
│   ├── pipeline.py                    # Main orchestrator ⭐
│   ├── gemini_fact_extraction.py      # Perception agent
│   ├── deescalation_agent.py          # De-escalation agent
│   ├── deescalation_prompt.py         # De-escalation system prompt
│   ├── post_incident_agent.py         # Post-incident agent
│   ├── post_incident_prompt.py        # Post-incident system prompt
│   └── prompts.py                     # Perception prompts
│
├── data/
│   └── videos/
│       └── road_rage_3.mp4            # Default test video
│
├── results/
│   ├── gemini-2.5-flash_road_rage_analysis_fps1.json
│   ├── audio/
│   │   ├── incident_N_guidance.wav
│   │   └── incident_N_guidance.txt
│   └── reports/
│       ├── incident_report.txt
│       ├── incident_report.json
│       ├── incident_report_summary.txt
│       ├── incident_report_timeline.txt
│       └── incident_report_police_report.txt
│
├── docs/
│   ├── PIPELINE_GUIDE.md              # Detailed usage guide ⭐
│   ├── DEESCALATION_AGENT.md
│   ├── AUDIO_QUALITY_GUIDE.md
│   └── SYSTEM_PROMPT_DESIGN.md
│
├── run_pipeline.py                    # Simple entry point ⭐
├── requirements.txt
└── README.md
```

## Quick Start Commands

```bash
# 1. Setup
conda activate zutec
pip install -r requirements.txt
echo "GEMINI_API_KEY=your_key" > .env

# 2. Run pipeline
python run_pipeline.py

# 3. Check results
ls -R results/
```

## Pipeline Output Summary

After successful execution, you'll have:

1. **Threat Analysis** - JSON with all detected incidents
2. **Audio Guidance** - WAV files for real-time driver assistance
3. **Text Transcripts** - Human-readable guidance text
4. **Incident Reports** - Multiple formats for different audiences
5. **Structured Data** - JSON for programmatic access

## Error Handling

The pipeline includes:
- Comprehensive error messages
- Progress indicators
- Partial result saving
- Detailed stack traces
- Automatic retry logic (in perception agent)

If a step fails, you can:
1. Check console output for specific error
2. Fix the issue
3. Resume from last successful step using `--mode from-perception`

## Performance Characteristics

| Operation | Duration | Model | Cost Estimate |
|-----------|----------|-------|---------------|
| Perception (5 min video) | 2-3 min | gemini-2.5-flash | ~$0.01 |
| De-escalation (per incident) | 10-15 sec | gemini-2.5-flash + TTS | ~$0.005 |
| Post-incident report | 30-60 sec | gemini-2.5-flash | ~$0.005 |
| **Total (2 incidents)** | **3-5 min** | - | **~$0.025** |

*Note: Costs are rough estimates and vary based on video length and incident count.*

## Advanced Features

### Batch Processing
Process multiple videos sequentially:
```python
for video in video_files:
    pipeline = RoadRagePipeline(output_base_dir=f"results/{video.stem}/")
    pipeline.run_full_pipeline(video_file=video)
```

### Custom Workflows
Access individual agents for specialized use cases:
```python
# Example: Generate multiple voice versions
voices = ['Puck', 'Aoede', 'Kore', 'Charon']
for voice in voices:
    pipeline = RoadRagePipeline(voice_name=voice)
    pipeline.run_deescalation_agent(perception_data)
```

### Integration
The pipeline can be imported and used in larger systems:
```python
from src.pipeline import RoadRagePipeline

# In your application
def process_dashcam_video(video_path):
    pipeline = RoadRagePipeline()
    results = pipeline.run_full_pipeline(video_file=video_path)
    return results['report']
```

## Next Steps

1. **Run the pipeline** - `python run_pipeline.py`
2. **Review outputs** - Check `results/` directory
3. **Read guides** - See `docs/PIPELINE_GUIDE.md` for details
4. **Customize** - Adjust voices, prompts, or add custom logic
5. **Integrate** - Use in your own applications

## Support

For detailed usage instructions, see:
- [Complete Pipeline Guide](docs/PIPELINE_GUIDE.md)
- [De-escalation Documentation](docs/DEESCALATION_AGENT.md)
- [Audio Quality Tips](docs/AUDIO_QUALITY_GUIDE.md)
