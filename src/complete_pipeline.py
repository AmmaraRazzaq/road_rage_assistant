"""
Complete Pipeline Example: Perception → De-escalation
Shows how to use both agents together for real-time road rage response
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
from deescalation_agent import DeescalationAgent


def simulate_realtime_monitoring():
    """
    Simulate real-time monitoring where:
    1. Perception agent analyzes video frames
    2. Threat detected
    3. De-escalation agent provides immediate audio guidance
    """
    
    print("=" * 70)
    print("REAL-TIME ROAD RAGE MONITORING SIMULATION")
    print("=" * 70)
    
    # Load pre-analyzed perception output
    # In production, this would be real-time from video stream
    perception_file = Path(__file__).parent.parent / "results" / "gemini-2.5-flash_road_rage_analysis_fps1.json"
    
    with open(perception_file, 'r') as f:
        perception_output = json.load(f)
    
    # Initialize de-escalation agent
    agent = DeescalationAgent()
    
    print("\n[00:00:00] Dashcam recording started...")
    print("[00:00:00] Perception agent monitoring for threats...\n")
    
    # Simulate incident detection and response
    for incident in perception_output["incidents"]:
        timestamp = incident["start_time"]
        threat_type = incident["threat_type"].replace("_", " ").title()
        threat_level = incident["threat_level"]
        
        print("=" * 70)
        print(f"⚠️  [{timestamp}] THREAT DETECTED")
        print("=" * 70)
        print(f"Type: {threat_type}")
        print(f"Level: {threat_level}")
        print(f"\nDescription: {incident['visual_observations']['description'][:150]}...")
        
        # Generate immediate de-escalation guidance
        print(f"\n🔊 [AUDIO GUIDANCE PLAYING]\n")
        
        guidance = agent.generate_guidance(
            perception_output,
            focus_incident=incident["incident_id"]
        )
        
        if 'text' in guidance:
            # Display what the driver hears
            print("─" * 70)
            print(guidance['text'])
            print("─" * 70)
        
        print(f"\n✓ Guidance delivered at [{timestamp}]")
        print()
    
    # Final summary
    print("=" * 70)
    print("SESSION SUMMARY")
    print("=" * 70)
    print(f"Duration: {perception_output['analysis_metadata']['video_duration']} seconds")
    print(f"Threats Detected: {perception_output['summary']['total_incidents']}")
    print(f"Overall Threat Level: {perception_output['analysis_metadata']['overall_threat_level']}")
    print(f"Safety Guidance Provided: {len(perception_output['incidents'])} times")
    print("\nRecommendation: Review full incident log and report to authorities if necessary.")
    print("=" * 70)


def demonstrate_threat_scenarios():
    """
    Demonstrate de-escalation responses to different threat scenarios
    """
    print("\n" + "=" * 70)
    print("DE-ESCALATION RESPONSES TO COMMON SCENARIOS")
    print("=" * 70)
    
    agent = DeescalationAgent()
    
    scenarios = [
        {
            "name": "Approaching Aggressive Person",
            "data": {
                "analysis_metadata": {"overall_threat_level": "High"},
                "incidents": [{
                    "incident_id": 1,
                    "start_time": "00:00:05",
                    "end_time": "00:00:15",
                    "threat_level": "High",
                    "threat_type": "approaching_person",
                    "visual_observations": {
                        "description": "Person exited vehicle and rapidly approaching driver's side door with aggressive posture",
                        "approaching_persons": {
                            "detected": True,
                            "count": 1,
                            "proximity": "0-1 meter",
                            "behavior": "Rapid, aggressive approach"
                        }
                    },
                    "audio_observations": {
                        "verbal_threats": {"detected": True, "tone": "Shouting"}
                    },
                    "recommended_action": "lock_doors"
                }],
                "summary": {"primary_threats": ["approaching_person"]}
            }
        },
        {
            "name": "Vehicle Blocking + Verbal Harassment",
            "data": {
                "analysis_metadata": {"overall_threat_level": "High"},
                "incidents": [{
                    "incident_id": 1,
                    "start_time": "00:00:10",
                    "end_time": "00:00:30",
                    "threat_level": "High",
                    "threat_type": "blocking_behavior",
                    "visual_observations": {
                        "description": "Vehicle deliberately blocking path while driver yells through window",
                        "blocking_behavior": {
                            "detected": True,
                            "type": "vehicle",
                            "duration": "20 seconds"
                        }
                    },
                    "audio_observations": {
                        "verbal_threats": {"detected": True, "tone": "Shouting"},
                        "aggressive_honking": {"detected": True, "intensity": "severe"}
                    },
                    "recommended_action": "call_911"
                }],
                "summary": {"primary_threats": ["blocking_behavior", "verbal_threat"]}
            }
        },
        {
            "name": "Tailgating + Aggressive Following",
            "data": {
                "analysis_metadata": {"overall_threat_level": "Medium"},
                "incidents": [{
                    "incident_id": 1,
                    "start_time": "00:01:00",
                    "end_time": "00:02:00",
                    "threat_level": "Medium",
                    "threat_type": "following_behavior",
                    "visual_observations": {
                        "description": "Vehicle following closely for extended period, matching all turns",
                        "following_behavior": {
                            "detected": True,
                            "duration": "60 seconds",
                            "distance": "less than 1 car length"
                        }
                    },
                    "recommended_action": "drive_to_safe_location"
                }],
                "summary": {"primary_threats": ["following_behavior"]}
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'─' * 70}")
        print(f"📋 SCENARIO: {scenario['name']}")
        print('─' * 70)
        
        guidance = agent.generate_guidance(scenario['data'])
        
        if 'text' in guidance:
            print("\n🔊 Audio Guidance:\n")
            print(guidance['text'])
        
        print()
    
    print("=" * 70)


def compare_threat_levels():
    """
    Show how guidance adapts to different threat levels
    """
    print("\n" + "=" * 70)
    print("ADAPTIVE GUIDANCE BY THREAT LEVEL")
    print("=" * 70)
    
    agent = DeescalationAgent()
    
    threat_levels = ["Low", "Medium", "High", "Critical"]
    
    for level in threat_levels:
        print(f"\n{'─' * 70}")
        print(f"🎚️  THREAT LEVEL: {level}")
        print('─' * 70)
        
        data = {
            "analysis_metadata": {"overall_threat_level": level},
            "incidents": [{
                "incident_id": 1,
                "threat_level": level,
                "threat_type": "approaching_person" if level in ["High", "Critical"] else "verbal_threat",
                "visual_observations": {
                    "description": f"Incident with {level.lower()} threat level"
                },
                "recommended_action": "lock_doors" if level in ["High", "Critical"] else "stay_alert"
            }],
            "summary": {"primary_threats": ["approaching_person"]}
        }
        
        guidance = agent.generate_guidance(data)
        
        if 'text' in guidance:
            print(f"\n🔊 Guidance:\n{guidance['text']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n" + "🚗" * 35)
    print("ROAD RAGE POC - Complete Pipeline Demonstration")
    print("🚗" * 35 + "\n")
    
    # Main simulation
    simulate_realtime_monitoring()
    
    # Additional demonstrations
    input("\nPress Enter to see scenario demonstrations...")
    demonstrate_threat_scenarios()
    
    input("\nPress Enter to see threat level adaptations...")
    compare_threat_levels()
    
    print("\n" + "=" * 70)
    print("✓ Demonstration Complete")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("1. Perception agent continuously monitors for threats")
    print("2. De-escalation agent provides immediate, calm guidance")
    print("3. Guidance adapts to threat type and severity")
    print("4. Focus is always on driver safety and de-escalation")
    print("=" * 70 + "\n")
