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

# ── Color palette ─────────────────────────────────────────────────────────────
# These are used for UI elements in the control panel and status bar.
# Node/edge colors are defined separately in graph.py so the graph renderer
# owns its own color scheme.
WHITE      = (255, 255, 255)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = (50,  50,  50)
BLUE       = (43,  146, 224)
GREEN      = (90,  207, 66)
RED        = (209, 48,  48)
YELLOW     = (227, 197, 91)
ORANGE     = (220, 140, 40)

# ── File paths ────────────────────────────────────────────────────────────────
# Locate the data directory relative to this source file so the program works
# regardless of the working directory it is launched from.
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

COORD_FILE = os.path.join(DATA_DIR, "coordinates.csv")  # city lat/lon
ADJ_FILE   = os.path.join(DATA_DIR, "Adjacencies.txt")  # city connections

# ── Timing constants ──────────────────────────────────────────────────────────
FPS          = 60           # target frame rate for the main display loop
DEFAULT_STEP = 300          # default ms between algorithm steps (medium speed)
MIN_STEP     = 0            # fastest possible (step every frame)
MAX_STEP     = 1000         # slowest possible (one step per second)

# ── Algorithm registry ────────────────────────────────────────────────────────
# Maps the dropdown's integer value to the corresponding algorithm class.
# Adding a new algorithm only requires adding an entry here and to the dropdown.
ALGO_MAPPING = {
    0: DFS,
    1: BFS,
    2: ID_DFS,
    3: GreedyBestFirst,
    4: AStar,
}


