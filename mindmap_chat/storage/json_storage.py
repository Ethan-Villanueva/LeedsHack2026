"""
JSON file-based storage for conversation graphs.
Simple, local, easy to debug and inspect.
"""

import json
import os
from pathlib import Path
from models import ConversationGraph


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

    def save(self, graph: ConversationGraph) -> None:
        """
        Save conversation graph to JSON file.
        
        Args:
            graph: Graph to save
        """
        data = graph.to_dict()
        
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"[SAVED] {self.file_path}")

    def load(self) -> ConversationGraph:
        """
        Load conversation graph from JSON file.
        
        Returns:
            Loaded ConversationGraph, or empty graph if file doesn't exist
        """
        if not self.file_path.exists():
            return ConversationGraph()
        
        with open(self.file_path, "r") as f:
            data = json.load(f)
        
        return ConversationGraph.from_dict(data)

    def clear(self) -> None:
        """Delete the storage file."""
        if self.file_path.exists():
            os.remove(self.file_path)
            print(f"[CLEARED] {self.file_path}")
