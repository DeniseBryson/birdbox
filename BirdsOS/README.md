# BirdsOS

BirdsOS is the web interface for the BirdBox project, allowing monitoring and control of the bird feeding system.

## Development Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)
- Git

### Installation

1. Clone the repository (if not already done):
```bash
git clone <repository-url>
cd birdbox
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r BirdsOS/requirements.txt
```

### Running the Development Server

1. Navigate to the BirdsOS directory:
```bash
cd BirdsOS
```

2. Start the Flask development server:
```bash
python app.py
```

The application will be available at:
- http://localhost:5000 (local access)
- http://<your-ip>:5000 (network access)

### Testing the Basic Setup

1. Open your web browser and navigate to http://localhost:5000

2. You should see:
   - A navigation bar with links to Dashboard, Configuration, Statistics, and Camera
   - Three status cards showing System Status, Storage, and Food Level
   - Motor control buttons (Start, Stop, Emergency Stop)
   - A placeholder for the camera feed

3. Current Functionality:
   - Basic web interface is loaded
   - Status updates every 5 seconds (currently showing mock data)
   - Motor control buttons are visible (API endpoints not yet implemented)
   - Responsive design works on different screen sizes

### Development Notes

- The application is currently configured for development with hardware-specific features disabled
- Raspberry Pi specific packages (RPi.GPIO, picamera2) are commented out in requirements.txt
- Hardware integration will be implemented in subsequent phases

### Next Steps

1. Implementation of Motor API endpoints
2. Storage monitoring system
3. Camera integration
4. Database setup for logging and analytics

## License

This project is part of the BirdBox system. See the LICENSE file in the root directory for details. 