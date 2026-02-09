# Road Rage POC

Proof of concept for detecting road rage from dashcam footage using Gemini Flash Vision and providing real-time de-escalation guidance.

## Components

### 1. **Perception Agent** (`src/gemini_fact_extraction.py`)
- Analyzes dashcam video and audio
- Detects road rage threats and behaviors
- Outputs structured threat assessments
- Model: `gemini-2.5-flash`

### 2. **De-escalation Agent** (`src/deescalation_agent.py`)
- Converts threat assessments into audio safety guidance
- Provides calm, actionable instructions to drivers
- Real-time de-escalation protocols
- Model: `gemini-2.5-flash-preview-tts`
- Voice options: **Puck** (recommended), Aoede, Charon, Kore
- Audio quality: See [Audio Quality Guide](docs/AUDIO_QUALITY_GUIDE.md)

### 3. **Post-Incident Agent** (`src/post_incident_agent.py`)
- Generates comprehensive incident reports
- Creates detailed timeline of events
- Produces police-ready neutral reports
- Model: `gemini-2.5-flash`
- Combines perception data and de-escalation guidance

### 4. **Pipeline** (`src/pipeline.py`) ⭐ NEW
- Orchestrates all three agents in sequence
- Automated workflow: Perception → De-escalation → Post-Incident
- Supports full pipeline or partial runs
- Saves all outputs (JSON, audio, reports)

## Quick Start

### Setup

```bash
# Activate environment
conda activate zutec

# Install dependencies
pip install -r requirements.txt

# Configure API key
echo "GOOGLE_API_KEY=your_key_here" > .env
```

### Web Application (NEW! 🎉)

**Easy-to-use web interface with real-time progress updates!**

```bash
# Start the web application
./start_webapp.sh

# Or manually:
conda activate zutec
python app.py
```

Then open your browser to `http://localhost:5000` and upload your dashcam video!

Features:
- 📹 Drag-and-drop video upload
- ⚡ Real-time processing updates
- 🎙️ Audio guidance playback
- 📊 Interactive results display
- 📥 Download reports and audio files

**See [WEB_APP_README.md](WEB_APP_README.md) for detailed documentation.**

### Run Complete Pipeline (Command Line)

```bash
# Run all three agents in sequence
python run_pipeline.py

# Or use the pipeline module directly
python src/pipeline.py --mode full

# Run from existing perception data (skip video analysis)
python src/pipeline.py --mode from-perception --perception-file results/gemini-2.5-flash_road_rage_analysis_fps1.json
```

### Run Individual Agents

```bash
# 1. Perception Agent (video analysis)
python src/gemini_fact_extraction.py

# 2. De-escalation Agent (audio guidance)
python src/deescalation_agent.py

# 3. Post-Incident Agent (reports)
python src/post_incident_agent.py
```

## Documentation

- **[Web Application Guide](WEB_APP_README.md)** - Web interface setup and usage 🎉 NEW
- **[Pipeline Overview](PIPELINE_OVERVIEW.md)** - System architecture and complete workflow ⭐ START HERE
- [Pipeline Guide](docs/PIPELINE_GUIDE.md) - Complete pipeline usage and configuration
- [De-escalation Agent Guide](docs/DEESCALATION_AGENT.md) - Comprehensive usage and system prompt documentation
- [Audio Quality Guide](docs/AUDIO_QUALITY_GUIDE.md) - Fix unclear audio, test voices
- [System Prompt Design](docs/SYSTEM_PROMPT_DESIGN.md) - Design philosophy and principles
- [API Migration Guide](docs/API_MIGRATION.md) - New Google Genai API changes
- [Quick Start](QUICKSTART.md) - 5-minute setup guide

## Complete Pipeline Workflow

```
Dashcam Video → Perception Agent → Threat Assessment (JSON)
                                           ↓
                                  De-escalation Agent
                                           ↓
                                  Audio Safety Guidance (WAV + TXT)
                                           ↓
                                  Post-Incident Agent
                                           ↓
                     Comprehensive Reports (Summary, Timeline, Police Report)
```

## Example Output

**Perception Agent Output:**
```json
{
  "overall_threat_level": "High",
  "incidents": [{
    "threat_type": "approaching_person",
    "threat_level": "High",
    "recommended_action": "lock_doors"
  }]
}
```

**De-escalation Agent Audio Guidance:**
> "Lock your doors now. Stay inside your vehicle. Keep your hands on the wheel. Start recording if you can safely reach your phone. Do not engage."

**Post-Incident Agent Report:**
- Incident summary with key events
- Detailed timeline with timestamps
- Police-ready neutral report format

## Project Structure

```
road_rage_poc/
├── app.py                         # Flask web application 🎉 NEW
├── start_webapp.sh                # Web app startup script 🎉 NEW
├── templates/
│   └── index.html                 # Web interface
├── static/
│   ├── css/style.css              # UI styles
│   └── js/app.js                  # Frontend JavaScript
├── src/
│   ├── gemini_fact_extraction.py  # Perception agent
│   ├── deescalation_agent.py      # De-escalation agent
│   ├── deescalation_prompt.py     # De-escalation system prompt
│   ├── post_incident_agent.py     # Post-incident report generator
│   ├── post_incident_prompt.py    # Post-incident system prompt
│   ├── pipeline.py                # Complete pipeline orchestrator ⭐
│   └── prompts.py                 # Perception prompts
├── uploads/                       # Uploaded videos (web app)
├── results/
│   ├── *.json                     # Threat assessments
│   ├── audio/                     # Generated audio guidance
│   └── reports/                   # Post-incident reports
├── docs/
│   └── DEESCALATION_AGENT.md      # Full documentation
├── run_pipeline.py                # Simple pipeline runner ⭐
├── WEB_APP_README.md              # Web application documentation 🎉
├── requirements.txt
└── README.md
```
