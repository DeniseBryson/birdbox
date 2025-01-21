# BirdsOS

A camera monitoring system with mock functionality for development and testing.

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Git
- pip (Python package manager)
- Access to GPIO pins (for Raspberry Pi deployment)

### Installation

1. Clone the repository:
~~~bash
git clone https://github.com/yourusername/BirdsOS.git
cd BirdsOS
~~~

2. Create and activate a virtual environment (recommended):
~~~bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
~~~

3. Install required packages:
~~~bash
pip install -r requirements.txt
~~~

### GPIO Permissions Setup (Raspberry Pi)

To access GPIO pins on a Raspberry Pi, you need to ensure your user has the correct permissions:

1. Add your user to the GPIO group:
~~~bash
sudo usermod -a -G gpio $USER
~~~

2. Create/modify GPIO rules:
~~~bash
sudo nano /etc/udev/rules.d/99-gpio.rules
~~~

Add the following line:
~~~
SUBSYSTEM=="gpio", KERNEL=="gpiochip*", GROUP="gpio", MODE="0660"
~~~

3. Create/modify SPI rules:
~~~bash
sudo nano /etc/udev/rules.d/99-spi.rules
~~~

Add the following line:
~~~
SUBSYSTEM=="spidev", GROUP="gpio", MODE="0660"
~~~

4. Reboot your Raspberry Pi:
~~~bash
sudo reboot
~~~

### Running the Application

1. Start the application:
~~~bash
python main.py
~~~

2. Access the web interface at `http://localhost:8000` (or your device's IP address)

## Features

- Mock camera implementation for development and testing
- Multiple test patterns (grid, circles, color bars)
- Motion simulation
- Video recording capabilities
- Real-time video streaming
- Automatic updates via web interface

## Auto-Update Feature

The application includes an auto-update feature accessible through the web interface. A dedicated update button allows you to:

- Pull the latest changes from the git repository
- Update dependencies automatically
- Restart the application when needed

To use the update feature, simply click the "Update Application" button in the web interface. The system will:
1. Fetch the latest code from the repository
2. Install any new dependencies
3. Prompt you to restart the application if necessary

Note: Make sure you have proper git credentials configured if you're using a private repository.
