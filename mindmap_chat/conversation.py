"""
Main conversation loop and orchestration.
Ties together all modules for the core functionality.
"""

from typing import Optional
from llm.base import LLMClient
from llm import prompts
from models import ConversationGraph, ConversationMessage, Block
from core import (
    detect_intent_shift,
    create_root_block,
    create_child_block,
    maybe_auto_summarize,
    construct_block_context,
    embed_text,
)
from storage import JSONStorage
from utils import print_block_tree


class ConversationManager:
    """Manages a multi-block conversation."""

    def __init__(self, llm_client: LLMClient, storage: JSONStorage):
        """
        Initialize conversation manager.
        
        Args:
            llm_client: LLM client instance
            storage: Storage backend
        """
        self.llm = llm_client
        self.storage = storage
        self.graph = storage.load()

    def start_new_conversation(self, user_message: str) -> str:
        """
        Start a completely new conversation.
        
        Args:
            user_message: First user message
            
        Returns:
            Assistant response
        """
        # Create root block
        root_block = create_root_block(self.llm, user_message)
        self.graph.root_block_id = root_block.block_id
        self.graph.current_block_id = root_block.block_id
        self.graph.add_block(root_block)
        
        # Store user message
        user_msg = ConversationMessage(
            block_id=root_block.block_id,
            role="user",
            content=user_message,
        )
        self.graph.add_message(user_msg)
        root_block.add_message_ref(user_msg.message_id)
        
        # Get response
        response = self._get_response_in_block(root_block, user_message)
        
        # Store assistant response
        assistant_msg = ConversationMessage(
            block_id=root_block.block_id,
            role="assistant",
            content=response,
        )
        self.graph.add_message(assistant_msg)
        root_block.add_message_ref(assistant_msg.message_id)
        
        # Save
        self.storage.save(self.graph)
        
        print(f"\n[OK] Started new conversation: '{root_block.title}'")
        return response

    def continue_conversation(self, user_message: str) -> str:
        """
        Continue conversation in current block or create new block.
        
        Args:
            user_message: User's message
            
        Returns:
            Assistant response
        """
        current_block = self.graph.blocks[self.graph.current_block_id]
        
        # Get recent messages for context
        block_messages = self.graph.get_block_messages(current_block.block_id)
        
        # Detect intent shift
        print(f"\n[Analyzing intent...]")
        classification = detect_intent_shift(
            self.llm,
            current_block,
            user_message,
            block_messages
        )
        
        print(f"  [ACTION] {classification.action} (confidence: {classification.confidence:.2f})")
        print(f"  [REASON] {classification.reasoning}")
        
        # Handle classification
        if classification.action in ["continue", "deepen"]:
            # Stay in current block
            target_block = current_block
        
        elif classification.action in ["new_child", "tangent"]:
            # Create new block
            new_title = classification.new_block_title or "Untitled"
            new_intent = classification.new_block_intent or "New discussion"
            
            target_block = create_child_block(
                self.llm,
                current_block,
                new_title,
                new_intent
            )
            self.graph.add_block(target_block)
            self.graph.current_block_id = target_block.block_id
            
            print(f"  [NEW] Created new block: '{target_block.title}'")
        
        else:
            # Fallback
            target_block = current_block
        
        # Store user message
        user_msg = ConversationMessage(
            block_id=target_block.block_id,
            role="user",
            content=user_message,
        )
        self.graph.add_message(user_msg)
        target_block.add_message_ref(user_msg.message_id)
        
        # Get response
        response = self._get_response_in_block(target_block, user_message)
        
        # Store assistant response
        assistant_msg = ConversationMessage(
            block_id=target_block.block_id,
            role="assistant",
            content=response,
        )
        self.graph.add_message(assistant_msg)
        target_block.add_message_ref(assistant_msg.message_id)
        
        # Auto-summarize if needed
        maybe_auto_summarize(self.llm, self.graph, target_block)
        
        # Save
        self.storage.save(self.graph)
        
        return response

    def _get_response_in_block(self, block: Block, user_message: str) -> str:
        """
        Get LLM response while maintaining block context.
        
        Args:
            block: Current block
            user_message: User's message
            
        Returns:
            Assistant response
        """
        # Construct block-scoped context
        context = construct_block_context(self.graph, block)
        
        # Build full prompt
        prompt = context + f"\nUSER: {user_message}\n\nASSISTANT:"
        prompt = prompts.prompt_answer_in_block_context(
            block.title,
            block.intent,
            block.summary or "(discussion just started)",
            "\n".join(f"- {kp}" for kp in block.key_points) if block.key_points else "(none yet)",
            "\n".join(f"- {oq}" for oq in block.open_questions) if block.open_questions else "(none yet)",
            construct_block_context(self.graph, block),
            user_message
        )
        
        response = self.llm.call(prompt)
        return response

    def switch_block(self, block_id: str) -> str:
        """
        Switch to a different block.
        
        Args:
            block_id: Block to switch to
            
        Returns:
            Summary of the block
        """
        if block_id not in self.graph.blocks:
            return "Block not found"
        
        self.graph.current_block_id = block_id
        block = self.graph.blocks[block_id]
        self.storage.save(self.graph)
        
        summary = f"\n[BLOCK] Switched to: {block.title}\n"
        summary += f"Intent: {block.intent}\n"
        summary += f"Summary: {block.summary or '(not yet summarized)'}\n"
        summary += f"Messages: {len(block.conversation_refs)}"
        
        return summary

    def print_mindmap(self) -> None:
        """Print the block tree."""
        print("\n[MINDMAP] CONVERSATION GRAPH:")
        print_block_tree(self.graph)

    def export_graph(self) -> dict:
        """Export graph as dict (for visualization, etc)."""
        return self.graph.to_dict()

    def delete_block(self, block_id: str) -> None:
        """Delete a block from the graph."""
        if block_id not in self.graph.blocks:
            raise ValueError(f"Block not found: {block_id}")
        
        if block_id == self.graph.root_block_id:
            raise ValueError("Cannot delete root block")
        
        # Remove the block and update storage
        del self.graph.blocks[block_id]
        self.storage.save(self.graph)
