"""
generator_dialog.py

A self-contained pygame popup window that collects random graph generation
parameters from the user.  Call GeneratorDialog().run() — it blocks until
the user confirms or cancels, then returns a dict of parameters (or None on
cancel).

Returned dict keys
------------------
    n_nodes      : int   — number of nodes (N)
    branching    : float — expected branching factor (b)
    weight_min   : int   — minimum edge weight
    weight_max   : int   — maximum edge weight
    connectedness: float — 0.0–1.0 connectivity fraction
    seed         : int   — RNG seed for reproducibility
"""

import pygame
import pygame_widgets
from pygame_widgets.button  import Button
from pygame_widgets.textbox import TextBox
from pygame_widgets.slider  import Slider

# ── Palette ───────────────────────────────────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = (50,  50,  50)
MID_GRAY   = (80,  80,  80)
BG         = (30,  30,  38)
PANEL      = (42,  42,  54)
BLUE       = (43,  146, 224)
GREEN      = (90,  207, 66)
RED        = (209, 48,  48)
ACCENT     = (100, 149, 237)   # cornflower — used for section headers

W, H = 520, 600
FPS  = 60


def _draw_text(surf, text, font, color, x, y):
    surf.blit(font.render(text, True, color), (x, y))


def _draw_panel(surf, rect, color=PANEL, radius=8):
    pygame.draw.rect(surf, color, rect, border_radius=radius)


