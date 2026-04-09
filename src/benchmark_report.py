"""
benchmark_report.py

Pygame popup window that renders a benchmark comparison report.
Call BenchmarkReportWindow(results).run() — blocks until the user closes it.
"""

import pygame
import pygame_widgets
from pygame_widgets.button import Button
from benchmark import BenchmarkResults

# ── Palette ───────────────────────────────────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
BG         = (25,  25,  30)
PANEL      = (38,  38,  48)
HEADER_BG  = (48,  48,  62)
ROW_A      = (32,  32,  42)
ROW_B      = (38,  38,  50)
BORDER     = (60,  60,  80)
LIGHT_GRAY = (180, 180, 180)
MID_GRAY   = (110, 110, 120)
DIM_GRAY   = (70,  70,  80)
GREEN      = (90,  207, 66)
YELLOW     = (227, 197, 91)
RED        = (209, 48,  48)
BLUE       = (43,  146, 224)
ORANGE     = (220, 140, 40)

W, H = 900, 620
FPS  = 60

# Column layout: (header label, width, alignment)
# alignment: 'l' = left, 'r' = right, 'c' = center
COLUMNS = [
    ("Algorithm",      140, 'l'),
    ("Time mean",       95, 'r'),
    ("Time ±std",       80, 'r'),
    ("Mem mean",        85, 'r'),
    ("Mem ±std",        75, 'r'),
    ("Nodes exp",       80, 'r'),
    ("Path len",        70, 'r'),
    ("Path cost",       75, 'r'),
    ("Optimal",         65, 'c'),
]

ROW_H       = 36
HEADER_H    = 38
TABLE_TOP   = 140    # y where the table header starts
TABLE_PAD_X = 20


def _draw_text(surf, text, font, color, x, y, align='l', max_w=None):
    img = font.render(str(text), True, color)
    if max_w and img.get_width() > max_w:
        # Truncate — re-render with ellipsis
        while img.get_width() > max_w and len(text) > 1:
            text = text[:-1]
        img = font.render(text + "…", True, color)
    if align == 'r':
        x = x - img.get_width()
    elif align == 'c':
        x = x - img.get_width() // 2
    surf.blit(img, (x, y))


