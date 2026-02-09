# Road Rage POC

Proof of concept for detecting road rage from dashcam footage using Gemini Flash Vision and providing real-time de-escalation guidance.

## Components

### 1. **Perception Agent** (`src/gemini_fact_extraction.py`)
- Analyzes dashcam video and audio
- Detects road rage threats and behaviors
- Outputs structured threat assessments
- Model: `gemini-2.5-flash`

### 2. **De-escalation Agent** (`src/deescalation_agent.py`) ⭐ NEW
- Converts threat assessments into audio safety guidance
- Provides calm, actionable instructions to drivers
- Real-time de-escalation protocols
- Model: `gemini-2.5-flash-preview-tts`
- Voice options: **Puck** (recommended), Aoede, Charon, Kore
- Audio quality: See [Audio Quality Guide](docs/AUDIO_QUALITY_GUIDE.md)

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

### Run Perception Agent

```bash
python src/gemini_fact_extraction.py
```

### Run De-escalation Agent

```bash
python src/deescalation_agent.py
```

## Documentation

- [De-escalation Agent Guide](docs/DEESCALATION_AGENT.md) - Comprehensive usage and system prompt documentation
- [Audio Quality Guide](docs/AUDIO_QUALITY_GUIDE.md) - Fix unclear audio, test voices ⭐
- [System Prompt Design](docs/SYSTEM_PROMPT_DESIGN.md) - Design philosophy and principles
- [API Migration Guide](docs/API_MIGRATION.md) - New Google Genai API changes
- [Quick Start](QUICKSTART.md) - 5-minute setup guide

## Example Pipeline

```
Dashcam Video → Perception Agent → Threat Assessment (JSON)
                                           ↓
                                  De-escalation Agent
                                           ↓
                                  Audio Safety Guidance
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

## Project Structure

```
road_rage_poc/
├── src/
│   ├── gemini_fact_extraction.py  # Perception agent
│   ├── deescalation_agent.py      # De-escalation agent
│   ├── deescalation_prompt.py     # System prompt
│   └── prompts.py                 # Perception prompts
├── results/
│   ├── *.json                     # Threat assessments
│   └── audio/                     # Generated audio guidance
├── docs/
│   └── DEESCALATION_AGENT.md      # Full documentation
├── requirements.txt
└── README.md
```
