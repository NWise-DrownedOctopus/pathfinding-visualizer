import pygame, sys, pygame_widgets
from pygame_widgets.dropdown import Dropdown
from pygame_widgets.textbox import TextBox
from pygame_widgets.button import Button

from enum import Enum, auto
import os

from graph import Graph
from control_panel import ControlPanel
from utils import draw_text, import_graph, Node
from grid_algorithms import BFS, DFS

WHITE      = (255, 255, 255)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = (50,  50,  50)
BLUE       = (43, 146, 224)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

COORD_FILE = os.path.join(DATA_DIR, "coordinates.csv")
ADJ_FILE   = os.path.join(DATA_DIR, "Adjacencies.txt")

FPS = 60

class algorithm_chosen(Enum):
    BFS    = auto()
    DFS    = auto()
    ID_DFS = auto()
    GBF    = auto()
    A_STAR = auto()
    NONE   = auto()

class GuidedSearch:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Intro To AI - Project 2 - Nicholas Wise")
        pygame.mouse.set_visible(True)

        BASE_DIR   = os.path.dirname(__file__)
        FONT_PATH  = os.path.join(BASE_DIR, "..", "fonts", "Oswald-Medium.ttf")

        self.clock     = pygame.time.Clock()
        self.screen    = pygame.display.set_mode((1280, 800))
        self.bg_color  = (25, 25, 25)

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

        # Selection / algorithm state
        self.set_start_mode      = False
        self.set_end_mode        = False
        self.hover_display       = False
        self.algorithim          = algorithm_chosen.BFS
        self.run_algo            = False
        self.pathfinding_started = False

        self.bfs = None
        self.dfs = None

        self.dropdown = Dropdown(
            self.screen, 40, 90, 220, 40, name='Select Algorithm',
            choices=['Depth-First Search', 'Breadth-First Search', 'Iterative Deepening DFS', 'Best-First Search', 'A*'],
            borderRadius=1, colour=(LIGHT_GRAY), values=[0, 1, 2, 3, 4],
            direction='down', textHAlign='left',
        )

        def output():
            print(self.textbox.getText())
            self.random_seed = int(self.textbox.getText())
            self.grid_reset = True

        self.textbox = TextBox(self.screen, 40, 400, 220, 50, fontSize=15,
                               borderColour=(0, 0, 0), textColour=(0, 0, 0),
                               onSubmit=output, radius=2, borderThickness=1)

        self.set_start_node_button = Button(
            self.screen, 40, 500, 220, 40,
            text='Set Start Node', fontSize=15, margin=10,
            inactiveColour=(255, 255, 255), hoverColour=(150, 0, 0),
            pressedColour=(0, 200, 20), radius=3,
            onClick=self.set_start_select_mode
        )

        self.set_end_node_button = Button(
            self.screen, 40, 550, 220, 40,
            text='Set End Node', fontSize=15, margin=10,
            inactiveColour=(255, 255, 255), hoverColour=(150, 0, 0),
            pressedColour=(0, 200, 20), radius=3,
            onClick=self.set_end_select_mode
        )

        self.start_algo_button = Button(
            self.screen, 40, 600, 220, 40,
            text='Run Algorithm', fontSize=15, margin=10,
            inactiveColour=(255, 255, 255), hoverColour=(150, 0, 0),
            pressedColour=(0, 200, 20), radius=3,
            onClick=self.start_algorithm
        )

    def _hide_widgets(self):
        for widget in (
            self.dropdown,
            self.set_start_node_button,
            self.set_end_node_button,
            self.start_algo_button,
            self.textbox,
        ):
            widget.hide()

    def set_start_select_mode(self):
        self.hover_display = True
        self.set_start_mode = True
        self.set_end_mode   = False

    def set_end_select_mode(self):
        self.hover_display  = True
        self.set_end_mode   = True
        self.set_start_mode = False

    def start_algorithm(self):
        algo_choice = self.dropdown.getSelected()
        mapping = {
            0: algorithm_chosen.DFS,
            1: algorithm_chosen.BFS,
            2: algorithm_chosen.ID_DFS,
            3: algorithm_chosen.GBF,
            4: algorithm_chosen.A_STAR,
        }
        if algo_choice not in mapping:
            print("Please select an algorithm")
            return
        self.algorithim = mapping[algo_choice]
        self.run_algo   = True

    def run(self):
        try:
            control_panel = ControlPanel()
            graph = Graph()
            graph.nodes = self.nodes
            graph.build_screen_positions(self.graph_window, 200)
        except Exception as e:
            print(f"Setup error: {e}")
            import traceback
            traceback.print_exc()
            return

        while True:
            self.screen.fill(self.bg_color)
            self.control_panel_window.fill(DARK_GRAY)
            self.graph_window.fill(DARK_GRAY)
            self.stats_panel.fill(DARK_GRAY)

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._hide_widgets()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._hide_widgets()
                        return

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.set_start_mode or self.set_end_mode:
                        clicked = graph.get_hovered_node(
                            pygame.mouse.get_pos(),
                            self.graph_window_pos
                        )
                        if clicked is not None:
                            if self.set_start_mode:
                                self.start_node      = clicked
                                graph.start_node     = clicked
                                self.set_start_mode  = False
                            else:
                                self.end_node        = clicked
                                graph.end_node       = clicked
                                self.set_end_mode    = False

            # Resolve which node (if any) the mouse is over
            hovered_node = graph.get_hovered_node(
                pygame.mouse.get_pos(),
                self.graph_window_pos   # [303, 40]
            )

            # Draw graph, passing hovered node so it can highlight + label it
            graph.draw_graph(self.graph_window, 5, 200, hovered_node)

            # Surfaces
            self.screen.blit(self.control_panel_window, (20, 40))
            self.screen.blit(self.graph_window, (self.graph_window_pos[0], self.graph_window_pos[1]))
            self.screen.blit(self.stats_panel, (20, 700))

            # Labels
            draw_text(self.screen, "Algorithm Selection",   self.body_font, WHITE,            23,  10)
            draw_text(self.screen, "Graph View",            self.body_font, WHITE,            self.graph_window_pos[0], self.graph_window_pos[1] - 30)
            draw_text(self.screen, "Stats",                 self.body_font, WHITE,            23,  700)
            draw_text(self.screen, "ESC — return to title", self.body_font, (100, 100, 100),  23,  770)
            draw_text(self.screen, f"Nodes loaded: {len(self.nodes)}", self.body_font, LIGHT_GRAY, 200, 720)

            # Show active selection mode as a prompt on the graph window
            if self.set_start_mode:
                draw_text(self.screen, "Click a node to set START",
                          self.body_font, (90, 207, 66),
                          self.graph_window_pos[0], self.graph_window_pos[1] + 10)
            elif self.set_end_mode:
                draw_text(self.screen, "Click a node to set END",
                          self.body_font, (209, 48, 48),
                          self.graph_window_pos[0], self.graph_window_pos[1] + 10)

            # Show selected node names in stats bar
            if self.start_node:
                draw_text(self.screen,
                          f"Start: {self.start_node.name.replace('_', ' ')}",
                          self.body_font, (90, 207, 66), 400, 705)
            if self.end_node:
                draw_text(self.screen,
                          f"End: {self.end_node.name.replace('_', ' ')}",
                          self.body_font, (209, 48, 48), 400, 730)

            # Show hovered city name in stats bar
            if hovered_node:
                draw_text(self.screen,
                          f"Hover: {hovered_node.name.replace('_', ' ')}",
                          self.body_font, WHITE, 650, 720)

            pygame_widgets.update(events)
            pygame.display.update()
            self.clock.tick(FPS)