# BirdsOS

BirdsOS is a Flask-based application for controlling and monitoring bird feeder hardware, with support for camera feeds and GPIO control. It includes development-friendly mock implementations for testing without physical hardware.

## Features

### Camera System
- Live video streaming with configurable resolution
- Recording capabilities with frame buffering
- Camera settings management
- Mock implementation for development with test pattern generation

### GPIO Control
- Hardware abstraction layer with Raspberry Pi detection
- Pin state monitoring and control
- Mock implementation for development and testing
- Interactive GPIO simulator interface

### Web Interface
- Main dashboard for system monitoring
- Camera simulator with live feed display
- GPIO simulator for hardware interaction
- RESTful API endpoints for system control

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd birdbox
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

The application will be available at:
- Main Dashboard: http://localhost:5000
- Camera Simulator: http://localhost:5000/camera
- GPIO Simulator: http://localhost:5000/gpio

## API Endpoints

### Camera Control
- `GET /video_feed` - Stream live video feed
- `POST /api/camera/record/start` - Start recording
- `POST /api/camera/record/stop` - Stop recording
- `POST /api/camera/settings` - Update camera settings
- `GET /api/camera/recordings` - List recorded videos

### GPIO Control
- `GET /api/gpio/status` - Get current pin states
- `POST /api/gpio/trigger` - Trigger input pin state change

### System Status
- `GET /status` - Get system operational status

## Development

The system includes mock implementations for both camera and GPIO functionality, allowing development and testing without physical hardware. When running on a Raspberry Pi, it automatically switches to using real hardware interfaces.

### Mock Implementations
- Camera mock generates test patterns with timestamps
- GPIO mock simulates pin state management
- Both provide realistic behavior for testing

## Current Status

### Implemented
- Core application structure
- Camera streaming and recording framework
- GPIO state management
- Web interface and simulators
- Hardware abstraction layer

### In Progress
- Motor control system
- Recording storage implementation
- Full status monitoring
- Enhanced simulator features

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

[License information to be added]

# BirdBox - Training Wild Birds to Clean the Environment

The BirdBox project is an innovative approach to environmental cleanup that trains wild birds to collect litter in exchange for food. This project combines environmental conservation with animal intelligence, creating a sustainable way to help clean our environment while engaging with local wildlife.

## Overview

The BirdBox is a device designed to train wild crows to pick up litter and deposit it into a designated container in exchange for food rewards. This project leverages the natural intelligence and adaptability of corvids (crows and ravens) to create a mutually beneficial relationship between humans and birds while addressing environmental pollution.

## How It Works

The system works on a simple principle: when a bird deposits litter into the collection area, it triggers sensors that activate a food dispenser, rewarding the bird with a treat. Over time, birds learn to associate cleaning up litter with receiving food rewards, creating a sustainable cycle of environmental cleanup.

## Project Goals

- Create a sustainable solution for environmental cleanup
- Engage wild birds in a meaningful way that benefits both wildlife and humans
- Raise awareness about environmental issues and animal intelligence
- Demonstrate how technology can be used to create innovative solutions for environmental challenges

## Community Impact

This project not only helps clean the environment but also:
- Creates awareness about environmental pollution
- Demonstrates the intelligence of wild birds
- Provides a unique way for communities to engage with local wildlife
- Offers an educational opportunity to learn about animal behavior and environmental conservation

## Contributing

This is an open-source project, and we welcome contributions from the community. Whether you're interested in hardware improvements, software development, or documentation, your input is valuable to the project's success.

## License

This project is licensed under the Creative Commons - Attribution - Non-Commercial license.


Spezifikation:
Motordurchmesser: 6 mm
Motorlänge: 12 mm
Kabellänge: 65 mm
Gewicht: 2 g
Spannungsbereich: 3,0 V -3,7 V
Testdaten:
Spannung: 3,0 V Strom: 160 mA
Spannung: 3,7 V Strom: 220 mA

# Camera Case
The Camera Case was used from https://www.thingiverse.com/thing:2317664 and modified, to make it attachable to the backboard.
