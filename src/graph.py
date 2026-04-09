import pygame
import math

NODE_AVG_LAT = 37.75793934
NODE_AVG_LON = -97.61909287

WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = (50,  50,  50)

# ── Node state colors — each state has a unique color ────────────────────────
START_COLOR     = (90,  207, 66)   # green
GOAL_COLOR      = (209, 48,  48)   # red
FRONTIER_COLOR  = (43,  146, 224)  # blue
VISITED_COLOR   = (136, 66,  207)  # purple
PATH_COLOR      = (227, 197, 91)   # yellow
HOVER_COLOR     = (220, 140, 40)   # orange
UNVISITED_COLOR = (136, 136, 128)  # gray

# Edge colors
EDGE_DEFAULT    = LIGHT_GRAY
EDGE_PATH       = FRONTIER_COLOR   # blue edges on the final path

HOVER_RADIUS    = 8
HOVER_FONT_SIZE = 16
HOVER_THRESHOLD = 12

# ── Legend bar ────────────────────────────────────────────────────────────────
LEGEND_HEIGHT  = 28
LEGEND_BG      = (45,  45,  45)
LEGEND_TEXT    = (180, 180, 180)
LEGEND_FONT_SZ = 13
LEGEND_PAD_X   = 14   # left/right padding inside the bar
LEGEND_GAP     = 22   # gap between each swatch+label pair
SWATCH_R       = 5    # radius of the circle swatch

_LEGEND_ITEMS = [
    ("Start",     START_COLOR),
    ("Goal",      GOAL_COLOR),
    ("Frontier",  FRONTIER_COLOR),
    ("Visited",   VISITED_COLOR),
    ("Path",      PATH_COLOR),
    ("Hover",     HOVER_COLOR),
    ("Unvisited", UNVISITED_COLOR),
]


