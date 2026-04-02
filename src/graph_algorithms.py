from collections import deque
import heapq
import math

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _heuristic(node_a, node_b):
    """Straight-line (Euclidean) distance between two nodes using lat/lon."""
    return math.hypot(node_a.lat - node_b.lat, node_a.lon - node_b.lon)


def _reconstruct_path(came_from, current):
    """Walk came_from back to the start and return the path as a list."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


# ---------------------------------------------------------------------------
# BFS
# ---------------------------------------------------------------------------

class BFS:
    """Breadth-First Search — guarantees shortest path (fewest hops)."""

    def __init__(self, start, end):
        self.end   = end
        self.done  = False
        self.found = False

        self._queue     = deque([start])
        self._visited   = {start.name}
        self._came_from = {}

        # Exposed for graph.py to colour each frame
        self.visited_nodes: list = []   # all nodes popped so far
        self.frontier:      list = [start]
        self.path:          list = []   # filled when goal is reached

    def update(self) -> bool:
        """Advance one step. Returns True when finished (found or exhausted)."""
        if self.done or not self._queue:
            self.done = True
            return True

        current = self._queue.popleft()
        self.visited_nodes.append(current)
        self.frontier = list(self._queue)

        if current == self.end:
            self.path  = _reconstruct_path(self._came_from, current)
            self.done  = True
            self.found = True
            return True

        for neighbour in current.adjacencies:
            if neighbour.name not in self._visited:
                self._visited.add(neighbour.name)
                self._came_from[neighbour] = current
                self._queue.append(neighbour)

        return False


# ---------------------------------------------------------------------------
# DFS
# ---------------------------------------------------------------------------

class DFS:
    """Depth-First Search — does not guarantee shortest path."""

    def __init__(self, start, end):
        self.end   = end
        self.done  = False
        self.found = False

        self._stack     = [start]
        self._visited   = {start.name}
        self._came_from = {}

        self.visited_nodes: list = []
        self.frontier:      list = [start]
        self.path:          list = []

    def update(self) -> bool:
        if self.done or not self._stack:
            self.done = True
            return True

        current = self._stack.pop()
        self.visited_nodes.append(current)
        self.frontier = list(self._stack)

        if current == self.end:
            self.path  = _reconstruct_path(self._came_from, current)
            self.done  = True
            self.found = True
            return True

        for neighbour in current.adjacencies:
            if neighbour.name not in self._visited:
                self._visited.add(neighbour.name)
                self._came_from[neighbour] = current
                self._stack.append(neighbour)

        return False


# ---------------------------------------------------------------------------
# Iterative Deepening DFS
# ---------------------------------------------------------------------------

class ID_DFS:
    """Iterative-Deepening DFS — completeness of BFS, memory of DFS."""

    def __init__(self, start, end):
        self.start = start
        self.end   = end
        self.done  = False
        self.found = False

        self._depth_limit = 0
        self._reset_iteration()

        self.visited_nodes: list = []
        self.frontier:      list = [start]
        self.path:          list = []

    def _reset_iteration(self):
        """Start a fresh DFS pass with the current depth limit."""
        self._stack      = [(self.start, 0)]   # (node, depth)
        self._came_from  = {}
        self._visited    = {self.start.name}

    def update(self) -> bool:
        if self.done:
            return True

        # If stack exhausted, increase depth limit and retry
        if not self._stack:
            self._depth_limit += 1
            self._reset_iteration()
            # Guard against infinite loops on disconnected graphs
            if self._depth_limit > len(self.visited_nodes) + 500:
                self.done = True
                return True

        current, depth = self._stack.pop()
        self.visited_nodes.append(current)
        self.frontier = [n for n, _ in self._stack]

        if current == self.end:
            self.path  = _reconstruct_path(self._came_from, current)
            self.done  = True
            self.found = True
            return True

        if depth < self._depth_limit:
            for neighbour in current.adjacencies:
                if neighbour.name not in self._visited:
                    self._visited.add(neighbour.name)
                    self._came_from[neighbour] = current
                    self._stack.append((neighbour, depth + 1))

        return False


# ---------------------------------------------------------------------------
# Greedy Best-First Search
# ---------------------------------------------------------------------------

class GreedyBestFirst:
    """Greedy Best-First — always expands the node closest to the goal
    by straight-line distance. Fast but not optimal."""

    def __init__(self, start, end):
        self.end   = end
        self.done  = False
        self.found = False

        self._came_from = {}
        self._visited   = {start.name}

        # Priority queue entries: (heuristic, counter, node)
        # The counter breaks ties and avoids comparing Node objects.
        self._counter = 0
        self._heap    = [(0, self._counter, start)]

        self.visited_nodes: list = []
        self.frontier:      list = [start]
        self.path:          list = []

    def update(self) -> bool:
        if self.done or not self._heap:
            self.done = True
            return True

        _, _, current = heapq.heappop(self._heap)
        self.visited_nodes.append(current)
        self.frontier = [n for _, _, n in self._heap]

        if current == self.end:
            self.path  = _reconstruct_path(self._came_from, current)
            self.done  = True
            self.found = True
            return True

        for neighbour in current.adjacencies:
            if neighbour.name not in self._visited:
                self._visited.add(neighbour.name)
                self._came_from[neighbour] = current
                h = _heuristic(neighbour, self.end)
                self._counter += 1
                heapq.heappush(self._heap, (h, self._counter, neighbour))

        return False


# ---------------------------------------------------------------------------
# A*
# ---------------------------------------------------------------------------

class AStar:
    """A* — optimal and complete; combines actual cost g(n) with heuristic h(n)."""

    def __init__(self, start, end):
        self.end   = end
        self.done  = False
        self.found = False

        self._came_from = {}
        self._g_score   = {start.name: 0.0}
        self._visited   = set()

        self._counter = 0
        f_start = _heuristic(start, end)
        self._heap = [(f_start, self._counter, start)]

        self.visited_nodes: list = []
        self.frontier:      list = [start]
        self.path:          list = []

    def update(self) -> bool:
        if self.done or not self._heap:
            self.done = True
            return True

        _, _, current = heapq.heappop(self._heap)

        if current.name in self._visited:
            return False   # stale heap entry — skip without marking done
        self._visited.add(current.name)
        self.visited_nodes.append(current)
        self.frontier = [n for _, _, n in self._heap if n.name not in self._visited]

        if current == self.end:
            self.path  = _reconstruct_path(self._came_from, current)
            self.done  = True
            self.found = True
            return True

        for neighbour in current.adjacencies:
            if neighbour.name in self._visited:
                continue
            # Edge weight = straight-line distance between the two nodes
            tentative_g = self._g_score[current.name] + _heuristic(current, neighbour)

            if tentative_g < self._g_score.get(neighbour.name, float('inf')):
                self._came_from[neighbour]    = current
                self._g_score[neighbour.name] = tentative_g
                f = tentative_g + _heuristic(neighbour, self.end)
                self._counter += 1
                heapq.heappush(self._heap, (f, self._counter, neighbour))

        return False