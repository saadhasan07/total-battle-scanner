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
        self.root.geometry("800x600")
        
        # Variables
        self.filter_var = StringVar(value="Silver Only")
        self.min_silver_var = StringVar()
        self.min_ingots_var = StringVar()
        self.min_wood_var = StringVar()
        self.min_stone_var = StringVar()
        self.shield_expiring_var = IntVar()
        self.only_offline_var = IntVar()
        self.continuous_scan_var = IntVar()
        self.scan_delay_var = IntVar(value=5)
        self.dark_mode_var = IntVar()
        self.sound_notification_var = IntVar(value=1)
        
        # Scan control
        self.is_scanning = False
        self.scan_thread = None
        
        # Configure style for dark mode
        self.style = ttk.Style()
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        # Create main container with padding
        main_container = Frame(self.root, padx=10, pady=10)
        main_container.pack(fill='both', expand=True)
        
        # Create left and right panels
        left_panel = Frame(main_container)
        left_panel.pack(side='left', fill='both', expand=True)
        
        right_panel = Frame(main_container)
        right_panel.pack(side='right', fill='both', expand=True)
        
        # Left Panel - Settings
        settings_frame = LabelFrame(left_panel, text="Scan Settings")
        settings_frame.pack(fill='x', pady=5)
        
        # Resource Filters
        filter_frame = Frame(settings_frame)
        filter_frame.pack(fill='x', padx=5, pady=5)
        
        Label(filter_frame, text="Scan For:").pack()
        OptionMenu(filter_frame, self.filter_var, 
                  "Silver Only", "Ingots Only", "Wood Only", "Stone Only", "All Resources").pack(fill='x')
        
        # Resource Thresholds
        thresholds_frame = Frame(settings_frame)
        thresholds_frame.pack(fill='x', padx=5, pady=5)
        
        # Create a grid layout for resource inputs
        Label(thresholds_frame, text="Min Silver:").grid(row=0, column=0, sticky='w', pady=2)
        Entry(thresholds_frame, textvariable=self.min_silver_var).grid(row=0, column=1, sticky='ew', padx=5)
        
        Label(thresholds_frame, text="Min Ingots:").grid(row=1, column=0, sticky='w', pady=2)
        Entry(thresholds_frame, textvariable=self.min_ingots_var).grid(row=1, column=1, sticky='ew', padx=5)
        
        Label(thresholds_frame, text="Min Wood:").grid(row=2, column=0, sticky='w', pady=2)
        Entry(thresholds_frame, textvariable=self.min_wood_var).grid(row=2, column=1, sticky='ew', padx=5)
        
        Label(thresholds_frame, text="Min Stone:").grid(row=3, column=0, sticky='w', pady=2)
        Entry(thresholds_frame, textvariable=self.min_stone_var).grid(row=3, column=1, sticky='ew', padx=5)
        
        thresholds_frame.grid_columnconfigure(1, weight=1)
        
        # Options Frame
        options_frame = LabelFrame(settings_frame, text="Options")
        options_frame.pack(fill='x', padx=5, pady=5)
        
        # Checkbuttons in options frame
        Checkbutton(options_frame, text="Include Shield Expiring Soon", 
                   variable=self.shield_expiring_var).pack(anchor='w', padx=5)
        Checkbutton(options_frame, text="Only Show Offline Players", 
                   variable=self.only_offline_var).pack(anchor='w', padx=5)
        Checkbutton(options_frame, text="Continuous Scan", 
                   variable=self.continuous_scan_var).pack(anchor='w', padx=5)
        
        # Scan Delay
        delay_frame = Frame(options_frame)
        delay_frame.pack(fill='x', padx=5, pady=5)
        Label(delay_frame, text="Scan Delay (seconds):").pack(side='left')
        Scale(delay_frame, from_=1, to=60, variable=self.scan_delay_var, 
              orient='horizontal').pack(side='left', fill='x', expand=True)
        
        # UI Options
        ui_frame = LabelFrame(settings_frame, text="UI Options")
        ui_frame.pack(fill='x', padx=5, pady=5)
        
        Checkbutton(ui_frame, text="Dark Mode", 
                   variable=self.dark_mode_var, 
                   command=self.toggle_theme).pack(anchor='w', padx=5)
        Checkbutton(ui_frame, text="Sound Notifications", 
                   variable=self.sound_notification_var).pack(anchor='w', padx=5)
        
        # Control Buttons Frame
        control_frame = Frame(settings_frame)
        control_frame.pack(fill='x', padx=5, pady=10)
        
        # Make buttons more prominent
        self.start_btn = Button(control_frame, text="Start Scan", 
                         command=self.start_scan, 
                         width=15, 
                         height=2,
                         bg='#4CAF50',  # Green background
                         fg='white',     # White text
                         font=('Arial', 10, 'bold'))
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = Button(control_frame, text="Stop Scan", 
                        command=self.stop_scan, 
                        width=15,
                        height=2,
                        bg='#f44336',  # Red background
                        fg='white',     # White text
                        font=('Arial', 10, 'bold'))
        self.stop_btn.pack(side='left', padx=5)
        
        self.export_btn = Button(control_frame, text="Export Data", 
                         command=self.export_data, 
                         width=15,
                         height=2)
        self.export_btn.pack(side='left', padx=5)
        
        # Right Panel - Status and History
        status_frame = LabelFrame(right_panel, text="Scan Status")
        status_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.status_output = Text(status_frame, height=15, width=50)
        self.status_output.pack(fill='both', expand=True, padx=5, pady=5)
        
        # History View
        history_frame = LabelFrame(right_panel, text="Scan History")
        history_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.history_tree = ttk.Treeview(history_frame, columns=("Time", "Resources", "Status"), show='headings')
        self.history_tree.heading("Time", text="Time")
        self.history_tree.heading("Resources", text="Resources")
        self.history_tree.heading("Status", text="Status")
        self.history_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
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
            self.status_output.insert(END, "Starting scan...\n")
            self.status_output.see(END)
            
            pyautogui.screenshot("screenshot.png")
            
            # Load and preprocess images
            screenshot = cv2.imread("screenshot.png")
            processed_screenshot = self.preprocess_image(screenshot)
            
            # Resource detection
            resources = {
                'silver': self.detect_resource("silver_area.png", self.min_silver_var.get()),
                'ingots': self.detect_resource("ingot_area.png", self.min_ingots_var.get()),
                'wood': self.detect_resource("wood_area.png", self.min_wood_var.get()),
                'stone': self.detect_resource("stone_area.png", self.min_stone_var.get())
            }
            
            # Status detection
            player_online = self.detect_online_status(processed_screenshot)
            shield_active = self.detect_shield(processed_screenshot)
            
            # Analyze results
            result = self.analyze_scan_results(resources, player_online, shield_active)
            
            # Update UI and log results
            self.update_ui(result)
            self.log_scan_result(result)
            
            # Play sound if enabled and valid target found
            if self.sound_notification_var.get() and result['valid_target']:
                winsound.Beep(1000, 500)
                
        except Exception as e:
            logging.error(f"Scan error: {str(e)}")
            self.status_output.insert(END, f"Error during scan: {str(e)}\n")
            self.status_output.see(END)
            
    def detect_resource(self, template_path, min_value):
        try:
            template = cv2.imread(template_path)
            if template is None:
                return {'amount': 0, 'confidence': 0}
                
            processed = self.preprocess_image(template)
            text = pytesseract.image_to_string(processed, config='--psm 6')
            amount = self.extract_number(text)
            
            # Calculate confidence based on text recognition
            confidence = len(text.strip()) / len(str(amount)) if amount > 0 else 0
            
            return {
                'amount': amount,
                'confidence': confidence,
                'meets_threshold': amount >= int(min_value or 0)
            }
        except Exception as e:
            logging.error(f"Resource detection error: {str(e)}")
            return {'amount': 0, 'confidence': 0, 'meets_threshold': False}
            
    def detect_online_status(self, image):
        text = pytesseract.image_to_string(image, config='--psm 6')
        return "Online" in text
        
    def detect_shield(self, image):
        shield_template = cv2.imread("peace_shield_icon.png", 0)
        if shield_template is None:
            return False
            
        res = cv2.matchTemplate(image, shield_template, cv2.TM_CCOEFF_NORMED)
        return np.any(res >= 0.8)
        
    def analyze_scan_results(self, resources, player_online, shield_active):
        result = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'resources': resources,
            'player_online': str(player_online),  # Convert to string
            'shield_active': str(shield_active),  # Convert to string
            'valid_target': False,
            'reason': ""
        }
        
        if shield_active:
            result['reason'] = "Shield active"
        elif self.only_offline_var.get() and player_online:
            result['reason'] = "Player is online"
        else:
            # Check resource thresholds based on filter
            filter_type = self.filter_var.get()
            if filter_type == "All Resources":
                result['valid_target'] = all(r['meets_threshold'] for r in resources.values())
            else:
                resource_type = filter_type.split()[0].lower()
                result['valid_target'] = resources[resource_type]['meets_threshold']
                
            if not result['valid_target']:
                result['reason'] = "Resources below threshold"
                
        # Convert valid_target to string for JSON serialization
        result['valid_target'] = str(result['valid_target'])
        return result
        
    def update_ui(self, result):
        # Update status output
        status_text = f"Scan at {result['timestamp']}\n"
        status_text += f"Resources:\n"
        for resource, data in result['resources'].items():
            status_text += f"  {resource.title()}: {data['amount']} (Confidence: {data['confidence']:.2f})\n"
        status_text += f"Status: {'Online' if result['player_online'] == 'True' else 'Offline'}\n"
        status_text += f"Shield: {'Active' if result['shield_active'] == 'True' else 'Inactive'}\n"
        status_text += f"Valid Target: {'Yes' if result['valid_target'] == 'True' else 'No'}\n"
        if result['reason']:
            status_text += f"Reason: {result['reason']}\n"
            
        self.status_output.insert(END, status_text + "\n")
        self.status_output.see(END)
        
        # Update history tree
        resources_text = ", ".join([f"{k}: {v['amount']}" for k, v in result['resources'].items()])
        self.history_tree.insert("", 0, values=(
            result['timestamp'],
            resources_text,
            "Valid" if result['valid_target'] == 'True' else "Invalid"
        ))
        
    def log_scan_result(self, result):
        logging.info(f"Scan Result: {json.dumps(result)}")
        
    def export_data(self):
        filename = f"scan_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                'scan_results': self.get_history_data(),
                'settings': self.get_current_settings()
            }, f, indent=2)
        self.status_output.insert(END, f"Data exported to {filename}\n")
        self.status_output.see(END)
        
    def get_history_data(self):
        return [self.history_tree.item(item)['values'] for item in self.history_tree.get_children()]
        
    def get_current_settings(self):
        return {
            'filter': self.filter_var.get(),
            'min_silver': self.min_silver_var.get(),
            'min_ingots': self.min_ingots_var.get(),
            'min_wood': self.min_wood_var.get(),
            'min_stone': self.min_stone_var.get(),
            'shield_expiring': self.shield_expiring_var.get(),
            'only_offline': self.only_offline_var.get(),
            'continuous_scan': self.continuous_scan_var.get(),
            'scan_delay': self.scan_delay_var.get()
        }
        
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
                    self.min_silver_var.set(settings.get('min_silver', ''))
                    self.min_ingots_var.set(settings.get('min_ingots', ''))
                    self.min_wood_var.set(settings.get('min_wood', ''))
                    self.min_stone_var.set(settings.get('min_stone', ''))
                    self.shield_expiring_var.set(settings.get('shield_expiring', 0))
                    self.only_offline_var.set(settings.get('only_offline', 0))
                    self.continuous_scan_var.set(settings.get('continuous_scan', 0))
                    self.scan_delay_var.set(settings.get('scan_delay', 5))
                    self.dark_mode_var.set(settings.get('dark_mode', 0))
                    self.sound_notification_var.set(settings.get('sound_notification', 1))
        except Exception as e:
            logging.error(f"Error loading settings: {str(e)}")
            
    def save_settings(self):
        try:
            settings = self.get_current_settings()
            settings['dark_mode'] = self.dark_mode_var.get()
            settings['sound_notification'] = self.sound_notification_var.get()
            
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

if __name__ == "__main__":
    app = TotalBattleScanner()
    app.run()
