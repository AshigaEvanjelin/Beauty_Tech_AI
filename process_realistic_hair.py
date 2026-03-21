import cv2
import numpy as np
import os

# Paths to the AI generated assets
assets = {
    "bob_cut": r"C:\Users\angel\.gemini\antigravity\brain\06ca744c-5c12-4519-b2da-fec12eb19706\bob_cut_asset_1773595287812.png",
    "layer_cut": r"C:\Users\angel\.gemini\antigravity\brain\06ca744c-5c12-4519-b2da-fec12eb19706\layer_cut_asset_1773595447071.png",
    "curtain_bangs": r"C:\Users\angel\.gemini\antigravity\brain\06ca744c-5c12-4519-b2da-fec12eb19706\curtain_bangs_asset_1773595470730.png",
    "long_waves": r"C:\Users\angel\.gemini\antigravity\brain\06ca744c-5c12-4519-b2da-fec12eb19706\long_waves_asset_1773595713220.png",
    "curly_style": r"C:\Users\angel\.gemini\antigravity\brain\06ca744c-5c12-4519-b2da-fec12eb19706\curly_style_asset_1773595776031.png",
    "korean_style": r"C:\Users\angel\.gemini\antigravity\brain\06ca744c-5c12-4519-b2da-fec12eb19706\korean_style_asset_1773595793308.png"
}

target_dir = r"c:\Users\angel\OneDrive\Desktop\Beauty_Tech_AI\backend\static\hairstyles"
os.makedirs(target_dir, exist_ok=True)

for name, path in assets.items():
    if not os.path.exists(path):
        continue
        
    img = cv2.imread(path)
    if img is None:
        continue
        
    # Convert to BGRA
    bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    
    # Precise transparency: 
    # Since background is plain white, we can use the grayscale inverse as alpha
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # White areas (255) should be transparent (0)
    # Dark areas (0) should be opaque (255)
    # We use a threshold to make the transition sharper but keep soften edges
    _, mask = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY)
    
    # Smooth the mask slightly to prevent jagged edges
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    
    # Invert mask (hair becomes 255, background becomes 0)
    alpha = cv2.bitwise_not(mask)
    
    bgra[:, :, 3] = alpha
    
    # Also, slightly darken the hair to make it look less 'flat' or to compensate for white bleed
    # but here we'll just focus on the alpha channel.
    
    target_path = os.path.join(target_dir, f"{name}.png")
    cv2.imwrite(target_path, bgra)
    print(f"Refined asset: {target_path}")
