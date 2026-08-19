"""
Display Manager for RouletVoc
Handles screen resolution query, safe margin calculation, display mode configuration,
and coordinate transformations between physical display and virtual game canvas.
"""

import os
import sys
import json
import pygame

# Default Virtual Game Canvas Dimensions (1080p Full HD)
VIRTUAL_WIDTH = 1920
VIRTUAL_HEIGHT = 1080
CONFIG_FILENAME = "display_config.json"

def get_config_dir():
    """Get writable directory for configuration files across dev and packaged modes."""
    if getattr(sys, 'frozen', False):
        # Packaged exe: Check if app directory is writable or use AppData
        app_dir = os.path.dirname(sys.executable)
        test_file = os.path.join(app_dir, ".write_test")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            return os.path.join(app_dir, "config")
        except Exception:
            appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
            user_config_dir = os.path.join(appdata, "RouletVoc", "config")
            os.makedirs(user_config_dir, exist_ok=True)
            return user_config_dir
    else:
        # Dev mode
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "config")

def get_config_path():
    cfg_dir = get_config_dir()
    os.makedirs(cfg_dir, exist_ok=True)
    return os.path.join(cfg_dir, CONFIG_FILENAME)

class DisplayManager:
    def __init__(self, virtual_w=VIRTUAL_WIDTH, virtual_h=VIRTUAL_HEIGHT):
        self.virtual_w = virtual_w
        self.virtual_h = virtual_h
        
        # Detected Hardware Metrics
        self.screen_w = virtual_w
        self.screen_h = virtual_h
        self.work_w = virtual_w
        self.work_h = virtual_h
        self.dpi_scale = 1.0
        
        # Active Viewport & Scaling
        self.display_mode = "borderless_fullscreen" # options: 'borderless_fullscreen', 'fullscreen', 'windowed'
        self.viewport_rect = pygame.Rect(0, 0, virtual_w, virtual_h)
        self.scale_factor = 1.0
        self.safe_margin_x = 0
        self.safe_margin_y = 0
        
        # Load or probe hardware
        self.load_or_probe()

    def probe_hardware_display(self):
        """Query physical screen resolution, work area (minus taskbar/dock), and DPI from OS."""
        w, h = self.virtual_w, self.virtual_h
        work_w, work_h = w, h
        dpi_scale = 1.0

        # Query desktop metrics from Pygame/SDL (Accurate logical coordinates on macOS/Linux/Windows)
        try:
            if not pygame.display.get_init():
                pygame.display.init()
            desktop_sizes = pygame.display.get_desktop_sizes()
            if desktop_sizes and len(desktop_sizes) > 0:
                w, h = desktop_sizes[0]
                work_w, work_h = w, h
            else:
                info = pygame.display.Info()
                if info.current_w > 0 and info.current_h > 0:
                    w, h = info.current_w, info.current_h
                    work_w, work_h = w, h
        except Exception:
            pass

        if sys.platform == "darwin":
            # macOS Safe Margin: Reserve space for Menu Bar (~36px) and Dock (~80px)
            work_h = max(600, h - 116)
            work_w = max(800, w - 40)

        elif sys.platform == "win32":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                
                # Make process DPI aware before query
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)
                except Exception:
                    try:
                        user32.SetProcessDPIAware()
                    except Exception:
                        pass
                
                # Query Work Area (Screen minus taskbar)
                class RECT(ctypes.Structure):
                    _fields_ = [('left', ctypes.c_long),
                                ('top', ctypes.c_long),
                                ('right', ctypes.c_long),
                                ('bottom', ctypes.c_long)]
                
                rect = RECT()
                if user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
                    work_w = rect.right - rect.left
                    work_h = rect.bottom - rect.top
                    
                try:
                    dpi = user32.GetDpiForSystem()
                    dpi_scale = round(dpi / 96.0, 2)
                except Exception:
                    dpi_scale = 1.0
            except Exception as e:
                print(f"[DisplayManager] Windows API probe exception: {e}")

        self.screen_w = max(w, 800)
        self.screen_h = max(h, 600)
        self.work_w = max(work_w, 800)
        self.work_h = max(work_h, 600)
        self.dpi_scale = dpi_scale

        self._calculate_viewport()
        return self.get_config_dict()

    def _calculate_viewport(self):
        """Calculate aspect-ratio preserved viewport filling the display with internal safe UI margins."""
        target_w = self.screen_w
        target_h = self.screen_h

        # Compute scaling factor to preserve virtual 1080x720 aspect ratio filling the screen
        scale_x = target_w / self.virtual_w
        scale_y = target_h / self.virtual_h
        self.scale_factor = min(scale_x, scale_y)

        render_w = int(self.virtual_w * self.scale_factor)
        render_h = int(self.virtual_h * self.scale_factor)

        # Center on the display screen
        offset_x = (target_w - render_w) // 2
        offset_y = (target_h - render_h) // 2

        self.viewport_rect = pygame.Rect(offset_x, offset_y, render_w, render_h)
        self.safe_margin_x = offset_x
        self.safe_margin_y = offset_y

    def get_config_dict(self):
        return {
            "screen_width": self.screen_w,
            "screen_height": self.screen_h,
            "work_width": self.work_w,
            "work_height": self.work_h,
            "dpi_scale": self.dpi_scale,
            "display_mode": self.display_mode,
            "virtual_width": self.virtual_w,
            "virtual_height": self.virtual_h,
            "scale_factor": round(self.scale_factor, 4),
            "viewport": {
                "x": self.viewport_rect.x,
                "y": self.viewport_rect.y,
                "width": self.viewport_rect.width,
                "height": self.viewport_rect.height
            },
            "safe_margin_x": self.safe_margin_x,
            "safe_margin_y": self.safe_margin_y
        }

    def save_config(self):
        """Save display configuration profile to JSON file."""
        cfg_path = get_config_path()
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(self.get_config_dict(), f, indent=4, ensure_ascii=False)
            print(f"[DisplayManager] Config saved successfully to: {cfg_path}")
            return True
        except Exception as e:
            print(f"[DisplayManager] Error saving config to {cfg_path}: {e}")
            return False

    def load_or_probe(self):
        """Load cached config or probe hardware if config does not exist."""
        cfg_path = get_config_path()
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.screen_w = data.get("screen_width", self.virtual_w)
                self.screen_h = data.get("screen_height", self.virtual_h)
                self.work_w = data.get("work_width", self.screen_w)
                self.work_h = data.get("work_height", self.screen_h)
                self.dpi_scale = data.get("dpi_scale", 1.0)
                self.display_mode = data.get("display_mode", "borderless_fullscreen")
                self._calculate_viewport()
                print(f"[DisplayManager] Loaded display config: {self.screen_w}x{self.screen_h} (Mode: {self.display_mode})")
                return
            except Exception as e:
                print(f"[DisplayManager] Failed to read {cfg_path}, probing live hardware: {e}")

        # If no config or load failed, probe live hardware and save
        self.probe_hardware_display()
        self.save_config()

    def create_display(self):
        """Initialize and return the optimal Pygame display surface based on config."""
        if not pygame.display.get_init():
            pygame.display.init()

        flags = pygame.DOUBLEBUF
        if self.display_mode == "borderless_fullscreen":
            flags |= (pygame.NOFRAME | pygame.RESIZABLE)
            screen = pygame.display.set_mode((self.screen_w, self.screen_h), flags)
        elif self.display_mode == "fullscreen":
            flags |= pygame.FULLSCREEN
            screen = pygame.display.set_mode((0, 0), flags)
        else: # Windowed mode with safe margins
            flags |= pygame.RESIZABLE
            win_w = min(self.virtual_w, self.work_w - 40)
            win_h = min(self.virtual_h, self.work_h - 40)
            screen = pygame.display.set_mode((win_w, win_h), flags)

        # Synchronize actual allocated screen dimensions from SDL window
        act_w, act_h = screen.get_size()
        if act_w > 0 and act_h > 0:
            self.screen_w = act_w
            self.screen_h = act_h
            self._calculate_viewport()

        return screen

    def screen_to_virtual_coords(self, screen_pos):
        """Convert physical screen/window mouse coordinates to virtual canvas (1080x720) coords."""
        sx, sy = screen_pos
        vx = (sx - self.viewport_rect.x) / self.scale_factor
        vy = (sy - self.viewport_rect.y) / self.scale_factor
        return int(vx), int(vy)

    def render_virtual_to_screen(self, virtual_surface, display_surface):
        """Render virtual 1080x720 surface onto physical display surface with aspect ratio preservation."""
        display_surface.fill((15, 23, 42))

        if self.viewport_rect.size == (self.virtual_w, self.virtual_h) and self.viewport_rect.topleft == (0, 0):
            display_surface.blit(virtual_surface, (0, 0))
        else:
            scaled_surf = pygame.transform.smoothscale(virtual_surface, self.viewport_rect.size)
            display_surface.blit(scaled_surf, self.viewport_rect.topleft)

# Standalone probe CLI for installation script or manual calibration
if __name__ == "__main__":
    dm = DisplayManager()
    cfg = dm.probe_hardware_display()
    dm.save_config()
    print("=== Display Calibration Profile ===")
    print(json.dumps(cfg, indent=2))
