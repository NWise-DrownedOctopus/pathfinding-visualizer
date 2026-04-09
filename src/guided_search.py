import pygame, sys, pygame_widgets
from pygame_widgets.dropdown import Dropdown
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox

import os
import time
import tracemalloc

from graph import Graph
from control_panel import ControlPanel
from utils import draw_text, import_graph, Node
from graph_algorithms import BFS, DFS, ID_DFS, GreedyBestFirst, AStar
from generator_dialog import GeneratorDialog
from graph_generator import generate_graph
from benchmark import run_benchmark
from benchmark_report import BenchmarkReportWindow

WHITE      = (255, 255, 255)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = (50,  50,  50)
BLUE       = (43,  146, 224)
GREEN      = (90,  207, 66)
RED        = (209, 48,  48)
YELLOW     = (227, 197, 91)
ORANGE     = (220, 140, 40)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

COORD_FILE = os.path.join(DATA_DIR, "coordinates.csv")
ADJ_FILE   = os.path.join(DATA_DIR, "Adjacencies.txt")

FPS           = 60
DEFAULT_STEP  = 300   # ms between steps
MIN_STEP      = 0
MAX_STEP      = 1000

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

        self.body_font  = pygame.font.Font(FONT_PATH, 20)
        self.small_font = pygame.font.Font(FONT_PATH, 15)

        self.control_panel_dimensions = (260, 590)
        self.control_panel_window = pygame.Surface(self.control_panel_dimensions)

        self.graph_window_dimensions = (950, 590)
        self.graph_window_pos = [303, 40]
        self.graph_window = pygame.Surface(self.graph_window_dimensions)

        self.stats_panel_dimensions = (1240, 165)
        self.stats_panel = pygame.Surface(self.stats_panel_dimensions)

        # Load preset graph data
        self.nodes: list[Node] = import_graph(COORD_FILE, ADJ_FILE)
        self.node_map: dict[str, Node] = {n.name: n for n in self.nodes}

        # Pending generator params — set when dialog confirms, consumed on next run
        self.pending_gen_params: dict | None = None
        self._rebuild_graph = False  # set True when nodes change mid-session
        self.graph: Graph | None = None  # set in run(), updated on generation

        self.start_node: Node | None = None
        self.end_node:   Node | None = None

        # Selection state
        self.set_start_mode = False
        self.set_end_mode   = False

        # Algorithm state
        self.active_algo   = None
        self.algo_class    = None
        self.running       = False
        self.paused        = False
        self.finished      = False
        self.step_elapsed  = 0
        self.step_delay    = DEFAULT_STEP

        # Stats tracking
        self.stat_time_ms        = None
        self.stat_memory_kb      = None
        self.stat_nodes_exp      = None
        self.stat_path_length    = None
        self.stat_solution_depth = None
        self.stat_heuristic      = None
        self._algo_start_time    = None

        # ── Widgets ──────────────────────────────────────────────────────
        self.dropdown = Dropdown(
            self.screen, 40, 90, 220, 40, name='Select Algorithm',
            choices=['Depth-First Search', 'Breadth-First Search',
                     'Iterative Deepening DFS', 'Best-First Search', 'A*'],
            borderRadius=1, colour=LIGHT_GRAY, values=[0, 1, 2, 3, 4],
            direction='down', textHAlign='left',
        )

        # Node selection buttons
        self.set_start_node_button = Button(
            self.screen, 40, 300, 220, 38,
            text='Set Start Node', fontSize=15, margin=10,
            inactiveColour=WHITE, hoverColour=(150, 0, 0),
            pressedColour=GREEN, radius=3,
            onClick=self.set_start_select_mode,
        )

        self.set_end_node_button = Button(
            self.screen, 40, 348, 220, 38,
            text='Set End Node', fontSize=15, margin=10,
            inactiveColour=WHITE, hoverColour=(150, 0, 0),
            pressedColour=GREEN, radius=3,
            onClick=self.set_end_select_mode,
        )

        # Playback buttons
        btn_w   = 68
        btn_gap = 8
        btn_y   = 410

        self.play_button = Button(
            self.screen, 40, btn_y, btn_w, 38,
            text='▶  Play', fontSize=14, margin=6,
            inactiveColour=WHITE, hoverColour=(0, 160, 0),
            pressedColour=GREEN, radius=3,
            onClick=self.on_play,
        )

        self.pause_button = Button(
            self.screen, 40 + btn_w + btn_gap, btn_y, btn_w, 38,
            text='⏸ Pause', fontSize=14, margin=6,
            inactiveColour=WHITE, hoverColour=(180, 140, 0),
            pressedColour=YELLOW, radius=3,
            onClick=self.on_pause,
        )

        self.restart_button = Button(
            self.screen, 40 + (btn_w + btn_gap) * 2, btn_y, btn_w, 38,
            text='↺ Reset', fontSize=14, margin=6,
            inactiveColour=WHITE, hoverColour=(150, 0, 0),
            pressedColour=RED, radius=3,
            onClick=self.on_restart,
        )

        # Speed slider
        self.speed_slider = Slider(
            self.screen, 40, 495, 220, 16,
            min=MIN_STEP, max=MAX_STEP,
            step=10, initial=MAX_STEP - DEFAULT_STEP,
            colour=DARK_GRAY, handleColour=WHITE,
        )

        # Generate New Graph button — bottom of control panel
        self.gen_graph_button = Button(
            self.screen, 40, 545, 220, 38,
            text='⚙  Generate New Graph', fontSize=13, margin=8,
            inactiveColour=ORANGE, hoverColour=(180, 100, 20),
            pressedColour=(140, 70, 10), radius=3,
            textColour=WHITE,
            onClick=self.on_generate_graph,
        )

        # Benchmark button
        self.benchmark_button = Button(
            self.screen, 40, 590, 220, 38,
            text='📊  Run Benchmark', fontSize=13, margin=8,
            inactiveColour=(60, 100, 160), hoverColour=(40, 80, 140),
            pressedColour=(25, 60, 120), radius=3,
            textColour=WHITE,
            onClick=self.on_benchmark,
        )

    # ------------------------------------------------------------------
    # Widget helpers
    # ------------------------------------------------------------------

    def _hide_widgets(self):
        for w in (
            self.dropdown,
            self.set_start_node_button,
            self.set_end_node_button,
            self.play_button,
            self.pause_button,
            self.restart_button,
            self.speed_slider,
            self.gen_graph_button,
            self.benchmark_button,
        ):
            w.hide()

    def set_start_select_mode(self):
        self.set_start_mode = True
        self.set_end_mode   = False

    def set_end_select_mode(self):
        self.set_end_mode   = True
        self.set_start_mode = False

    # ------------------------------------------------------------------
    # Graph generation
    # ------------------------------------------------------------------

    def on_generate_graph(self):
        """Open the parameter dialog. Store params for use on next Play."""
        # Hide main widgets so they don't bleed into the dialog surface
        self._hide_widgets()

        dialog = GeneratorDialog()
        params = dialog.run()

        # Restore the main display and re-show widgets
        self.screen = pygame.display.set_mode((1280, 800))
        pygame.display.set_caption("Intro To AI - Project 2 - Nicholas Wise")
        self._show_widgets()

        if params is not None:
            self.pending_gen_params = params
            print(f"[GuidedSearch] Generator params received: {params}")

            # Generate the new node list and rebuild the graph
            self.nodes    = generate_graph(params)
            self.node_map = {n.name: n for n in self.nodes}

            # Clear any existing selection and algo state — nodes have changed
            self.start_node = None
            self.end_node   = None
            self._clear_algo()

            # Rebuild self.graph immediately (it's an instance var now)
            self.graph = Graph()
            self.graph.nodes = self.nodes
            self.graph.build_screen_positions(self.graph_window, 200)
            self._rebuild_graph = False   # already done, no need to repeat in loop
            print(f"[GuidedSearch] Graph rebuilt with {len(self.nodes)} nodes.")
        else:
            print("[GuidedSearch] Generator dialog cancelled.")

    def _show_widgets(self):
        """Re-show all widgets after returning from a sub-window."""
        for w in (
            self.dropdown,
            self.set_start_node_button,
            self.set_end_node_button,
            self.play_button,
            self.pause_button,
            self.restart_button,
            self.speed_slider,
            self.gen_graph_button,
            self.benchmark_button,
        ):
            w.show()

    def on_benchmark(self):
        """Run the benchmark harness and display the report popup."""
        if self.start_node is None or self.end_node is None:
            print("[GuidedSearch] Set both start and end nodes before benchmarking.")
            return

        print(f"[GuidedSearch] Starting benchmark: "
              f"{self.start_node.name} → {self.end_node.name}")

        # Pause any running algo so it doesn't interfere
        self.running = False
        self._hide_widgets()

        # Run the harness (blocks — no animation)
        results = run_benchmark(self.start_node, self.end_node, runs=5)

        # Show report popup
        report = BenchmarkReportWindow(results)
        report.run()

        # Restore main display and widgets
        self.screen = pygame.display.set_mode((1280, 800))
        pygame.display.set_caption("Intro To AI - Project 2 - Nicholas Wise")
        self._show_widgets()

    # ------------------------------------------------------------------
    # Playback controls
    # ------------------------------------------------------------------

    def _build_algo(self):
        if self.start_node is None or self.end_node is None:
            print("[GuidedSearch] Set both start and end nodes first.")
            return False

        algo_choice = self.dropdown.getSelected()
        if algo_choice is None:
            algo_choice = 0
        if algo_choice not in ALGO_MAPPING:
            print(f"[GuidedSearch] Unknown algo choice: {algo_choice!r}")
            return False

        self.algo_class  = ALGO_MAPPING[algo_choice]
        self.active_algo = self.algo_class(self.start_node, self.end_node)
        self.finished    = False
        self.step_elapsed = 0

        self.stat_time_ms        = None
        self.stat_memory_kb      = None
        self.stat_nodes_exp      = None
        self.stat_path_length    = None
        self.stat_solution_depth = None
        self.stat_heuristic      = None
        self._algo_start_time    = time.perf_counter()
        tracemalloc.start()

        print(f"[GuidedSearch] Built {self.algo_class.__name__} "
              f"{self.start_node.name} → {self.end_node.name}")
        return True

    def on_play(self):
        if self.finished:
            return
        if self.active_algo is None:
            if not self._build_algo():
                return
        self.running = True
        self.paused  = False

    def on_pause(self):
        if self.running:
            self.running = False
            self.paused  = True

    def on_restart(self):
        self.running      = False
        self.paused       = False
        self.finished     = False
        self.step_elapsed = 0
        if self._build_algo():
            self.running = True

    def _clear_algo(self):
        self.active_algo         = None
        self.algo_class          = None
        self.running             = False
        self.paused              = False
        self.finished            = False
        self.step_elapsed        = 0
        self.stat_time_ms        = None
        self.stat_memory_kb      = None
        self.stat_nodes_exp      = None
        self.stat_path_length    = None
        self.stat_solution_depth = None
        self.stat_heuristic      = None
        self._algo_start_time    = None
        if tracemalloc.is_tracing():
            tracemalloc.stop()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        try:
            self.graph = Graph()
            self.graph.nodes = self.nodes
            self.graph.build_screen_positions(self.graph_window, 200)
        except Exception as e:
            print(f"Setup error: {e}")
            import traceback; traceback.print_exc()
            return

        while True:
            self.dt = self.clock.tick(FPS)

            # Rebuild graph if nodes were replaced by the generator
            if self._rebuild_graph:
                self.graph = Graph()
                self.graph.nodes = self.nodes
                self.graph.build_screen_positions(self.graph_window, 200)
                self._rebuild_graph = False
                print(f"[GuidedSearch] Graph rebuilt with {len(self.nodes)} nodes.")

            # Read slider — right = faster = lower delay
            self.step_delay = MAX_STEP - self.speed_slider.getValue()

            self.screen.fill(self.bg_color)
            self.control_panel_window.fill(DARK_GRAY)
            self.graph_window.fill(DARK_GRAY)
            self.stats_panel.fill(DARK_GRAY)

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._hide_widgets(); return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._hide_widgets(); return

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.set_start_mode or self.set_end_mode:
                        clicked = self.graph.get_hovered_node(
                            pygame.mouse.get_pos(), self.graph_window_pos)
                        if clicked is not None:
                            if self.set_start_mode:
                                self.start_node          = clicked
                                self.graph.start_node    = clicked
                                self.set_start_mode      = False
                                self._clear_algo()
                            else:
                                self.end_node            = clicked
                                self.graph.end_node      = clicked
                                self.set_end_mode        = False
                                self._clear_algo()

            # Step algorithm
            if self.running and self.active_algo is not None and not self.finished:
                self.step_elapsed += self.dt
                if self.step_elapsed >= self.step_delay:
                    self.step_elapsed = 0
                    done = self.active_algo.update()
                    if done:
                        self.running  = False
                        self.finished = True
                        self.stat_time_ms    = (time.perf_counter() - self._algo_start_time) * 1000
                        _, peak = tracemalloc.get_traced_memory()
                        tracemalloc.stop()
                        self.stat_memory_kb      = peak / 1024
                        self.stat_nodes_exp      = len(self.active_algo.visited_nodes)
                        self.stat_path_length    = max(0, len(self.active_algo.path) - 1)
                        self.stat_solution_depth = self.stat_path_length
                        self.stat_heuristic      = None
                        print(f"[GuidedSearch] Done. Found={self.active_algo.found}  "
                              f"Time={self.stat_time_ms:.1f}ms  "
                              f"Mem={self.stat_memory_kb:.1f}KB  "
                              f"Expanded={self.stat_nodes_exp}  "
                              f"PathLen={self.stat_path_length}")

            # Draw
            hovered_node = self.graph.get_hovered_node(
                pygame.mouse.get_pos(), self.graph_window_pos)

            self.graph.draw_graph(self.graph_window, 5, 200, hovered_node, self.active_algo)

            self.screen.blit(self.control_panel_window, (20, 40))
            self.screen.blit(self.graph_window,
                             (self.graph_window_pos[0], self.graph_window_pos[1]))
            self.screen.blit(self.stats_panel, (20, 633))

            # Status line above stats panel
            if self.active_algo is not None:
                if self.finished:
                    status = "✓ Path found" if self.active_algo.found else "✗ No path"
                elif self.paused:
                    status = "⏸ Paused"
                elif self.running:
                    status = "▶ Running…"
                else:
                    status = "Ready"
                draw_text(self.screen,
                          f"{status}  |  Frontier: {len(self.active_algo.frontier)}",
                          self.small_font, LIGHT_GRAY, 25, 622)

            # Pending params notification
            if self.pending_gen_params is not None:
                draw_text(self.screen,
                          f"⚙ Generator ready — N={self.pending_gen_params['n_nodes']}  "
                          f"b={self.pending_gen_params['branching']}  "
                          f"seed={self.pending_gen_params['seed']}",
                          self.small_font, ORANGE, 303, 622)

            # ── Control panel labels ──────────────────────────────────────
            draw_text(self.screen, "Algorithm Selection",
                      self.body_font, WHITE, 23, 10)
            draw_text(self.screen, "Graph View",
                      self.body_font, WHITE,
                      self.graph_window_pos[0], self.graph_window_pos[1] - 30)
            draw_text(self.screen, "Stats",
                      self.body_font, WHITE, 23, 615)
            draw_text(self.screen, "ESC — return to title",
                      self.body_font, (100, 100, 100), 900, 770)

            draw_text(self.screen, "Node Selection",
                      self.small_font, LIGHT_GRAY, 40, 275)
            draw_text(self.screen, "Playback",
                      self.small_font, LIGHT_GRAY, 40, 390)

            slow_x, fast_x = 40, 185
            draw_text(self.screen, "Speed",
                      self.small_font, LIGHT_GRAY, 40, 470)
            draw_text(self.screen, "Slow",
                      self.small_font, (200, 100, 100), slow_x, 515)
            draw_text(self.screen, "Fast",
                      self.small_font, (100, 200, 100), fast_x, 515)

            draw_text(self.screen, "Graph Source",
                      self.small_font, LIGHT_GRAY, 40, 528)
            draw_text(self.screen, "Benchmark",
                      self.small_font, LIGHT_GRAY, 40, 573)

            # ── Stats panel ───────────────────────────────────────────────
            STAT_X0 = 25
            COL_W   = 410
            ROW1_Y  = 643
            ROW2_Y  = 663
            ROW3_Y  = 698
            ROW4_Y  = 718

            def _fmtval(v, fmt="{}", suffix=""):
                return (fmt.format(v) + suffix) if v is not None else "—"

            draw_text(self.screen, "Time",
                      self.small_font, LIGHT_GRAY, STAT_X0, ROW1_Y)
            draw_text(self.screen, "Memory",
                      self.small_font, LIGHT_GRAY, STAT_X0 + COL_W, ROW1_Y)
            draw_text(self.screen, "Nodes Expanded",
                      self.small_font, LIGHT_GRAY, STAT_X0 + COL_W * 2, ROW1_Y)

            draw_text(self.screen, _fmtval(self.stat_time_ms, "{:.1f}", " ms"),
                      self.body_font, WHITE, STAT_X0, ROW2_Y)
            draw_text(self.screen, _fmtval(self.stat_memory_kb, "{:.1f}", " KB"),
                      self.body_font, WHITE, STAT_X0 + COL_W, ROW2_Y)
            draw_text(self.screen, _fmtval(self.stat_nodes_exp, "{}"),
                      self.body_font, WHITE, STAT_X0 + COL_W * 2, ROW2_Y)

            draw_text(self.screen, "Path Length",
                      self.small_font, LIGHT_GRAY, STAT_X0, ROW3_Y)
            draw_text(self.screen, "Solution Depth",
                      self.small_font, LIGHT_GRAY, STAT_X0 + COL_W, ROW3_Y)
            draw_text(self.screen, "Heuristic (h avg)",
                      self.small_font, LIGHT_GRAY, STAT_X0 + COL_W * 2, ROW3_Y)

            draw_text(self.screen, _fmtval(self.stat_path_length, "{}", " edges"),
                      self.body_font, WHITE, STAT_X0, ROW4_Y)
            draw_text(self.screen, _fmtval(self.stat_solution_depth, "{}"),
                      self.body_font, WHITE, STAT_X0 + COL_W, ROW4_Y)
            draw_text(self.screen, _fmtval(self.stat_heuristic, "{:.4f}"),
                      self.body_font, WHITE, STAT_X0 + COL_W * 2, ROW4_Y)

            # ── Selection mode prompts ────────────────────────────────────
            if self.set_start_mode:
                draw_text(self.screen, "Click a node to set START",
                          self.body_font, GREEN,
                          self.graph_window_pos[0], self.graph_window_pos[1] + 10)
            elif self.set_end_mode:
                draw_text(self.screen, "Click a node to set END",
                          self.body_font, RED,
                          self.graph_window_pos[0], self.graph_window_pos[1] + 10)

            if self.start_node:
                draw_text(self.screen,
                          f"Start: {self.start_node.name.replace('_', ' ')}",
                          self.small_font, GREEN, 700, 615)
            if self.end_node:
                draw_text(self.screen,
                          f"End: {self.end_node.name.replace('_', ' ')}",
                          self.small_font, RED, 900, 615)
            if hovered_node:
                draw_text(self.screen,
                          f"Hover: {hovered_node.name.replace('_', ' ')}",
                          self.small_font, WHITE, 1100, 615)

            pygame_widgets.update(events)
            pygame.display.update()