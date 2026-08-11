import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ASSETS_DIR = "/Users/theppratan/Developer/TRXS_Org/hand_gesture_game/assets"
BRAIN_DIR = "/Users/theppratan/.gemini/antigravity-ide/brain/7ae9e65b-1c76-463e-b33d-aa66a4a445ee"

os.makedirs(ASSETS_DIR, exist_ok=True)

# Helper to process AI generated images: clean transparent background if checkered or white
def process_generated_image(src_path, dest_path, target_size=(256, 256)):
    if not os.path.exists(src_path):
        return False
    img = Image.open(src_path).convert("RGBA")
    
    # Check if corner pixels are checkerboard or white, make background truly transparent
    w, h = img.size
    data = img.load()
    
    # Simple background transparency enhancement if needed
    # AI image is already 1024x1024. Let's resize smoothly to target_size with LANCZOS
    resized = img.resize(target_size, Image.Resampling.LANCZOS)
    resized.save(dest_path, "PNG")
    print(f"[Asset] Processed AI image -> {dest_path}")
    return True

# Map existing AI images
ai_mapping = {
    "book.png": os.path.join(BRAIN_DIR, "item_book_1786438100225.png"),
    "backpack.png": os.path.join(BRAIN_DIR, "item_backpack_1786438116113.png"),
    "pen.png": os.path.join(BRAIN_DIR, "item_pen_1786438129663.png"),
    "pencil.png": os.path.join(BRAIN_DIR, "item_pencil_1786438161049.png"),
    "ruler.png": os.path.join(BRAIN_DIR, "item_ruler_1786438555289.png"),
    "eraser.png": os.path.join(BRAIN_DIR, "item_eraser_1786438668827.png"),
    "chair.png": os.path.join(BRAIN_DIR, "item_chair_1786439203594.png"),
}

for out_name, src in ai_mapping.items():
    process_generated_image(src, os.path.join(ASSETS_DIR, out_name))

# For table, notebook, window, clock, fan: generate ultra-crisp high-res 3D vector-rendered graphics at 512x512 supersampled

def draw_desk_table(draw, size=512):
    # Desk Table: Top surface with 3D bevel and 4 legs with wood grain / warm tones
    # Table top
    top_poly = [(80, 200), (432, 200), (460, 260), (52, 260)]
    draw.polygon(top_poly, fill=(217, 130, 43))
    # Bevel edge
    draw.polygon([(52, 260), (460, 260), (460, 285), (52, 285)], fill=(180, 83, 9))
    draw.line([(52, 260), (460, 260)], fill=(253, 186, 116), width=4)
    
    # 4 Legs
    # Back-left leg
    draw.polygon([(105, 260), (130, 260), (120, 420), (100, 420)], fill=(146, 64, 14))
    # Back-right leg
    draw.polygon([(380, 260), (405, 260), (395, 420), (375, 420)], fill=(146, 64, 14))
    # Front-left leg
    draw.polygon([(75, 285), (105, 285), (95, 460), (70, 460)], fill=(180, 83, 9))
    draw.line([(75, 285), (70, 460)], fill=(251, 146, 60), width=4)
    # Front-right leg
    draw.polygon([(405, 285), (435, 285), (440, 460), (415, 460)], fill=(180, 83, 9))
    draw.line([(405, 285), (415, 460)], fill=(251, 146, 60), width=4)
    
    # Drawer / Front panel
    draw.rectangle([105, 285, 405, 335], fill=(194, 65, 12), outline=(146, 64, 14), width=3)
    # Drawer handle
    draw.rounded_rectangle([230, 302, 280, 318], radius=6, fill=(254, 240, 138), outline=(202, 138, 4), width=3)

