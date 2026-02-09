#!/usr/bin/env python3
"""
Flask Web Application for Road Rage Detection Pipeline
Provides a web interface for video upload and real-time agent output display
"""

import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, send_file
from werkzeug.utils import secure_filename
import threading
import queue

from src.pipeline import RoadRagePipeline

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = Path('uploads')
app.config['RESULTS_FOLDER'] = Path('results')

# Create necessary directories
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['RESULTS_FOLDER'].mkdir(exist_ok=True)

# Store active processing jobs
active_jobs = {}

# Allowed video extensions
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class JobProgress:
    """Track progress of a pipeline job"""
    def __init__(self, job_id):
        self.job_id = job_id
        self.status = 'pending'
        self.current_step = None
        self.perception_output = None
        self.deescalation_results = []
        self.report = None
        self.error = None
        self.progress_queue = queue.Queue()
        self.completed = False
        self.started_at = datetime.now()
        self.completed_at = None
    
    def update(self, message_type, data):
        """Add an update to the progress queue"""
        update = {
            'type': message_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        self.progress_queue.put(update)
    
    def set_status(self, status, step=None):
        """Update job status"""
        self.status = status
        if step:
            self.current_step = step
        self.update('status', {'status': status, 'step': step})
    
    def set_perception_output(self, output):
        """Store perception agent output"""
        self.perception_output = output
        self.update('perception_complete', {
            'total_incidents': output['summary']['total_incidents'],
            'threat_level': output['analysis_metadata']['overall_threat_level'],
            'incidents': output['incidents']
        })
    
    def add_deescalation_result(self, incident_id, guidance, audio_path):
        """Store de-escalation agent result"""
        result = {
            'incident_id': incident_id,
            'guidance_text': guidance.get('text', ''),
            'audio_path': str(audio_path) if audio_path else None
        }
        self.deescalation_results.append(result)
        self.update('deescalation_complete', result)
    
    def set_report(self, report, report_files):
        """Store post-incident report"""
        self.report = {
            'content': report,
            'files': report_files
        }
        self.update('report_complete', {
            'files': report_files
        })
    
    def set_error(self, error):
        """Set error status"""
        self.error = str(error)
        self.status = 'failed'
        self.completed = True
        self.completed_at = datetime.now()
        self.update('error', {'error': str(error)})
    
    def set_complete(self):
        """Mark job as complete"""
        self.status = 'completed'
        self.completed = True
        self.completed_at = datetime.now()
        elapsed = (self.completed_at - self.started_at).total_seconds()
        self.update('complete', {'elapsed_seconds': elapsed})


def run_pipeline_async(job_id, video_path, voice_name='Puck'):
    """Run the pipeline asynchronously and update job progress"""
    job = active_jobs[job_id]
    
    try:
        job.set_status('running', 'initializing')
        
        # Create job-specific output directory
        job_output_dir = app.config['RESULTS_FOLDER'] / job_id
        job_output_dir.mkdir(exist_ok=True)
        
        # Initialize pipeline
        pipeline = RoadRagePipeline(
            output_base_dir=str(job_output_dir),
            voice_name=voice_name
        )
        
        # Step 1: Perception Agent
        job.set_status('running', 'perception')
        job.update('step_start', {
            'step': 'perception',
            'message': 'Analyzing video for road rage incidents...'
        })
        
        perception_output = pipeline.run_perception_agent(video_path)
        job.set_perception_output(perception_output)
        
        # Step 2: De-escalation Agent
        job.set_status('running', 'deescalation')
        job.update('step_start', {
            'step': 'deescalation',
            'message': 'Generating real-time safety guidance...'
        })
        
        incidents = perception_output.get("incidents", [])
        for idx, incident in enumerate(incidents, 1):
            incident_id = incident["incident_id"]
            
            job.update('deescalation_progress', {
                'incident_id': incident_id,
                'current': idx,
                'total': len(incidents),
                'threat_type': incident['threat_type'],
                'threat_level': incident['threat_level']
            })
            
            try:
                guidance = pipeline.deescalation_agent.generate_guidance(
                    perception_output,
                    focus_incident=incident_id,
                    return_audio=True,
                    return_text=True
                )
                
                # Save text transcript
                text_path = pipeline.audio_dir / f"incident_{incident_id}_guidance.txt"
                if 'text' in guidance:
                    with open(text_path, 'w') as f:
                        f.write(guidance['text'])
                
                # Save audio
                audio_path = None
                if 'audio' in guidance:
                    audio_path = pipeline.audio_dir / f"incident_{incident_id}_guidance"
                    saved_path = pipeline.deescalation_agent.save_guidance_audio(
                        guidance, 
                        str(audio_path)
                    )
                    audio_path = Path(saved_path)
                
                job.add_deescalation_result(incident_id, guidance, audio_path)
                
            except Exception as e:
                job.update('warning', {
                    'message': f'Error generating guidance for incident {incident_id}: {str(e)}'
                })
        
        # Step 3: Post-Incident Report
        job.set_status('running', 'report')
        job.update('step_start', {
            'step': 'report',
            'message': 'Generating comprehensive incident report...'
        })
        
        guidance_files = sorted(pipeline.audio_dir.glob("incident_*_guidance.txt"))
        report = pipeline.post_incident_agent.generate_report(
            perception_output=perception_output,
            guidance_files=[str(f) for f in guidance_files]
        )
        
        # Save report
        report_path = pipeline.reports_dir / "incident_report"
        saved_files = pipeline.post_incident_agent.save_report(
            report, 
            str(report_path),
            save_sections_separately=True
        )
        
        job.set_report(report, saved_files)
        
        # Mark as complete
        job.set_complete()
        
    except Exception as e:
        job.set_error(e)
        import traceback
        traceback.print_exc()


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video upload and start pipeline processing"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
        }), 400
    
    # Get optional parameters
    voice_name = request.form.get('voice', 'Puck')
    
    # Create unique job ID
    job_id = str(uuid.uuid4())
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    upload_path = app.config['UPLOAD_FOLDER'] / job_id
    upload_path.mkdir(exist_ok=True)
    video_path = upload_path / filename
    file.save(str(video_path))
    
    # Create job tracker
    job = JobProgress(job_id)
    active_jobs[job_id] = job
    
    # Start pipeline processing in background thread
    thread = threading.Thread(
        target=run_pipeline_async,
        args=(job_id, str(video_path), voice_name)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'job_id': job_id,
        'message': 'Video uploaded successfully. Processing started.',
        'filename': filename
    })


