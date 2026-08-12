import os
import pygame
from PIL import Image, ImageDraw, ImageFont
from config.constants import ASSETS_DIR

# Global caches
_font_cache = {}
_image_cache = {}

def get_thai_font(size):
    if size in _font_cache:
        return _font_cache[size]
    
    font_paths = [
        "/System/Library/Fonts/Supplemental/SukhumvitSet.ttc",
        "/System/Library/Fonts/Supplemental/Thonburi.ttc",
        "/System/Library/Fonts/Supplemental/Ayuthaya.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size)
                _font_cache[size] = font
                return font
            except Exception:
                pass
                
    font = ImageFont.load_default()
    _font_cache[size] = font
    return font

def render_thai_text(text, font_size=24, color=(255, 255, 255)):
    font = get_thai_font(font_size)
    dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dummy_img)
    
    bbox = draw.textbbox((0, 0), text, font=font)
    w = max(1, bbox[2] - bbox[0] + 16)
    h = max(1, bbox[3] - bbox[1] + 16)
    
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((8 - bbox[0], 8 - bbox[1]), text, font=font, fill=(color[0], color[1], color[2], 255))
    
    raw = img.tobytes("raw", "RGBA")
    return pygame.image.fromstring(raw, img.size, "RGBA")

def get_image(filename, target_size=None):
    key = (filename, target_size)
    if key in _image_cache:
        return _image_cache[key]
        
    stem = os.path.splitext(os.path.basename(filename))[0]
    ext = os.path.splitext(filename)[1] or ".png"
    
    # Priority search with macOS "Remove Background" filenames & transparent stems
    candidates = [
        f"พื้นหลัง {stem} ถูกเอาออก{ext}",
        f"{stem}_transparent{ext}",
        f"{stem}{ext}",
        filename
    ]
    
    # Prioritize specialized subdirectories first!
    subdirs = ["items", "gestures", "ui", "custom", ""]
    search_paths = []
    for cand in candidates:
        for sub in subdirs:
            p = os.path.join(ASSETS_DIR, sub, cand) if sub else os.path.join(ASSETS_DIR, cand)
            if p not in search_paths:
                search_paths.append(p)
    
    for path in search_paths:
        if os.path.exists(path):
            try:
                surf = pygame.image.load(path).convert_alpha()
                if target_size:
                    surf = pygame.transform.smoothscale(surf, target_size)
                _image_cache[key] = surf
                return surf
            except Exception:
                pass
        
    surf = pygame.Surface(target_size if target_size else (80, 80), pygame.SRCALPHA)
    surf.fill((60, 60, 80, 200))
    _image_cache[key] = surf
    return surf
