import pygame, sys, pygame_widgets
from pygame_widgets.dropdown import Dropdown
from pygame_widgets.textbox import TextBox
from pygame_widgets.button import Button

from enum import Enum, auto
import os

from graph import Graph
from control_panel import ControlPanel
from utils import draw_text, import_graph, Node
from algorithms import BFS, DFS

WHITE      = (255, 255, 255)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = (50,  50,  50)
BLUE       = (43, 146, 224)

BASE_DIR = os.path.dirname(__file__)          # src/
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

COORD_FILE = os.path.join(DATA_DIR, "coordinates.csv")
ADJ_FILE   = os.path.join(DATA_DIR, "Adjacencies.txt")

FPS = 60

class algorithm_chosen(Enum):
    BFS = auto()
    DFS = auto()
    ID_DFS = auto()
    GBF = auto()
    A_STAR = auto()
    NONE = auto()

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
        
        self.control_panel_dimensions = (260, 640)
        self.control_panel_window = pygame.Surface((self.control_panel_dimensions))

        self.graph_window_dimensions = (950, 640)
        self.graph_window_pos = [303, 40]
        self.graph_window = pygame.Surface((self.graph_window_dimensions))

        self.stats_panel_dimensions = (1240, 100)
        self.stats_panel = pygame.Surface((self.stats_panel_dimensions))
        
        # -----------------------------------------------------------------
        # Load graph data
        # -----------------------------------------------------------------
        self.nodes: list[Node] = import_graph(COORD_FILE, ADJ_FILE)
        # Quick-access dict to look up any node by name
        self.node_map: dict[str, Node] = {n.name: n for n in self.nodes}
 
        self.start_node: Node | None = None
        self.end_node:   Node | None = None
        
        # Selection / algorithm state
        self.set_start_mode = False
        self.set_end_mode = False
        self.hover_display = False
        self.algorithim = algorithm_chosen.BFS
        self.run_algo = False
        self.pathfinding_started = False

        # Algo instances
        self.bfs = None
        self.dfs = None
        
        # Algorithm dropdown 
        self.dropdown = Dropdown(
            self.screen, 40, 90, 220, 40, name='Select Algorithm',
            choices=['Depth-First Search', 'Breadth-First Search', 'Iterative Deepening DFS', 'Best-First Search', 'A*'],
            borderRadius=1, colour=(LIGHT_GRAY), values=[0, 1, 2, 3, 4],
            direction='down', textHAlign='left',
        )
        
        # Set random seed based on textbox input
        def output():
            print(self.textbox.getText())
            self.random_seed = int(self.textbox.getText())
            self.grid_reset = True

        self.textbox = TextBox(self.screen, 40, 400, 220, 50, fontSize=15,
                            borderColour=(0, 0, 0), textColour=(0, 0, 0),
                            onSubmit=output, radius=2, borderThickness=1)

        # --- Starts Set Start Node Mode via GUI
        self.set_start_node_button = Button(
            self.screen, 40, 500, 220, 40,
            text='Set Start Node', fontSize=15, margin=10,
            inactiveColour=(255, 255, 255), hoverColour=(150, 0, 0),
            pressedColour=(0, 200, 20), radius=3,
            onClick=self.set_start_select_mode
        )
        
        # --- Starts Set End Node Mode via GUI
        self.set_end_node_button = Button(
            self.screen, 40, 550, 220, 40,
            text='Set End Node', fontSize=15, margin=10,
            inactiveColour=(255, 255, 255), hoverColour=(150, 0, 0),
            pressedColour=(0, 200, 20), radius=3,
            onClick=self.set_end_select_mode
        )

        # --- Set Run Algo Mode via GUI
        self.start_algo_button = Button(
            self.screen, 40, 600, 220, 40,
            text='Run Algorithm', fontSize=15, margin=10,
            inactiveColour=(255, 255, 255), hoverColour=(150, 0, 0),
            pressedColour=(0, 200, 20), radius=3,
            onClick=self.start_algorithm
        )
        
    # ------------------------------------------------------------------
    # Widget cleanup
    # ------------------------------------------------------------------
    
    def _hide_widgets(self):
        """Unregister all pygame_widgets so they don't bleed into the title screen."""
        for widget in (
            self.dropdown,
            self.set_start_node_button,
            self.set_end_node_button,
            self.start_algo_button,
            self.textbox
        ):
            widget.hide() 
            
    # ------------------------------------------------------------------
    # Mode setters
    # ------------------------------------------------------------------
            
    def set_start_select_mode(self):
        self.hover_display = True
        self.set_start_mode = True
        self.set_end_mode = False

    def set_end_select_mode(self):
        self.hover_display = True
        self.set_end_mode = True
        self.set_start_mode = False

    def start_algorithm(self):
        algo_choice = self.dropdown.getSelected()
        if algo_choice == 0:
            self.algorithim = algorithm_chosen.BFS
        elif algo_choice == 1:
            self.algorithim = algorithm_chosen.DFS
        elif algo_choice == 2:
            self.algorithim = algorithm_chosen.ID_DFS
        elif algo_choice == 3:
            self.algorithim = algorithm_chosen.GBF
        elif algo_choice == 4:
            self.algorithim = algorithm_chosen.A_STAR
        else:
            print("Please select an algorithm")
            return
        self.run_algo = True
        
    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        control_panel = ControlPanel()
        graph = Graph()
        graph.nodes = self.nodes
        
        while True:
            self.screen.fill(self.bg_color)
            self.control_panel_window.fill(DARK_GRAY)
            self.graph_window.fill(DARK_GRAY)
            self.stats_panel.fill(DARK_GRAY)

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._hide_widgets()
                    return  # Return to title screen
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._hide_widgets()
                        return # Return to title screen
                    
            # --- Grpah ---
            graph.draw_graph(self.graph_window, 5, 200)
            
            # --- Surfaces ---
            self.screen.blit(self.control_panel_window, (20, 40))
            self.screen.blit(self.graph_window, (self.graph_window_pos[0], self.graph_window_pos[1]))
            self.screen.blit(self.stats_panel, (20, 700))
            
            # --- Labels ---
            draw_text(self.screen, "Algorithm Selection", self.body_font, (255, 255, 255), 23, 10)
            draw_text(self.screen, "Grid View", self.body_font, (255, 255, 255), self.graph_window_pos[0], self.graph_window_pos[1] - 30)
            draw_text(self.screen, "Stats", self.body_font, (255, 255, 255), 23, 700)
            draw_text(self.screen, "ESC — return to title", self.body_font, (100, 100, 100), 23, 770)
            
            # --- Debug: node count in stats bar ---
            draw_text(self.screen, f"Nodes loaded: {len(self.nodes)}", self.body_font, LIGHT_GRAY, 200, 720)

            pygame_widgets.update(events)
            pygame.display.update()
            self.clock.tick(FPS)