@app.route('/progress/<job_id>')
def progress_stream(job_id):
    """Server-Sent Events stream for job progress"""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = active_jobs[job_id]
    
    def generate():
        """Generate SSE messages"""
        # Send initial status
        yield f"data: {json.dumps({'type': 'connected', 'job_id': job_id})}\n\n"
        
        # Stream updates from queue
        while not job.completed:
            try:
                # Wait for updates with timeout
                update = job.progress_queue.get(timeout=1)
                yield f"data: {json.dumps(update)}\n\n"
            except queue.Empty:
                # Send keepalive
                yield f": keepalive\n\n"
        
        # Send final updates if any remain in queue
        while not job.progress_queue.empty():
            update = job.progress_queue.get_nowait()
            yield f"data: {json.dumps(update)}\n\n"
        
        # Send completion message
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/status/<job_id>')
def get_status(job_id):
    """Get current job status"""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = active_jobs[job_id]
    
    return jsonify({
        'job_id': job_id,
        'status': job.status,
        'current_step': job.current_step,
        'completed': job.completed,
        'error': job.error,
        'started_at': job.started_at.isoformat(),
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'has_perception': job.perception_output is not None,
        'deescalation_count': len(job.deescalation_results),
        'has_report': job.report is not None
    })


@app.route('/results/<job_id>')
def get_results(job_id):
    """Get complete results for a job"""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = active_jobs[job_id]
    
    if not job.completed:
        return jsonify({'error': 'Job not yet completed'}), 400
    
    return jsonify({
        'job_id': job_id,
        'status': job.status,
        'perception': job.perception_output,
        'deescalation': job.deescalation_results,
        'report': job.report,
        'error': job.error
    })


@app.route('/report/<job_id>')
def get_report_content(job_id):
    """Get the formatted report content"""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = active_jobs[job_id]
    
    if not job.report:
        return jsonify({'error': 'Report not yet generated'}), 400
    
    # Read individual section files
    reports_dir = app.config['RESULTS_FOLDER'] / job_id / 'reports'
    
    # Read summary
    summary = ''
    summary_file = reports_dir / 'incident_report_summary.txt'
    if summary_file.exists():
        with open(summary_file, 'r') as f:
            summary = f.read()
    
    # Read timeline
    timeline = ''
    timeline_file = reports_dir / 'incident_report_timeline.txt'
    if timeline_file.exists():
        with open(timeline_file, 'r') as f:
            timeline = f.read()
    
    # Read police report
    police_report = ''
    police_file = reports_dir / 'incident_report_police_report.txt'
    if police_file.exists():
        with open(police_file, 'r') as f:
            police_report = f.read()
    
    # Read full report as fallback
    full_report = ''
    report_file = reports_dir / 'incident_report.txt'
    if report_file.exists():
        with open(report_file, 'r') as f:
            full_report = f.read()
    
    return jsonify({
        'full_content': full_report,
        'generated_at': job.report['content'].get('generated_at', '') if 'content' in job.report else '',
        'summary': summary,
        'timeline': timeline,
        'police_report': police_report
    })


@app.route('/download/<job_id>/<path:filename>')
def download_file(job_id, filename):
    """Download a result file"""
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    file_path = app.config['RESULTS_FOLDER'] / job_id / filename
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(str(file_path), as_attachment=True)


@app.route('/jobs')
def list_jobs():
    """List all jobs"""
    jobs_list = []
    for job_id, job in active_jobs.items():
        jobs_list.append({
            'job_id': job_id,
            'status': job.status,
            'current_step': job.current_step,
            'started_at': job.started_at.isoformat(),
            'completed': job.completed
        })
    
    return jsonify({'jobs': jobs_list})


if __name__ == '__main__':
    print("=" * 80)
    print("Road Rage Detection Pipeline - Web Interface")
    print("=" * 80)
    # Get port from environment variable (for deployment platforms)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    print(f"Starting server on http://0.0.0.0:{port}")
    print("=" * 80)
    app.run(debug=debug, threaded=True, host='0.0.0.0', port=port)
