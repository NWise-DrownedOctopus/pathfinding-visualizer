import os
import csv
import pygame
from graph import Node

os.chdir('.')

BASE_IMG_PATH  = r"art/"
BASE_AUDIO_PATH = r"audio/"
pygame.init()
pygame.mixer.init()
pygame.display.set_mode((1280, 720))

sfx_assets   = {}
sheet_assets = {}

def import_graph(coord_path: str, adj_path: str) -> list[Node]:
    """Parse coordinates and adjacency files and return a list of Node objects.

    Args:
        coord_path: Path to the CSV file with columns  name, lat, lon
        adj_path:   Path to the text file where each line is:
                        CityName  Neighbour1  Neighbour2 ...

    Returns:
        A list of fully linked Node objects (adjacencies populated).
    """

    # ------------------------------------------------------------------
    # Pass 1 — build a name → Node mapping from the coordinates file
    # ------------------------------------------------------------------
    nodes: dict[str, Node] = {}

    with open(coord_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 3:
                continue                          # skip blank / malformed lines
            name = row[0].strip()
            try:
                lat = float(row[1].strip())
                lon = float(row[2].strip())
            except ValueError:
                print(f"[import_graph] Skipping bad coordinate row: {row}")
                continue
            nodes[name] = Node(name, lat, lon)

    # ------------------------------------------------------------------
    # Pass 2 — parse adjacency file and wire up Node.adjacencies
    # ------------------------------------------------------------------
    # Store raw neighbour name lists first; link after all names are known.
    raw_adj: dict[str, list[str]] = {}

    with open(adj_path, encoding='utf-8') as f:
        for line in f:
            tokens = line.strip().split()
            if not tokens:
                continue
            city       = tokens[0]
            neighbours = tokens[1:]
            raw_adj[city] = neighbours

            # If a city appears here but not in the CSV, create a placeholder
            # node with NaN coordinates so nothing crashes.
            if city not in nodes:
                print(f"[import_graph] '{city}' found in adjacency file but not in coordinates — adding placeholder.")
                nodes[city] = Node(city, float('nan'), float('nan'))

            for neighbour in neighbours:
                if neighbour not in nodes:
                    print(f"[import_graph] '{neighbour}' found in adjacency file but not in coordinates — adding placeholder.")
                    nodes[neighbour] = Node(neighbour, float('nan'), float('nan'))

    # Now convert name lists to actual Node tuples
    for city, neighbour_names in raw_adj.items():
        linked = tuple(nodes[n] for n in neighbour_names if n in nodes)
        nodes[city].adjacencies = linked

    node_list = list(nodes.values())
    print(f"[import_graph] Loaded {len(node_list)} nodes.")
    return node_list

def get_sheet_dim(sheet):
    max_frame_width  = sheet_assets[sheet][1]
    max_frame_height = sheet_assets[sheet][2]
    return max_frame_width, max_frame_height


def get_image(sheet, frame, width, height):
    image = pygame.Surface((width, height)).convert_alpha()
    image.blit(sheet_assets[sheet][0], (0, 0), ((frame[0] * width), (frame[1] * width), width, height))
    image.set_colorkey((0, 0, 0))
    return image


def load_sheet_images(sheet):
    size = sheet_assets[sheet][1]
    rows = sheet_assets[sheet][2]
    cols = sheet_assets[sheet][3]
    images = []
    for row in range(1, rows):
        for col in range(1, cols):
            image = pygame.Surface((size, size)).convert_alpha()
            image.blit(sheet_assets[sheet][0], (0, 0), ((row * size), (col * size), size, size))
            image.set_colorkey((0, 0, 0))
            images.append(image)
            print("row = {} col = {}".format(row, col))
    print(images)
    return images


def play_audio(sound, loop=False):
    if loop:
        print(sfx_assets[sound])
        pygame.mixer.music.load(sfx_assets[sound])
        pygame.mixer.music.play(-1, 0.0)
        return
    sfx_assets[sound].play()


def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img


def load_images(path):
    images = []
    for img_name in os.listdir(BASE_IMG_PATH + path):
        images.append(load_image(path + '/' + img_name))
    print(images)
    return images


def draw_text(surf, text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    surf.blit(img, (x, y))