#!/bin/bash
# Road Rage Detection Pipeline - Web Application Startup Script

echo "=========================================="
echo "Road Rage Detection Pipeline"
echo "Web Application Startup"
echo "=========================================="
echo ""

# Activate conda environment
echo "Activating grounded_sam conda environment..."
eval "$(conda shell.bash hook)"
conda activate grounded_sam

if [ $? -ne 0 ]; then
    echo "Error: Failed to activate grounded_sam conda environment"
    echo "Please ensure the environment exists: conda env list"
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "Warning: .env file not found!"
    echo "Please create a .env file with your GEMINI_API_KEY"
    echo ""
    echo "Example:"
    echo "GEMINI_API_KEY=your_api_key_here"
    echo ""
    read -p "Press Enter to continue anyway or Ctrl+C to exit..."
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: ffmpeg is not installed"
    echo "Video processing requires ffmpeg. Install with:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo ""
    read -p "Press Enter to continue anyway or Ctrl+C to exit..."
fi

# Create necessary directories
echo "Creating required directories..."
mkdir -p uploads results/audio results/reports

# Start the Flask application
echo ""
echo "Starting Flask web server..."
echo "Access the application at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
