from grid import CellState, Grid
from tree import TreeVisualizer
from collections import deque 
from collections import defaultdict

class BFS:    
    def __init__(self, grid: Grid, tree: TreeVisualizer):
        self.grid = grid
        self.nodes = deque([])
        self.visited = set()
        self.came_from = {}
        self.tree = tree
        
        self.nodes.append(grid.start_node)
        self.visited.add((grid.start_node.x, grid.start_node.y))
        
    def reconstruct_path(self, current):
        self.tree.mark_path(current)
        while current in self.came_from:
            current = self.came_from[current]
            if current.cell_type not in (CellState.START, CellState.END):
                current.cell_type = CellState.PATH
            self.tree.mark_path(current)
    
    def update(self):     
        if not self.nodes:
            return True
              
        # grab leftmost node (oldest node) and set as current agent position
        current = self.nodes.popleft()
        
        # if the agents current position is the end_node we have found the path, and can return
        if current == self.grid.end_node:
            self.reconstruct_path(current)
            return True
        
        # Check neighbors based on current agent position
        for neighbor in self.grid.get_neighbors(current):
            # ignore blocked cells
            if neighbor.cell_type == CellState.BLOCKED:
                continue
            
            # If we haven't visited the cell then add it to visited and add it to the deque and set it as open
            if (neighbor.x, neighbor.y) not in self.visited:
                self.visited.add((neighbor.x, neighbor.y))
                self.nodes.append(neighbor)
                self.tree.add_child(current, neighbor)
                
                # record parent node
                self.came_from[neighbor] = current
                
                if neighbor.cell_type not in (CellState.END, CellState.START):
                    neighbor.cell_type = CellState.OPEN
                    
        # once we are done with current cell, set it to closed, we are done with it for now  
        if current.cell_type not in (CellState.END, CellState.START):
            current.cell_type = CellState.CLOSED
        self.tree.mark_inactive(current)
            
        # If we never found the end, then return false
        return False
    
class DFS:
    def __init__(self, grid: Grid, tree: TreeVisualizer):
        self.grid = grid
        self.nodes = deque()
        self.visited = set()
        self.came_from = {}
        self.tree = tree
        
        self.nodes.append(self.grid.start_node)
        self.visited.add((self.grid.start_node.x, self.grid.start_node.y))
        
    def reconstruct_path(self, current):
        self.tree.mark_path(current)
        while current in self.came_from:
            current = self.came_from[current]
            if current.cell_type not in (CellState.START, CellState.END):
                current.cell_type = CellState.PATH
            self.tree.mark_path(current)
        
    def update(self):
        # grab right most node (newest node) and set as current agent position
        if not self.nodes:
            return True   # or False depending on how you want to signal failure
        current = self.nodes.pop()
        
        # if the agents current position is the end_node we have found the path, and can return
        if current == self.grid.end_node:
            self.reconstruct_path(current)
            return True
        
        for neighbor in self.grid.get_neighbors(current):
            # ignore blocked cells
            if neighbor.cell_type == CellState.BLOCKED:
                continue
            
            # Add   
            if (neighbor.x, neighbor.y) not in self.visited:
                self.visited.add((neighbor.x, neighbor.y))
                self.nodes.append(neighbor)
                self.tree.add_child(current, neighbor)
                
                # record parent node
                self.came_from[neighbor] = current
                
                if neighbor.cell_type not in (CellState.END, CellState.START):
                    neighbor.cell_type = CellState.OPEN     
                                   
        # once we are done with current cell, set it to closed, we are done with it for now  
        if current.cell_type not in (CellState.END, CellState.START):
            current.cell_type = CellState.CLOSED
        self.tree.mark_inactive(current)
            
        return False