class BenchmarkReportWindow:
    def __init__(self, results: BenchmarkResults):
        self.results = results
        self.running = True

        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Benchmark Report")
        self.clock = pygame.time.Clock()

        import os
        BASE_DIR  = os.path.dirname(__file__)
        font_path = os.path.join(BASE_DIR, "..", "fonts", "Oswald-Medium.ttf")

        self.title_font  = pygame.font.Font(font_path, 26)
        self.header_font = pygame.font.Font(font_path, 14)
        self.cell_font   = pygame.font.Font(font_path, 15)
        self.small_font  = pygame.font.Font(font_path, 13)

        self.close_button = Button(
            self.screen, W - 130, H - 54, 110, 36,
            text="Close", fontSize=14, margin=8,
            inactiveColour=LIGHT_GRAY, hoverColour=(200, 200, 200),
            pressedColour=WHITE, radius=4,
            textColour=BLACK,
            onClick=self._on_close,
        )

    def _on_close(self):
        self.running = False

    def _hide_widgets(self):
        self.close_button.hide()

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _col_x_positions(self):
        """Return the left-edge x for each column."""
        xs = []
        x = TABLE_PAD_X
        for _, w, _ in COLUMNS:
            xs.append(x)
            x += w
        return xs

    def _draw_table_header(self):
        col_xs = self._col_x_positions()
        y = TABLE_TOP

        # Header background
        pygame.draw.rect(self.screen, HEADER_BG,
                         pygame.Rect(0, y, W, HEADER_H))
        pygame.draw.line(self.screen, BORDER, (0, y + HEADER_H - 1),
                         (W, y + HEADER_H - 1), 1)

        for i, (label, col_w, align) in enumerate(COLUMNS):
            x = col_xs[i]
            if align == 'r':
                tx = x + col_w - 4
            elif align == 'c':
                tx = x + col_w // 2
            else:
                tx = x + 4
            _draw_text(self.screen, label, self.header_font,
                       MID_GRAY, tx, y + 11, align)

        # Vertical dividers
        for i, x in enumerate(col_xs[1:], 1):
            pygame.draw.line(self.screen, BORDER,
                             (x - 1, y), (x - 1, y + HEADER_H), 1)

    def _draw_table_rows(self):
        col_xs  = self._col_x_positions()
        results = self.results.algo_results

        # Find fastest time and lowest memory for highlighting
        found_results = [r for r in results if r.found]
        best_time  = min((r.time_mean  for r in found_results), default=None)
        best_mem   = min((r.mem_mean   for r in found_results), default=None)
        best_nodes = min((r.nodes_mean for r in found_results), default=None)

        for row_i, result in enumerate(results):
            y      = TABLE_TOP + HEADER_H + row_i * ROW_H
            row_bg = ROW_A if row_i % 2 == 0 else ROW_B
            pygame.draw.rect(self.screen, row_bg,
                             pygame.Rect(0, y, W, ROW_H))

            # Bottom border
            pygame.draw.line(self.screen, BORDER,
                             (0, y + ROW_H - 1), (W, y + ROW_H - 1), 1)

            cy = y + ROW_H // 2 - 7   # text baseline y

            # Build cell values
            if result.found:
                time_color  = GREEN  if result.time_mean  == best_time  else LIGHT_GRAY
                mem_color   = GREEN  if result.mem_mean   == best_mem   else LIGHT_GRAY
                nodes_color = GREEN  if result.nodes_mean == best_nodes else LIGHT_GRAY
                time_mean   = f"{result.time_mean:.2f} ms"
                time_std    = f"± {result.time_std:.2f}"
                mem_mean    = f"{result.mem_mean:.1f} KB"
                mem_std     = f"± {result.mem_std:.1f}"
                nodes_exp   = f"{result.nodes_mean:.1f}"
                path_len    = str(result.path_length)
                path_cost   = f"{result.path_cost:.1f}"
                optimal_str = "✓" if result.optimal else "—"
                opt_color   = GREEN if result.optimal else MID_GRAY
            else:
                time_color = mem_color = nodes_color = DIM_GRAY
                time_mean = time_std = mem_mean = mem_std = "—"
                nodes_exp = path_len = path_cost = "—"
                optimal_str = "✗"
                opt_color   = RED

            cells = [
                (result.name, LIGHT_GRAY),
                (time_mean,   time_color),
                (time_std,    MID_GRAY),
                (mem_mean,    mem_color),
                (mem_std,     MID_GRAY),
                (nodes_exp,   nodes_color),
                (path_len,    LIGHT_GRAY),
                (path_cost,   LIGHT_GRAY),
                (optimal_str, opt_color),
            ]

            for i, (text, color) in enumerate(cells):
                _, col_w, align = COLUMNS[i]
                x = col_xs[i]
                if align == 'r':
                    tx = x + col_w - 4
                elif align == 'c':
                    tx = x + col_w // 2
                else:
                    tx = x + 4
                _draw_text(self.screen, text, self.cell_font,
                           color, tx, cy, align, max_w=col_w - 6)

            # Vertical dividers
            for x in col_xs[1:]:
                pygame.draw.line(self.screen, BORDER,
                                 (x - 1, y), (x - 1, y + ROW_H), 1)

    def _draw_summary(self):
        """Render a one-line summary of key findings below the table."""
        results      = self.results.algo_results
        found        = [r for r in results if r.found]
        n_found      = len(found)
        n_total      = len(results)
        table_bottom = TABLE_TOP + HEADER_H + len(results) * ROW_H

        y = table_bottom + 16

        summary = (
            f"{n_found}/{n_total} algorithms found a path.  "
            f"Runs per algorithm: {self.results.n_runs}."
        )
        _draw_text(self.screen, summary, self.small_font, MID_GRAY, TABLE_PAD_X, y)

        if found:
            fastest  = min(found, key=lambda r: r.time_mean)
            leanest  = min(found, key=lambda r: r.mem_mean)
            thorough = max(found, key=lambda r: r.nodes_mean)
            optimals = [r.name for r in found if r.optimal]

            lines = [
                f"Fastest:    {fastest.name}  ({fastest.time_mean:.2f} ms avg)",
                f"Lowest mem: {leanest.name}  ({leanest.mem_mean:.1f} KB avg)",
                f"Most nodes: {thorough.name}  ({thorough.nodes_mean:.1f} avg expanded)",
                f"Optimal:    {', '.join(optimals) if optimals else 'none'}",
            ]
            for i, line in enumerate(lines):
                _draw_text(self.screen, line, self.small_font,
                           LIGHT_GRAY, TABLE_PAD_X, y + 20 + i * 18)

    def _draw(self):
        self.screen.fill(BG)

        # ── Title bar ─────────────────────────────────────────────────────
        pygame.draw.rect(self.screen, PANEL, pygame.Rect(0, 0, W, 90))
        pygame.draw.line(self.screen, BORDER, (0, 90), (W, 90), 1)

        _draw_text(self.screen, "Benchmark Report",
                   self.title_font, WHITE, 20, 16)
        _draw_text(self.screen,
                   f"Start: {self.results.start_name.replace('_', ' ')}   "
                   f"→   Goal: {self.results.end_name.replace('_', ' ')}   "
                   f"   ({self.results.n_runs} runs per algorithm)",
                   self.small_font, MID_GRAY, 22, 56)

        # ── Column key ────────────────────────────────────────────────────
        _draw_text(self.screen,
                   "Green = best value in column.   ✓ = optimal path cost.",
                   self.small_font, DIM_GRAY, 22, 110)

        # ── Table ─────────────────────────────────────────────────────────
        self._draw_table_header()
        self._draw_table_rows()

        # ── Summary ───────────────────────────────────────────────────────
        self._draw_summary()

        # ── Footer ────────────────────────────────────────────────────────
        pygame.draw.line(self.screen, BORDER, (0, H - 60), (W, H - 60), 1)
        _draw_text(self.screen, "ESC or Close to dismiss",
                   self.small_font, DIM_GRAY, 20, H - 42)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self._on_close()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._on_close()

            self._draw()
            pygame_widgets.update(events)
            pygame.display.update()
            self.clock.tick(FPS)

        self._hide_widgets()
