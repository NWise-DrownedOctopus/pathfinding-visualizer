"""
benchmark.py

Runs all 5 search algorithms against a given start/end node pair,
repeating each algorithm `runs` times (default 5) to gather mean ± std
statistics.

Public API
----------
    run_benchmark(start_node, end_node, runs=5) -> BenchmarkResults
"""

import time
import tracemalloc
import math
import statistics
from dataclasses import dataclass, field

from graph_algorithms import BFS, DFS, ID_DFS, GreedyBestFirst, AStar

ALGO_CLASSES = [
    ("DFS",        DFS),
    ("BFS",        BFS),
    ("ID-DFS",     ID_DFS),
    ("Greedy BFS", GreedyBestFirst),
    ("A*",         AStar),
]


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class SingleRun:
    """Stats from one execution of one algorithm."""
    time_ms     : float
    memory_kb   : float
    nodes_exp   : int
    path_length : int        # edges in solution path
    depth       : int        # same as path_length for unit-cost graphs
    path_cost   : float      # sum of edge weights (1.0 per hop for unweighted)
    found       : bool


@dataclass
class AlgoResult:
    """Aggregated stats across all runs of one algorithm."""
    name        : str
    runs        : list[SingleRun] = field(default_factory=list)

    # Computed after all runs finish
    time_mean   : float = 0.0
    time_std    : float = 0.0
    mem_mean    : float = 0.0
    mem_std     : float = 0.0
    nodes_mean  : float = 0.0
    nodes_std   : float = 0.0
    path_length : int   = 0       # from first successful run
    depth       : int   = 0
    path_cost   : float = 0.0
    found       : bool  = False
    optimal     : bool  = False   # set after cross-algo comparison

    def compute_stats(self):
        if not self.runs:
            return
        times  = [r.time_ms   for r in self.runs]
        mems   = [r.memory_kb for r in self.runs]
        nodes  = [r.nodes_exp for r in self.runs]

        self.time_mean  = statistics.mean(times)
        self.time_std   = statistics.stdev(times) if len(times) > 1 else 0.0
        self.mem_mean   = statistics.mean(mems)
        self.mem_std    = statistics.stdev(mems)  if len(mems)  > 1 else 0.0
        self.nodes_mean = statistics.mean(nodes)
        self.nodes_std  = statistics.stdev(nodes) if len(nodes) > 1 else 0.0

        # Grab path info from first successful run
        for r in self.runs:
            if r.found:
                self.found       = True
                self.path_length = r.path_length
                self.depth       = r.depth
                self.path_cost   = r.path_cost
                break


@dataclass
class BenchmarkResults:
    """Full results for one benchmark session."""
    start_name  : str
    end_name    : str
    n_runs      : int
    algo_results: list[AlgoResult] = field(default_factory=list)

    def mark_optimal(self):
        """
        Mark the optimality flag on each result.
        The optimal algorithm is whichever found-path has the lowest path_cost.
        BFS is optimal for unweighted graphs; A* for weighted.
        If multiple share the minimum cost, all are marked optimal.
        """
        found = [r for r in self.algo_results if r.found]
        if not found:
            return
        best_cost = min(r.path_cost for r in found)
        for r in found:
            r.optimal = math.isclose(r.path_cost, best_cost, rel_tol=1e-6)


# ── Runner ────────────────────────────────────────────────────────────────────

def _run_once(algo_class, start_node, end_node) -> SingleRun:
    """
    Execute one algorithm to completion and capture stats.
    Runs synchronously — no animation.
    """
    tracemalloc.start()
    t0 = time.perf_counter()

    algo = algo_class(start_node, end_node)
    while not algo.update():
        pass

    elapsed_ms = (time.perf_counter() - t0) * 1000
    _, peak    = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    path_len  = max(0, len(algo.path) - 1)  # edges
    path_cost = float(path_len)              # unit cost; replace with weighted sum later

    return SingleRun(
        time_ms     = elapsed_ms,
        memory_kb   = peak / 1024,
        nodes_exp   = len(algo.visited_nodes),
        path_length = path_len,
        depth       = path_len,
        path_cost   = path_cost,
        found       = algo.found,
    )


def run_benchmark(start_node, end_node, runs: int = 5) -> BenchmarkResults:
    """
    Run all 5 algorithms `runs` times each against the given node pair.
    Returns a BenchmarkResults with fully-computed stats.
    """
    results = BenchmarkResults(
        start_name = start_node.name,
        end_name   = end_node.name,
        n_runs     = runs,
    )

    for name, algo_class in ALGO_CLASSES:
        print(f"[benchmark] Running {name} ({runs} runs)…")
        algo_result = AlgoResult(name=name)

        for i in range(runs):
            run = _run_once(algo_class, start_node, end_node)
            algo_result.runs.append(run)
            print(f"  run {i+1}: {run.time_ms:.2f}ms  "
                  f"{run.memory_kb:.1f}KB  "
                  f"expanded={run.nodes_exp}  "
                  f"path={run.path_length}  "
                  f"found={run.found}")

        algo_result.compute_stats()
        results.algo_results.append(algo_result)

    results.mark_optimal()
    print("[benchmark] Complete.")
    return results
