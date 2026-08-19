import sys
import os
import argparse
import pygame

# Set Windows DPI Awareness before pygame initialization to prevent blurry scaling or window clipping
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from config.constants import WIDTH, HEIGHT, FPS
from config.items import ITEMS_POOL
from config.display_manager import DisplayManager
from states.game import GestureMemoryGame

def parse_arguments():
    parser = argparse.ArgumentParser(description="RouletVoc Game Launcher")
    parser.add_argument("--calibrate", "--probe", action="store_true", help="Query and save display hardware profile then exit")
    parser.add_argument("--mode", choices=["borderless", "fullscreen", "windowed"], default=None, help="Force specific display mode")
    return parser.parse_args()

def main():
    args = parse_arguments()
    display_manager = DisplayManager()

    # Hardware Calibration Hook for Installer / Setup
    if args.calibrate:
        print("[Launcher] Running hardware screen resolution calibration...")
        cfg = display_manager.probe_hardware_display()
        display_manager.save_config()
        print(f"[Launcher] Calibration complete. Screen: {cfg['screen_width']}x{cfg['screen_height']}, Safe Margin: X={cfg['safe_margin_x']}, Y={cfg['safe_margin_y']}")
        sys.exit(0)

    if args.mode:
        display_manager.display_mode = "borderless_fullscreen" if args.mode == "borderless" else args.mode
        display_manager._calculate_viewport()

    pygame.display.init()
    screen = display_manager.create_display()
    virtual_surface = pygame.Surface((WIDTH, HEIGHT), depth=24)
    pygame.display.set_caption("RouletVoc • AR Hand Gesture & Voice Vocabulary Game")
    clock = pygame.time.Clock()

    game = GestureMemoryGame()
    running = True

    while running:
        mouse_clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                display_manager.screen_w = event.w
                display_manager.screen_h = event.h
                display_manager._calculate_viewport()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_clicked = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    # Toggle between borderless/fullscreen and windowed
                    if display_manager.display_mode in ["borderless_fullscreen", "fullscreen"]:
                        display_manager.display_mode = "windowed"
                    else:
                        display_manager.display_mode = "borderless_fullscreen"
                    screen = display_manager.create_display()
                    display_manager._calculate_viewport()
                elif event.key == pygame.K_ESCAPE:
                    if game.state == "LANDING_MENU":
                        running = False
                    elif game.state in ["PODIUM_DASHBOARD", "REVIEW_MODE_SELECT", "REVIEW_CONGRATS"]:
                        game.state = "LANDING_MENU"
                    elif game.state in ["REVIEW_WHEEL", "REVIEW_RESULT"]:
                        game.state = "REVIEW_MODE_SELECT"
                    else:
                        game.state = "LANDING_MENU"
                elif event.key == pygame.K_m:
                    game.debug_mouse_mode = not game.debug_mouse_mode
                    print(f"[QA Debug] Mouse control debug mode: {game.debug_mouse_mode}")
                elif game.state == "PODIUM_DASHBOARD":
                    if event.key in [pygame.K_r, pygame.K_SPACE, pygame.K_RETURN]:
                        game.state = "TEAM_SETUP"
                elif game.state == "TEAM_SETUP":
                    if event.key == pygame.K_LEFT and game.num_teams > 2:
                        game.num_teams -= 1
                    elif event.key == pygame.K_RIGHT and game.num_teams < 8:
                        game.num_teams += 1
                    elif event.key == pygame.K_DOWN and game.words_per_team > 1:
                        game.words_per_team -= 1
                    elif event.key == pygame.K_UP and game.words_per_team < len(ITEMS_POOL):
                        game.words_per_team += 1
                    elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        game.start_team_tournament()
                elif game.state == "REVIEW_WHEEL":
                    if event.key in [pygame.K_SPACE, pygame.K_RETURN] and not game.review_wheel.is_spinning:
                        game.spin_review_wheel()
                elif game.state == "REVIEW_RESULT":
                    if event.key == pygame.K_r and game.review_target_item:
                        from core.audio_engine import sound_engine
                        sound_engine.play_vocab(game.review_target_item["id"])
                    elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                        if game.review_submode == "FLASHCARD" and len(game.review_deck) == 0:
                            from core.audio_engine import sound_engine
                            sound_engine.play("podium_fanfare")
                            game.fireworks.clear()
                            game.fireworks.trigger_burst()
                            game.state = "REVIEW_CONGRATS"
                        else:
                            game.spin_review_wheel()
                elif game.state == "REVIEW_CONGRATS":
                    if event.key in [pygame.K_r, pygame.K_SPACE, pygame.K_RETURN]:
                        game.start_review_submode("FLASHCARD")

        # Transform physical screen mouse coordinates to virtual 1080x720 canvas coordinates
        phys_mouse_pos = pygame.mouse.get_pos()
        v_mouse_pos = display_manager.screen_to_virtual_coords(phys_mouse_pos)

        is_gameplay_active = game.state not in [
            "SETUP_CAMERA", "SETUP_WIFI", "LANDING_MENU", "TEAM_SETUP", 
            "PODIUM_DASHBOARD", "REVIEW_MODE_SELECT", "REVIEW_WHEEL", 
            "REVIEW_RESULT", "REVIEW_CONGRATS"
        ]
        bg_cam = game.tracking_engine.process_frame(is_gameplay_active=is_gameplay_active)
        
        game.update(mouse_clicked, mouse_pos=v_mouse_pos)
        game.draw(virtual_surface, bg_cam, mouse_clicked, mouse_pos=v_mouse_pos)

        # Smoothscale virtual surface to display surface with safe margins
        display_manager.render_virtual_to_screen(virtual_surface, screen)

        pygame.display.flip()
        clock.tick(FPS)

    if game.tracking_engine.cap:
        game.tracking_engine.cap.release()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
