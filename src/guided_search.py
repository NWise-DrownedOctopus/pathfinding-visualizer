import pygame, sys, pygame_widgets
from pygame_widgets.dropdown import Dropdown
from pygame_widgets.button import Button

import os

from graph import Graph
from control_panel import ControlPanel
from utils import draw_text, import_graph, Node
from graph_algorithms import BFS, DFS, ID_DFS, GreedyBestFirst, AStar

WHITE      = (255, 255, 255)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = (50,  50,  50)
BLUE       = (43, 146, 224)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

COORD_FILE = os.path.join(DATA_DIR, "coordinates.csv")
ADJ_FILE   = os.path.join(DATA_DIR, "Adjacencies.txt")

FPS          = 60
DEFAULT_STEP = 300   # ms between steps

ALGO_MAPPING = {
    0: DFS,
    1: BFS,
    2: ID_DFS,
    3: GreedyBestFirst,
    4: AStar,
}


class GuidedSearch:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Intro To AI - Project 2 - Nicholas Wise")
        pygame.mouse.set_visible(True)

        BASE_DIR  = os.path.dirname(__file__)
        FONT_PATH = os.path.join(BASE_DIR, "..", "fonts", "Oswald-Medium.ttf")

        self.clock    = pygame.time.Clock()
        self.screen   = pygame.display.set_mode((1280, 800))
        self.bg_color = (25, 25, 25)
        self.dt       = 0

        self.title_font = pygame.font.Font(FONT_PATH, 36)
        self.body_font  = pygame.font.Font(FONT_PATH, 20)

        self.control_panel_dimensions = (260, 640)
        self.control_panel_window = pygame.Surface((self.control_panel_dimensions))

        self.graph_window_dimensions = (950, 640)
        self.graph_window_pos = [303, 40]
        self.graph_window = pygame.Surface((self.graph_window_dimensions))

        self.stats_panel_dimensions = (1240, 100)
        self.stats_panel = pygame.Surface((self.stats_panel_dimensions))

        # Load graph data
        self.nodes: list[Node] = import_graph(COORD_FILE, ADJ_FILE)
        self.node_map: dict[str, Node] = {n.name: n for n in self.nodes}

        self.start_node: Node | None = None
        self.end_node:   Node | None = None

        # Selection state
        self.set_start_mode = False
        self.set_end_mode   = False

        # Algorithm state
        self.active_algo  = None   # current algo instance
        self.running      = False  # True while stepping
        self.step_delay   = DEFAULT_STEP
        self.step_elapsed = 0

        # ── Widgets ──────────────────────────────────────────────────────
        self.dropdown = Dropdown(
            self.screen, 40, 90, 220, 40, name='Select Algorithm',
            choices=['Depth-First Search', 'Breadth-First Search',
                     'Iterative Deepening DFS', 'Best-First Search', 'A*'],
            borderRadius=1, colour=LIGHT_GRAY, values=[0, 1, 2, 3, 4],
            direction='down', textHAlign='left',
        )

        self.set_start_node_button = Button(
            self.screen, 40, 460, 220, 40,
            text='Set Start Node', fontSize=15, margin=10,
            inactiveColour=WHITE, hoverColour=(150, 0, 0),
            pressedColour=(0, 200, 20), radius=3,
            onClick=self.set_start_select_mode,
        )

        self.set_end_node_button = Button(
            self.screen, 40, 510, 220, 40,
            text='Set End Node', fontSize=15, margin=10,
            inactiveColour=WHITE, hoverColour=(150, 0, 0),
            pressedColour=(0, 200, 20), radius=3,
            onClick=self.set_end_select_mode,
        )

        self.run_button = Button(
            self.screen, 40, 570, 220, 40,
            text='Run Algorithm', fontSize=15, margin=10,
            inactiveColour=WHITE, hoverColour=(150, 0, 0),
            pressedColour=(0, 200, 20), radius=3,
            onClick=self.start_algorithm,
        )

        self.reset_button = Button(
            self.screen, 40, 620, 220, 40,
            text='Reset', fontSize=15, margin=10,
            inactiveColour=WHITE, hoverColour=(150, 0, 0),
            pressedColour=(0, 200, 20), radius=3,
            onClick=self.reset,
        )

    # ------------------------------------------------------------------
    # Widget / state helpers
    # ------------------------------------------------------------------

    def _hide_widgets(self):
        for w in (self.dropdown, self.set_start_node_button,
                  self.set_end_node_button, self.run_button, self.reset_button):
            w.hide()

    def set_start_select_mode(self):
        self.set_start_mode = True
        self.set_end_mode   = False

    def set_end_select_mode(self):
        self.set_end_mode   = True
        self.set_start_mode = False

    def reset(self):
        """Clear the current result so a fresh run can be started."""
        self.active_algo  = None
        self.running      = False
        self.step_elapsed = 0

    def start_algorithm(self):
        if self.start_node is None or self.end_node is None:
            print("[GuidedSearch] Set both start and end nodes first.")
            return

        algo_choice = self.dropdown.getSelected()
        if algo_choice is None:
            algo_choice = 0
        if algo_choice not in ALGO_MAPPING:
            print(f"[GuidedSearch] Unknown algo choice: {algo_choice!r}")
            return

        algo_class       = ALGO_MAPPING[algo_choice]
        self.active_algo = algo_class(self.start_node, self.end_node)
        self.running      = True
        self.step_elapsed = 0
        print(f"[GuidedSearch] Starting {algo_class.__name__} "
              f"{self.start_node.name} → {self.end_node.name}")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        try:
            graph = Graph()
            graph.nodes = self.nodes
            graph.build_screen_positions(self.graph_window, 200)
        except Exception as e:
            print(f"Setup error: {e}")
            import traceback; traceback.print_exc()
            return

        while True:
            # ── Tick FIRST so dt is always valid this frame ───────────────
            self.dt = self.clock.tick(FPS)

            self.screen.fill(self.bg_color)
            self.control_panel_window.fill(DARK_GRAY)
            self.graph_window.fill(DARK_GRAY)
            self.stats_panel.fill(DARK_GRAY)

            # ── Events ───────────────────────────────────────────────────
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._hide_widgets(); return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._hide_widgets(); return
                    # +/- adjust step speed
                    if event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                        self.step_delay = max(0, self.step_delay - 50)
                    if event.key == pygame.K_MINUS:
                        self.step_delay = min(2000, self.step_delay + 50)

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.set_start_mode or self.set_end_mode:
                        clicked = graph.get_hovered_node(
                            pygame.mouse.get_pos(), self.graph_window_pos)
                        if clicked is not None:
                            if self.set_start_mode:
                                self.start_node     = clicked
                                graph.start_node    = clicked
                                self.set_start_mode = False
                                self.reset()
                            else:
                                self.end_node       = clicked
                                graph.end_node      = clicked
                                self.set_end_mode   = False
                                self.reset()

            # ── Step the algorithm one node per interval ──────────────────
            if self.running and self.active_algo is not None:
                self.step_elapsed += self.dt
                if self.step_elapsed >= self.step_delay:
                    self.step_elapsed = 0
                    finished = self.active_algo.update()
                    if finished:
                        self.running = False
                        print(f"[GuidedSearch] Done. "
                              f"Found={self.active_algo.found}  "
                              f"Visited={len(self.active_algo.visited_nodes)}  "
                              f"Path={len(self.active_algo.path)}")

            # ── Draw ──────────────────────────────────────────────────────
            hovered_node = graph.get_hovered_node(
                pygame.mouse.get_pos(), self.graph_window_pos)

            graph.draw_graph(self.graph_window, 5, 200,
                             hovered_node, self.active_algo)

            self.screen.blit(self.control_panel_window, (20, 40))
            self.screen.blit(self.graph_window,
                             (self.graph_window_pos[0], self.graph_window_pos[1]))
            self.screen.blit(self.stats_panel, (20, 700))

            # ── UI labels ────────────────────────────────────────────────
            draw_text(self.screen, "Algorithm Selection",
                      self.body_font, WHITE, 23, 10)
            draw_text(self.screen, "Graph View",
                      self.body_font, WHITE,
                      self.graph_window_pos[0], self.graph_window_pos[1] - 30)
            draw_text(self.screen, "Stats",
                      self.body_font, WHITE, 23, 700)
            draw_text(self.screen, "ESC — return to title  |  +/- adjust speed",
                      self.body_font, (100, 100, 100), 23, 770)
            draw_text(self.screen, f"Nodes loaded: {len(self.nodes)}",
                      self.body_font, LIGHT_GRAY, 200, 720)
            draw_text(self.screen,
                      f"Step delay: {self.step_delay} ms",
                      self.body_font, LIGHT_GRAY, 23, 740)

            # Stats once an algo exists (running or finished)
            if self.active_algo is not None:
                status = ""
                if not self.running:
                    status = "✓ Path found" if self.active_algo.found else "✗ No path"
                else:
                    status = "Running…"
                draw_text(self.screen,
                          f"{status}  |  "
                          f"Visited: {len(self.active_algo.visited_nodes)}  |  "
                          f"Frontier: {len(self.active_algo.frontier)}  |  "
                          f"Path: {len(self.active_algo.path)}",
                          self.body_font, LIGHT_GRAY, 200, 740)

            # Selection mode prompts
            if self.set_start_mode:
                draw_text(self.screen, "Click a node to set START",
                          self.body_font, (90, 207, 66),
                          self.graph_window_pos[0], self.graph_window_pos[1] + 10)
            elif self.set_end_mode:
                draw_text(self.screen, "Click a node to set END",
                          self.body_font, (209, 48, 48),
                          self.graph_window_pos[0], self.graph_window_pos[1] + 10)

            if self.start_node:
                draw_text(self.screen,
                          f"Start: {self.start_node.name.replace('_', ' ')}",
                          self.body_font, (90, 207, 66), 400, 705)
            if self.end_node:
                draw_text(self.screen,
                          f"End: {self.end_node.name.replace('_', ' ')}",
                          self.body_font, (209, 48, 48), 400, 730)
            if hovered_node:
                draw_text(self.screen,
                          f"Hover: {hovered_node.name.replace('_', ' ')}",
                          self.body_font, WHITE, 650, 720)

            pygame_widgets.update(events)
            pygame.display.update()