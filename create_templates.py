from PIL import Image, ImageDraw, ImageFont
import os
import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from PIL import ImageTk

def create_template_image(filename, text, size=(200, 50), bg_color=(240, 240, 240), text_color=(0, 0, 0)):
    # Create a new image with the specified background color
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add a border
    draw.rectangle([(0, 0), (size[0]-1, size[1]-1)], outline=(200, 200, 200))
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        
    # Center the text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    draw.text((x, y), text, fill=text_color, font=font)
    
    # Save the image
    img.save(filename)
    print(f"Created {filename}")

# Create template images
templates = {
    'silver_area.png': 'Silver: 1000',
    'ingot_area.png': 'Ingots: 500',
    'wood_area.png': 'Wood: 2000',
    'stone_area.png': 'Stone: 1500',
    'peace_shield_icon.png': 'Shield',
    'online_status.png': 'Online',
    'troop_area.png': 'Troops: 1000'
}

for filename, text in templates.items():
    create_template_image(filename, text)

class TemplateCreator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Template Creator")
        
        # Variables
        self.current_template = ""
        self.templates_to_create = [
            "silver_area",
            "ingot_area",
            "wood_area",
            "stone_area",
            "peace_shield_icon",
            "online_status"
        ]
        self.template_index = 0
        self.selection_start = None
        self.selection_end = None
        self.image = None
        self.photo = None
        
        # UI Elements
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack(fill="both", expand=True)
        
        # Bind events
        self.canvas.bind("<Button-1>", self.start_selection)
        self.canvas.bind("<B1-Motion>", self.update_selection)
        self.canvas.bind("<ButtonRelease-1>", self.end_selection)
        
        # Instructions label
        self.instruction_label = tk.Label(self.root, 
            text="Select the area for silver_area template")
        self.instruction_label.pack()
        
        # Load screenshot
        self.load_screenshot()
        
    def load_screenshot(self):
        file_path = filedialog.askopenfilename(
            title="Select game screenshot",
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        
        if file_path:
            # Load and display the image
            self.image = cv2.imread(file_path)
            if self.image is not None:
                # Convert BGR to RGB for display
                rgb_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
                # Convert to PhotoImage
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(rgb_image))
                
                # Update canvas size and display image
                self.canvas.config(width=self.image.shape[1], height=self.image.shape[0])
                self.canvas.create_image(0, 0, image=self.photo, anchor="nw")
                
    def start_selection(self, event):
        self.selection_start = (event.x, event.y)
        
    def update_selection(self, event):
        if self.selection_start:
            # Remove previous rectangle
            self.canvas.delete("selection")
            # Draw new rectangle
            self.canvas.create_rectangle(
                self.selection_start[0], self.selection_start[1],
                event.x, event.y,
                outline="red",
                tags="selection"
            )
            
    def end_selection(self, event):
        if self.selection_start and self.image is not None:
            self.selection_end = (event.x, event.y)
            
            # Get coordinates
            x1 = min(self.selection_start[0], self.selection_end[0])
            y1 = min(self.selection_start[1], self.selection_end[1])
            x2 = max(self.selection_start[0], self.selection_end[0])
            y2 = max(self.selection_start[1], self.selection_end[1])
            
            # Crop the image
            cropped = self.image[int(y1):int(y2), int(x1):int(x2)]
            
            # Save template
            template_name = self.templates_to_create[self.template_index]
            cv2.imwrite(f"{template_name}.png", cropped)
            
            # Move to next template
            self.template_index += 1
            if self.template_index < len(self.templates_to_create):
                self.instruction_label.config(
                    text=f"Select the area for {self.templates_to_create[self.template_index]} template"
                )
            else:
                self.root.destroy()
                print("All templates created successfully!")
            
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    creator = TemplateCreator()
    creator.run() 