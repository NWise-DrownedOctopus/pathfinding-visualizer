import pygame
 
class TreeNode:
    def __init__(self, grid_node, parent=None, depth=0):
        self.grid_node = grid_node
        self.parent = parent
        self.children = []
        self.active = True       # True = currently being explored
        self.on_path = False
        self.depth = depth       # Depth in tree
        self.x = 0               # Will be set by TreeVisualizer
        self.y = 0
            
class TreeVisualizer:
    def __init__(self, surface, width, height, max_depth=20, node_radius=5):
        self.surface = surface
        self.width = width
        self.height = height
        self.max_depth = max_depth
        self.node_radius = node_radius
        self.root = None
        self.nodes = []          # Flat list of TreeNodes for easy iteration
        self.node_spacing_x = 40
        self.node_spacing_y = 50

    def reset(self, start_node):
        """Start a new tree with root at the start node."""
        self.root = None
        self.nodes = []
        if start_node is None:
            return
        self.root = TreeNode(start_node, parent=None, depth=0)
        self.nodes = [self.root]

    def add_child(self, parent_grid_node, child_grid_node):
        """Add a new child to a parent identified by its grid_node."""
        parent_node = next((n for n in self.nodes if n.grid_node == parent_grid_node), None)
        print("Adding child:", parent_grid_node, "found parent:", parent_node)
        if parent_node is None:
            return None
        child_node = TreeNode(child_grid_node, parent=parent_node, depth=parent_node.depth + 1)
        parent_node.children.append(child_node)
        self.nodes.append(child_node)
        return child_node

    def mark_inactive(self, grid_node):
        """Mark a node as inactive (branch fully explored)."""
        node = next((n for n in self.nodes if n.grid_node == grid_node), None)
        if node:
            node.active = False
            
    def mark_path(self, grid_node):
        """Mark a node as part of the final path."""
        node = next((n for n in self.nodes if n.grid_node == grid_node), None)
        if node:
            node.on_path = True

    def draw(self):
        """Draw the entire tree onto the surface, scaled to fit."""
        self.surface.fill((50, 50, 50))  # Background

        if not self.nodes:
            return

        # Group nodes by depth
        layers = {}
        max_depth = 0
        for node in self.nodes:
            layers.setdefault(node.depth, []).append(node)
            max_depth = max(max_depth, node.depth)

        # Calculate vertical spacing dynamically
        if max_depth == 0:
            spacing_y = self.height // 2
        else:
            spacing_y = (self.height - 2 * self.node_radius) / (max_depth + 1)

        # Assign positions
        for depth, layer_nodes in layers.items():
            n = len(layer_nodes)
            for i, node in enumerate(layer_nodes):
                # Spread nodes evenly horizontally in the layer
                node.x = int((i + 1) * self.width / (n + 1))
                # Scale Y based on depth
                node.y = int(depth * spacing_y + self.node_radius)

        # Draw edges
        for node in self.nodes:
            if node.parent:
                if node.on_path and node.parent.on_path:
                    color = (227, 197, 91)   # YELLOW for path edges
                elif node.active:
                    color = (200, 0, 0)
                else:
                    color = (100, 100, 100)
                pygame.draw.line(self.surface, color, (node.x, node.y), (node.parent.x, node.parent.y), 2)

        # Draw nodes
        for node in self.nodes:
            if node.on_path:
                color = (227, 197, 91)       # YELLOW for path nodes
            elif node.active:
                color = (0, 200, 0)
            else:
                color = (255, 255, 255)
            pygame.draw.circle(self.surface, color, (node.x, node.y), self.node_radius)
            
        