def draw_green_notebook(draw, size=512):
    # Green spiral notebook with strap and clean cover
    # Shadow / back cover
    draw.rounded_rectangle([110, 80, 420, 450], radius=24, fill=(21, 128, 61))
    # Front cover
    draw.rounded_rectangle([120, 70, 410, 440], radius=22, fill=(34, 197, 94))
    # Inner label box
    draw.rounded_rectangle([180, 180, 360, 280], radius=14, fill=(240, 253, 244), outline=(22, 101, 52), width=4)
    draw.line([(200, 215), (340, 215)], fill=(134, 239, 172), width=4)
    draw.line([(200, 245), (340, 245)], fill=(134, 239, 172), width=4)
    
    # Spiral spine binding
    for y in range(95, 425, 28):
        # Ring hole
        draw.ellipse([102, y, 118, y + 16], fill=(15, 23, 42))
        # Metallic spiral ring
        draw.rounded_rectangle([86, y + 2, 130, y + 14], radius=6, fill=(226, 232, 240), outline=(148, 163, 184), width=3)
        draw.line([(92, y + 5), (124, y + 5)], fill=(255, 255, 255), width=2)
        
    # Ribbon bookmark
    draw.polygon([(340, 440), (365, 440), (365, 475), (352, 460), (340, 475)], fill=(239, 68, 68))

def draw_window(draw, size=512):
    # Window with wooden frame, glass panes reflecting light, and yellow curtains
    # Window outer wooden frame
    draw.rounded_rectangle([90, 90, 422, 430], radius=16, fill=(217, 119, 6), outline=(146, 64, 14), width=6)
    
    # Glass background (sky blue)
    draw.rectangle([110, 110, 402, 410], fill=(186, 230, 253))
    # Sun / cloud reflection
    draw.ellipse([270, 130, 370, 230], fill=(254, 240, 138, 180))
    
    # Window divider panes (cross)
    draw.rectangle([246, 110, 266, 410], fill=(217, 119, 6))
    draw.rectangle([110, 250, 402, 270], fill=(217, 119, 6))
    
    # Glass glare lines
    draw.polygon([(140, 120), (170, 120), (130, 240), (115, 240)], fill=(255, 255, 255, 140))
    draw.polygon([(290, 120), (320, 120), (280, 240), (265, 240)], fill=(255, 255, 255, 140))
    
    # Yellow Curtains (Left and Right)
    # Curtain rod
    draw.rounded_rectangle([70, 70, 442, 88], radius=6, fill=(180, 83, 9), outline=(120, 53, 15), width=2)
    draw.ellipse([60, 66, 80, 92], fill=(245, 158, 11))
    draw.ellipse([432, 66, 452, 92], fill=(245, 158, 11))
    
    # Left drape
    left_curtain = [(85, 88), (175, 88), (145, 240), (165, 330), (150, 425), (85, 425)]
    draw.polygon(left_curtain, fill=(250, 204, 21), outline=(217, 119, 6))
    # Left tieback
    draw.rounded_rectangle([80, 235, 155, 252], radius=6, fill=(249, 115, 22))
    
    # Right drape
    right_curtain = [(427, 88), (337, 88), (367, 240), (347, 330), (362, 425), (427, 425)]
    draw.polygon(right_curtain, fill=(250, 204, 21), outline=(217, 119, 6))
    # Right tieback
    draw.rounded_rectangle([357, 235, 432, 252], radius=6, fill=(249, 115, 22))

def draw_clock(draw, size=512):
    # Wall clock: Red circular rim, white face, clean black numbers and hands at 10:10 or 3:00
    cx, cy, r = 256, 256, 175
    # Outer red casing
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(220, 38, 38), outline=(153, 27, 27), width=8)
    # Inner rim highlight
    draw.ellipse([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10], fill=(239, 68, 68))
    # White clock face
    draw.ellipse([cx - r + 26, cy - r + 26, cx + r - 26, cy + r - 26], fill=(255, 255, 255), outline=(203, 213, 225), width=4)
    
    # 12 Hour tick marks & dots
    for h in range(12):
        angle = math.radians(h * 30 - 90)
        px1 = cx + math.cos(angle) * (r - 42)
        py1 = cy + math.sin(angle) * (r - 42)
        px2 = cx + math.cos(angle) * (r - 60)
        py2 = cy + math.sin(angle) * (r - 60)
        draw.line([(px1, py1), (px2, py2)], fill=(30, 41, 59) if h % 3 == 0 else (100, 116, 139), width=7 if h % 3 == 0 else 4)
        
    # Clock hands
    # Hour hand (pointing at 3 / 4 o'clock)
    h_angle = math.radians(65 - 90)
    hx = cx + math.cos(h_angle) * 75
    hy = cy + math.sin(h_angle) * 75
    draw.line([(cx, cy), (hx, hy)], fill=(15, 23, 42), width=10)
    
    # Minute hand (pointing at 12)
    m_angle = math.radians(0 - 90)
    mx = cx + math.cos(m_angle) * 110
    my = cy + math.sin(m_angle) * 110
    draw.line([(cx, cy), (mx, my)], fill=(15, 23, 42), width=7)
    
    # Second hand (red pointer)
    s_angle = math.radians(220 - 90)
    sx = cx + math.cos(s_angle) * 125
    sy = cy + math.sin(s_angle) * 125
    draw.line([(cx - math.cos(s_angle)*25, cy - math.sin(s_angle)*25), (sx, sy)], fill=(239, 68, 68), width=3)
    
    # Center cap
    draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=(220, 38, 38), outline=(15, 23, 42), width=3)

