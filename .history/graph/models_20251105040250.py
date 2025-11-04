# graph/models.py
from dataclasses import dataclass

@dataclass
class Edge:
    target: int
    weight: float
