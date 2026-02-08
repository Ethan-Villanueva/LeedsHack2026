"""
Abstract base class for LLM clients.
Allows easy swapping of different LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
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
            extracted = _extract_json_payload(response)
            if extracted is not None:
                try:
                    return json.loads(extracted)
                except json.JSONDecodeError:
                    pass
            print(f"Failed to parse JSON response: {response}")
            raise

def _extract_json_payload(response: str) -> Optional[str]:
    if not response:
        return None
    stripped = response.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    start = response.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for idx in range(start, len(response)):
        char = response[idx]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return response[start:idx + 1].strip()
    return None
