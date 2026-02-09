# Road Rage Assitance

A modern web interface for the AI-powered Road Rage Assitance. The goal of this application is to provide real time assistance to drivers in case of emergency situations. For real-world use case, the app needs to be extended to a deployment ready version for dashcams where it can provide real time assistance. The purpose of the webapp is to demonstrate the capabilities of the application. 

## Features

- **Video Upload**: Easy drag-and-drop interface for dashcam videos
- **Real-time Processing**: Live updates as each agent completes its analysis
- **Three-Stage Pipeline**:
  1. **Perception Agent**: Analyzes video for road rage incidents
  2. **De-escalation Agent**: Generates audio safety guidance
  3. **Post-Incident Report**: Creates comprehensive documentation
- **Interactive Results**: View incidents, listen to audio guidance, and download reports
- **Beautiful UI**: Modern, responsive design with progress tracking

## Prerequisites

- Python 3.8+
- `ffmpeg` and `ffprobe` (for video processing)
- Google Gemini API key

## Installation

1. **Install Python dependencies**:
   ```bash
   conda activate zutec
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

3. **Install ffmpeg** (if not already installed):
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```

## Running the Web Application

1. **Activate your conda environment**:
   ```bash
   conda activate zutec
   ```

2. **Start the Flask server**:
   ```bash
   python app.py
   ```

3. **Open your browser**:
   Navigate to `http://localhost:5000`

## Usage

1. **Upload a Video**:
   - Click "Choose video file" or drag and drop a dashcam video
   - Supported formats: MP4, AVI, MOV, MKV, WEBM
   - Select your preferred audio voice for guidance
   - Click "Start Analysis"

2. **Monitor Progress**:
   - Watch real-time updates as each agent processes the video
   - View activity log for detailed progress
   - See incidents as they're detected

3. **Review Results**:
   - **Threat Assessment**: View all detected incidents with threat levels
   - **Safety Guidance**: Read transcripts and listen to audio guidance
   - **Post-Incident Report**: Download comprehensive reports

## API Endpoints

### Upload Video
```
POST /upload
Form Data:
  - video: Video file
  - voice: Voice name (Puck, Aoede, Kore, Charon)
Returns:
  - job_id: Unique identifier for the processing job
```

### Progress Stream
```
GET /progress/<job_id>
Returns: Server-Sent Events stream with real-time updates
```

### Get Job Status
```
GET /status/<job_id>
Returns: Current status and progress of the job
```

### Get Results
```
GET /results/<job_id>
Returns: Complete analysis results (when job is finished)
```

### Download File
```
GET /download/<job_id>/<path>
Returns: Audio file or report document
```

### List Jobs
```
GET /jobs
Returns: List of all processing jobs
```

## Architecture

### Backend (Flask)
- **app.py**: Main web server and API endpoints
- **JobProgress**: Tracks processing state and streams updates
- **Background Processing**: Asynchronous video analysis

### Frontend
- **HTML/CSS/JS**: Modern, responsive single-page application
- **Server-Sent Events**: Real-time progress updates
- **Dynamic Results**: Updates UI as agents complete

### Pipeline
- **Perception Agent**: Gemini-powered video analysis
- **De-escalation Agent**: TTS audio guidance generation
- **Post-Incident Agent**: Comprehensive report creation

## File Structure

```
road_rage_poc/
├── app.py                      # Flask web application
├── templates/
│   └── index.html             # Main web interface
├── static/
│   ├── css/
│   │   └── style.css          # UI styles
│   └── js/
│       └── app.js             # Frontend logic
├── src/
│   ├── pipeline.py            # Pipeline orchestration
│   ├── gemini_fact_extraction.py  # Perception agent
│   ├── deescalation_agent.py # De-escalation agent
│   └── post_incident_agent.py # Report generation
├── uploads/                    # Uploaded videos (by job ID)
└── results/                    # Analysis outputs (by job ID)
    ├── audio/                 # Generated audio guidance
    └── reports/               # Post-incident reports
```

## Configuration

### Voice Options
- **Puck**: Clear male voice (recommended)
- **Aoede**: Clear female voice
- **Kore**: Professional female voice (default)
- **Charon**: Deep male voice

### Video Processing
- Maximum file size: 500MB
- Supported formats: MP4, AVI, MOV, MKV, WEBM
- Processing time: ~2-5 minutes for typical dashcam footage

## Troubleshooting

### Video Upload Fails
- Check file size (max 500MB)
- Verify video format is supported
- Ensure enough disk space

### Processing Hangs
- Check API key is valid
- Verify ffmpeg is installed
- Check activity log for errors

### Audio Not Playing
- Ensure browser supports WAV audio
- Check audio file was generated (look in activity log)
- Try downloading the audio file directly

### No Results Displayed
- Wait for all agents to complete
- Check browser console for JavaScript errors
- Refresh the page and check job status

## Development

### Running in Debug Mode
```bash
# The app.py already runs in debug mode by default
python app.py
```

### Adding Custom Voices
Edit the voice selector in `templates/index.html` and update the `DeescalationAgent` in `src/deescalation_agent.py`.

### Modifying UI
- Styles: `static/css/style.css`
- JavaScript: `static/js/app.js`
- HTML: `templates/index.html`

## Security Considerations

- Files are stored with unique job IDs to prevent conflicts
- File extensions are validated before upload
- No authentication is implemented (add for production use)
- Consider adding rate limiting for production deployment

## Performance Tips

1. **Shorter videos process faster**: Consider splitting long videos
2. **Lower quality videos**: Reduce file size without losing detection accuracy
3. **Batch processing**: Process multiple videos by opening multiple tabs
4. **Clean up old jobs**: Periodically delete old upload and result folders

## Future Enhancements

- User authentication
- Job history and search
- Video preview before upload
- Real-time video progress indicator
- Export results as PDF
- Email notifications when processing completes
- WebSocket support for lower latency updates

## Deployment

For deployment to production servers, see the comprehensive [DEPLOYMENT.md](DEPLOYMENT.md) guide which covers:
- Docker deployment (easiest)
- Render.com (recommended for cloud)
- VPS setup with Nginx (best for production)
- Railway deployment
- Production configuration and security

## Support

For issues or questions:
1. Check the activity log for detailed error messages
2. Verify all dependencies are installed
3. Ensure your Gemini API key has sufficient quota
4. Check the terminal output for backend errors


