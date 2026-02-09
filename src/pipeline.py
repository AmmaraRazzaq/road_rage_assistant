"""
Road Rage Detection Pipeline
Orchestrates the complete workflow: Perception → De-escalation → Post-Incident Report
"""

import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import all agents
from deescalation_agent import DeescalationAgent
from post_incident_agent import PostIncidentAgent

# Load environment variables
load_dotenv()


class RoadRagePipeline:
    """
    Complete pipeline for road rage detection and response system.
    Coordinates: Perception Agent → De-escalation Agent → Post-Incident Agent
    """
    
    def __init__(
        self, 
        api_key: str = None,
        output_base_dir: str = None,
        voice_name: str = "Puck"
    ):
        """
        Initialize the complete pipeline.
        
        Args:
            api_key: Google API key. If None, uses GEMINI_API_KEY from environment
            output_base_dir: Base directory for all outputs. Defaults to 'results/'
            voice_name: Voice for de-escalation audio guidance
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key required. Set GEMINI_API_KEY environment variable.")
        
        # Setup output directories
        self.base_path = Path(__file__).parent.parent
        self.output_base = Path(output_base_dir) if output_base_dir else self.base_path / "results"
        self.audio_dir = self.output_base / "audio"
        self.reports_dir = self.output_base / "reports"
        
        # Create directories
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize agents
        print("Initializing pipeline agents...")
        self.deescalation_agent = DeescalationAgent(
            api_key=self.api_key,
            voice_name=voice_name
        )
        self.post_incident_agent = PostIncidentAgent(api_key=self.api_key)
        
        print(f"✓ De-escalation Agent initialized (voice: {voice_name})")
        print(f"✓ Post-Incident Agent initialized")
        print(f"✓ Output directory: {self.output_base}")
    
    def run_perception_agent(self, video_file: str = None) -> dict:
        """
        Step 1: Run perception agent to analyze video and detect threats.
        
        Args:
            video_file: Path to video file. If None, runs gemini_fact_extraction.py
        
        Returns:
            Dictionary containing perception analysis results
        """
        print("\n" + "=" * 80)
        print("STEP 1: PERCEPTION AGENT - Analyzing Video for Road Rage Incidents")
        print("=" * 80)
        
        # Import and run perception agent
        import subprocess
        
        perception_script = self.base_path / "src" / "gemini_fact_extraction.py"
        
        print(f"Running perception agent: {perception_script}")
        print("This may take several minutes depending on video length...")
        
        try:
            result = subprocess.run(
                ["python", str(perception_script)],
                capture_output=True,
                text=True,
                cwd=str(self.base_path)
            )
            
            if result.returncode != 0:
                print(f"Error running perception agent:")
                print(result.stderr)
                raise RuntimeError("Perception agent failed")
            
            print(result.stdout)
            
            # Load the generated perception output
            # The perception agent saves to results/gemini-2.5-flash_road_rage_analysis_fps1.json
            perception_file = self.output_base / "gemini-2.5-flash_road_rage_analysis_fps1.json"
            
            if not perception_file.exists():
                raise FileNotFoundError(f"Perception output not found at {perception_file}")
            
            with open(perception_file, 'r') as f:
                perception_data = json.load(f)
            
            print(f"\n✓ Perception analysis complete!")
            print(f"  - Total incidents detected: {perception_data['summary']['total_incidents']}")
            print(f"  - Overall threat level: {perception_data['analysis_metadata']['overall_threat_level']}")
            print(f"  - Output saved to: {perception_file}")
            
            return perception_data
            
        except Exception as e:
            print(f"Error in perception agent: {e}")
            raise
    
    def run_deescalation_agent(self, perception_output: dict) -> list:
        """
        Step 2: Generate de-escalation audio guidance for each incident.
        
        Args:
            perception_output: Output from perception agent
        
        Returns:
            List of tuples: (incident_id, guidance_dict, audio_path)
        """
        print("\n" + "=" * 80)
        print("STEP 2: DE-ESCALATION AGENT - Generating Real-Time Safety Guidance")
        print("=" * 80)
        
        guidance_results = []
        
        # Generate guidance for each incident
        incidents = perception_output.get("incidents", [])
        
        if not incidents:
            print("No incidents detected. Skipping de-escalation guidance.")
            return guidance_results
        
        print(f"Generating guidance for {len(incidents)} incidents...\n")
        
        for idx, incident in enumerate(incidents, 1):
            incident_id = incident["incident_id"]
            
            print(f"[{idx}/{len(incidents)}] Processing Incident {incident_id}")
            print(f"  - Threat: {incident['threat_type']} ({incident['threat_level']})")
            print(f"  - Time: {incident['start_time']} - {incident['end_time']}")
            
            try:
                # Generate guidance with both text and audio
                guidance = self.deescalation_agent.generate_guidance(
                    perception_output,
                    focus_incident=incident_id,
                    return_audio=True,
                    return_text=True
                )
                
                # Save text transcript
                text_path = self.audio_dir / f"incident_{incident_id}_guidance.txt"
                if 'text' in guidance:
                    with open(text_path, 'w') as f:
                        f.write(guidance['text'])
                    print(f"  ✓ Text guidance saved: {text_path.name}")
                
                # Save audio
                audio_path = None
                if 'audio' in guidance:
                    audio_path = self.audio_dir / f"incident_{incident_id}_guidance"
                    saved_path = self.deescalation_agent.save_guidance_audio(
                        guidance, 
                        str(audio_path)
                    )
                    audio_path = Path(saved_path)
                    print(f"  ✓ Audio guidance saved: {audio_path.name}")
                
                guidance_results.append((incident_id, guidance, audio_path))
                
            except Exception as e:
                print(f"  ✗ Error generating guidance for incident {incident_id}: {e}")
                continue
        
        print(f"\n✓ De-escalation guidance generation complete!")
        print(f"  - Generated guidance for {len(guidance_results)} incidents")
        print(f"  - Audio files saved to: {self.audio_dir}")
        
        return guidance_results
    
    def run_post_incident_agent(
        self, 
        perception_output: dict, 
        guidance_results: list
    ) -> dict:
        """
        Step 3: Generate comprehensive post-incident report.
        
        Args:
            perception_output: Output from perception agent
            guidance_results: List of guidance results from de-escalation agent
        
        Returns:
            Dictionary containing generated reports
        """
        print("\n" + "=" * 80)
        print("STEP 3: POST-INCIDENT AGENT - Generating Comprehensive Report")
        print("=" * 80)
        
        # Collect all guidance text files
        guidance_files = sorted(self.audio_dir.glob("incident_*_guidance.txt"))
        
        print(f"Generating report from:")
        print(f"  - Perception data: {perception_output['summary']['total_incidents']} incidents")
        print(f"  - Guidance files: {len(guidance_files)} transcripts")
        print("\nGenerating comprehensive incident report...\n")
        
        try:
            # Generate report
            report = self.post_incident_agent.generate_report(
                perception_output=perception_output,
                guidance_files=[str(f) for f in guidance_files]
            )
            
            # Save report
            report_path = self.reports_dir / "incident_report"
            saved_files = self.post_incident_agent.save_report(
                report, 
                str(report_path),
                save_sections_separately=True
            )
            
            print(f"\n✓ Post-incident report generation complete!")
            print(f"  - Reports saved to: {self.reports_dir}")
            print(f"\nGenerated files:")
            for file_type, path in saved_files.items():
                print(f"  - {file_type}: {Path(path).name}")
            
            return report
            
        except Exception as e:
            print(f"Error generating post-incident report: {e}")
            raise
    
    def run_full_pipeline(self, video_file: str = None) -> dict:
        """
        Run the complete pipeline: Perception → De-escalation → Post-Incident.
        
        Args:
            video_file: Path to dashcam video. If None, uses default from perception agent.
        
        Returns:
            Dictionary with results from all three agents
        """
        start_time = time.time()
        
        print("\n" + "=" * 80)
        print("ROAD RAGE DETECTION PIPELINE - Starting Complete Workflow")
        print("=" * 80)
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Output directory: {self.output_base}")
        print("=" * 80)
        
        results = {}
        
        try:
            # Step 1: Perception
            perception_output = self.run_perception_agent(video_file)
            results['perception'] = perception_output
            
            # Step 2: De-escalation
            guidance_results = self.run_deescalation_agent(perception_output)
            results['deescalation'] = guidance_results
            
            # Step 3: Post-Incident Report
            report = self.run_post_incident_agent(perception_output, guidance_results)
            results['report'] = report
            
            # Pipeline complete
            elapsed = time.time() - start_time
            
            print("\n" + "=" * 80)
            print("PIPELINE COMPLETE - All Agents Executed Successfully")
            print("=" * 80)
            print(f"Total execution time: {elapsed/60:.2f} minutes")
            print(f"\nSummary:")
            print(f"  - Incidents detected: {perception_output['summary']['total_incidents']}")
            print(f"  - Guidance generated: {len(guidance_results)} audio files")
            print(f"  - Reports created: {len(results.get('report', {}))} sections")
            print(f"\nAll outputs saved to: {self.output_base}")
            print("=" * 80)
            
            return results
            
        except Exception as e:
            print(f"\n{'=' * 80}")
            print(f"PIPELINE FAILED")
            print(f"{'=' * 80}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def run_from_existing_perception(self, perception_file: str) -> dict:
        """
        Run only de-escalation and post-incident agents using existing perception output.
        Useful for re-running later stages without re-analyzing video.
        
        Args:
            perception_file: Path to existing perception JSON output
        
        Returns:
            Dictionary with results from de-escalation and post-incident agents
        """
        print("\n" + "=" * 80)
        print("ROAD RAGE PIPELINE - Running from Existing Perception Output")
        print("=" * 80)
        
        # Load perception data
        with open(perception_file, 'r') as f:
            perception_output = json.load(f)
        
        print(f"Loaded perception data from: {perception_file}")
        print(f"  - Incidents: {perception_output['summary']['total_incidents']}")
        print(f"  - Threat level: {perception_output['analysis_metadata']['overall_threat_level']}")
        
        results = {'perception': perception_output}
        
        # Run de-escalation
        guidance_results = self.run_deescalation_agent(perception_output)
        results['deescalation'] = guidance_results
        
        # Run post-incident
        report = self.run_post_incident_agent(perception_output, guidance_results)
        results['report'] = report
        
        print("\n" + "=" * 80)
        print("PIPELINE COMPLETE")
        print("=" * 80)
        
        return results


def main():
    """
    Main entry point for the pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Road Rage Detection Pipeline")
    parser.add_argument(
        '--mode',
        choices=['full', 'from-perception'],
        default='full',
        help='Pipeline mode: full (run all agents) or from-perception (skip perception)'
    )
    parser.add_argument(
        '--perception-file',
        type=str,
        help='Path to existing perception JSON (for from-perception mode)'
    )
    parser.add_argument(
        '--video',
        type=str,
        help='Path to video file (for full mode)'
    )
    parser.add_argument(
        '--voice',
        type=str,
        default='Puck',
        help='Voice for audio guidance (default: Puck)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory for results (default: results/)'
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = RoadRagePipeline(
        output_base_dir=args.output_dir,
        voice_name=args.voice
    )
    
    # Run pipeline based on mode
    if args.mode == 'full':
        results = pipeline.run_full_pipeline(video_file=args.video)
    else:
        if not args.perception_file:
            print("Error: --perception-file required for from-perception mode")
            sys.exit(1)
        results = pipeline.run_from_existing_perception(args.perception_file)
    
    return results


if __name__ == "__main__":
    main()
