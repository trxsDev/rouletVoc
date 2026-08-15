import sys
import os
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
from states.game import GestureMemoryGame

def main():
    pygame.display.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("RouletVoc • AR Hand Gesture & Voice Vocabulary Game")
    clock = pygame.time.Clock()
    fullscreen = False

    game = GestureMemoryGame()
    running = True

    while running:
        mouse_clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_clicked = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                elif event.key == pygame.K_ESCAPE:
                    if game.state == "LANDING_MENU":
                        running = False
                    elif game.state == "PODIUM_DASHBOARD":
                        game.state = "LANDING_MENU"
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

        is_gameplay_active = game.state not in ["SETUP_CAMERA", "SETUP_WIFI", "LANDING_MENU", "TEAM_SETUP", "PODIUM_DASHBOARD"]
        bg_cam = game.tracking_engine.process_frame(is_gameplay_active=is_gameplay_active)
        
        game.update(mouse_clicked)
        game.draw(screen, bg_cam, mouse_clicked)

        pygame.display.flip()
        clock.tick(FPS)

    if game.tracking_engine.cap:
        game.tracking_engine.cap.release()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
