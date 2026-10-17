"""CLI: python -m ecomind.seed  — (re)creates the synthetic demo graph in FalkorDB."""
from .config import load_config
from .db import GraphStore

if __name__ == "__main__":
    store = GraphStore(load_config())
    n = store.seed(reset=True)
    print(f"Seeded synthetic graph with {n} statements.")
    for name in ("problems", "driver_fanout"):
        print(name, store.run(name))
