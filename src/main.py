import pygame, sys
import pygame_widgets

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY = (50, 50, 50)
BLUE = (43, 146, 224)
PURPLE = (136, 66, 207)
GREEN = (90, 207, 66)
RED = (209, 48, 48)
YELLOW = (227, 197, 91)

FPS = 60


def draw_text(surface, text, font, color, x, y):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))


class TitleScreen:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Intro To AI - Nicholas Wise")
        pygame.mouse.set_visible(True)

        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((1280, 800))
        self.bg_color = (25, 25, 25)

        self.title_font  = pygame.font.Font("fonts/Oswald-Medium.ttf", 52)
        self.sub_font    = pygame.font.Font("fonts/Oswald-Medium.ttf", 24)
        self.button_font = pygame.font.Font("fonts/Oswald-Medium.ttf", 20)

        # Button rects
        btn_w, btn_h = 380, 80
        cx = self.screen.get_width() // 2
        self.btn_search = pygame.Rect(cx - btn_w // 2, 340, btn_w, btn_h)
        self.btn_guided = pygame.Rect(cx - btn_w // 2, 460, btn_w, btn_h)
        self.btn_quit   = pygame.Rect(cx - btn_w // 2, 580, btn_w, btn_h)

        self.hovered = None  # tracks which button is hovered

    def draw_button(self, rect, label, hovered):
        base_color   = (60, 60, 60)
        hover_color  = (90, 90, 130)
        border_color = BLUE if hovered else LIGHT_GRAY

        pygame.draw.rect(self.screen, hover_color if hovered else base_color, rect, border_radius=6)
        pygame.draw.rect(self.screen, border_color, rect, width=2, border_radius=6)

        text_surf = self.button_font.render(label, True, WHITE)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)

    def run(self):
        while True:
            self.screen.fill(self.bg_color)

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONUP:
                    if self.btn_search.collidepoint(event.pos):
                        self.launch_search_methods()
                    elif self.btn_guided.collidepoint(event.pos):
                        self.launch_guided_search()
                    elif self.btn_quit.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()

            mouse_pos = pygame.mouse.get_pos()
            self.hovered = None
            if self.btn_search.collidepoint(mouse_pos):
                self.hovered = "search"
            elif self.btn_guided.collidepoint(mouse_pos):
                self.hovered = "guided"
            elif self.btn_quit.collidepoint(mouse_pos):
                self.hovered = "quit"

            # --- Title ---
            title_surf = self.title_font.render("Intro To AI", True, WHITE)
            self.screen.blit(title_surf, title_surf.get_rect(centerx=self.screen.get_width() // 2, y=120))

            sub_surf = self.sub_font.render("Select a project to begin", True, LIGHT_GRAY)
            self.screen.blit(sub_surf, sub_surf.get_rect(centerx=self.screen.get_width() // 2, y=200))

            divider_y = 270
            pygame.draw.line(self.screen, DARK_GRAY,
                             (self.screen.get_width() // 2 - 300, divider_y),
                             (self.screen.get_width() // 2 + 300, divider_y), 1)

            # --- Buttons ---
            self.draw_button(self.btn_search, "Project 1 — Search Methods (BFS / DFS)", self.hovered == "search")
            self.draw_button(self.btn_guided, "Project 2 — Guided Search",               self.hovered == "guided")
            self.draw_button(self.btn_quit,   "Quit",                                     self.hovered == "quit")

            pygame_widgets.update(events)
            pygame.display.update()
            self.clock.tick(FPS)

    def launch_search_methods(self):
        """Hand off to Project 1."""
        from search_methods import Game
        Game().run()
        # When the sub-game window closes it returns here; re-init the display
        # so the title screen is restored cleanly.
        pygame.display.set_caption("Intro To AI - Nicholas Wise")
        self.screen = pygame.display.set_mode((1280, 800))

    def launch_guided_search(self):
        """Hand off to Project 2."""
        from guided_search import GuidedSearch
        GuidedSearch().run()
        pygame.display.set_caption("Intro To AI - Nicholas Wise")
        self.screen = pygame.display.set_mode((1280, 800))


if __name__ == "__main__":
    TitleScreen().run()