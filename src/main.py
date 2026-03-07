import pygame, sys, pygame_widgets, math
from enum import Enum, auto

from utils import draw_text
from grid import Grid
from control_panel import ControlPanel

from pygame_widgets.textbox import TextBox
from pygame_widgets.dropdown import Dropdown
from pygame_widgets.button import Button

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY = (50, 50, 50)
BLUE = (43, 146, 224)
PURPLE = (136, 66, 207)
GREEN = (90, 207, 66)
RED = (209, 48, 48)
YELLOW = (227, 197, 91)

class algorithm_chosen(Enum):
    BFS = auto()
    DFS = auto()
    NONE = auto()

FPS = 60

class Game:
        def __init__(self):
            pygame.init()
            pygame.display.set_caption("Intro To AI - Project 1 - Nicholas Wise")            
            pygame.mouse.set_visible(True)

            self.clock = pygame.time.Clock()

            # Grid stuff
            self.grid_x_count = 40
            self.grid_y_count = 40
            self.grid_cell_size = 16
            self.random_seed = 3
            self.grid_reset = False
            self.grid_obstacle_sparsity = 0.25
            self.grid_cell_count = self.grid_x_count * self.grid_y_count

            # UI Stuff
            self.bg_color = (25, 25, 25)
            self.text_font = pygame.font.Font("fonts/Oswald-Medium.ttf", 20)

            self.screen = pygame.display.set_mode((1280, 800))

            self.control_panel_dimensions = (160, 640)  
            self.control_panel_window = pygame.Surface((self.control_panel_dimensions))     

            self.grid_window_dimensions = (self.grid_cell_size * self.grid_x_count, self.grid_cell_size * self.grid_y_count)
            self.grid_window_pos = [203, 40, 203 + self.grid_window_dimensions[0], 40 + self.grid_window_dimensions[1]]
            self.grid_window = pygame.Surface((self.grid_window_dimensions))

            self.tree_window_dimensions = (400, 640)  
            self.tree_window = pygame.Surface((self.tree_window_dimensions))   

            self.stats_panel_dimensions = (1240, 100)
            self.stats_panel = pygame.Surface((self.stats_panel_dimensions))

            # Selection Stuff
            self.set_start_mode = False  
            self.set_end_mode = False 
            self.hover_display = False 
            self.algorithim = algorithm_chosen.NONE
            
            # Algorithm dropdown selection
            self.dropdown = Dropdown(
                self.screen, 40, 90, 120, 40, name='Select Algorithm',
                choices=[
                    'BFS',
                    'DFS',
                ],
                borderRadius=1, colour=(LIGHT_GRAY), values=[1, 2],
                direction='down', textHAlign='left',
            )            

            # Set random seed based on textbox input
            # note: I should probobly add some type checking / protection here to avoid crashes
            def output():
                # Get text in the textbox
                print(textbox.getText())
                self.random_seed = int(textbox.getText())
                self.grid_reset = True

            # Text boxed used to grab random seed input
            textbox = TextBox(self.screen, 40, 220, 130, 23, fontSize=15,
                  borderColour=(0, 0, 0), textColour=(0, 0, 0),
                  onSubmit=output, radius=2, borderThickness=1)

            # Used to turn on start node selection
            self.set_start_node_button = Button(
                self.screen,  # Surface to place button on
                40,  # X-coordinate of top left corner
                350,  # Y-coordinate of top left corner
                130,  # Width
                40,  # Height

                text='Set Start Node',  # Text to display
                fontSize=15,  # Size of font
                margin=10,  # Minimum distance between text/image and edge of button
                inactiveColour=(255, 255, 255),  # Colour of button when not being interacted with
                hoverColour=(150, 0, 0),  # Colour of button when being hovered over
                pressedColour=(0, 200, 20),  # Colour of button when being clicked
                radius=3,  # Radius of border corners (leave empty for not curved)
                onClick=self.set_start_select_mode  # Function to call when clicked on
            )

            # Used to turn on end node selection
            self.set_end_node_button = Button(
                self.screen,  # Surface to place button on
                40,  # X-coordinate of top left corner
                450,  # Y-coordinate of top left corner
                130,  # Width
                40,  # Height

                text='Set End Node',  # Text to display
                fontSize=15,  # Size of font
                margin=10,  # Minimum distance between text/image and edge of button
                inactiveColour=(255, 255, 255),  # Colour of button when not being interacted with
                hoverColour=(150, 0, 0),  # Colour of button when being hovered over
                pressedColour=(0, 200, 20),  # Colour of button when being clicked
                radius=3,  # Radius of border corners (leave empty for not curved)
                onClick=self.set_end_select_mode  # Function to call when clicked on
            )

            # Used to run algorithm
            self.start_algo_button = Button(
                self.screen,  # Surface to place button on
                40,  # X-coordinate of top left corner
                600,  # Y-coordinate of top left corner
                130,  # Width
                40,  # Height

                text='Run Algorithm',  # Text to display
                fontSize=15,  # Size of font
                margin=10,  # Minimum distance between text/image and edge of button
                inactiveColour=(255, 255, 255),  # Colour of button when not being interacted with
                hoverColour=(150, 0, 0),  # Colour of button when being hovered over
                pressedColour=(0, 200, 20),  # Colour of button when being clicked
                radius=3,  # Radius of border corners (leave empty for not curved)
                onClick=self.start_algorithm  # Function to call when clicked on
            )

        # returns cords of grid position relative to mouse position
        def get_grid_pos(self):
            cell_pos = None
            m_pos = pygame.mouse.get_pos()
            if m_pos[0] < self.grid_window_pos[0]:
                return cell_pos
            if m_pos[0] > self.grid_window_pos[2]:
                return cell_pos
            if m_pos[1] < self.grid_window_pos[1]:
                return cell_pos
            if m_pos[1] > self.grid_window_pos[3]:
                return cell_pos
            
            grid_pos = [m_pos[0] - self.grid_window_pos[0], m_pos[1] - self.grid_window_pos[1]]

            cell_pos = [math.floor(grid_pos[0] / self.grid_cell_size), math.floor(grid_pos[1] / self.grid_cell_size)]
            return cell_pos
        
        def set_start_select_mode(self):
            self.hover_display = True
            self.set_start_mode = True
            self.set_end_mode = False

        def set_end_select_mode(self):
            self.hover_display = True
            self.set_end_mode = True
            self.set_start_mode = False

        def start_algorithm(self):
            algo_choice_str = self.dropdown.getSelected()
            if algo_choice_str == 'BFS':
                self.algorithim = algorithm_chosen.BFS
            elif algo_choice_str == 'DFS':
                self.algorithim = algorithm_chosen.DFS
            else:
                return
            
        def run(self):
            # Generate Grid
            grid = Grid(self.grid_cell_size, self.grid_x_count, self.grid_y_count)
            grid.populate_grid()

            # Generate Control Panel
            control_panel = ControlPanel()

            # Generate Obstacles        
            grid.generate_obstacles(self.grid_obstacle_sparsity, self.random_seed)

            count = 0
            for cell in grid.grid:
                print("Cell " + str(count) + ": " + str(cell.cell_type))
                count += 1

            # Here we enter the game loop, it is called "every frame"
            while True:
                # Here is where we can draw our background
                self.screen.fill(self.bg_color)
                self.control_panel_window.fill(DARK_GRAY)
                self.grid_window.fill(DARK_GRAY)
                self.tree_window.fill(DARK_GRAY)
                self.stats_panel.fill(DARK_GRAY)      

                cell_pos = self.get_grid_pos()    

                # Handle Events
                events = pygame.event.get()

                for event in events:
                    # This is where we make sure the game breaks out of the loop when the player wishes to exit
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                    if event.type == pygame.MOUSEBUTTONUP:
                        if self.set_start_mode and cell_pos is not None:
                            cell = grid.get_cell(cell_pos[0], cell_pos[1])
                            grid.set_start_node(cell)
                            self.set_start_mode = False
                            self.hover_display = False
             
                        if self.set_end_mode and cell_pos is not None:
                            cell = grid.get_cell(cell_pos[0], cell_pos[1])
                            grid.set_end_node(cell)
                            self.set_end_mode = False
                            self.hover_display = False

                # Reset Grid if needed
                if self.grid_reset:
                    grid.reset_grid()
                    grid.generate_obstacles(0.25, self.random_seed)
                    self.grid_reset = False

                # Draw Grid
                grid.draw_grid(self.grid_window, self.grid_y_count, self.grid_x_count)
                # Draw Control Panel
                control_panel.draw_control_panel(self.control_panel_window, self.text_font)

                # Apply game_window onto our display
                self.screen.blit(self.control_panel_window, (20, 40))
                self.screen.blit(self.grid_window, (self.grid_window_pos[0], self.grid_window_pos[1]))                
                self.screen.blit(self.tree_window, (860, 40))
                self.screen.blit(self.stats_panel, (20, 700))

                # Generate UI Elements
                draw_text(self.screen, "Algorithm Selection", self.text_font, (255, 255, 255), 23, 10)                
                draw_text(self.screen, "Grid View", self.text_font, (255, 255, 255), self.grid_window_pos[0], self.grid_window_pos[1] - 30)
                draw_text(self.screen, "Tree View", self.text_font, (255, 255, 255), 863, 10)
                draw_text(self.screen, "Stats", self.text_font, (255, 255, 255), 23, 700)
                pygame_widgets.update(events)

                # Display grid pos
                if self.hover_display:
                    if cell_pos != None:
                        hovered_cell = grid.get_cell(cell_pos[0], cell_pos[1])
                        if hovered_cell != None:
                            pygame.draw.rect(
                                self.screen,
                                RED,
                                (
                                    (hovered_cell.x * self.grid_cell_size) + self.grid_window_pos[0],
                                    (hovered_cell.y * self.grid_cell_size) + self.grid_window_pos[1],
                                    self.grid_cell_size,
                                    self.grid_cell_size
                                )
                            )

                pygame.display.update()
                self.dt = self.clock.tick(FPS) / 1000

Game().run()