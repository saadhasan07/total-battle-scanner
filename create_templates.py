from PIL import Image, ImageDraw, ImageFont
import os

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