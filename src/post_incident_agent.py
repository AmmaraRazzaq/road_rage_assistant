"""
Post-Incident Report Generator Implementation
Processes perception agent output and de-escalation guidance to create comprehensive incident reports
"""

import os
import json
from datetime import datetime
from google import genai
from google.genai import types
from pathlib import Path
from post_incident_prompt import POST_INCIDENT_SYSTEM_PROMPT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PostIncidentAgent:
    """
    Generates comprehensive incident reports from perception data and de-escalation guidance.
    Produces: incident summary, detailed timeline, and police-ready neutral reports.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the post-incident report generator with Gemini model.
        
        Args:
            api_key: Google API key. If None, will use GEMINI_API_KEY from environment.
        """
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Google API key is required. Set GEMINI_API_KEY environment variable.")
        
        # Initialize client
        self.client = genai.Client(api_key=api_key)
        
        # Model configuration
        self.model = "gemini-2.5-flash"  # Using flash for fast, accurate report generation
        
        # System prompt for report generation
        self.system_prompt = POST_INCIDENT_SYSTEM_PROMPT
        
        # Generation configuration optimized for detailed, accurate reports
        self.temperature = 0.2      # Low temperature for consistent, factual reporting
        self.top_p = 0.9
        self.top_k = 40
        self.max_output_tokens = 8000  # Allow for comprehensive reports
    
    def generate_report(
        self, 
        perception_output: dict,
        guidance_texts: list[str] = None,
        guidance_files: list[str] = None
    ) -> dict:
        """
        Generate a comprehensive post-incident report.
        
        Args:
            perception_output: JSON output from perception agent (dict or path to JSON file)
            guidance_texts: List of guidance text strings from de-escalation agent
            guidance_files: List of paths to guidance text files
        
        Returns:
            Dictionary with 'report' (full text), 'summary', 'timeline', and 'police_report' keys
        """
        # Load perception data if path provided
        if isinstance(perception_output, str):
            with open(perception_output, 'r') as f:
                perception_data = json.load(f)
        else:
            perception_data = perception_output
        
        # Collect all guidance texts
        all_guidance = []
        
        if guidance_texts:
            all_guidance.extend(guidance_texts)
        
        if guidance_files:
            for file_path in guidance_files:
                with open(file_path, 'r') as f:
                    all_guidance.append(f.read())
        
        # Construct the user prompt
        user_prompt = self._build_user_prompt(perception_data, all_guidance)
        
        # Generate report using Gemini
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{self.system_prompt}\n\n{user_prompt}",
            config=types.GenerateContentConfig(
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                max_output_tokens=self.max_output_tokens
            )
        )
        
        report_text = response.text
        
        # Parse the report into sections (basic parsing - could be enhanced)
        result = {
            'report': report_text,
            'generated_at': datetime.now().isoformat(),
            'perception_metadata': perception_data.get('analysis_metadata', {}),
        }
        
        # Try to extract sections
        try:
            result['summary'] = self._extract_section(report_text, "SECTION 1: INCIDENT SUMMARY")
            result['timeline'] = self._extract_section(report_text, "SECTION 2: DETAILED TIMELINE")
            result['police_report'] = self._extract_section(report_text, "SECTION 3: POLICE-READY REPORT")
        except Exception as e:
            print(f"Warning: Could not parse report sections: {e}")
            # If parsing fails, at least we have the full report
        
        return result
    
    def _build_user_prompt(self, perception_data: dict, guidance_texts: list[str]) -> str:
        """
        Build the user prompt combining perception and guidance data.
        """
        prompt = "Generate a comprehensive post-incident report based on the following data:\n\n"
        
        # Add perception agent output
        prompt += "=" * 60 + "\n"
        prompt += "PERCEPTION AGENT OUTPUT (JSON)\n"
        prompt += "=" * 60 + "\n"
        prompt += json.dumps(perception_data, indent=2)
        prompt += "\n\n"
        
        # Add de-escalation guidance if available
        if guidance_texts:
            prompt += "=" * 60 + "\n"
            prompt += "DE-ESCALATION GUIDANCE TRANSCRIPTS\n"
            prompt += "=" * 60 + "\n"
            for idx, guidance in enumerate(guidance_texts, 1):
                prompt += f"\n--- Guidance #{idx} ---\n"
                prompt += guidance
                prompt += "\n"
        
        prompt += "\n" + "=" * 60 + "\n"
        prompt += "Please generate the complete post-incident report with all three sections.\n"
        
        return prompt
    
    def _extract_section(self, report_text: str, section_header: str) -> str:
        """
        Extract a specific section from the report.
        """
        start_idx = report_text.find(section_header)
        if start_idx == -1:
            return ""
        
        # Find the start of the actual content (skip the header and separator)
        content_start = report_text.find('\n', start_idx) + 1
        while content_start < len(report_text) and report_text[content_start] in ['-', '─', '\n', ' ']:
            content_start = report_text.find('\n', content_start) + 1
        
        # Find the next section or end
        next_section = report_text.find("SECTION ", content_start)
        end_marker = report_text.find("═══════════════════════════════════════════════════════\nEND OF REPORT", content_start)
        
        if next_section != -1 and (end_marker == -1 or next_section < end_marker):
            end_idx = next_section
        elif end_marker != -1:
            end_idx = end_marker
        else:
            end_idx = len(report_text)
        
        return report_text[content_start:end_idx].strip()
    
    def save_report(
        self, 
        report: dict, 
        output_path: str,
        save_sections_separately: bool = True
    ) -> dict:
        """
        Save generated report to file(s).
        
        Args:
            report: Output from generate_report()
            output_path: Base path for saving report (without extension)
            save_sections_separately: If True, saves each section as separate file
        
        Returns:
            Dictionary with paths to saved files
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        # Save full report
        full_report_path = output_file.with_suffix('.txt')
        with open(full_report_path, 'w') as f:
            f.write(report['report'])
        saved_files['full_report'] = str(full_report_path)
        print(f"Full report saved to: {full_report_path}")
        
        # Save as JSON for programmatic access
        json_path = output_file.with_suffix('.json')
        with open(json_path, 'w') as f:
            json.dump({
                'generated_at': report['generated_at'],
                'perception_metadata': report['perception_metadata'],
                'summary': report.get('summary', ''),
                'timeline': report.get('timeline', ''),
                'police_report': report.get('police_report', '')
            }, f, indent=2)
        saved_files['json'] = str(json_path)
        print(f"JSON report saved to: {json_path}")
        
        # Save individual sections if requested
        if save_sections_separately:
            if 'summary' in report:
                summary_path = output_file.parent / f"{output_file.stem}_summary.txt"
                with open(summary_path, 'w') as f:
                    f.write(report['summary'])
                saved_files['summary'] = str(summary_path)
                print(f"Summary saved to: {summary_path}")
            
            if 'timeline' in report:
                timeline_path = output_file.parent / f"{output_file.stem}_timeline.txt"
                with open(timeline_path, 'w') as f:
                    f.write(report['timeline'])
                saved_files['timeline'] = str(timeline_path)
                print(f"Timeline saved to: {timeline_path}")
            
            if 'police_report' in report:
                police_path = output_file.parent / f"{output_file.stem}_police_report.txt"
                with open(police_path, 'w') as f:
                    f.write(report['police_report'])
                saved_files['police_report'] = str(police_path)
                print(f"Police report saved to: {police_path}")
        
        return saved_files


def main():
    """
    Example usage: Generate post-incident report from perception and guidance data
    """
    print("=" * 60)
    print("POST-INCIDENT REPORT GENERATOR")
    print("=" * 60)
    
    # Initialize agent
    print("\nInitializing Post-Incident Agent...")
    agent = PostIncidentAgent()
    
    # Define paths to input data
    base_path = Path(__file__).parent.parent
    perception_file = base_path / "results" / "gemini-2.5-flash_road_rage_analysis_fps1.json"
    guidance_dir = base_path / "results" / "audio"
    
    # Check if files exist
    if not perception_file.exists():
        print(f"Error: Perception file not found at {perception_file}")
        print("Please run the perception agent first to generate analysis data.")
        return
    
    print(f"\nLoading perception data from: {perception_file.name}")
    
    # Collect all guidance text files
    guidance_files = []
    if guidance_dir.exists():
        guidance_files = sorted(guidance_dir.glob("incident_*_guidance.txt"))
        print(f"Found {len(guidance_files)} guidance files")
    else:
        print("No guidance files found. Report will be generated from perception data only.")
    
    # Generate report
    print("\n" + "=" * 60)
    print("GENERATING COMPREHENSIVE INCIDENT REPORT...")
    print("=" * 60)
    
    try:
        report = agent.generate_report(
            perception_output=str(perception_file),
            guidance_files=[str(f) for f in guidance_files]
        )
        
        # Display report sections
        print("\n" + "=" * 60)
        print("REPORT GENERATED SUCCESSFULLY")
        print("=" * 60)
        
        if 'summary' in report:
            print("\n--- INCIDENT SUMMARY (Preview) ---")
            summary_preview = report['summary'][:500] + "..." if len(report['summary']) > 500 else report['summary']
            print(summary_preview)
        
        # Save report
        output_path = base_path / "results" / "reports" / "incident_report"
        print(f"\n\nSaving report to: {output_path}")
        saved_files = agent.save_report(report, str(output_path))
        
        print("\n" + "=" * 60)
        print("REPORT GENERATION COMPLETE")
        print("=" * 60)
        print("\nGenerated files:")
        for file_type, path in saved_files.items():
            print(f"  - {file_type}: {path}")
        
    except Exception as e:
        print(f"\nError generating report: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
