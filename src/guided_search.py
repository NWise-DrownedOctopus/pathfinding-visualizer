import pygame, sys, pygame_widgets

"""
guided_search.py — Project 2: Guided Search
============================================
Stub file. Implement your guided-search logic here.
The entry point expected by main.py is GuidedSearch().run().
"""

WHITE      = (255, 255, 255)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = (50,  50,  50)
BLUE       = (43, 146, 224)

FPS = 60


class GuidedSearch:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Intro To AI - Project 2 - Nicholas Wise")
        pygame.mouse.set_visible(True)

        self.clock  = pygame.time.Clock()
        self.screen = pygame.display.set_mode((1280, 800))
        self.bg_color = (25, 25, 25)

        self.title_font = pygame.font.Font("fonts/Oswald-Medium.ttf", 36)
        self.body_font  = pygame.font.Font("fonts/Oswald-Medium.ttf", 20)

    def run(self):
        while True:
            self.screen.fill(self.bg_color)

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    return  # Return to title screen
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return  # Return to title screen

            # --- Placeholder UI ---
            title = self.title_font.render("Project 2 — Guided Search", True, WHITE)
            self.screen.blit(title, title.get_rect(centerx=640, y=180))

            hint = self.body_font.render("Coming soon.  Press ESC to return to the title screen.", True, LIGHT_GRAY)
            self.screen.blit(hint, hint.get_rect(centerx=640, y=260))

            pygame_widgets.update(events)
            pygame.display.update()
            self.clock.tick(FPS)