class Graph:
    def __init__(self):
        self.nodes = []
        self.start_node = None
        self.end_node   = None
        self._screen_pos: dict[str, tuple[int, int]] = {}
        self._label_font  = None
        self._legend_font = None

    # ------------------------------------------------------------------
    # Position cache
    # ------------------------------------------------------------------

    def build_screen_positions(self, surface, dist_multi):
        cx = surface.get_width()  / 2
        cy = surface.get_height() / 2
        self._screen_pos = {}
        for node in self.nodes:
            if math.isnan(node.lat) or math.isnan(node.lon):
                continue
            x = int(cx + (node.lon - NODE_AVG_LON) * dist_multi)
            # Offset y down by half the legend bar so the graph is centred
            # in the remaining space below the legend
            y = int(cy - (node.lat - NODE_AVG_LAT) * dist_multi) + LEGEND_HEIGHT // 2
            self._screen_pos[node.name] = (x, y)

    # ------------------------------------------------------------------
    # Hover detection
    # ------------------------------------------------------------------

    def get_hovered_node(self, screen_mouse_pos, graph_window_offset):
        local_x = screen_mouse_pos[0] - graph_window_offset[0]
        local_y = screen_mouse_pos[1] - graph_window_offset[1]

        closest_node = None
        closest_dist = HOVER_THRESHOLD

        for node in self.nodes:
            pos = self._screen_pos.get(node.name)
            if pos is None:
                continue
            dist = math.hypot(local_x - pos[0], local_y - pos[1])
            if dist < closest_dist:
                closest_dist = dist
                closest_node = node

        return closest_node

    # ------------------------------------------------------------------
    # Legend bar
    # ------------------------------------------------------------------

    def draw_legend(self, surface):
        """Draw a slim color-coded legend bar at the top of the surface."""
        if self._legend_font is None:
            self._legend_font = pygame.font.SysFont(None, LEGEND_FONT_SZ)

        # Background bar
        pygame.draw.rect(surface, LEGEND_BG,
                         pygame.Rect(0, 0, surface.get_width(), LEGEND_HEIGHT))

        # Divider line at the bottom of the bar
        pygame.draw.line(surface, (70, 70, 70),
                         (0, LEGEND_HEIGHT - 1),
                         (surface.get_width(), LEGEND_HEIGHT - 1), 1)

        x = LEGEND_PAD_X
        cy = LEGEND_HEIGHT // 2   # vertical centre of bar

        for label, color in _LEGEND_ITEMS:
            # Circle swatch
            pygame.draw.circle(surface, color, (x + SWATCH_R, cy), SWATCH_R)
            x += SWATCH_R * 2 + 6

            # Label
            text_surf = self._legend_font.render(label, True, LEGEND_TEXT)
            surface.blit(text_surf, (x, cy - text_surf.get_height() // 2))
            x += text_surf.get_width() + LEGEND_GAP

        # "Legend" label flush right
        tag = self._legend_font.render("Legend", True, (90, 90, 90))
        surface.blit(tag, (surface.get_width() - tag.get_width() - LEGEND_PAD_X,
                           cy - tag.get_height() // 2))

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw_graph(self, surface, node_size, dist_multi,
                   hovered_node=None, algo=None):
        if not self._screen_pos:
            self.build_screen_positions(surface, dist_multi)

        if self._label_font is None:
            self._label_font = pygame.font.SysFont(None, HOVER_FONT_SIZE)

        hovered_name = hovered_node.name if hovered_node else None
        start_name   = self.start_node.name if self.start_node else None
        end_name     = self.end_node.name   if self.end_node   else None

        visited_names  = set()
        frontier_names = set()
        path_names     = set()
        if algo is not None:
            visited_names  = {n.name for n in algo.visited_nodes}
            frontier_names = {n.name for n in algo.frontier}
            path_names     = {n.name for n in algo.path}

        # Path edges
        path_edges: set[frozenset] = set()
        if algo is not None and len(algo.path) > 1:
            for i in range(len(algo.path) - 1):
                path_edges.add(frozenset({algo.path[i].name, algo.path[i + 1].name}))

        # ── Edges ─────────────────────────────────────────────────────────
        for node in self.nodes:
            src = self._screen_pos.get(node.name)
            if src is None:
                continue
            for neighbour in node.adjacencies:
                dst = self._screen_pos.get(neighbour.name)
                if dst is None:
                    continue
                if frozenset({node.name, neighbour.name}) in path_edges:
                    pygame.draw.line(surface, EDGE_PATH, src, dst, 3)
                else:
                    pygame.draw.line(surface, EDGE_DEFAULT, src, dst, 1)

        # ── Nodes ─────────────────────────────────────────────────────────
        # Priority: hover > start > goal > path > frontier > visited > unvisited
        for node in self.nodes:
            pos = self._screen_pos.get(node.name)
            if pos is None:
                continue

            if node.name == hovered_name:
                pygame.draw.circle(surface, HOVER_COLOR, pos, HOVER_RADIUS)
                pygame.draw.circle(surface, WHITE,       pos, HOVER_RADIUS, 2)
            elif node.name == start_name:
                pygame.draw.circle(surface, START_COLOR, pos, HOVER_RADIUS)
                pygame.draw.circle(surface, WHITE,       pos, HOVER_RADIUS, 2)
            elif node.name == end_name:
                pygame.draw.circle(surface, GOAL_COLOR,  pos, HOVER_RADIUS)
                pygame.draw.circle(surface, WHITE,       pos, HOVER_RADIUS, 2)
            elif node.name in path_names:
                pygame.draw.circle(surface, PATH_COLOR,  pos, node_size + 2)
                pygame.draw.circle(surface, WHITE,       pos, node_size + 2, 1)
            elif node.name in frontier_names:
                pygame.draw.circle(surface, FRONTIER_COLOR, pos, node_size + 1)
            elif node.name in visited_names:
                pygame.draw.circle(surface, VISITED_COLOR,  pos, node_size)
            else:
                pygame.draw.circle(surface, UNVISITED_COLOR, pos, node_size)

        # ── Legend bar (drawn on top so it's always visible) ───────────────
        self.draw_legend(surface)

        # ── Hover label ───────────────────────────────────────────────────
        if hovered_node and hovered_name in self._screen_pos:
            pos   = self._screen_pos[hovered_name]
            label = self._label_font.render(
                hovered_node.name.replace("_", " "), True, WHITE
            )
            lx = pos[0] + HOVER_RADIUS + 4
            ly = pos[1] - label.get_height() // 2
            if lx + label.get_width() > surface.get_width():
                lx = pos[0] - label.get_width() - HOVER_RADIUS - 4
            surface.blit(label, (lx, ly))


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class Node:
    def __init__(self, name: str, lat: float, lon: float):
        self.name        = name
        self.lat         = lat
        self.lon         = lon
        self.adjacencies: tuple = ()

    def __repr__(self):
        return (
            f"Node({self.name}, lat={self.lat:.4f}, lon={self.lon:.4f}, "
            f"adj={[n.name for n in self.adjacencies]})"
        )