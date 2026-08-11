import sys
import pygame
from config.constants import WIDTH, HEIGHT, FPS
from config.items import ITEMS_POOL
from states.game import GestureMemoryGame

def main():
    pygame.display.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("RouletVoc • AR Hand Gesture & Voice Vocabulary Game")
    clock = pygame.time.Clock()

    game = GestureMemoryGame()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.state in ["LANDING_MENU", "PODIUM_DASHBOARD"]:
                        running = False
                    else:
                        game.state = "LANDING_MENU"
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

        is_gameplay_active = game.state not in ["LANDING_MENU", "TEAM_SETUP", "PODIUM_DASHBOARD"]
        bg_cam = game.tracking_engine.process_frame(is_gameplay_active=is_gameplay_active)
        
        game.update()
        game.draw(screen, bg_cam)

        pygame.display.flip()
        clock.tick(FPS)

    if game.tracking_engine.cap:
        game.tracking_engine.cap.release()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
