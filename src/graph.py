import pygame
import math

NODE_AVG_LAT = 37.75793934
NODE_AVG_LON = -97.61909287

WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = (50,  50,  50)
BLUE       = (43,  146, 224)
PURPLE     = (136, 66,  207)
GREEN      = (90,  207, 66)
RED        = (209, 48,  48)
YELLOW     = (227, 197, 91)

HOVER_COLOR     = YELLOW
HOVER_RADIUS    = 8    # slightly larger circle when hovered
HOVER_FONT_SIZE = 16
HOVER_THRESHOLD = 12   # pixel radius within which hover activates


class Graph:
    def __init__(self):
        self.nodes = []

        # Selected start / end nodes (set from guided_search.py)
        self.start_node = None
        self.end_node   = None

        # Cached screen-space positions: { node.name -> (screen_x, screen_y) }
        # Populated once by build_screen_positions() whenever nodes or layout changes.
        self._screen_pos: dict[str, tuple[int, int]] = {}

        # Font for hover labels — initialised lazily on first draw so we don't
        # require pygame.font to be ready before __init__ is called.
        self._label_font = None

    # ------------------------------------------------------------------
    # Position cache
    # ------------------------------------------------------------------

    def build_screen_positions(self, surface, dist_multi):
        """Compute and cache the screen position for every node."""
        cx = surface.get_width()  / 2
        cy = surface.get_height() / 2

        self._screen_pos = {}
        for node in self.nodes:
            if math.isnan(node.lat) or math.isnan(node.lon):
                continue
            x = int(cx + (node.lon - NODE_AVG_LON) * dist_multi)
            y = int(cy - (node.lat - NODE_AVG_LAT) * dist_multi)
            self._screen_pos[node.name] = (x, y)

    # ------------------------------------------------------------------
    # Hover detection
    # ------------------------------------------------------------------

    def get_hovered_node(self, screen_mouse_pos, graph_window_offset):
        """Return the Node under the mouse, or None.

        Args:
            screen_mouse_pos:    (x, y) from pygame.mouse.get_pos()
            graph_window_offset: (x, y) of the top-left corner of the
                                 graph_window surface on the main screen
                                 (i.e. self.graph_window_pos in guided_search)
        """
        # Translate screen-space mouse into graph-window-local space
        local_x = screen_mouse_pos[0] - graph_window_offset[0]
        local_y = screen_mouse_pos[1] - graph_window_offset[1]

        closest_node = None
        closest_dist = HOVER_THRESHOLD  # only snap if within this many pixels

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
    # Drawing
    # ------------------------------------------------------------------

    def draw_graph(self, surface, node_size, dist_multi,
                   hovered_node=None, algo=None):
        """Draw edges, nodes, algorithm state, and an optional hover label.

        Args:
            surface:      The pygame.Surface to draw onto (graph_window).
            node_size:    Radius in pixels for normal nodes.
            dist_multi:   Scale factor (only used if cache needs rebuilding).
            hovered_node: Node returned by get_hovered_node(), or None.
            algo:         A live algorithm instance (BFS/DFS/etc.) or None.
                          If provided, its visited_nodes, frontier, and path
                          lists are used to colour nodes each frame.
        """
        if not self._screen_pos:
            self.build_screen_positions(surface, dist_multi)

        if self._label_font is None:
            self._label_font = pygame.font.SysFont(None, HOVER_FONT_SIZE)

        hovered_name = hovered_node.name if hovered_node else None
        start_name   = self.start_node.name if self.start_node else None
        end_name     = self.end_node.name   if self.end_node   else None

        # Build name-sets from algo state for O(1) lookup
        visited_names  = set()
        frontier_names = set()
        path_names     = set()
        if algo is not None:
            visited_names  = {n.name for n in algo.visited_nodes}
            frontier_names = {n.name for n in algo.frontier}
            path_names     = {n.name for n in algo.path}

        # --- Build exact path edges (consecutive pairs only) ---
        path_edges: set[frozenset] = set()
        if algo is not None and len(algo.path) > 1:
            for i in range(len(algo.path) - 1):
                path_edges.add(frozenset({algo.path[i].name, algo.path[i + 1].name}))

        # --- Edges: highlight actual path edges in blue, rest in gray ---
        for node in self.nodes:
            src = self._screen_pos.get(node.name)
            if src is None:
                continue
            for neighbour in node.adjacencies:
                dst = self._screen_pos.get(neighbour.name)
                if dst is None:
                    continue
                if frozenset({node.name, neighbour.name}) in path_edges:
                    pygame.draw.line(surface, BLUE, src, dst, 3)
                else:
                    pygame.draw.line(surface, LIGHT_GRAY, src, dst, 1)

        # --- Nodes ---
        # Priority (highest to lowest):
        #   hover > start > end > path > frontier > visited > default
        for node in self.nodes:
            pos = self._screen_pos.get(node.name)
            if pos is None:
                continue

            if node.name == hovered_name:
                pygame.draw.circle(surface, HOVER_COLOR, pos, HOVER_RADIUS)
                pygame.draw.circle(surface, WHITE,       pos, HOVER_RADIUS, 2)
            elif node.name == start_name:
                pygame.draw.circle(surface, GREEN, pos, HOVER_RADIUS)
                pygame.draw.circle(surface, WHITE, pos, HOVER_RADIUS, 2)
            elif node.name == end_name:
                pygame.draw.circle(surface, RED,   pos, HOVER_RADIUS)
                pygame.draw.circle(surface, WHITE, pos, HOVER_RADIUS, 2)
            elif node.name in path_names:
                # Final path — bright blue filled
                pygame.draw.circle(surface, BLUE,  pos, node_size + 2)
                pygame.draw.circle(surface, WHITE, pos, node_size + 2, 1)
            elif node.name in frontier_names:
                # Currently in the open/frontier set — yellow outline
                pygame.draw.circle(surface, YELLOW, pos, node_size + 1)
            elif node.name in visited_names:
                # Already expanded — purple
                pygame.draw.circle(surface, PURPLE, pos, node_size)
            else:
                pygame.draw.circle(surface, LIGHT_GRAY, pos, node_size)

        # --- Hover label (drawn last so it sits on top of everything) ---
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
    """Represents a city on the map."""

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