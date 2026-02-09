#!/usr/bin/env python3
"""
Simple script to run the complete Road Rage Detection Pipeline
"""

from src.pipeline import RoadRagePipeline

def main():
    """
    Run the complete pipeline with default settings.
    """
    # Initialize pipeline
    pipeline = RoadRagePipeline(
        voice_name="Puck"  # You can change to "Aoede", "Kore", or "Charon"
    )
    
    # Option 1: Run full pipeline (perception → de-escalation → post-incident)
    print("Running full pipeline...")
    results = pipeline.run_full_pipeline()
    
    # Option 2: Run from existing perception data (uncomment to use)
    # perception_file = "results/gemini-2.5-flash_road_rage_analysis_fps1.json"
    # results = pipeline.run_from_existing_perception(perception_file)
    
    return results

if __name__ == "__main__":
    main()
