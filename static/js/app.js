// Road Rage Detection Pipeline - Frontend JavaScript

let currentJobId = null;
let eventSource = null;

// DOM Elements
const uploadSection = document.getElementById('uploadSection');
const processingSection = document.getElementById('processingSection');
const resultsSection = document.getElementById('resultsSection');
const uploadForm = document.getElementById('uploadForm');
const videoInput = document.getElementById('videoInput');
const fileName = document.getElementById('fileName');
const uploadBtn = document.getElementById('uploadBtn');
const activityFeed = document.getElementById('activityFeed');
const statusBadge = document.getElementById('statusBadge');

// File input change handler
videoInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        fileName.textContent = file.name;
        fileName.parentElement.classList.add('has-file');
    } else {
        fileName.textContent = 'Choose video file';
        fileName.parentElement.classList.remove('has-file');
    }
});

// Form submission
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const file = videoInput.files[0];
    if (!file) {
        alert('Please select a video file');
        return;
    }
    
    const formData = new FormData();
    formData.append('video', file);
    formData.append('voice', document.getElementById('voiceSelect').value);
    
    // Disable upload button
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Uploading...';
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentJobId = data.job_id;
            
            // Switch to processing view
            uploadSection.classList.add('hidden');
            processingSection.classList.remove('hidden');
            
            // Start listening to progress
            startProgressStream(currentJobId);
        } else {
            alert('Error: ' + data.error);
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Start Analysis';
        }
    } catch (error) {
        alert('Upload failed: ' + error.message);
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Start Analysis';
    }
});

// Start Server-Sent Events stream for progress
function startProgressStream(jobId) {
    eventSource = new EventSource(`/progress/${jobId}`);
    
    eventSource.onmessage = (event) => {
        const update = JSON.parse(event.data);
        handleProgressUpdate(update);
    };
    
    eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
        eventSource.close();
    };
}

// Handle progress updates
function handleProgressUpdate(update) {
    console.log('Progress update:', update);
    
    const timestamp = new Date(update.timestamp).toLocaleTimeString();
    
    switch (update.type) {
        case 'connected':
            addActivity('Connected to processing stream', 'info', timestamp);
            break;
            
        case 'status':
            updateStatus(update.data.status, update.data.step);
            addActivity(`Status: ${update.data.status} - ${update.data.step || ''}`, 'info', timestamp);
            break;
            
        case 'step_start':
            updateStepStatus(update.data.step, 'active');
            addActivity(update.data.message, 'info', timestamp);
            break;
            
        case 'perception_complete':
            updateStepStatus('perception', 'complete');
            displayPerceptionResults(update.data);
            addActivity(`Perception complete: ${update.data.total_incidents} incidents detected`, 'success', timestamp);
            showResultsSection();
            break;
            
        case 'deescalation_progress':
            const progress = update.data;
            addActivity(
                `Processing incident ${progress.current}/${progress.total}: ${progress.threat_type} (${progress.threat_level})`,
                'info',
                timestamp
            );
            break;
            
        case 'deescalation_complete':
            addGuidanceResult(update.data);
            addActivity(`Guidance generated for incident ${update.data.incident_id}`, 'success', timestamp);
            break;
            
        case 'report_complete':
            updateStepStatus('deescalation', 'complete');
            updateStepStatus('report', 'complete');
            displayReportResults(update.data);
            addActivity('Post-incident report generated', 'success', timestamp);
            break;
            
        case 'warning':
            addActivity(update.data.message, 'warning', timestamp);
            break;
            
        case 'error':
            updateStepStatus('all', 'error');
            addActivity(`Error: ${update.data.error}`, 'error', timestamp);
            statusBadge.textContent = 'Failed';
            statusBadge.style.background = 'var(--danger-color)';
            break;
            
        case 'complete':
            statusBadge.textContent = 'Complete';
            statusBadge.style.background = 'var(--success-color)';
            statusBadge.style.animation = 'none';
            addActivity(`Analysis complete (${Math.round(update.data.elapsed_seconds)}s)`, 'success', timestamp);
            if (eventSource) {
                eventSource.close();
            }
            break;
            
        case 'done':
            if (eventSource) {
                eventSource.close();
            }
            break;
    }
}

// Update status badge and step
function updateStatus(status, step) {
    statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    
    if (step) {
        statusBadge.textContent += `: ${step}`;
    }
}

