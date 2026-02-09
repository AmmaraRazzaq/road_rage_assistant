# Quick Start Guide - De-escalation Agent

Get the de-escalation agent running in 5 minutes.

## Prerequisites

- Python 3.8+
- Google API key with Gemini access
- Conda (zutec environment)

## Step 1: Setup Environment

```bash
# Activate conda environment
conda activate zutec

# Install dependencies
pip install google-genai python-dotenv
```

## Step 2: Configure API Key

```bash
# Create .env file with your API key
echo "GOOGLE_API_KEY=your_actual_api_key_here" > .env
```

## Step 3: Run the Agent

### Option A: Process Existing Results

```bash
# Run on the sample perception output
python src/deescalation_agent.py
```

**Expected Output:**
```
============================================================
DE-ESCALATION AGENT - Real-time Safety Guidance
============================================================

Analyzing perception output from: gemini-2.5-flash_road_rage_analysis_fps1.json
Overall Threat Level: High
Total Incidents: 2

============================================================

[GENERATING OVERALL SAFETY GUIDANCE]

Audio Transcript:
------------------------------------------------------------
Lock your doors now. Stay inside your vehicle and keep your
hands visible. Do not engage with the person blocking you.
If you can safely drive away, proceed to a well-lit public
area. If blocked, call 911.
------------------------------------------------------------
```

### Option B: Run Complete Pipeline Demo

```bash
python examples/complete_pipeline.py
```

This demonstrates:
- Real-time monitoring simulation
- Different threat scenarios
- Adaptive guidance by threat level

### Option C: Use in Your Code

```python
from src.deescalation_agent import DeescalationAgent
import json

# Initialize
agent = DeescalationAgent()

# Load perception output
with open("results/perception_output.json") as f:
    data = json.load(f)

# Generate guidance
guidance = agent.generate_guidance(data)

# Get text transcript
print(guidance['text'])

# Save audio (if available)
if 'audio' in guidance:
    with open("guidance.mp3", "wb") as f:
        f.write(guidance['audio'])
```

## Step 4: Test with Custom Scenarios

```python
from src.deescalation_agent import DeescalationAgent

agent = DeescalationAgent()

# Create test scenario
test_scenario = {
    "analysis_metadata": {"overall_threat_level": "High"},
    "incidents": [{
        "incident_id": 1,
        "threat_level": "High",
        "threat_type": "approaching_person",
        "visual_observations": {
            "description": "Aggressive person approaching driver's door",
            "approaching_persons": {
                "detected": True,
                "proximity": "0-1 meter"
            }
        },
        "recommended_action": "lock_doors"
    }],
    "summary": {"primary_threats": ["approaching_person"]}
}

# Generate guidance
guidance = agent.generate_guidance(test_scenario)
print(guidance['text'])
```

## Common Use Cases

### 1. Process Single Incident

```python
guidance = agent.generate_guidance(
    perception_output,
    focus_incident=1  # Focus on incident ID 1
)
```

### 2. Monitor Continuously

```python
for incident_id, guidance in agent.generate_continuous_guidance(perception_output):
    print(f"Incident {incident_id}: {guidance['text']}")
    # Play audio, log, etc.
```

### 3. Save Audio Output

```python
if 'audio' in guidance:
    agent.save_guidance_audio(guidance, "output/guidance.mp3")
```

## Troubleshooting

### "API key is required"
Make sure `.env` file exists with `GOOGLE_API_KEY=your_key`

### "Module not found: deescalation_prompt"
Make sure you're running from the project root or adjust `sys.path`

### "No audio in response"
The Gemini audio preview model may return text-only in some cases. Check `guidance['text']` for transcript.

### Model not available
Ensure you have access to `gemini-2.5-flash-preview-tts` (the current audio model)

## Next Steps

- Read full documentation: [`docs/DEESCALATION_AGENT.md`](docs/DEESCALATION_AGENT.md)
- Understand prompt design: [`docs/SYSTEM_PROMPT_DESIGN.md`](docs/SYSTEM_PROMPT_DESIGN.md)
- Customize system prompt: [`src/deescalation_prompt.py`](src/deescalation_prompt.py)
- Integrate with your perception agent
- Add audio playback in your app

## File Overview

| File | Purpose |
|------|---------|
| `src/deescalation_prompt.py` | System prompt definition |
| `src/deescalation_agent.py` | Main agent implementation |
| `examples/complete_pipeline.py` | Demo script |
| `docs/DEESCALATION_AGENT.md` | Full documentation |
| `docs/SYSTEM_PROMPT_DESIGN.md` | Prompt design guide |

## Support

Questions? Check:
1. Documentation in `docs/`
2. Example code in `examples/`
3. System prompt in `src/deescalation_prompt.py`

---

Ready to build? Start with: `python src/deescalation_agent.py`