class GeneratorDialog:
    """
    Blocking popup window.  Call .run() — returns a parameter dict or None.
    """

    def __init__(self):
        # Don't call pygame.init() here — the caller already did it.
        # We just open a new display surface.
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Random Graph Generator — Parameters")

        self.clock = pygame.time.Clock()

        import os
        BASE_DIR  = os.path.dirname(__file__)
        font_path = os.path.join(BASE_DIR, "..", "fonts", "Oswald-Medium.ttf")

        self.title_font  = pygame.font.Font(font_path, 28)
        self.header_font = pygame.font.Font(font_path, 16)
        self.label_font  = pygame.font.Font(font_path, 14)

        self.result   = None   # filled on confirm
        self.running  = True

        # ── Default values (also shown as placeholder text) ────────────────
        self._defaults = {
            "n_nodes"      : "30",
            "branching"    : "3",
            "weight_min"   : "1",
            "weight_max"   : "10",
            "connectedness": "0.4",
            "seed"         : "42",
        }

        # ── Textboxes ─────────────────────────────────────────────────────
        tb_style = dict(
            fontSize=16,
            borderColour=LIGHT_GRAY,
            textColour=BLACK,
            radius=4,
            borderThickness=1,
        )

        col_l = 40          # left column x
        col_r = 280         # right column x
        tb_w  = 180
        tb_h  = 32

        # Row y positions
        r1y = 155
        r2y = 285
        r3y = 385
        r4y = 455

        self.tb_n_nodes = TextBox(
            self.screen, col_l, r1y, tb_w, tb_h,
            **tb_style
        )
        self.tb_n_nodes.setText(self._defaults["n_nodes"])

        self.tb_branching = TextBox(
            self.screen, col_r, r1y, tb_w, tb_h,
            **tb_style
        )
        self.tb_branching.setText(self._defaults["branching"])

        self.tb_weight_min = TextBox(
            self.screen, col_l, r2y, tb_w, tb_h,
            **tb_style
        )
        self.tb_weight_min.setText(self._defaults["weight_min"])

        self.tb_weight_max = TextBox(
            self.screen, col_r, r2y, tb_w, tb_h,
            **tb_style
        )
        self.tb_weight_max.setText(self._defaults["weight_max"])

        self.tb_connectedness = TextBox(
            self.screen, col_l, r3y, tb_w, tb_h,
            **tb_style
        )
        self.tb_connectedness.setText(self._defaults["connectedness"])

        self.tb_seed = TextBox(
            self.screen, col_r, r3y, tb_w, tb_h,
            **tb_style
        )
        self.tb_seed.setText(self._defaults["seed"])

        # ── Error message state ───────────────────────────────────────────
        self.error_msg = ""

        # ── Buttons ───────────────────────────────────────────────────────
        btn_y  = 530
        btn_w  = 180
        btn_h  = 42

        self.btn_confirm = Button(
            self.screen, col_l, btn_y, btn_w, btn_h,
            text="Generate Graph", fontSize=15, margin=8,
            inactiveColour=GREEN, hoverColour=(60, 180, 40),
            pressedColour=(30, 140, 20), radius=5,
            textColour=WHITE,
            onClick=self._on_confirm,
        )

        self.btn_cancel = Button(
            self.screen, col_r, btn_y, btn_w, btn_h,
            text="Cancel", fontSize=15, margin=8,
            inactiveColour=MID_GRAY, hoverColour=(100, 100, 100),
            pressedColour=(60, 60, 60), radius=5,
            textColour=WHITE,
            onClick=self._on_cancel,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _all_widgets(self):
        return [
            self.tb_n_nodes, self.tb_branching,
            self.tb_weight_min, self.tb_weight_max,
            self.tb_connectedness, self.tb_seed,
            self.btn_confirm, self.btn_cancel,
        ]

    def _hide_widgets(self):
        for w in self._all_widgets():
            w.hide()

    def _parse(self):
        """
        Validate and parse all textbox inputs.
        Returns a dict on success, sets self.error_msg and returns None on failure.
        """
        self.error_msg = ""
        raw = {
            "n_nodes"      : self.tb_n_nodes.getText().strip(),
            "branching"    : self.tb_branching.getText().strip(),
            "weight_min"   : self.tb_weight_min.getText().strip(),
            "weight_max"   : self.tb_weight_max.getText().strip(),
            "connectedness": self.tb_connectedness.getText().strip(),
            "seed"         : self.tb_seed.getText().strip(),
        }

        # Fall back to defaults for empty fields
        for k, v in raw.items():
            if v == "":
                raw[k] = self._defaults[k]

        try:
            n = int(raw["n_nodes"])
            if n < 2:
                raise ValueError("N must be ≥ 2")
        except ValueError as e:
            self.error_msg = f"Nodes: {e}"
            return None

        try:
            b = float(raw["branching"])
            if b <= 0:
                raise ValueError("must be > 0")
        except ValueError as e:
            self.error_msg = f"Branching factor: {e}"
            return None

        try:
            wmin = int(raw["weight_min"])
            wmax = int(raw["weight_max"])
            if wmin < 0 or wmax < 0:
                raise ValueError("weights must be ≥ 0")
            if wmin > wmax:
                raise ValueError("min must be ≤ max")
        except ValueError as e:
            self.error_msg = f"Edge weights: {e}"
            return None

        try:
            c = float(raw["connectedness"])
            if not (0.0 < c <= 1.0):
                raise ValueError("must be in (0, 1]")
        except ValueError as e:
            self.error_msg = f"Connectedness: {e}"
            return None

        try:
            seed = int(raw["seed"])
        except ValueError:
            self.error_msg = "Seed: must be an integer"
            return None

        return {
            "n_nodes"      : n,
            "branching"    : b,
            "weight_min"   : wmin,
            "weight_max"   : wmax,
            "connectedness": c,
            "seed"         : seed,
        }

    def _on_confirm(self):
        params = self._parse()
        if params is not None:
            self.result  = params
            self.running = False

    def _on_cancel(self):
        self.result  = None
        self.running = False

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self):
        self.screen.fill(BG)

        # Title bar
        _draw_panel(self.screen, pygame.Rect(0, 0, W, 70), PANEL, radius=0)
        _draw_text(self.screen, "Random Graph Generator",
                   self.title_font, WHITE, 20, 18)

        # ── Section: Graph Structure ───────────────────────────────────────
        _draw_panel(self.screen, pygame.Rect(20, 90, W - 40, 130), PANEL)
        _draw_text(self.screen, "GRAPH STRUCTURE",
                   self.header_font, ACCENT, 32, 98)

        _draw_text(self.screen, "Number of Nodes (N)",
                   self.label_font, LIGHT_GRAY, 40, 135)
        _draw_text(self.screen, "Branching Factor (b)",
                   self.label_font, LIGHT_GRAY, 280, 135)

        # ── Section: Edge Weights ──────────────────────────────────────────
        _draw_panel(self.screen, pygame.Rect(20, 230, W - 40, 130), PANEL)
        _draw_text(self.screen, "EDGE WEIGHTS  (uniform distribution)",
                   self.header_font, ACCENT, 32, 238)

        _draw_text(self.screen, "Min Weight",
                   self.label_font, LIGHT_GRAY, 40, 265)
        _draw_text(self.screen, "Max Weight",
                   self.label_font, LIGHT_GRAY, 280, 265)

        # ── Section: Connectivity & Seed ──────────────────────────────────
        _draw_panel(self.screen, pygame.Rect(20, 330, W - 40, 130), PANEL)
        _draw_text(self.screen, "CONNECTIVITY & REPRODUCIBILITY",
                   self.header_font, ACCENT, 32, 338)

        _draw_text(self.screen, "Connectedness (0–1)",
                   self.label_font, LIGHT_GRAY, 40, 365)
        _draw_text(self.screen, "Random Seed",
                   self.label_font, LIGHT_GRAY, 280, 365)

        # ── Hint row under each field ──────────────────────────────────────
        hint_col = (90, 140, 90)
        _draw_text(self.screen, "integer ≥ 2",
                   self.label_font, hint_col, 40, 192)
        _draw_text(self.screen, "avg neighbors per node",
                   self.label_font, hint_col, 280, 192)
        _draw_text(self.screen, "integer ≥ 0",
                   self.label_font, hint_col, 40, 322)
        _draw_text(self.screen, "integer ≥ min",
                   self.label_font, hint_col, 280, 322)
        _draw_text(self.screen, "fraction of max edges",
                   self.label_font, hint_col, 40, 422)
        _draw_text(self.screen, "any integer",
                   self.label_font, hint_col, 280, 422)

        # ── Error message ──────────────────────────────────────────────────
        if self.error_msg:
            _draw_text(self.screen, f"⚠  {self.error_msg}",
                       self.label_font, RED, 40, 505)

    # ── Main blocking loop ────────────────────────────────────────────────────

    def run(self):
        """
        Block until the user confirms or cancels.
        Returns a parameter dict, or None on cancel.
        """
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._on_cancel()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._on_cancel()
                    if event.key == pygame.K_RETURN:
                        self._on_confirm()

            self._draw()
            pygame_widgets.update(events)
            pygame.display.update()
            self.clock.tick(FPS)

        self._hide_widgets()
        return self.result
