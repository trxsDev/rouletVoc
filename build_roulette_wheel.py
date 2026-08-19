import os
import math
from PIL import Image, ImageDraw

WIDTH, HEIGHT = 2048, 2048
CX, CY = WIDTH // 2, HEIGHT // 2
R_OUTER = 980
R_SECTOR = 870
R_HUB = 210

# Initialize High-Res RGBA Canvas
canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
draw = ImageDraw.Draw(canvas)

# 1. 4 Quadrant Sectors
sectors = [
    {"idx": 0, "file": "gesture_pinch.png", "col1": (245, 158, 11, 255), "deg_start": 0, "deg_end": 90, "deg_mid": 45},
    {"idx": 1, "file": "gesture_fist.png", "col1": (239, 68, 68, 255), "deg_start": 90, "deg_end": 180, "deg_mid": 135},
    {"idx": 2, "file": "gesture_peace.png", "col1": (168, 85, 247, 255), "deg_start": 180, "deg_end": 270, "deg_mid": 225},
    {"idx": 3, "file": "gesture_palm.png", "col1": (16, 185, 129, 255), "deg_start": 270, "deg_end": 360, "deg_mid": 315},
]

# Draw smooth anti-aliased sectors
for s in sectors:
    bbox = [CX - R_SECTOR, CY - R_SECTOR, CX + R_SECTOR, CY + R_SECTOR]
    draw.pieslice(bbox, start=s["deg_start"], end=s["deg_end"], fill=s["col1"], outline=(15, 23, 42, 255), width=4)

# 2. Golden Embossed Divider Spokes
for s in sectors:
    ang_rad = math.radians(s["deg_start"])
    x2 = CX + int(R_SECTOR * math.cos(ang_rad))
    y2 = CY + int(R_SECTOR * math.sin(ang_rad))
    # Golden Spoke Line with dual highlight
    draw.line([(CX, CY), (x2, y2)], fill=(254, 240, 138, 255), width=14)
    draw.line([(CX, CY), (x2, y2)], fill=(180, 83, 9, 255), width=4)

# 3. Paste 4 Pure White Circular Pods with Radially Rotated 3D Gestures
base_dir = os.path.dirname(os.path.abspath(__file__))
assets_gestures = os.path.join(base_dir, "assets", "gestures")
badge_r = 580

for s in sectors:
    rad = math.radians(s["deg_mid"])
    
    pod_x = int(CX + badge_r * math.cos(rad))
    pod_y = int(CY + badge_r * math.sin(rad))
    pod_rad = 176

    # Outer drop shadow for pod
    draw.ellipse([pod_x - pod_rad - 8, pod_y - pod_rad - 8, pod_x + pod_rad + 8, pod_y + pod_rad + 8], fill=(15, 23, 42, 120))
    # Pure Solid White Circular Pod
    draw.ellipse([pod_x - pod_rad, pod_y - pod_rad, pod_x + pod_rad, pod_y + pod_rad], fill=(255, 255, 255, 255), outline=(254, 240, 138, 255), width=8)
    draw.ellipse([pod_x - (pod_rad - 12), pod_y - (pod_rad - 12), pod_x + (pod_rad - 12), pod_y + (pod_rad - 12)], outline=(226, 232, 240, 255), width=4)

    radial_rotation_deg = (s["deg_mid"] - 270.0)

    g_path = os.path.join(assets_gestures, s["file"])
    if os.path.exists(g_path):
        g_img = Image.open(g_path).convert("RGBA")
        g_size = (272, 272)
        g_resized = g_img.resize(g_size, Image.Resampling.LANCZOS)
        
        g_rotated = g_resized.rotate(-radial_rotation_deg, expand=True, resample=Image.Resampling.BICUBIC)
        
        gw, gh = g_rotated.size
        canvas.paste(g_rotated, (pod_x - gw // 2, pod_y - gh // 2), g_rotated)

# 4. Outer Golden Metallic Rim & LED Bulbs
draw.ellipse([CX - R_OUTER, CY - R_OUTER, CX + R_OUTER, CY + R_OUTER], outline=(217, 119, 6, 255), width=64)
draw.ellipse([CX - (R_OUTER - 16), CY - (R_OUTER - 16), CX + (R_OUTER - 16), CY + (R_OUTER - 16)], outline=(254, 240, 138, 255), width=16)
draw.ellipse([CX - (R_OUTER - 32), CY - (R_OUTER - 32), CX + (R_OUTER - 32), CY + (R_OUTER - 32)], outline=(180, 83, 9, 255), width=12)
draw.ellipse([CX - R_SECTOR, CY - R_SECTOR, CX + R_SECTOR, CY + R_SECTOR], outline=(15, 23, 42, 255), width=10)

# 24 Glowing LED Bulbs on the rim
num_leds = 24
for i in range(num_leds):
    led_ang = math.radians(i * (360.0 / num_leds))
    lx = int(CX + (R_OUTER - 28) * math.cos(led_ang))
    ly = int(CY + (R_OUTER - 28) * math.sin(led_ang))
    # Glowing bulb
    draw.ellipse([lx - 24, ly - 24, lx + 24, ly + 24], fill=(254, 240, 138, 255), outline=(245, 158, 11, 255), width=4)
    draw.ellipse([lx - 12, ly - 12, lx + 12, ly + 12], fill=(255, 255, 255, 255))

# 5. Center Golden Hub with Diamond Accent
draw.ellipse([CX - R_HUB, CY - R_HUB, CX + R_HUB, CY + R_HUB], fill=(15, 23, 42, 255), outline=(217, 119, 6, 255), width=20)
draw.ellipse([CX - (R_HUB - 16), CY - (R_HUB - 16), CX + (R_HUB - 16), CY + (R_HUB - 16)], fill=(245, 158, 11, 255), outline=(254, 240, 138, 255), width=12)
draw.ellipse([CX - (R_HUB - 70), CY - (R_HUB - 70), CX + (R_HUB - 70), CY + (R_HUB - 70)], fill=(254, 240, 138, 255), outline=(217, 119, 6, 255), width=8)
draw.ellipse([CX - 56, CY - 56, CX + 56, CY + 56], fill=(255, 255, 255, 255))

# Save High-Definition Roulette Wheel
target_path = os.path.join(base_dir, "assets", "ui", "roulette_wheel.png")
canvas.save(target_path, "PNG")
print("Ultra-HD 2048x2048 Roulette Wheel generated successfully at:", target_path)
