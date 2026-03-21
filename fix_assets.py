import cv2
import numpy as np
import os

# Create the folder in the correct Flask static path
path = 'static/hairstyles'
os.makedirs(path, exist_ok=True)

styles = [
    ("bob_cut", (0, 0, 255)),     # Reddish
    ("layer_cut", (0, 255, 0)),   # Greenish
    ("curtain_bangs", (255, 0, 0)), # Blueish
    ("long_waves", (0, 255, 255)),  # Yellowish
    ("curly_style", (255, 0, 255)), # Magenta
    ("korean_style", (255, 255, 0)) # Cyan
]

def create_hair_png(name, color):
    # Create a 500x500 empty image with alpha channel
    img = np.zeros((500, 500, 4), dtype=np.uint8)
    
    # Draw an ellipse representing hair (semi-transparent)
    center = (250, 200)
    axes = (200, 150)
    angle = 0
    startAngle = 180
    endAngle = 360 # Top half circle
    
    cv2.ellipse(img, center, axes, angle, startAngle, endAngle, (*color, 255), -1) 
    
    # Add some text
    cv2.putText(img, name.replace('_', ' ').title(), (130, 200), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255, 255), 2)
                
    filepath = os.path.join(path, f'{name}.png')
    cv2.imwrite(filepath, img)
    print(f"Generated {filepath}")

for name, color in styles:
    create_hair_png(name, color)
