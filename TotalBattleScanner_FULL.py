import cv2
import pytesseract
import pyautogui
import numpy as np
from tkinter import ttk, Tk, Label, Button, Entry, StringVar, OptionMenu, Checkbutton, IntVar, Text, END, Frame, Scale, LabelFrame
from plyer import notification
import time
import json
import os
from datetime import datetime
import threading
import winsound
from PIL import Image, ImageTk
import logging
import re
import csv
import pyperclip
import random

# Configure logging
logging.basicConfig(
    filename='scanner_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Path to Tesseract (adjust if installed elsewhere)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class TotalBattleScanner:
    def __init__(self):
        self.root = Tk()
        self.root.title("Total Battle Scanner Pro")
        self.root.geometry("1200x800")  # Increased window size
        
        # Variables
        self.filter_var = StringVar(value="Silver Only")
        self.min_silver_var = StringVar(value="50000")  # Default minimum silver
        self.min_ingots_var = StringVar(value="100")
        self.min_wood_var = StringVar(value="100")
        self.min_stone_var = StringVar(value="100")
        self.shield_expiring_var = IntVar(value=1)  # Enable by default
        self.shield_hours_var = StringVar(value="6")  # Alert for shields expiring in 6 hours
        self.continuous_scan_var = IntVar(value=1)  # Enable by default
        self.scan_delay_var = IntVar(value=5)
        self.dark_mode_var = IntVar()
        self.sound_notification_var = IntVar(value=1)
        self.auto_next_var = IntVar(value=1)  # Automatically move to next target
        
        # Scanning pattern options
        self.scan_pattern_var = StringVar(value="Spiral")
        self.scan_radius_var = StringVar(value="50")  # Maximum tiles to scan
        self.scan_direction_var = StringVar(value="Clockwise")
        
        # Advanced filtering
        self.min_total_resources_var = StringVar(value="100000")  # Minimum total resources
        self.exclude_alliance_var = StringVar(value="")  # Alliance tags to exclude
        self.max_power_var = StringVar(value="")  # Maximum target power
        self.min_inactive_time_var = StringVar(value="24")  # Hours inactive
        
        # Export options
        self.export_format_var = StringVar(value="CSV")
        
        # Target tracking
        self.current_coords = None
        self.scanned_targets = set()
        self.profitable_targets = []
        self.current_pattern = []
        self.pattern_index = 0
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        # Create main container with padding
        main_container = Frame(self.root, padx=10, pady=10)
        main_container.pack(fill='both', expand=True)
        
        # Create left and right panels
        left_panel = Frame(main_container, width=400)
        left_panel.pack(side='left', fill='both', padx=(0, 10))
        
        right_panel = Frame(main_container)
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Left Panel - Settings
        settings_frame = LabelFrame(left_panel, text="Scan Settings")
        settings_frame.pack(fill='x', pady=5)
        
        # Resource Filters with better layout
        filter_frame = Frame(settings_frame)
        filter_frame.pack(fill='x', padx=5, pady=5)
        
        Label(filter_frame, text="Target Priority:").pack()
        OptionMenu(filter_frame, self.filter_var, 
                  "Silver Only", "Ingots Only", "Wood Only", "Stone Only", "All Resources").pack(fill='x')
        
        # Resource Thresholds
        thresholds_frame = LabelFrame(settings_frame, text="Minimum Resources")
        thresholds_frame.pack(fill='x', padx=5, pady=5)
        
        # Grid layout for resource inputs
        Label(thresholds_frame, text="Silver:").grid(row=0, column=0, sticky='w', pady=2)
        Entry(thresholds_frame, textvariable=self.min_silver_var).grid(row=0, column=1, sticky='ew', padx=5)
        
        Label(thresholds_frame, text="Ingots:").grid(row=1, column=0, sticky='w', pady=2)
        Entry(thresholds_frame, textvariable=self.min_ingots_var).grid(row=1, column=1, sticky='ew', padx=5)
        
        Label(thresholds_frame, text="Wood:").grid(row=2, column=0, sticky='w', pady=2)
        Entry(thresholds_frame, textvariable=self.min_wood_var).grid(row=2, column=1, sticky='ew', padx=5)
        
        Label(thresholds_frame, text="Stone:").grid(row=3, column=0, sticky='w', pady=2)
        Entry(thresholds_frame, textvariable=self.min_stone_var).grid(row=3, column=1, sticky='ew', padx=5)
        
        # Shield Settings
        shield_frame = LabelFrame(settings_frame, text="Shield Settings")
        shield_frame.pack(fill='x', padx=5, pady=5)
        
        Checkbutton(shield_frame, text="Include Targets with Expiring Shield", 
                   variable=self.shield_expiring_var).pack(anchor='w', padx=5)
        
        shield_hours_frame = Frame(shield_frame)
        shield_hours_frame.pack(fill='x', padx=5)
        Label(shield_hours_frame, text="Alert when shield < ").pack(side='left')
        Entry(shield_hours_frame, textvariable=self.shield_hours_var, width=5).pack(side='left')
        Label(shield_hours_frame, text=" hours").pack(side='left')
        
        # Scan Options
        options_frame = LabelFrame(settings_frame, text="Scan Options")
        options_frame.pack(fill='x', padx=5, pady=5)
        
        Checkbutton(options_frame, text="Continuous Scan", 
                   variable=self.continuous_scan_var).pack(anchor='w', padx=5)
        
        Checkbutton(options_frame, text="Auto-move to Next Target", 
                   variable=self.auto_next_var).pack(anchor='w', padx=5)
        
        delay_frame = Frame(options_frame)
        delay_frame.pack(fill='x', padx=5, pady=5)
        Label(delay_frame, text="Scan Delay (seconds):").pack(side='left')
        Scale(delay_frame, from_=1, to=60, variable=self.scan_delay_var, 
              orient='horizontal').pack(side='left', fill='x', expand=True)
        
        # Right Panel - Results
        # Profitable Targets
        targets_frame = LabelFrame(right_panel, text="Profitable Targets")
        targets_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        # Create Treeview for targets
        self.targets_tree = ttk.Treeview(targets_frame, 
            columns=("Coords", "Resources", "Shield", "Last Scan"),
            show='headings'
        )
        
        # Configure columns
        self.targets_tree.heading("Coords", text="Coordinates")
        self.targets_tree.heading("Resources", text="Resources")
        self.targets_tree.heading("Shield", text="Shield Status")
        self.targets_tree.heading("Last Scan", text="Last Scan")
        
        # Add scrollbar
        targets_scroll = ttk.Scrollbar(targets_frame, orient="vertical", 
                                     command=self.targets_tree.yview)
        self.targets_tree.configure(yscrollcommand=targets_scroll.set)
        
        self.targets_tree.pack(side='left', fill='both', expand=True)
        targets_scroll.pack(side='right', fill='y')
        
        # Scan Status
        status_frame = LabelFrame(right_panel, text="Scan Status")
        status_frame.pack(fill='both', expand=True)
        
        self.status_output = Text(status_frame, height=10)
        self.status_output.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Control Buttons Frame
        control_frame = Frame(right_panel)
        control_frame.pack(fill='x', pady=10)
        
        self.start_btn = Button(control_frame, text="Start Scanning", 
                         command=self.start_scan, 
                         width=15, 
                         height=2,
                         bg='#4CAF50',
                         fg='white',
                         font=('Arial', 10, 'bold'))
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = Button(control_frame, text="Stop Scanning", 
                        command=self.stop_scan, 
                        width=15,
                        height=2,
                        bg='#f44336',
                        fg='white',
                        font=('Arial', 10, 'bold'))
        self.stop_btn.pack(side='left', padx=5)
        
        self.export_btn = Button(control_frame, text="Export Targets", 
                         command=self.export_targets, 
                         width=15,
                         height=2)
        self.export_btn.pack(side='left', padx=5)
        
        # Apply initial theme
        self.toggle_theme()
        
    def toggle_theme(self):
        if self.dark_mode_var.get():
            # Dark theme colors
            bg_color = '#2b2b2b'
            fg_color = 'white'
            entry_bg = '#3c3c3c'
            
            self.root.configure(bg=bg_color)
            
            # Configure all frames and their children
            for widget in self.root.winfo_children():
                if isinstance(widget, Frame):
                    widget.configure(bg=bg_color)
                    for child in widget.winfo_children():
                        try:
                            if isinstance(child, (Frame, LabelFrame)):
                                child.configure(bg=bg_color)
                            elif isinstance(child, Label):
                                child.configure(bg=bg_color, foreground=fg_color)
                            elif isinstance(child, Entry):
                                child.configure(bg=entry_bg, foreground=fg_color)
                            elif isinstance(child, Text):
                                child.configure(bg=entry_bg, foreground=fg_color)
                            elif isinstance(child, Scale):
                                child.configure(bg=bg_color, foreground=fg_color)
                            elif isinstance(child, Button) and child not in (self.start_btn, self.stop_btn):
                                child.configure(bg=bg_color, foreground=fg_color)
                        except:
                            pass
                            
            # Configure Treeview
            self.style.configure("Treeview",
                               background=entry_bg,
                               foreground=fg_color,
                               fieldbackground=entry_bg)
            self.style.configure("Treeview.Heading",
                               background=bg_color,
                               foreground=fg_color)
            
            # Configure LabelFrame labels
            self.style.configure('TLabelframe.Label', foreground=fg_color, background=bg_color)
            self.style.configure('TLabelframe', background=bg_color)
            
        else:
            # Light theme colors
            bg_color = '#f0f0f0'
            fg_color = 'black'
            entry_bg = 'white'
            
            self.root.configure(bg=bg_color)
            
            # Configure all frames and their children
            for widget in self.root.winfo_children():
                if isinstance(widget, Frame):
                    widget.configure(bg=bg_color)
                    for child in widget.winfo_children():
                        try:
                            if isinstance(child, (Frame, LabelFrame)):
                                child.configure(bg=bg_color)
                            elif isinstance(child, Label):
                                child.configure(bg=bg_color, foreground=fg_color)
                            elif isinstance(child, Entry):
                                child.configure(bg=entry_bg, foreground=fg_color)
                            elif isinstance(child, Text):
                                child.configure(bg=entry_bg, foreground=fg_color)
                            elif isinstance(child, Scale):
                                child.configure(bg=bg_color, foreground=fg_color)
                            elif isinstance(child, Button) and child not in (self.start_btn, self.stop_btn):
                                child.configure(bg=bg_color, foreground=fg_color)
                        except:
                            pass
            
            # Configure Treeview
            self.style.configure("Treeview",
                               background=entry_bg,
                               foreground=fg_color,
                               fieldbackground=entry_bg)
            self.style.configure("Treeview.Heading",
                               background=bg_color,
                               foreground=fg_color)
                               
            # Configure LabelFrame labels
            self.style.configure('TLabelframe.Label', foreground=fg_color, background=bg_color)
            self.style.configure('TLabelframe', background=bg_color)
            
    def extract_number(self, text):
        try:
            return int(''.join(filter(str.isdigit, text)))
        except:
            return 0
            
    def preprocess_image(self, image):
        # Apply various preprocessing techniques to improve OCR accuracy
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (3,3), 0)
        thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        return thresh
        
    def scan_game(self):
        try:
            if not self.current_coords:
                self.find_next_target()
                return
                
            self.status_output.insert(END, f"Scanning coordinates {self.current_coords}...\n")
            self.status_output.see(END)
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # Check for shield status
            shield_info = self.detect_shield_status(screenshot_cv)
            
            # If shield is active and not expiring soon, move to next target
            if shield_info['active'] and not shield_info['expiring_soon']:
                self.status_output.insert(END, "Shield active, moving to next target...\n")
                self.scanned_targets.add(self.current_coords)
                self.find_next_target()
                return
            
            # Detect resources
            resources = self.detect_resources(screenshot_cv)
            
            # Analyze if this is a profitable target
            result = self.analyze_target(resources, shield_info)
            
            if result['valid_target'] == 'True':
                self.add_profitable_target(result)
                
            # Update UI
            self.update_ui(result)
            
            # Move to next target if auto-next is enabled
            if self.auto_next_var.get():
                self.find_next_target()
                
        except Exception as e:
            logging.error(f"Scan error: {str(e)}")
            self.status_output.insert(END, f"Error during scan: {str(e)}\n")
            self.status_output.see(END)

    def detect_shield_status(self, image):
        try:
            # Get the top portion of the screen where shield info appears
            height, width = image.shape[:2]
            top_area = image[0:int(height*0.2), :]
            
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(top_area, cv2.COLOR_BGR2HSV)
            
            # Look for shield icon (blue/white colors)
            lower_blue = np.array([100, 50, 50])
            upper_blue = np.array([130, 255, 255])
            shield_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            # Check for shield time text using OCR
            gray = cv2.cvtColor(top_area, cv2.COLOR_BGR2GRAY)
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 21, 4)
            
            text = pytesseract.image_to_string(thresh)
            
            # Look for time patterns (e.g., "6d 23h" or "23h 45m")
            shield_time = self.extract_shield_time(text)
            
            shield_active = np.any(shield_mask > 0) or shield_time > 0
            expiring_soon = shield_time > 0 and shield_time <= float(self.shield_hours_var.get())
            
            return {
                'active': shield_active,
                'expiring_soon': expiring_soon,
                'hours_remaining': shield_time
            }
            
        except Exception as e:
            logging.error(f"Shield detection error: {str(e)}")
            return {'active': False, 'expiring_soon': False, 'hours_remaining': 0}

    def extract_shield_time(self, text):
        try:
            # Look for patterns like "6d 23h" or "23h 45m"
            days = re.findall(r'(\d+)d', text)
            hours = re.findall(r'(\d+)h', text)
            
            total_hours = 0
            if days:
                total_hours += int(days[0]) * 24
            if hours:
                total_hours += int(hours[0])
                
            return total_hours
            
        except Exception:
            return 0

    def find_next_target(self):
        try:
            # Get current map position
            if not self.current_coords:
                # Start from center of the map
                self.current_coords = self.get_current_coordinates()
            
            # Move to next unscanned coordinate
            next_coords = self.get_next_coordinates()
            if next_coords:
                self.current_coords = next_coords
                # TODO: Implement map navigation to next_coords
                self.status_output.insert(END, f"Moving to coordinates {next_coords}...\n")
            else:
                self.status_output.insert(END, "No more unscanned targets in range.\n")
                self.stop_scan()
                
        except Exception as e:
            logging.error(f"Error finding next target: {str(e)}")
            self.status_output.insert(END, f"Error finding next target: {str(e)}\n")

    def get_current_coordinates(self):
        # Extract coordinates from the game UI
        try:
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # OCR to find coordinates
            text = pytesseract.image_to_string(screenshot_cv)
            coords = re.findall(r'K[:\s]?(\d+)[,\s]+X[:\s]?(\d+)[,\s]+Y[:\s]?(\d+)', text)
            
            if coords:
                return f"K{coords[0][0]} X{coords[0][1]} Y{coords[0][2]}"
            return None
            
        except Exception as e:
            logging.error(f"Error getting coordinates: {str(e)}")
            return None

    def get_next_coordinates(self):
        if not self.current_coords:
            return None
            
        pattern = self.scan_pattern_var.get()
        direction = self.scan_direction_var.get()
        radius = int(self.scan_radius_var.get())
        
        if not self.current_pattern:
            self.current_pattern = self.generate_pattern(pattern, direction, radius)
            self.pattern_index = 0
            
        if self.pattern_index >= len(self.current_pattern):
            return None
            
        next_coords = self.current_pattern[self.pattern_index]
        self.pattern_index += 1
        
        return next_coords

    def generate_pattern(self, pattern_type, direction, radius):
        base_coords = self.parse_coordinates(self.current_coords)
        if not base_coords:
            return []
            
        k, x, y = base_coords
        coords = []
        
        if pattern_type == "Spiral":
            coords = self.generate_spiral_pattern(k, x, y, radius, direction == "Clockwise")
        elif pattern_type == "Grid":
            coords = self.generate_grid_pattern(k, x, y, radius, direction)
        elif pattern_type == "Linear":
            coords = self.generate_linear_pattern(k, x, y, radius, direction)
        else:  # Random
            coords = self.generate_random_pattern(k, x, y, radius)
            
        return [c for c in coords if c not in self.scanned_targets]

    def generate_spiral_pattern(self, k, x, y, radius, clockwise=True):
        coords = []
        dx = 1 if clockwise else -1
        dy = 1
        steps = 1
        current_x, current_y = x, y
        
        while steps <= radius:
            # Move horizontally
            for _ in range(steps):
                current_x += dx
                coords.append(f"K{k} X{current_x} Y{current_y}")
            
            # Move vertically
            for _ in range(steps):
                current_y += dy
                coords.append(f"K{k} X{current_x} Y{current_y}")
                
            steps += 1
            dx *= -1
            dy *= -1
            
        return coords

    def generate_grid_pattern(self, k, x, y, radius, direction):
        coords = []
        if direction in ["North-South", "South-North"]:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    coords.append(f"K{k} X{x+dx} Y{y+dy}")
        else:  # East-West
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    coords.append(f"K{k} X{x+dx} Y{y+dy}")
        return coords

    def generate_linear_pattern(self, k, x, y, radius, direction):
        coords = []
        if direction in ["North-South", "South-North"]:
            for dy in range(-radius, radius + 1):
                coords.append(f"K{k} X{x} Y{y+dy}")
        else:  # East-West
            for dx in range(-radius, radius + 1):
                coords.append(f"K{k} X{x+dx} Y{y}")
        return coords

    def generate_random_pattern(self, k, x, y, radius):
        coords = []
        for _ in range(radius * 8):  # Generate more points for better coverage
            dx = random.randint(-radius, radius)
            dy = random.randint(-radius, radius)
            if dx*dx + dy*dy <= radius*radius:  # Check if within circular radius
                coords.append(f"K{k} X{x+dx} Y{y+dy}")
        return list(set(coords))  # Remove duplicates

    def add_profitable_target(self, result):
        coords = self.current_coords or "Unknown"
        resources_text = ", ".join([f"{k}: {self.format_number(v['amount'])}" 
                                  for k, v in result['resources'].items()])
        shield_text = "Expiring Soon" if result['shield_info']['expiring_soon'] else "No Shield"
        
        # Add to tree view
        self.targets_tree.insert("", 0, values=(
            coords,
            resources_text,
            shield_text,
            result['timestamp']
        ))
        
        # Add to profitable targets list
        self.profitable_targets.append({
            'coords': coords,
            'resources': result['resources'],
            'shield_info': result['shield_info'],
            'timestamp': result['timestamp']
        })

    def analyze_target(self, resources, shield_info):
        result = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'resources': resources,
            'shield_info': shield_info,
            'valid_target': False,
            'reason': "",
            'power': self.detect_power(),
            'alliance': self.detect_alliance()
        }
        
        # Check alliance exclusion
        excluded_alliances = [a.strip() for a in self.exclude_alliance_var.get().split(',') if a.strip()]
        if result['alliance'] in excluded_alliances:
            result['reason'] = f"Excluded alliance: {result['alliance']}"
            result['valid_target'] = str(False)
            return result
            
        # Check power limit
        max_power = self.max_power_var.get()
        if max_power and result['power'] != 'Unknown':
            try:
                if int(result['power']) > int(max_power):
                    result['reason'] = f"Power too high: {result['power']}"
                    result['valid_target'] = str(False)
                    return result
            except ValueError:
                pass
        
        # Check total resources
        total_resources = sum(r['amount'] for r in resources.values())
        min_total = int(self.min_total_resources_var.get() or 0)
        if total_resources < min_total:
            result['reason'] = f"Total resources below minimum: {total_resources} < {min_total}"
            result['valid_target'] = str(False)
            return result
        
        if shield_info['active'] and not shield_info['expiring_soon']:
            result['reason'] = "Shield active"
            result['valid_target'] = str(False)
        else:
            # Original resource threshold checks
            filter_type = self.filter_var.get()
            if filter_type == "All Resources":
                result['valid_target'] = str(all(r['meets_threshold'] for r in resources.values()))
            else:
                resource_type = filter_type.split()[0].lower()
                result['valid_target'] = str(resources[resource_type]['meets_threshold'])
            
            if result['valid_target'] == 'False':
                result['reason'] = "Resources below threshold"
        
        return result

    def detect_power(self):
        try:
            # Implementation of power detection using OCR
            # This would need to be customized based on where power is displayed in the game
            return "Unknown"
        except Exception:
            return "Unknown"

    def detect_alliance(self):
        try:
            # Implementation of alliance detection using OCR
            # This would need to be customized based on where alliance tags are displayed
            return "Unknown"
        except Exception:
            return "Unknown"

    def update_ui(self, result):
        # Update status output
        status_text = f"Scan at {result['timestamp']}\n"
        if result['shield_info']['expiring_soon']:
            status_text += "Shield expiring soon!\n"
        status_text += f"Resources:\n"
        for resource, data in result['resources'].items():
            amount_str = self.format_number(data['amount'])
            status_text += f"  {resource.title()}: {amount_str} (Confidence: {data['confidence']:.2f})\n"
        status_text += f"Shield: {'Active' if result['shield_info']['active'] else 'Inactive'}\n"
        status_text += f"Valid Target: {'Yes' if result['valid_target'] == 'True' else 'No'}\n"
        if result['reason']:
            status_text += f"Reason: {result['reason']}\n"
            
        self.status_output.insert(END, status_text + "\n")
        self.status_output.see(END)
        
        # Update history tree
        resources_text = ", ".join([f"{k}: {self.format_number(v['amount'])}" 
                                  for k, v in result['resources'].items()])
        self.targets_tree.insert("", 0, values=(
            result['coords'],
            resources_text,
            "Expiring Soon" if result['shield_info']['expiring_soon'] else "No Shield",
            result['timestamp']
        ))
        
    def log_scan_result(self, result):
        logging.info(f"Scan Result: {json.dumps(result)}")
        
    def export_targets(self):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            format_type = self.export_format_var.get()
            
            if format_type == "CSV":
                self.export_to_csv(f"targets_{timestamp}.csv")
            elif format_type == "JSON":
                self.export_to_json(f"targets_{timestamp}.json")
            elif format_type == "Excel":
                self.export_to_excel(f"targets_{timestamp}.xlsx")
            else:  # Text
                self.export_to_text(f"targets_{timestamp}.txt")
                
            self.status_output.insert(END, f"Targets exported to targets_{timestamp}.{format_type.lower()}\n")
            self.status_output.see(END)
            
        except Exception as e:
            logging.error(f"Export error: {str(e)}")
            self.status_output.insert(END, f"Export error: {str(e)}\n")

    def export_to_csv(self, filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Coordinates", "Resources", "Shield Status", "Last Scan", "Power", "Alliance"])
            for target in self.profitable_targets:
                writer.writerow([
                    target['coords'],
                    self.format_resources(target['resources']),
                    self.format_shield_status(target['shield_info']),
                    target['timestamp'],
                    target.get('power', 'Unknown'),
                    target.get('alliance', 'Unknown')
                ])

    def export_to_json(self, filename):
        with open(filename, 'w') as f:
            json.dump({
                'targets': self.profitable_targets,
                'scan_settings': self.get_current_settings(),
                'export_time': datetime.now().isoformat()
            }, f, indent=2)

    def export_to_excel(self, filename):
        try:
            import pandas as pd
            
            data = []
            for target in self.profitable_targets:
                data.append({
                    'Coordinates': target['coords'],
                    'Resources': self.format_resources(target['resources']),
                    'Shield Status': self.format_shield_status(target['shield_info']),
                    'Last Scan': target['timestamp'],
                    'Power': target.get('power', 'Unknown'),
                    'Alliance': target.get('alliance', 'Unknown'),
                    'Notes': ''
                })
            
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False, sheet_name='Profitable Targets')
            
        except ImportError:
            self.status_output.insert(END, "Excel export requires pandas. Please install it first.\n")

    def export_to_text(self, filename):
        with open(filename, 'w') as f:
            f.write("Total Battle Scanner - Target Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for target in self.profitable_targets:
                f.write(f"Target: {target['coords']}\n")
                f.write(f"Resources: {self.format_resources(target['resources'])}\n")
                f.write(f"Shield: {self.format_shield_status(target['shield_info'])}\n")
                f.write(f"Last Scan: {target['timestamp']}\n")
                f.write(f"Power: {target.get('power', 'Unknown')}\n")
                f.write(f"Alliance: {target.get('alliance', 'Unknown')}\n")
                f.write("-" * 50 + "\n")

    def copy_to_clipboard(self):
        try:
            text = []
            for target in self.profitable_targets:
                text.append(f"{target['coords']} - {self.format_resources(target['resources'])}")
            
            pyperclip.copy("\n".join(text))
            self.status_output.insert(END, "Target list copied to clipboard!\n")
            self.status_output.see(END)
            
        except Exception as e:
            self.status_output.insert(END, f"Copy error: {str(e)}\n")

    def format_resources(self, resources):
        return ", ".join([f"{k}: {self.format_number(v['amount'])}" 
                         for k, v in resources.items()])

    def format_shield_status(self, shield_info):
        if shield_info['active']:
            if shield_info['expiring_soon']:
                return f"Expiring in {shield_info['hours_remaining']}h"
            return "Active"
        return "No Shield"

    def start_scan(self):
        if not self.is_scanning:
            self.is_scanning = True
            self.scan_thread = threading.Thread(target=self.scan_loop)
            self.scan_thread.start()
            self.status_output.insert(END, "Scanning started...\n")
            self.status_output.see(END)
            
    def stop_scan(self):
        if self.is_scanning:
            self.is_scanning = False
            if self.scan_thread:
                self.scan_thread.join()
            self.status_output.insert(END, "Scanning stopped.\n")
            self.status_output.see(END)
            
    def scan_loop(self):
        while self.is_scanning:
            self.scan_game()
            if not self.continuous_scan_var.get():
                break
            time.sleep(self.scan_delay_var.get())
            
    def load_settings(self):
        try:
            if os.path.exists('scanner_settings.json'):
                with open('scanner_settings.json', 'r') as f:
                    settings = json.load(f)
                    self.filter_var.set(settings.get('filter', "Silver Only"))
                    self.min_silver_var.set(settings.get('min_silver', '50000'))
                    self.min_ingots_var.set(settings.get('min_ingots', '100'))
                    self.min_wood_var.set(settings.get('min_wood', '100'))
                    self.min_stone_var.set(settings.get('min_stone', '100'))
                    self.shield_expiring_var.set(settings.get('shield_expiring', 1))
                    self.shield_hours_var.set(settings.get('shield_hours', '6'))
                    self.continuous_scan_var.set(settings.get('continuous_scan', 1))
                    self.scan_delay_var.set(settings.get('scan_delay', 5))
                    self.dark_mode_var.set(settings.get('dark_mode', 0))
                    self.sound_notification_var.set(settings.get('sound_notification', 1))
                    self.scan_pattern_var.set(settings.get('scan_pattern', "Spiral"))
                    self.scan_radius_var.set(settings.get('scan_radius', "50"))
                    self.scan_direction_var.set(settings.get('scan_direction', "Clockwise"))
                    self.min_total_resources_var.set(settings.get('min_total_resources', "100000"))
                    self.exclude_alliance_var.set(settings.get('exclude_alliance', ""))
                    self.max_power_var.set(settings.get('max_power', ""))
                    self.min_inactive_time_var.set(settings.get('min_inactive_time', "24"))
                    self.export_format_var.set(settings.get('export_format', "CSV"))
        except Exception as e:
            logging.error(f"Error loading settings: {str(e)}")
            
    def save_settings(self):
        try:
            settings = self.get_current_settings()
            settings['dark_mode'] = self.dark_mode_var.get()
            settings['sound_notification'] = self.sound_notification_var.get()
            settings['scan_pattern'] = self.scan_pattern_var.get()
            settings['scan_radius'] = self.scan_radius_var.get()
            settings['scan_direction'] = self.scan_direction_var.get()
            settings['min_total_resources'] = self.min_total_resources_var.get()
            settings['exclude_alliance'] = self.exclude_alliance_var.get()
            settings['max_power'] = self.max_power_var.get()
            settings['min_inactive_time'] = self.min_inactive_time_var.get()
            settings['export_format'] = self.export_format_var.get()
            
            with open('scanner_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving settings: {str(e)}")
            
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        
    def on_closing(self):
        self.stop_scan()
        self.save_settings()
        self.root.destroy()

    def format_number(self, number):
        if number >= 1000000000:
            return f"{number/1000000000:.1f}B"
        elif number >= 1000000:
            return f"{number/1000000:.1f}M"
        elif number >= 1000:
            return f"{number/1000:.1f}K"
        return str(number)

if __name__ == "__main__":
    app = TotalBattleScanner()
    app.run()
