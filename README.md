# AI Search — Visualize, Compare & Benchmark

**Intro to AI · Project 2 · Nicholas Wise**

An interactive visualization and benchmarking tool for five classic search algorithms — DFS, BFS, Iterative Deepening DFS, Greedy Best-First, and A* — built with Python and pygame.

---

## Features

- **Step-by-step visualization** of all five algorithms with play, pause, reset, and speed controls
- **Preset graph** — a real Kansas city road network loaded from data files
- **Random graph generator** — parameterized by node count, branching factor, edge weight range, connectedness, and seed
- **Benchmark harness** — runs all five algorithms five times each and reports mean ± std for runtime, memory, nodes expanded, path length, and optimality
- **Color-coded legend** with unique colors for every node state
- **Stats panel** showing per-run metrics after each visualization

---

## Project Structure

```
project/
├── src/
│   ├── main.py               # Entry point — title screen
│   ├── guided_search.py      # Project 2 main controller
│   ├── graph.py              # Graph rendering and Node class
│   ├── graph_algorithms.py   # BFS, DFS, ID-DFS, Greedy, A*
│   ├── graph_generator.py    # Random graph generation
│   ├── generator_dialog.py   # Parameter input popup
│   ├── benchmark.py          # Benchmarking harness
│   ├── benchmark_report.py   # Benchmark results popup
│   ├── search_methods.py     # Project 1 grid search (BFS/DFS)
│   ├── control_panel.py      # Shared control panel helpers
│   ├── tree.py               # Tree visualizer (Project 1)
│   └── utils.py              # Graph import, draw helpers
├── data/
│   ├── coordinates.csv       # City lat/lon data
│   └── Adjacencies.txt       # City connection data
├── fonts/
│   └── Oswald-Medium.ttf
├── PROMPTS.md                # AI prompt sequences and generation methods
└── README.md
```

---

## Requirements

- Python 3.10+
- pygame
- pygame_widgets

Install dependencies:

```bash
pip install pygame pygame_widgets
```

---

## Running the Program

From the `src/` directory:

```bash
python main.py
```

This opens the title screen. Select a project to begin:

- **Project 1 — Search Methods** — BFS/DFS on a grid with obstacles
- **Project 2 — Guided Search** — the main visualization and benchmark tool

---

## Usage Guide — Guided Search (Project 2)

### 1. Select an Algorithm

Use the **Algorithm** dropdown in the left panel to choose one of:

| Algorithm | Description |
|---|---|
| Depth-First Search | Fast but not optimal; explores deep paths first |
| Breadth-First Search | Guarantees shortest path; explores level by level |
| Iterative Deepening DFS | Complete like BFS, memory-efficient like DFS |
| Best-First Search | Heuristic-guided; fast but not optimal |
| A* | Optimal and efficient; combines path cost and heuristic |

### 2. Set Start and End Nodes

1. Click **Set Start Node** — the panel label turns green
2. Click any node on the graph view to assign it as the start
3. Click **Set End Node** — the panel label turns red
4. Click any node on the graph view to assign it as the goal

The selected node names appear in the strip below the graph view.

### 3. Run the Algorithm

Use the **Playback** controls:

| Button | Action |
|---|---|
| ▶ Play | Start a fresh run, or resume from pause |
| ⏸ Pause | Freeze mid-run without losing state |
| ↺ Reset | Re-run from scratch with the same start/end nodes |

Drag the **Speed** slider to control how fast the algorithm steps:
- Left (Slow) — one step per second; good for following the logic
- Right (Fast) — steps every frame; good for seeing the final result quickly

### 4. Read the Graph

| Color | State |
|---|---|
| Green | Start node |
| Red | Goal node |
| Blue | Frontier — currently being considered |
| Purple | Visited — already expanded |
| Yellow | Solution path |
| Orange | Hovered node |
| Gray | Unvisited — not yet reached |

Blue edges trace the final solution path when the algorithm completes.

### 5. Read the Stats Panel

After a run completes, the bottom panel shows:

| Stat | Description |
|---|---|
| Time | Wall-clock milliseconds from start to finish |
| Memory | Peak process memory via tracemalloc (KB) |
| Nodes Expanded | Total nodes popped from the frontier |
| Path Length | Number of edges in the solution path |
| Solution Depth | Depth of the goal node (equals path length for unit-cost graphs) |
| Heuristic (h avg) | Placeholder — not yet wired |

---

## Generating a Random Graph

Click **⚙ Generate New Graph** to open the parameter dialog:

| Parameter | Description |
|---|---|
| Number of Nodes (N) | Total nodes in the graph (integer ≥ 2) |
| Branching Factor (b) | Expected average number of neighbours per node |
| Min / Max Weight | Edge weight range (uniform random integers) |
| Connectedness | Fraction of maximum possible edges (0–1) |
| Random Seed | Integer seed for reproducibility |

Click **Generate Graph** to confirm. The graph view updates immediately. Set new start/end nodes and run any algorithm as normal.

To reproduce a specific graph, use the same seed and parameters.

---

## Running the Benchmark

1. Set a start node and an end node
2. Click **📊 Run Benchmark**
3. Wait a few seconds while all five algorithms each run five times
4. The benchmark report window opens automatically

The report shows a comparison table with:
- Mean and standard deviation for runtime and memory
- Nodes expanded, path length, and path cost
- A **✓** marker on algorithms that found the optimal (lowest-cost) path
- Green highlighting on the best value in each column
- A summary naming the fastest, lowest-memory, and most-thorough algorithm

Press **ESC** or **Close** to dismiss the report and return to the main view.

---

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `ESC` | Return to the title screen |

---

## Known Limitations

- Heuristic stats (h avg) in the stats panel are not yet wired — shows `—`
- The grid world generator (Project 1 extension) is not yet implemented
- Batch compare mode (multiple graphs, multiple seeds) is not yet implemented

---

## Notes on Reproducibility

All random graph generation uses Python's `random.Random(seed)` with an explicit seed, so any graph can be exactly reproduced by supplying the same parameters and seed. The seed used for a generated graph is shown in the status bar below the graph view after generation.
