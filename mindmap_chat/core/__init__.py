"""Core business logic module."""

from .embeddings import compute_similarity, embed_text
from .context_builder import construct_block_context, construct_summary_prompt_context
from .intent_detector import detect_intent_shift
from .block_manager import create_root_block, create_child_block, summarize_block, maybe_auto_summarize

__all__ = [
    "compute_similarity",
    "embed_text",
    "construct_block_context",
    "construct_summary_prompt_context",
    "detect_intent_shift",
    "create_root_block",
    "create_child_block",
    "summarize_block",
    "maybe_auto_summarize",
]