class GuidedSearch:
    """
    Main controller for the guided search visualization screen (Project 2).

    Responsibilities:
      - Own the pygame display and all pygame_widgets for this screen
      - Load and display the preset city graph (or a generated graph)
      - Step the selected search algorithm frame-by-frame at a user-controlled speed
      - Collect and display per-run stats (time, memory, nodes expanded, path length)
      - Launch sub-windows for graph generation (GeneratorDialog) and
        benchmarking (BenchmarkReportWindow)

    Lifecycle:
      GuidedSearch.__init__() creates all widgets (positions are fixed at
      construction time by pygame_widgets).
      GuidedSearch.run() enters the main event/draw loop and blocks until
      the user presses ESC or closes the window.
    """

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Intro To AI - Project 2 - Nicholas Wise")
        pygame.mouse.set_visible(True)

        BASE_DIR  = os.path.dirname(__file__)
        FONT_PATH = os.path.join(BASE_DIR, "..", "fonts", "Oswald-Medium.ttf")

        self.clock    = pygame.time.Clock()
        self.screen   = pygame.display.set_mode((1280, 800))
        self.bg_color = (25, 25, 25)

        # dt holds the milliseconds elapsed since the previous frame.
        # It is assigned at the very top of each loop iteration by clock.tick()
        # so that all time-dependent logic uses a fresh, accurate value.
        self.dt = 0

        self.body_font  = pygame.font.Font(FONT_PATH, 20)
        self.small_font = pygame.font.Font(FONT_PATH, 15)

        # ── Surface layout ────────────────────────────────────────────────
        # The 1280x800 screen is divided into three non-overlapping regions,
        # each backed by its own pygame.Surface:
        #
        #   ┌─────────────┬──────────────────────────────┐  y=40
        #   │ Control     │ Graph view (950×590)          │
        #   │ panel       │                               │
        #   │ (260×590)   │                               │
        #   ├─────────────┴──────────────────────────────┤  y=633
        #   │ Stats panel (1240×165)                      │
        #   └────────────────────────────────────────────┘  y=798
        #
        # Using separate surfaces means drawing to one region cannot
        # accidentally overwrite another.
        self.control_panel_dimensions = (260, 590)
        self.control_panel_window = pygame.Surface(self.control_panel_dimensions)

        self.graph_window_dimensions = (950, 590)
        self.graph_window_pos = [303, 40]   # top-left corner on self.screen
        self.graph_window = pygame.Surface(self.graph_window_dimensions)

        self.stats_panel_dimensions = (1240, 165)
        self.stats_panel = pygame.Surface(self.stats_panel_dimensions)

        # ── Graph data ────────────────────────────────────────────────────
        # Load the preset Kansas city graph from disk.
        # self.nodes is replaced wholesale when the user generates a random graph.
        self.nodes: list[Node] = import_graph(COORD_FILE, ADJ_FILE)
        self.node_map: dict[str, Node] = {n.name: n for n in self.nodes}

        # ── Generator state ───────────────────────────────────────────────
        # Stores the last confirmed parameters from GeneratorDialog so they
        # can be shown in the status bar as a reminder of what is loaded.
        self.pending_gen_params: dict | None = None

        # _rebuild_graph is a fallback flag — set True when nodes change so
        # the main loop can reconstruct the Graph object if needed.
        self._rebuild_graph = False

        # self.graph is an instance variable (not a local inside run()) so
        # that button callbacks like on_generate_graph() can directly replace
        # it without needing a deferred flag mechanism.
        self.graph: Graph | None = None

        # ── Node selection state ──────────────────────────────────────────
        self.start_node: Node | None = None
        self.end_node:   Node | None = None

        # When either flag is True, the next mouse click on the graph view
        # is interpreted as a node selection rather than being ignored.
        self.set_start_mode = False
        self.set_end_mode   = False

        # ── Algorithm playback state ──────────────────────────────────────
        self.active_algo  = None   # live algorithm instance currently being stepped
        self.algo_class   = None   # stored so restart can re-instantiate cleanly
        self.running      = False  # True while the algorithm is actively stepping
        self.paused       = False  # True when the user has paused mid-run
        self.finished     = False  # True once the algorithm signals completion
        self.step_elapsed = 0      # accumulated ms since the last algorithm step
        self.step_delay   = DEFAULT_STEP  # ms between steps; driven by the slider

        # ── Per-run stats ─────────────────────────────────────────────────
        # All stats default to None and render as "—" until a run completes.
        self.stat_time_ms        = None  # wall-clock ms via time.perf_counter()
        self.stat_memory_kb      = None  # peak process memory via tracemalloc
        self.stat_nodes_exp      = None  # total nodes popped from the frontier
        self.stat_path_length    = None  # number of edges in the solution path
        self.stat_solution_depth = None  # depth of goal node (= path_length for unit cost)
        self.stat_heuristic      = None  # placeholder for avg h(n) — not yet wired
        self._algo_start_time    = None  # perf_counter snapshot when algo was started

        # ── Widget layout ─────────────────────────────────────────────────
        # All pygame_widgets are created with fixed screen-space (y) positions.
        # The layout uses a consistent formula:
        #
        #   _XX_LY  = y-coordinate of the section divider/label line
        #   widget  = placed at _XX_LY + W_OFF
        #
        # This guarantees a uniform label-to-widget gap across all sections,
        # and makes the whole panel easy to re-space by adjusting W_OFF alone.

        BTN_H = 34   # standard button height in pixels
        GAP   = 4    # vertical gap between stacked buttons in the same section
        W_OFF = 28   # pixels from section label top edge to widget top edge

        # ── Section: Algorithm ────────────────────────────────────────────
        # Dropdown value (0–4) is mapped to an algorithm class via ALGO_MAPPING.
        # getSelected() returns None before the user interacts with the widget,
        # so _build_algo() defaults to DFS (0) in that case.
        _DD_LY = 50
        self.dropdown = Dropdown(
            self.screen, 40, _DD_LY + W_OFF, 220, 40, name='Select Algorithm',
            choices=['Depth-First Search', 'Breadth-First Search',
                     'Iterative Deepening DFS', 'Best-First Search', 'A*'],
            borderRadius=1, colour=LIGHT_GRAY, values=[0, 1, 2, 3, 4],
            direction='down', textHAlign='left',
        )

        # ── Section: Node Setup ───────────────────────────────────────────
        # Pressing either button enters "pick mode". The user then clicks
        # a node on the graph to assign it. Selecting a new node automatically
        # clears any existing algorithm state so stale results never persist.
        _NS_LY = 138
        self.set_start_node_button = Button(
            self.screen, 40, _NS_LY + W_OFF, 220, BTN_H,
            text='Set Start Node', fontSize=15, margin=10,
            inactiveColour=WHITE, hoverColour=(150, 0, 0),
            pressedColour=GREEN, radius=3,
            onClick=self.set_start_select_mode,
        )
        self.set_end_node_button = Button(
            self.screen, 40, _NS_LY + W_OFF + BTN_H + GAP, 220, BTN_H,
            text='Set End Node', fontSize=15, margin=10,
            inactiveColour=WHITE, hoverColour=(150, 0, 0),
            pressedColour=GREEN, radius=3,
            onClick=self.set_end_select_mode,
        )

        # ── Section: Playback ─────────────────────────────────────────────
        # Three buttons share one row at equal width with a small gap between.
        # Total width = 3 × 68 + 2 × 8 = 220 px (matches the other widgets).
        #
        # Play  — starts a fresh algo on first press, or resumes from pause
        # Pause — freezes stepping without discarding frontier/visited state
        # Reset — re-instantiates the algo from scratch and auto-plays
        _PB_LY = 270
        _btn_w = 68
        _btn_g = 8
        self.play_button = Button(
            self.screen, 40, _PB_LY + W_OFF, _btn_w, BTN_H,
            text='▶  Play', fontSize=14, margin=6,
            inactiveColour=WHITE, hoverColour=(0, 160, 0),
            pressedColour=GREEN, radius=3,
            onClick=self.on_play,
        )
        self.pause_button = Button(
            self.screen, 40 + _btn_w + _btn_g, _PB_LY + W_OFF, _btn_w, BTN_H,
            text='⏸ Pause', fontSize=14, margin=6,
            inactiveColour=WHITE, hoverColour=(180, 140, 0),
            pressedColour=YELLOW, radius=3,
            onClick=self.on_pause,
        )
        self.restart_button = Button(
            self.screen, 40 + (_btn_w + _btn_g) * 2, _PB_LY + W_OFF, _btn_w, BTN_H,
            text='↺ Reset', fontSize=14, margin=6,
            inactiveColour=WHITE, hoverColour=(150, 0, 0),
            pressedColour=RED, radius=3,
            onClick=self.on_restart,
        )

        # ── Section: Speed ────────────────────────────────────────────────
        # The slider value is read every frame and INVERTED to produce step_delay:
        #   delay = MAX_STEP - slider_value
        # So dragging right (higher slider value) = shorter delay = faster stepping.
        # initial = MAX_STEP - DEFAULT_STEP positions the handle at medium speed.
        _SP_LY = 362
        self.speed_slider = Slider(
            self.screen, 40, _SP_LY + W_OFF, 220, 16,
            min=MIN_STEP, max=MAX_STEP,
            step=10, initial=MAX_STEP - DEFAULT_STEP,
            colour=DARK_GRAY, handleColour=WHITE,
        )

        # ── Section: Graph Source ─────────────────────────────────────────
        # Opens GeneratorDialog to collect graph parameters (N, branching factor,
        # edge weight range, connectedness, seed), then immediately generates
        # and displays the new graph.
        _GS_LY = 442
        self.gen_graph_button = Button(
            self.screen, 40, _GS_LY + W_OFF, 220, BTN_H,
            text='⚙  Generate New Graph', fontSize=13, margin=8,
            inactiveColour=ORANGE, hoverColour=(180, 100, 20),
            pressedColour=(140, 70, 10), radius=3,
            textColour=WHITE,
            onClick=self.on_generate_graph,
        )

        # ── Section: Benchmark ────────────────────────────────────────────
        # Runs all 5 algorithms synchronously (no animation) against the current
        # start/end pair, then opens BenchmarkReportWindow with a comparison
        # table showing time, memory, nodes expanded, path length, and optimality.
        _BM_LY = 534
        self.benchmark_button = Button(
            self.screen, 40, _BM_LY + W_OFF, 220, BTN_H,
            text='📊  Run Benchmark', fontSize=13, margin=8,
            inactiveColour=(60, 100, 160), hoverColour=(40, 80, 140),
            pressedColour=(25, 60, 120), radius=3,
            textColour=WHITE,
            onClick=self.on_benchmark,
        )

    # ── Widget visibility helpers ──────────────────────────────────────────────

    def _hide_widgets(self):
        """
        Hide all pygame_widgets before opening a sub-window.

        pygame_widgets draw themselves directly onto the display surface inside
        pygame_widgets.update(). If we open a new pygame window without hiding
        them first they continue rendering on top of the sub-window's content.
        """
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

    def set_start_select_mode(self):
        """Enter start-node pick mode. The next graph click sets the start node."""
        self.set_start_mode = True
        self.set_end_mode   = False

    def set_end_select_mode(self):
        """Enter end-node pick mode. The next graph click sets the end node."""
        self.set_end_mode   = True
        self.set_start_mode = False

    # ── Graph generation ───────────────────────────────────────────────────────

    def on_generate_graph(self):
        """
        Open the parameter dialog, generate a new random graph, and rebuild
        the display so the new graph is visible on the next frame.

        Flow:
          1. Hide widgets — prevents them bleeding onto the dialog surface.
          2. Open GeneratorDialog (blocks until the user confirms or cancels).
          3. Restore the main 1280×800 display and re-show widgets.
          4. If confirmed: call generate_graph(), replace self.nodes, rebuild
             self.graph immediately. No deferred flag needed because self.graph
             is an instance variable accessible from any method.
          5. Clear start/end nodes and algorithm state — the old nodes no
             longer exist in the new graph.
        """
        self._hide_widgets()

        dialog = GeneratorDialog()
        params = dialog.run()   # blocks until confirmed or cancelled

        # GeneratorDialog resizes the pygame window — restore it
        self.screen = pygame.display.set_mode((1280, 800))
        pygame.display.set_caption("Intro To AI - Project 2 - Nicholas Wise")
        self._show_widgets()

        if params is not None:
            self.pending_gen_params = params
            print(f"[GuidedSearch] Generator params received: {params}")

            # Replace the node list with a freshly generated random graph
            self.nodes    = generate_graph(params)
            self.node_map = {n.name: n for n in self.nodes}

            # Old start/end nodes belong to the previous graph — discard them
            self.start_node = None
            self.end_node   = None
            self._clear_algo()

            # Rebuild self.graph immediately so the very next frame renders
            # the new graph correctly
            self.graph = Graph()
            self.graph.nodes = self.nodes
            self.graph.build_screen_positions(self.graph_window, 200)
            self._rebuild_graph = False
            print(f"[GuidedSearch] Graph rebuilt with {len(self.nodes)} nodes.")
        else:
            print("[GuidedSearch] Generator dialog cancelled.")

    # ── Benchmarking ───────────────────────────────────────────────────────────

    def on_benchmark(self):
        """
        Run all 5 algorithms to completion and open a comparison report popup.

        Unlike the step-by-step visualizer, the benchmark executes each algorithm
        in a tight while-loop with no animation delay, allowing accurate wall-clock
        timing. tracemalloc captures peak memory inside benchmark.py.

        Each algorithm is run 5 times and mean ± std are reported. The optimality
        marker flags whichever found path has the lowest cost.

        Uses the same hide/show/restore display pattern as on_generate_graph().
        """
        if self.start_node is None or self.end_node is None:
            print("[GuidedSearch] Set both start and end nodes before benchmarking.")
            return

        print(f"[GuidedSearch] Starting benchmark: "
              f"{self.start_node.name} → {self.end_node.name}")

        self.running = False   # stop any live animation so it doesn't interfere
        self._hide_widgets()

        # run_benchmark() blocks here — 5 algorithms × 5 runs each
        results = run_benchmark(self.start_node, self.end_node, runs=5)

        # BenchmarkReportWindow blocks until the user closes it
        report = BenchmarkReportWindow(results)
        report.run()

        self.screen = pygame.display.set_mode((1280, 800))
        pygame.display.set_caption("Intro To AI - Project 2 - Nicholas Wise")
        self._show_widgets()

    # ── Algorithm playback ─────────────────────────────────────────────────────

    def _build_algo(self):
        """
        Instantiate the selected algorithm class and reset all stat fields.

        Returns True on success. Returns False (and prints a message) if:
          - start_node or end_node is not set
          - the dropdown selection is unrecognised

        Also starts tracemalloc so memory tracking begins from the moment the
        algorithm object is created, not just from the first update() call.
        """
        if self.start_node is None or self.end_node is None:
            print("[GuidedSearch] Set both start and end nodes first.")
            return False

        algo_choice = self.dropdown.getSelected()
        if algo_choice is None:
            algo_choice = 0   # default to DFS if dropdown untouched
        if algo_choice not in ALGO_MAPPING:
            print(f"[GuidedSearch] Unknown algo choice: {algo_choice!r}")
            return False

        self.algo_class  = ALGO_MAPPING[algo_choice]
        self.active_algo = self.algo_class(self.start_node, self.end_node)
        self.finished    = False
        self.step_elapsed = 0

        # Clear stats from any previous run so the panel shows "—" until
        # this run completes
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
        """
        Start or resume the algorithm.

          - If finished: do nothing (user must hit Reset first).
          - If no algorithm built yet: call _build_algo() then start.
          - If paused: simply resume by setting running=True.
        """
        if self.finished:
            return
        if self.active_algo is None:
            if not self._build_algo():
                return
        self.running = True
        self.paused  = False

    def on_pause(self):
        """
        Pause mid-run without discarding any algorithm state.
        The frontier, visited set, and came_from map are preserved so the
        run can resume exactly where it left off.
        """
        if self.running:
            self.running = False
            self.paused  = True

    def on_restart(self):
        """
        Re-instantiate the algorithm from scratch using the same start/end
        nodes and currently selected algorithm, then immediately begin playing.
        """
        self.running      = False
        self.paused       = False
        self.finished     = False
        self.step_elapsed = 0
        if self._build_algo():
            self.running = True

    def _clear_algo(self):
        """
        Wipe all algorithm and stat state.

        Called whenever the underlying graph changes (new generation or new
        node selection) to ensure stale frontier/path coloring from the
        previous graph is never drawn over the new one.
        """
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

    # ── Main loop ──────────────────────────────────────────────────────────────

    def run(self):
        """
        Enter the main event/draw loop. Blocks until ESC or window close.

        Each frame follows this sequence:
          1. clock.tick(FPS)       — cap frame rate, capture dt
          2. Rebuild graph         — if _rebuild_graph flag is set
          3. Read speed slider     — update step_delay
          4. Clear surfaces        — fill all surfaces with background color
          5. Process events        — quit, keyboard, node-pick mouse clicks
          6. Step algorithm        — advance one step if interval elapsed
          7. Draw everything       — graph, UI labels, stats panel
          8. pygame_widgets.update — widgets draw themselves, callbacks fire
          9. pygame.display.update — push frame to screen
        """
        try:
            self.graph = Graph()
            self.graph.nodes = self.nodes
            self.graph.build_screen_positions(self.graph_window, 200)
        except Exception as e:
            print(f"Setup error: {e}")
            import traceback; traceback.print_exc()
            return

        while True:

            # ── 1. Tick ───────────────────────────────────────────────────
            # Must be called FIRST so self.dt is accurate for the whole frame.
            # Earlier versions called clock.get_time() mid-loop which returned
            # stale values and caused the step accumulator to never fire.
            self.dt = self.clock.tick(FPS)

            # ── 2. Graph rebuild ──────────────────────────────────────────
            if self._rebuild_graph:
                self.graph = Graph()
                self.graph.nodes = self.nodes
                self.graph.build_screen_positions(self.graph_window, 200)
                self._rebuild_graph = False
                print(f"[GuidedSearch] Graph rebuilt with {len(self.nodes)} nodes.")

            # ── 3. Speed slider ───────────────────────────────────────────
            # Invert: right = high slider value = low delay = fast stepping
            self.step_delay = MAX_STEP - self.speed_slider.getValue()

            # ── 4. Clear surfaces ─────────────────────────────────────────
            self.screen.fill(self.bg_color)
            self.control_panel_window.fill(DARK_GRAY)
            self.graph_window.fill(DARK_GRAY)
            self.stats_panel.fill(DARK_GRAY)

            # ── 5. Events ─────────────────────────────────────────────────
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._hide_widgets(); return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._hide_widgets(); return

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    # Only intercept clicks when in node-pick mode.
                    # get_hovered_node() snaps to the nearest node within a
                    # pixel threshold, returning None if nothing is close enough.
                    if self.set_start_mode or self.set_end_mode:
                        clicked = self.graph.get_hovered_node(
                            pygame.mouse.get_pos(), self.graph_window_pos)
                        if clicked is not None:
                            if self.set_start_mode:
                                self.start_node          = clicked
                                self.graph.start_node    = clicked  # for draw coloring
                                self.set_start_mode      = False
                                self._clear_algo()
                            else:
                                self.end_node            = clicked
                                self.graph.end_node      = clicked
                                self.set_end_mode        = False
                                self._clear_algo()

            # ── 6. Algorithm step ─────────────────────────────────────────
            # Accumulate elapsed ms each frame. When the total crosses
            # step_delay, call update() once and reset the accumulator.
            # This decouples algorithm speed from frame rate — the algorithm
            # advances at the user-selected interval regardless of FPS.
            if self.running and self.active_algo is not None and not self.finished:
                self.step_elapsed += self.dt
                if self.step_elapsed >= self.step_delay:
                    self.step_elapsed = 0
                    done = self.active_algo.update()
                    if done:
                        # Capture all stats the moment the algorithm finishes
                        self.running  = False
                        self.finished = True
                        self.stat_time_ms = (
                            time.perf_counter() - self._algo_start_time
                        ) * 1000
                        _, peak = tracemalloc.get_traced_memory()
                        tracemalloc.stop()
                        self.stat_memory_kb      = peak / 1024
                        self.stat_nodes_exp      = len(self.active_algo.visited_nodes)
                        # Edges in path = nodes - 1
                        self.stat_path_length    = max(0, len(self.active_algo.path) - 1)
                        # For unit-cost graphs, depth equals path length
                        self.stat_solution_depth = self.stat_path_length
                        self.stat_heuristic      = None   # placeholder, not yet wired
                        print(f"[GuidedSearch] Done. Found={self.active_algo.found}  "
                              f"Time={self.stat_time_ms:.1f}ms  "
                              f"Mem={self.stat_memory_kb:.1f}KB  "
                              f"Expanded={self.stat_nodes_exp}  "
                              f"PathLen={self.stat_path_length}")

            # ── 7. Draw ───────────────────────────────────────────────────

            # Resolve hover before drawing so draw_graph() can highlight it.
            hovered_node = self.graph.get_hovered_node(
                pygame.mouse.get_pos(), self.graph_window_pos)

            # draw_graph() colors each node based on the algorithm's live
            # visited_nodes, frontier, and path lists, so the graph updates
            # visually every frame as the algorithm steps.
            self.graph.draw_graph(
                self.graph_window, 5, 200, hovered_node, self.active_algo)

            # Blit sub-surfaces onto the main screen at their fixed positions
            self.screen.blit(self.control_panel_window, (20, 40))
            self.screen.blit(self.graph_window,
                             (self.graph_window_pos[0], self.graph_window_pos[1]))
            self.screen.blit(self.stats_panel, (20, 633))

            # ── Status line ───────────────────────────────────────────────
            # Shows current algorithm state and live frontier size in the
            # strip between the graph view and the stats panel.
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

            # ── Generator params notification ──────────────────────────────
            # Remind the user which generated graph is currently loaded.
            if self.pending_gen_params is not None:
                draw_text(self.screen,
                          f"⚙ Generator ready — N={self.pending_gen_params['n_nodes']}  "
                          f"b={self.pending_gen_params['branching']}  "
                          f"seed={self.pending_gen_params['seed']}",
                          self.small_font, ORANGE, 303, 622)

            # ── Control panel: section dividers and labels ─────────────────
            # Each section gets a 1px horizontal rule followed by a small
            # label 4px below. Label y-values match the _XX_LY constants
            # defined in __init__ so the labels always sit directly above
            # their corresponding widgets.
            DIVIDER_X1  = 25
            DIVIDER_X2  = 255
            DIV_COLOR   = (70, 70, 80)
            LABEL_COLOR = (130, 130, 145)

            def _section(label, y):
                """Draw a faint rule then a section label just below it."""
                pygame.draw.line(self.screen, DIV_COLOR,
                                 (DIVIDER_X1, y), (DIVIDER_X2, y), 1)
                draw_text(self.screen, label, self.small_font, LABEL_COLOR, 40, y + 4)

            draw_text(self.screen, "Algorithm Selection",
                      self.body_font, WHITE, 23, 10)

            _section("Algorithm",     50)
            _section("Node Setup",   138)
            _section("Playback",     270)
            _section("Speed",        362)
            _section("Graph Source", 442)
            _section("Benchmark",    534)

            # Slow/Fast labels sit just below the slider track (slider y=390, h=16)
            draw_text(self.screen, "Slow",
                      self.small_font, (200, 100, 100), 40,  412)
            draw_text(self.screen, "Fast",
                      self.small_font, (100, 200, 100), 185, 412)

            draw_text(self.screen, "Graph View",
                      self.body_font, WHITE,
                      self.graph_window_pos[0], self.graph_window_pos[1] - 30)
            draw_text(self.screen, "Stats",
                      self.body_font, WHITE, 23, 615)
            draw_text(self.screen, "ESC — return to title",
                      self.body_font, (100, 100, 100), 900, 770)

            # ── Stats panel ────────────────────────────────────────────────
            # Two rows of three columns. All values display "—" until a run
            # completes (_fmtval() returns "—" for None).
            #
            # Row 1: Time  |  Memory  |  Nodes Expanded
            # Row 2: Path Length  |  Solution Depth  |  Heuristic (h avg)
            STAT_X0 = 25    # left edge of first column (screen coords)
            COL_W   = 410   # column width
            ROW1_Y  = 643   # y for row 1 labels
            ROW2_Y  = 663   # y for row 1 values
            ROW3_Y  = 698   # y for row 2 labels
            ROW4_Y  = 718   # y for row 2 values

            def _fmtval(v, fmt="{}", suffix=""):
                """Format a stat value, or return '—' if the value is None."""
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

            # ── Node pick mode prompts ─────────────────────────────────────
            # Overlay a colored instruction on the graph view so the user
            # always knows what is expected when in pick mode.
            if self.set_start_mode:
                draw_text(self.screen, "Click a node to set START",
                          self.body_font, GREEN,
                          self.graph_window_pos[0], self.graph_window_pos[1] + 10)
            elif self.set_end_mode:
                draw_text(self.screen, "Click a node to set END",
                          self.body_font, RED,
                          self.graph_window_pos[0], self.graph_window_pos[1] + 10)

            # ── Selected node names ────────────────────────────────────────
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

            # ── 8. Widget update ──────────────────────────────────────────
            # pygame_widgets.update() lets each widget process hover/click
            # state and draw itself onto self.screen. Button onClick callbacks
            # (on_play, on_generate_graph, on_benchmark, etc.) fire inside
            # this call — which is why self.graph must be an instance variable
            # rather than a local: locals inside run() are out of scope here.
            pygame_widgets.update(events)

            # ── 9. Display flip ───────────────────────────────────────────
            pygame.display.update()