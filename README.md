[github_readme.md](https://github.com/user-attachments/files/21705960/github_readme.md)
# SSD1306 System Monitor

A Python-based system monitor that displays real-time system information on an Adafruit SSD1306 OLED bonnet with button navigation support. Designed for Ubuntu ARM64 systems (Raspberry Pi).

![System Monitor Demo](https://img.shields.io/badge/Platform-Ubuntu%20ARM64-orange) ![Python Version](https://img.shields.io/badge/Python-3.6%2B-blue) ![License](https://img.shields.io/badge/License-MIT-green)

## Features

### 📊 Multiple Information Screens
- **IP Address Screen**: System IP, hostname, current time, auto-advance status
- **CPU Monitor Screen**: Temperature (°C/°F), CPU usage percentage, load average
- **Disk Usage Screen**: Total/used/free space with visual usage bar
- **Command Menu Screen**: Navigate and execute shell commands.

### 🎮 Interactive Navigation
- **Left/Right Buttons**: Navigate between screens
- **Up/Down Buttons**: Navigate the command menu
- **Center Button**: Execute commands
- **Auto-advance**: Automatically cycles through information screens every 10 seconds

### ⚙️ System Integration
- **Systemd Service**: Auto-start on boot with automatic restart on failure
- **Robust Error Handling**: Graceful fallbacks for missing sensors or libraries
- **Multiple I2C Address Support**: Automatically detects display on 0x3C or 0x3D

## Hardware Requirements

- Ubuntu ARM64 system (Raspberry Pi 3/4/5)
- Adafruit SSD1306 OLED Bonnet (128x64 pixels)
- I2C interface enabled

### GPIO Pin Mapping (Adafruit SSD1306 Bonnet)
- GPIO 5 (Button A): Navigate Up (in command menu)
- GPIO 6 (Button B): Navigate Down (in command menu)
- GPIO 27 (Left Button): Previous screen
- GPIO 23 (Right Button): Next screen  
- GPIO 4 (Center Button): Execute command (in command menu)

## Installation

### 1. Install System Dependencies

```bash
# Update system
sudo apt update

# Install I2C tools and Python dependencies
sudo apt install i2c-tools python3-pip python3-pil

# Enable I2C interface
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/firmware/config.txt

# Reboot to enable I2C
sudo reboot
```

### 2. Install Python Libraries

```bash
# Install required Python packages
pip3 install luma.oled psutil RPi.GPIO Pillow
```

### 3. Verify Hardware Connection

```bash
# Check if OLED display is detected (should show 0x3C or 0x3D)
i2cdetect -y 1
```

### 4. Install the Program

```bash
# Clone the repository
git clone https://github.com/yourusername/ssd1306-system-monitor.git
cd ssd1306-system-monitor

# Make script executable
chmod +x ip_display.py

# Test run (optional)
python3 ip_display.py
```

## System Service Setup

### Install as System Service

```bash
# Create installation directory
sudo mkdir -p /opt/ip-display

# Copy script to system location
sudo cp ip_display.py /opt/ip-display/
sudo chown root:root /opt/ip-display/ip_display.py

# Create systemd service file
sudo tee /etc/systemd/system/ip-display.service > /dev/null <<EOF
[Unit]
Description=IP Address OLED Display
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/ip-display
ExecStart=/usr/bin/python3 /opt/ip-display/ip_display.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### Enable and Start Service

```bash
# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable ip-display.service
sudo systemctl start ip-display.service

# Check service status
sudo systemctl status ip-display.service
```

## Usage

### Button Controls
- **Left/Right Buttons**: Navigate between screens.
- **Up/Down Buttons**: In the command menu, navigate the command list.
- **Center Button**: In the command menu, execute the selected command.

### Auto-Advance Mode
- **Enabled**: Automatically cycles through information screens every 10 seconds
- **Disabled**: Manual navigation only
- **Smart Pause**: Auto-advance pauses when buttons are pressed

### Screen Information

#### Screen 1: IP Address
- System IP address
- Hostname (truncated to fit)
- Current time (HH:MM:SS)
- Auto-advance status

#### Screen 2: CPU Monitor  
- CPU temperature in Celsius and Fahrenheit
- Current CPU usage percentage
- System load average (1-minute)

#### Screen 3: Disk Usage
- Total disk space
- Used disk space
- Free disk space
- Usage percentage with visual bar

#### Screen 4: Command Menu
- Navigate a list of predefined shell commands.
- Execute commands with the press of a button.

## Service Management

```bash
# View logs
sudo journalctl -u ip-display.service -f

# Stop service
sudo systemctl stop ip-display.service

# Restart service
sudo systemctl restart ip-display.service

# Disable auto-start
sudo systemctl disable ip-display.service
```

## Troubleshooting

### Display Not Working
1. Verify I2C is enabled: `ls /dev/i2c*` should show `/dev/i2c-1`
2. Check display connection: `i2cdetect -y 1` should show device at 0x3C or 0x3D
3. Verify wiring and power connections

### Service Issues
```bash
# Check service status
sudo systemctl status ip-display.service

# View detailed logs
sudo journalctl -u ip-display.service --since "10 minutes ago"
```

### Button Navigation Not Working
- Ensure RPi.GPIO is installed: `pip3 install RPi.GPIO`
- Check GPIO permissions (service runs as root by default)
- Verify button connections to correct GPIO pins

### Temperature Reading Issues
The program tries multiple methods to read CPU temperature:
- `/sys/class/thermal/thermal_zone0/temp`
- `/sys/class/thermal/thermal_zone1/temp`  
- `psutil.sensors_temperatures()`

## Customization

### Modify Update Intervals
Edit these variables in the script:
```python
self.update_interval = 5      # Data refresh interval (seconds)
self.auto_advance_interval = 10  # Screen change interval (seconds)
```

### Change GPIO Pin Assignments
Update these constants for different button mappings:
```python
self.BUTTON_A = 5   # Up button
self.BUTTON_B = 6   # Down button  
self.BUTTON_L = 27  # Left button (previous screen)
self.BUTTON_R = 23  # Right button (next screen)
self.BUTTON_C = 4   # Center button (execute)
```

### Customize Commands
Edit the `self.commands` list in the script to add, remove, or modify commands and their labels.
```python
self.commands = [
    ("Restart", "sudo reboot"),
    ("Shutdown", "sudo shutdown -h now"),
    # Add more commands here
]
```

### Add Custom Screens
Extend the `SystemMonitor` class with additional `draw_*_screen()` methods and increment `self.total_screens`.

## Dependencies

- **luma.oled**: OLED display driver
- **psutil**: System monitoring library
- **RPi.GPIO**: GPIO control library
- **Pillow**: Image processing library

## License

GNU 

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- Adafruit for the SSD1306 OLED bonnet hardware
- The luma.oled project for the excellent display library
- Contributors to psutil for system monitoring capabilities
