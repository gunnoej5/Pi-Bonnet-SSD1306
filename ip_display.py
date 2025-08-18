#!/usr/bin/env python3
"""
Display system information on Adafruit SSD1306 OLED bonnet with button navigation
Compatible with Ubuntu ARM64 using luma.oled library
Screens: IP Address, CPU Temperature, Disk Usage
"""

import time
import socket
import subprocess
import psutil
import threading
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("RPi.GPIO not available, button navigation disabled")
    GPIO_AVAILABLE = False

class SystemMonitor:
    def __init__(self):
        self.current_screen = 0
        self.total_screens = 4  # Added command screen
        self.last_update = 0
        self.update_interval = 5  # Update every 5 seconds
        self.auto_advance = True
        self.auto_advance_interval = 10  # Auto advance every 10 seconds
        self.last_button_press = time.time()
        
        # Button GPIO pins for Adafruit bonnet (adjust if different)
        self.BUTTON_A = 5   # Up button
        self.BUTTON_B = 6   # Down button  
        self.BUTTON_L = 27  # Left button (previous screen)
        self.BUTTON_R = 23  # Right button (next screen)
        self.BUTTON_C = 4   # Center button (execute)
        
        self.commands = [
            ("Restart", "sudo reboot"),
            ("Shutdown", "sudo shutdown -h now")
        ]
        self.selected_command = 0

        self.device = None
        self.font = None
        self.small_font = None
        
        self.setup_buttons()
        
    def setup_buttons(self):
        """Setup GPIO buttons if available"""
        if not GPIO_AVAILABLE:
            return
            
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup button pins with pull-up resistors
            buttons = [self.BUTTON_A, self.BUTTON_B, self.BUTTON_L, self.BUTTON_R, self.BUTTON_C]
            for button in buttons:
                GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                
            # Add event detection for buttons
            GPIO.add_event_detect(self.BUTTON_L, GPIO.FALLING, callback=self.prev_screen, bouncetime=300)
            GPIO.add_event_detect(self.BUTTON_R, GPIO.FALLING, callback=self.next_screen, bouncetime=300)
            GPIO.add_event_detect(self.BUTTON_A, GPIO.FALLING, callback=self.prev_command, bouncetime=300)
            GPIO.add_event_detect(self.BUTTON_B, GPIO.FALLING, callback=self.next_command, bouncetime=300)
            GPIO.add_event_detect(self.BUTTON_C, GPIO.FALLING, callback=self.execute_command, bouncetime=300)
            
            print("Button navigation enabled")
        except Exception as e:
            print(f"Error setting up buttons: {e}")

    def prev_command(self, channel=None):
        """Go to previous command in the list"""
        if self.current_screen == 3:  # Only in command screen
            self.selected_command = (self.selected_command - 1) % len(self.commands)
            self.last_button_press = time.time()
            print(f"Selected command: {self.commands[self.selected_command][0]}")

    def next_command(self, channel=None):
        """Go to next command in the list"""
        if self.current_screen == 3:  # Only in command screen
            self.selected_command = (self.selected_command + 1) % len(self.commands)
            self.last_button_press = time.time()
            print(f"Selected command: {self.commands[self.selected_command][0]}")

    def execute_command(self, channel=None):
        """Execute the selected command"""
        if self.current_screen == 3:  # Only in command screen
            command_label, command = self.commands[self.selected_command]
            print(f"Executing command: {command_label}")
            try:
                # Display "Executing..." message
                with canvas(self.device) as draw:
                    draw.text((2, 2), "Executing...", font=self.font, fill="white")
                    draw.text((2, 16), command_label, font=self.small_font, fill="white")
                
                # Execute the command
                subprocess.run(command.split(), check=True)
            except Exception as e:
                print(f"Error executing command: {e}")
                # Display error message
                with canvas(self.device) as draw:
                    draw.text((2, 2), "Error:", font=self.font, fill="white")
                    draw.text((2, 16), str(e), font=self.small_font, fill="white")
                time.sleep(3)

    def prev_screen(self, channel=None):
        """Go to previous screen"""
        self.current_screen = (self.current_screen - 1) % self.total_screens
        self.last_button_press = time.time()
        print(f"Switched to screen {self.current_screen}")
        
    def next_screen(self, channel=None):
        """Go to next screen"""
        self.current_screen = (self.current_screen + 1) % self.total_screens
        self.last_button_press = time.time()
        print(f"Switched to screen {self.current_screen}")

    def get_ip_address(self):
        """Get the system's IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                if ip.startswith("127."):
                    result = subprocess.run(['hostname', '-I'], 
                                          capture_output=True, text=True)
                    ip = result.stdout.strip().split()[0]
                return ip
            except:
                return "No IP Found"

    def get_cpu_temperature(self):
        """Get CPU temperature"""
        try:
            # Try multiple methods to get CPU temperature
            temp_paths = [
                '/sys/class/thermal/thermal_zone0/temp',
                '/sys/class/thermal/thermal_zone1/temp'
            ]
            
            for path in temp_paths:
                try:
                    with open(path, 'r') as f:
                        temp_str = f.read().strip()
                        temp_c = float(temp_str) / 1000.0
                        temp_f = (temp_c * 9/5) + 32
                        return temp_c, temp_f
                except:
                    continue
                    
            # Fallback using psutil
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        temp_c = entries[0].current
                        temp_f = (temp_c * 9/5) + 32
                        return temp_c, temp_f
                        
            return None, None
        except:
            return None, None

    def get_disk_usage(self):
        """Get disk usage information"""
        try:
            usage = psutil.disk_usage('/')
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            percent = (usage.used / usage.total) * 100
            return total_gb, used_gb, free_gb, percent
        except:
            return None, None, None, None

    def draw_ip_screen(self, draw, font, small_font):
        """Draw IP address screen"""
        ip_address = self.get_ip_address()
        hostname = socket.gethostname()
        current_time = time.strftime("%H:%M:%S")
        
        draw.text((2, 2), "System IP (1/4):", font=small_font, fill="white")
        draw.text((2, 16), ip_address, font=font, fill="white")
        draw.text((2, 30), f"Host: {hostname[:16]}", font=small_font, fill="white")
        draw.text((2, 42), f"Time: {current_time}", font=small_font, fill="white")
        
        # Show auto-advance status
        if self.auto_advance:
            draw.text((2, 54), "Auto: ON", font=small_font, fill="white")
        else:
            draw.text((2, 54), "Auto: OFF", font=small_font, fill="white")

    def draw_cpu_screen(self, draw, font, small_font):
        """Draw CPU temperature screen"""
        temp_c, temp_f = self.get_cpu_temperature()
        
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=None)
        
        # Get load average
        try:
            load_avg = psutil.getloadavg()
            load_1min = load_avg[0]
        except:
            load_1min = 0.0
            
        draw.text((2, 2), "CPU Info (2/4):", font=small_font, fill="white")
        
        if temp_c is not None:
            draw.text((2, 16), f"Temp: {temp_c:.1f}°C", font=font, fill="white")
            draw.text((2, 28), f"      {temp_f:.1f}°F", font=font, fill="white")
        else:
            draw.text((2, 16), "Temp: N/A", font=font, fill="white")
            
        draw.text((2, 42), f"Usage: {cpu_percent:.1f}%", font=small_font, fill="white")
        draw.text((2, 54), f"Load: {load_1min:.2f}", font=small_font, fill="white")

    def draw_disk_screen(self, draw, font, small_font):
        """Draw disk usage screen"""
        total_gb, used_gb, free_gb, percent = self.get_disk_usage()
        
        draw.text((2, 2), "Disk Usage (3/4):", font=small_font, fill="white")
        
        if total_gb is not None:
            draw.text((2, 16), f"Total: {total_gb:.1f} GB", font=small_font, fill="white")
            draw.text((2, 28), f"Used:  {used_gb:.1f} GB", font=small_font, fill="white")
            draw.text((2, 40), f"Free:  {free_gb:.1f} GB", font=small_font, fill="white")
            draw.text((2, 52), f"Usage: {percent:.1f}%", font=small_font, fill="white")
            
            # Draw usage bar
            bar_width = 120
            bar_height = 4
            bar_x = 4
            bar_y = 58
            
            # Background bar
            draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], 
                         outline="white", fill=None)
            
            # Usage bar
            used_width = int((percent / 100) * bar_width)
            if used_width > 0:
                draw.rectangle([bar_x, bar_y, bar_x + used_width, bar_y + bar_height], 
                             outline="white", fill="white")
        else:
            draw.text((2, 16), "Disk info N/A", font=font, fill="white")

    def draw_command_screen(self, draw, font, small_font):
        """Draw command menu screen"""
        draw.text((2, 2), "Commands (4/4):", font=small_font, fill="white")
        
        for i, (label, cmd) in enumerate(self.commands):
            if i == self.selected_command:
                draw.rectangle([0, 14 + (i * 12), 127, 26 + (i * 12)], fill="white")
                draw.text((2, 16 + (i * 12)), f"> {label}", font=small_font, fill="black")
            else:
                draw.text((2, 16 + (i * 12)), f"  {label}", font=small_font, fill="white")

    def run(self):
        """Main display loop"""
        # Initialize I2C interface and OLED display
        try:
            serial = i2c(port=1, address=0x3C)
            self.device = ssd1306(serial, width=128, height=64)
            print("OLED initialized successfully on address 0x3C")
        except Exception as e:
            try:
                serial = i2c(port=1, address=0x3D)
                self.device = ssd1306(serial, width=128, height=64)
                print("OLED initialized successfully on address 0x3D")
            except Exception as e2:
                print(f"Error initializing OLED: {e}")
                print(f"Also tried 0x3D: {e2}")
                return
        
        # Load fonts
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 11)
            self.small_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf", 9)
        except:
            try:
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
                self.small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 9)
            except:
                self.font = ImageFont.load_default()
                self.small_font = ImageFont.load_default()
        
        print("Starting multi-screen display...")
        print("Buttons: Left/Right = navigate, Up/Down = command menu, Center = execute")
        print("Press Ctrl+C to exit")
        
        try:
            while True:
                current_time = time.time()
                
                # Auto-advance screens if enabled and no recent button press
                if (self.auto_advance and self.current_screen != 3 and
                    current_time - self.last_button_press > self.auto_advance_interval):
                    self.current_screen = (self.current_screen + 1) % self.total_screens
                    self.last_button_press = current_time
                
                # Update display
                with canvas(self.device) as draw:
                    # Draw border
                    draw.rectangle([0, 0, self.device.width-1, self.device.height-1], 
                                 outline="white", fill=None)
                    
                    # Draw current screen
                    if self.current_screen == 0:
                        self.draw_ip_screen(draw, self.font, self.small_font)
                    elif self.current_screen == 1:
                        self.draw_cpu_screen(draw, self.font, self.small_font)
                    elif self.current_screen == 2:
                        self.draw_disk_screen(draw, self.font, self.small_font)
                    elif self.current_screen == 3:
                        self.draw_command_screen(draw, self.font, self.small_font)
                
                time.sleep(1)  # Update every second for responsive button presses
                
        except KeyboardInterrupt:
            print("\nExiting...")
            self.device.clear()
            if GPIO_AVAILABLE:
                GPIO.cleanup()


def main():
    monitor = SystemMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
