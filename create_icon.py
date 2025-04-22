from PIL import Image, ImageDraw

# Create a 256x256 image with a transparent background
icon_size = 256
img = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a shield shape
shield_color = (52, 152, 219)  # Nice blue color
shield_points = [
    (128, 40),  # Top point
    (200, 80),  # Top right
    (200, 180),  # Bottom right
    (128, 220),  # Bottom point
    (56, 180),   # Bottom left
    (56, 80),    # Top left
]
draw.polygon(shield_points, fill=shield_color)

# Draw a scanner effect
scan_color = (255, 255, 255, 180)  # Semi-transparent white
for i in range(0, icon_size, 20):
    draw.line([(0, i), (icon_size, i)], fill=scan_color, width=2)

# Save as ICO
img.save('app_icon.ico', format='ICO') 