import os
import math
from PIL import Image, ImageDraw

ASSETS_DIR = "/Users/theppratan/Developer/TRXS_Org/hand_gesture_game/assets"
BRAIN_DIR = "/Users/theppratan/.gemini/antigravity-ide/brain/7ae9e65b-1c76-463e-b33d-aa66a4a445ee"

os.makedirs(ASSETS_DIR, exist_ok=True)

# 4 Core Gestures
SECTOR_CONFIGS = [
    {
        "id": "PINCH",
        "name": "จีบนิ้ว",
        "en": "PINCH",
        "file": "gesture_pinch.png",
        "bg_col": (245, 158, 11),     # Vibrant Amber
        "rim_col": (217, 119, 6)
    },
    {
        "id": "FIST",
        "name": "กำมือ",
        "en": "FIST",
        "file": "gesture_fist.png",
        "bg_col": (239, 68, 68),      # Vibrant Red / Rose
        "rim_col": (185, 28, 28)
    },
    {
        "id": "PEACE",
        "name": "ชู 2 นิ้ว",
        "en": "PEACE",
        "file": "gesture_peace.png",
        "bg_col": (168, 85, 247),     # Royal Purple
        "rim_col": (126, 34, 206)
    },
    {
        "id": "PALM",
        "name": "แบมือ",
        "en": "PALM",
        "file": "gesture_palm.png",
        "bg_col": (16, 185, 129),     # Emerald Green
        "rim_col": (4, 120, 87)
    }
]

wheel_size = 1024
wheel_img = Image.new("RGBA", (wheel_size, wheel_size), (0, 0, 0, 0))
draw = ImageDraw.Draw(wheel_img)

cx, cy = wheel_size // 2, wheel_size // 2
outer_r = 490
inner_r = 460
hub_r = 120

# Outer Glowing Gold Rim
draw.ellipse([cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r], fill=(30, 41, 59), outline=(245, 158, 11), width=18)
draw.ellipse([cx - outer_r + 14, cy - outer_r + 14, cx + outer_r - 14, cy + outer_r - 14], fill=None, outline=(251, 191, 36), width=6)

# 4 Pieslices (90 degrees each)
num_sectors = len(SECTOR_CONFIGS)
wedge_angle = 360.0 / num_sectors

for i, config in enumerate(SECTOR_CONFIGS):
    start_ang = i * wedge_angle
    end_ang = (i + 1) * wedge_angle
    
    draw.pieslice(
        [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
        start=start_ang,
        end=end_ang,
        fill=config["bg_col"],
        outline=(255, 255, 255, 240),
        width=8
    )

# Composite Circular Badges (เป็นวงๆ) with Radially Oriented Hand Icons
for i, config in enumerate(SECTOR_CONFIGS):
    mid_deg = i * wedge_angle + (wedge_angle / 2.0)
    mid_rad = math.radians(mid_deg)
    
    # 1. Circular Badge
    badge_size = 230
    badge_img = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
    bdraw = ImageDraw.Draw(badge_img)
    bdraw.ellipse([6, 6, badge_size - 6, badge_size - 6], fill=(255, 255, 255, 240), outline=config["rim_col"], width=6)
    bdraw.ellipse([16, 16, badge_size - 16, badge_size - 16], fill=(248, 250, 252, 255))
    
    # 2. Hand Gesture Image with Radial Spoke Orientation (Wrist at bottom, Fingers at top towards outer rim)
    hand_path = os.path.join(ASSETS_DIR, config["file"])
    if os.path.exists(hand_path):
        hand_img = Image.open(hand_path).convert("RGBA")
        hand_icon = hand_img.resize((180, 180), Image.Resampling.LANCZOS)
        
        rot_angle = -(mid_deg + 90.0)
        rot_hand = hand_icon.rotate(rot_angle, resample=Image.Resampling.BICUBIC, expand=True)
        
        hw, hh = rot_hand.size
        badge_img.paste(rot_hand, ((badge_size - hw) // 2, (badge_size - hh) // 2), rot_hand)
    
    # 3. Paste Circular Badge on Wheel Spoke
    pos_r = inner_r * 0.58
    ix = cx + math.cos(mid_rad) * pos_r
    iy = cy + math.sin(mid_rad) * pos_r
    
    wheel_img.paste(badge_img, (int(ix - badge_size // 2), int(iy - badge_size // 2)), badge_img)

# 24 Perimeter Gold Studs
num_bulbs = 24
for b in range(num_bulbs):
    b_ang = math.radians(b * (360.0 / num_bulbs))
    bx = cx + math.cos(b_ang) * (outer_r - 10)
    by = cy + math.sin(b_ang) * (outer_r - 10)
    draw.ellipse([bx - 10, by - 10, bx + 10, by + 10], fill=(254, 240, 138), outline=(202, 138, 4), width=3)
    draw.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=(255, 255, 255))

# Central Clean Metallic Chrome Dome Cap (No text)
draw.ellipse([cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r], fill=(30, 41, 59), outline=(245, 158, 11), width=12)
draw.ellipse([cx - hub_r + 14, cy - hub_r + 14, cx + hub_r - 14, cy + hub_r - 14], fill=(15, 23, 42), outline=(251, 191, 36), width=6)
draw.ellipse([cx - hub_r + 34, cy - hub_r + 34, cx + hub_r - 34, cy + hub_r - 34], fill=(30, 41, 59), outline=(245, 158, 11), width=4)
# Metallic shine highlight
draw.ellipse([cx - 36, cy - 48, cx + 36, cy - 20], fill=(255, 255, 255, 180))

# Generate OK gesture illustration icon (👌)
def generate_ok_gesture_icon():
    icon_size = 512
    img = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Palm Base / Wrist
    draw.rounded_rectangle([190, 310, 330, 480], radius=40, fill=(245, 158, 11), outline=(217, 119, 6), width=10)
    
    # 3 Extended Fingers (Middle, Ring, Pinky) pointing upwards
    # Middle Finger
    draw.rounded_rectangle([270, 70, 330, 330], radius=30, fill=(251, 191, 36), outline=(217, 119, 6), width=10)
    # Ring Finger
    draw.rounded_rectangle([320, 110, 375, 340], radius=28, fill=(245, 158, 11), outline=(217, 119, 6), width=10)
    # Pinky Finger
    draw.rounded_rectangle([365, 170, 415, 350], radius=25, fill=(251, 191, 36), outline=(217, 119, 6), width=10)
    
    # Index Finger & Thumb making the iconic "O" circle on the left
    # Thumb arc
    draw.ellipse([90, 200, 240, 350], fill=(251, 191, 36), outline=(217, 119, 6), width=12)
    # Index finger arc
    draw.ellipse([150, 150, 290, 300], fill=(245, 158, 11), outline=(217, 119, 6), width=12)
    # Inner circle cutout for the "O" hole
    draw.ellipse([160, 210, 230, 280], fill=(255, 255, 255, 255), outline=(217, 119, 6), width=8)
    
    ok_path = os.path.join(ASSETS_DIR, "gesture_ok.png")
    img.save(ok_path, "PNG")
    print(f"[Asset] Generated {ok_path}")

generate_ok_gesture_icon()

