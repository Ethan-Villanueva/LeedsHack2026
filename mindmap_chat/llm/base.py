"""
Abstract base class for LLM clients.
Allows easy swapping of different LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import json


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def call(self, prompt: str, json_mode: bool = False) -> str:
        """
        Call the LLM with a prompt.
        
        Args:
            prompt: The prompt to send
            json_mode: If True, expect JSON-formatted response
            
        Returns:
            The LLM's response as a string
        """
        pass

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """
        Generate an embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        pass

    def call_json(self, prompt: str) -> Dict[str, Any]:
        """
        Call the LLM and parse response as JSON.
        
        Args:
            prompt: The prompt
            
        Returns:
            Parsed JSON as dict
        """
        response = self.call(prompt, json_mode=True)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON response: {response}")
            raise
