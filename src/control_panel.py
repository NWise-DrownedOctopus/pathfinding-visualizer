from enum import Enum, auto
from utils import draw_text

class algorithm_selection(Enum):
    DFS = auto()
    BFS = auto()

class ControlPanel:

    def __init__(self):
        self.algorithm_choice = algorithm_selection.DFS

    def draw_control_panel(self, surf, text_font):
        draw_text(surf, "Algorithm", text_font, (255, 255, 255), 23, 20)
        draw_text(surf, "Seed", text_font, (255, 255, 255), 23, 130)