// Update step status
function updateStepStatus(step, status) {
    const stepElement = document.querySelector(`.step[data-step="${step}"]`);
    if (stepElement) {
        stepElement.classList.remove('active', 'complete');
        if (status === 'active') {
            stepElement.classList.add('active');
            stepElement.querySelector('.step-status').textContent = 'In Progress...';
        } else if (status === 'complete') {
            stepElement.classList.add('complete');
            stepElement.querySelector('.step-status').textContent = 'Complete';
        }
    }
}

// Add activity log entry
function addActivity(message, type = 'info', timestamp = null) {
    const activity = document.createElement('div');
    activity.className = `activity-item ${type}`;
    
    const time = timestamp || new Date().toLocaleTimeString();
    activity.innerHTML = `
        <span class="activity-time">${time}</span>
        ${message}
    `;
    
    activityFeed.insertBefore(activity, activityFeed.firstChild);
}

// Show results section
function showResultsSection() {
    if (resultsSection.classList.contains('hidden')) {
        resultsSection.classList.remove('hidden');
    }
}

// Display perception results
function displayPerceptionResults(data) {
    document.getElementById('totalIncidents').textContent = data.total_incidents;
    
    const threatBadge = document.getElementById('overallThreat');
    threatBadge.textContent = data.threat_level;
    threatBadge.className = `metric-value threat-badge ${data.threat_level}`;
    
    const incidentsList = document.getElementById('incidentsList');
    incidentsList.innerHTML = '';
    
    data.incidents.forEach(incident => {
        const incidentDiv = document.createElement('div');
        incidentDiv.className = 'incident';
        incidentDiv.innerHTML = `
            <div class="incident-header">
                <span class="incident-id">Incident ${incident.incident_id}</span>
                <span class="incident-time">${incident.start_time} - ${incident.end_time}</span>
            </div>
            <div class="incident-details">
                <strong>Threat:</strong> ${incident.threat_type} (${incident.threat_level})<br>
                <strong>Description:</strong> ${incident.visual_observations.description}<br>
                <strong>Action:</strong> ${incident.recommended_action}
            </div>
        `;
        incidentsList.appendChild(incidentDiv);
    });
}

// Add guidance result
function addGuidanceResult(data) {
    const guidanceList = document.getElementById('guidanceList');
    
    const guidanceDiv = document.createElement('div');
    guidanceDiv.className = 'guidance-item';
    guidanceDiv.innerHTML = `
        <div class="guidance-header">
            <h4>Incident ${data.incident_id}</h4>
        </div>
        <div class="guidance-text">${data.guidance_text}</div>
        ${data.audio_path ? `
            <audio controls class="audio-player">
                <source src="/download/${currentJobId}/${data.audio_path.split('/').slice(-2).join('/')}" type="audio/wav">
                Your browser does not support the audio element.
            </audio>
        ` : ''}
    `;
    
    guidanceList.appendChild(guidanceDiv);
}

// Display report results
function displayReportResults(data) {
    const reportFiles = document.getElementById('reportFiles');
    reportFiles.innerHTML = '';
    
    Object.entries(data.files).forEach(([type, path]) => {
        const fileDiv = document.createElement('div');
        fileDiv.className = 'report-file';
        
        const filename = path.split('/').pop();
        const relativePath = path.split(currentJobId + '/')[1];
        
        fileDiv.innerHTML = `
            <span class="file-name">${type}: ${filename}</span>
            <a href="/download/${currentJobId}/${relativePath}" class="download-btn" download>
                Download
            </a>
        `;
        
        reportFiles.appendChild(fileDiv);
    });
}

// Reset interface to upload new video
function resetInterface() {
    // Reset form
    uploadForm.reset();
    fileName.textContent = 'Choose video file';
    fileName.parentElement.classList.remove('has-file');
    uploadBtn.disabled = false;
    uploadBtn.textContent = 'Start Analysis';
    
    // Clear results
    activityFeed.innerHTML = '';
    document.getElementById('incidentsList').innerHTML = '';
    document.getElementById('guidanceList').innerHTML = '';
    document.getElementById('reportFiles').innerHTML = '';
    
    // Reset steps
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active', 'complete');
        step.querySelector('.step-status').textContent = 'Pending';
    });
    
    // Show upload section
    uploadSection.classList.remove('hidden');
    processingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    
    // Close event source
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
    
    currentJobId = null;
}