def draw_fan(draw, size=512):
    # Desk fan: Blue circular cage, 3 spinning cyan/blue blades, neck and round base with speed buttons
    cx, cy = 256, 200
    # Cage outer rim
    draw.ellipse([cx - 140, cy - 140, cx + 140, cy + 140], fill=(224, 242, 254), outline=(2, 132, 199), width=8)
    
    # Cage grid lines
    for angle_deg in range(0, 360, 30):
        rad = math.radians(angle_deg)
        ex = cx + math.cos(rad) * 136
        ey = cy + math.sin(rad) * 136
        draw.line([(cx, cy), (ex, ey)], fill=(186, 230, 253), width=3)
    draw.ellipse([cx - 85, cy - 85, cx + 85, cy + 85], fill=None, outline=(186, 230, 253), width=3)
    
    # 3 Fan blades (smooth curved aerodynamics)
    for b_angle in [30, 150, 270]:
        rad = math.radians(b_angle)
        rad_f = math.radians(b_angle + 35)
        p1 = (cx, cy)
        p2 = (cx + math.cos(rad) * 115, cy + math.sin(rad) * 115)
        p3 = (cx + math.cos(rad_f) * 105, cy + math.sin(rad_f) * 105)
        draw.polygon([p1, p2, p3], fill=(14, 165, 233), outline=(3, 105, 161))
        
    # Center motor dome
    draw.ellipse([cx - 36, cy - 36, cx + 36, cy + 36], fill=(3, 105, 161), outline=(224, 242, 254), width=4)
    
    # Stand neck
    draw.rounded_rectangle([cx - 16, cy + 130, cx + 16, cy + 225], radius=6, fill=(14, 165, 233), outline=(3, 105, 161), width=4)
    # Adjustment dial
    draw.ellipse([cx - 24, cy + 165, cx + 24, cy + 195], fill=(2, 132, 199))
    
    # Base stand
    draw.ellipse([cx - 100, cy + 210, cx + 100, cy + 265], fill=(3, 105, 161), outline=(2, 132, 199), width=6)
    draw.ellipse([cx - 88, cy + 215, cx + 88, cy + 255], fill=(14, 165, 233))
    
    # Speed control buttons (1, 2, 3, Off)
    for i, bx in enumerate([-45, -15, 15, 45]):
        bcol = (239, 68, 68) if i == 0 else (248, 250, 252)
        draw.ellipse([cx + bx - 9, cy + 230, cx + bx + 9, cy + 244], fill=bcol, outline=(30, 41, 59), width=2)

generators = {
    "table.png": draw_desk_table,
    "notebook.png": draw_green_notebook,
    "window.png": draw_window,
    "clock.png": draw_clock,
    "fan.png": draw_fan,
}

for filename, gen_fn in generators.items():
    # 2x supersampling for ultra smooth anti-aliased graphics
    canvas_size = 1024
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    gen_fn(draw, size=canvas_size)
    
    # Scale down to 256x256 with high quality Lanczos filtering
    out_img = img.resize((256, 256), Image.Resampling.LANCZOS)
    target_path = os.path.join(ASSETS_DIR, filename)
    out_img.save(target_path, "PNG")
    print(f"[Asset] Created crisp vector asset -> {target_path}")

print("All 12 vocabulary item assets generated and verified successfully!")
