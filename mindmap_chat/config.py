"""
Configuration and environment settings.
Centralized place for API keys, model names, thresholds.
"""

import os
from dataclasses import dataclass, field


@dataclass
class GeminiConfig:
    """Gemini API configuration."""
    api_key: str = os.getenv("GEMINI_API_KEY", "")
    model_name: str = "gemini-1.5-flash"  # Fast and generous free tier
    temperature: float = 0.7
    max_output_tokens: int = 1024


@dataclass
class DeepSeekConfig:
    """DeepSeek API configuration."""
    api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    model_name: str = "deepseek-chat"  # Fast and cheap
    temperature: float = 0.7
    max_output_tokens: int = 1024


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""
    model: str = "all-MiniLM-L6-v2"  # Free, local, lightweight
    embedding_dim: int = 384


@dataclass
class DetectionThresholds:
    """Thresholds for intent detection."""
    continue_threshold: float = 0.85  # Same topic
    deepen_threshold: float = 0.70  # Deeper dive
    sibling_threshold: float = 0.75  # Related subtopic
    tangent_threshold: float = 0.65  # Unrelated


@dataclass
class AppConfig:
    """Application-wide configuration."""
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    deepseek: DeepSeekConfig = field(default_factory=DeepSeekConfig)
    embeddings: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    thresholds: DetectionThresholds = field(default_factory=DetectionThresholds)
    auto_summarize_after_n_messages: int = 6
    storage_path: str = "./data/conversation.json"
    context_window_size: int = 3  # Last N messages to include in context


# Global config instance
config = AppConfig()


def validate_config():
    """Validate that all required config is set."""
    if not config.gemini.api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    print("[OK] Configuration validated")
