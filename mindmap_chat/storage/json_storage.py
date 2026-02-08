"""
JSON file-based storage for conversation graphs.
Simple, local, easy to debug and inspect.
"""

import json
import os
from pathlib import Path
from models import ConversationGraph, Mindmap


class JSONStorage:
    """JSON file storage for conversation graphs."""

    def __init__(self, file_path: str = "./data/conversation.json"):
        """
        Initialize storage.
        
        Args:
            file_path: Path to JSON file
        """
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, mindmap: Mindmap) -> None:
        """
        Save mindmap to JSON file.
        
        Args:
            mindmap: Mindmap to save
        """
        data = mindmap.to_dict()
        
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"[SAVED] {self.file_path}")

    def load(self) -> Mindmap:
        """
        Load conversation graph from JSON file.
        
        Returns:
            Loaded Mindmap, or empty mindmap if file doesn't exist
        """
        if not self.file_path.exists():
            return Mindmap()
        
        with open(self.file_path, "r") as f:
            data = json.load(f)
        
        if "graphs" in data:
            mindmap = Mindmap.from_dict(data)
            for graph in mindmap.graphs.values():
                graph.rebuild_children()
            return mindmap

        graph = ConversationGraph.from_dict(data)
        graph.rebuild_children()
        mindmap = Mindmap()
        mindmap.add_graph(graph)
        return mindmap

    def clear(self) -> None:
        """Delete the storage file."""
        if self.file_path.exists():
            os.remove(self.file_path)
            print(f"[CLEARED] {self.file_path}")
