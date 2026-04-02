import pygame

NODE_AVERAGE_X = 37.75793934
NODE_AVERAGE_Y = -97.61909287

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY = (50, 50, 50)
BLUE = (43, 146, 224)
PURPLE = (136, 66, 207)
GREEN = (90, 207, 66)
RED = (209, 48, 48)
YELLOW = (227, 197, 91)

# ---------------------------------------------------------------------------
# Graph data structures
# ---------------------------------------------------------------------------
class Graph:
    def __init__(self):
        self.nodes = []  
        
    def draw_graph(self, surface, node_size, dist_multi):
        cx = surface.get_width()  / 2
        cy = surface.get_height() / 2

        for node in self.nodes:
            # Longitude  → X  (east is right, no flip needed)
            # Latitude   → Y  (north is up, so negate to match screen coords)
            x = cx + (node.lon - NODE_AVERAGE_Y) * dist_multi
            y = cy - (node.lat - NODE_AVERAGE_X) * dist_multi

            pygame.draw.circle(surface, RED, (x, y), node_size)
        
    
class Node:
    """Represents a city on the map.

    Attributes:
        name        (str)         : City name as it appears in the data files.
        lat         (float)       : Latitude coordinate.
        lon         (float)       : Longitude coordinate.
        adjacencies (tuple[Node]) : Neighbouring nodes (populated after all
                                    nodes are created via import_graph).
    """

    def __init__(self, name: str, lat: float, lon: float):
        self.name        = name
        self.lat         = lat
        self.lon         = lon
        self.adjacencies: tuple = ()   # filled in by import_graph

    def __repr__(self):
        return f"Node({self.name}, lat={self.lat:.4f}, lon={self.lon:.4f}, adj={[n.name for n in self.adjacencies]})"
    