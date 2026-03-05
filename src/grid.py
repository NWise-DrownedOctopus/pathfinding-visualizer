import pygame, random

from enum import Enum, auto

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY = (50, 50, 50)
BLUE = (43, 146, 224)
PURPLE = (136, 66, 207)
GREEN = (90, 207, 66)
RED = (209, 48, 48)
YELLOW = (227, 197, 91)

class CellState(Enum):
    NORMAL = auto()
    BLOCKED = auto()
    START = auto()
    END = auto()
    OPEN = auto()
    CLOSED = auto()
    PATH = auto()


class Grid:

    def __init__(self, tile_size, x_count, y_count):
        self.tile_size = tile_size
        self.x_count = x_count
        self.y_count = y_count
        self.grid = []

    def populate_grid(self):
        print("Populate Grid")
        count = 0
        for row in range(self.y_count):
            for col in range(self.x_count):
                cell = Cell(row, col, CellState.NORMAL)
                self.grid.append(cell)
                print(str("Created cell at: " + str(row) + ", " + str(col)))
                count += 1
        print("We created " + str(count) + " cells")

    def reset_grid(self):
        for cell in self.grid:
            cell.cell_type = CellState.NORMAL        

    def get_cell(self, x, y):
        for cell in self.grid:
            if cell.x == x:
                if cell.y == y:
                    return cell
                
    def get_neighbors(self, cell):
        neighbors = []
        if cell.y > 0:
            north = (cell.x, cell.y - 1)
            neighbors.append(self.get_cell(north))
        
        if cell.x < self.x_count - 1:
            east = (cell.x + 1, cell.y)
            neighbors.append(self.get_cell(east))
        
        if cell.y < self.y_count - 1:
            south = (cell.x, cell.y + 1)
            neighbors.append(self.get_cell(south))

        if cell.x > 0:
            west = (cell.x - 1, cell.y)
            neighbors.append(self.get_cell(west))

        return neighbors

    def generate_obstacles(self, obstacle_sparcity, random_seed):
        random.seed(random_seed)
        sample_size = int(len(self.grid) * obstacle_sparcity)
        random_cells = random.sample(self.grid, sample_size)
        count = 0
        for cell in random_cells:
            print(str(cell.x) + ", " + str(cell.y))
            count += 1
        print("We generated " + str(count) + " obstacles")

        # modify existing grid to have blocked state based on generated random cells
        coords_to_update = {(cell.x, cell.y) for cell in random_cells}
        for cell in self.grid:
            if (cell.x, cell.y) in coords_to_update:
                cell.cell_type = CellState.BLOCKED
                print("We have updated cell: " + str((cell.x, cell.y)) + "to contain blocked cells")


    # Generate visuals for grid based on given grid diminsions
    def draw_grid(self, surface, x_count, y_count):
        for cell in self.grid:
            if cell.cell_type == CellState.BLOCKED:
                # print("We found a blocked grid cell")
                pygame.draw.rect(
                    surface,
                    LIGHT_GRAY,
                    (
                        cell.y * self.tile_size,
                        cell.x * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                )
            if cell.cell_type == CellState.NORMAL:
                pygame.draw.rect(
                    surface,
                    DARK_GRAY,
                    (
                        cell.y * self.tile_size,
                        cell.x * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                )
            if cell.cell_type == CellState.START:
                pygame.draw.rect(
                    surface,
                    BLUE,
                    (
                        cell.y * self.tile_size,
                        cell.x * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                )
            if cell.cell_type == CellState.END:
                pygame.draw.rect(
                    surface,
                    PURPLE
                    (
                        cell.y * self.tile_size,
                        cell.x * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                )
            if cell.cell_type == CellState.OPEN:
                pygame.draw.rect(
                    surface,
                    GREEN,
                    (
                        cell.y * self.tile_size,
                        cell.x * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                )
            if cell.cell_type == CellState.CLOSED:
                pygame.draw.rect(
                    surface,
                    RED,
                    (
                        cell.y * self.tile_size,
                        cell.x * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                )
            if cell.cell_type == CellState.PATH:
                pygame.draw.rect(
                    surface,
                    YELLOW,
                    (
                        cell.y * self.tile_size,
                        cell.x * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                )
                
        # Top bar
        pygame.draw.line(surface, BLACK, (0, 0), (self.tile_size * y_count, 0), 5)
        # Bottom bar
        pygame.draw.line(surface, BLACK, (0, self.tile_size * x_count), (self.tile_size * y_count, self.tile_size * x_count), 5)
        # Left bar
        pygame.draw.line(surface, BLACK, (0, 0), (0, self.tile_size * x_count), 5)
        # Right bar
        pygame.draw.line(surface, BLACK, (self.tile_size * (y_count), 0), (self.tile_size * (y_count), self.tile_size * x_count), 5)

        # Draw horizontal lines
        x = 0
        while x < x_count:
            pygame.draw.line(surface, BLACK, (0, self.tile_size * x), (self.tile_size * y_count, x * self.tile_size))
            x += 1
        # Draw vertical Lines
        y = 0
        while y < y_count:
            pygame.draw.line(surface, BLACK, (self.tile_size * y, 0), (self.tile_size * y, self.tile_size * x_count))
            y += 1

class Cell:
    def __init__(self, x, y, cell_type: CellState):
        self.x = x
        self.y = y
        self.cell_type = cell_type