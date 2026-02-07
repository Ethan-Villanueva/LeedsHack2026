"""
Main conversation loop and orchestration.
Ties together all modules for the core functionality.
"""

from typing import Optional
from llm.base import LLMClient
from llm import prompts
from models import ConversationGraph, ConversationMessage, Block, Mindmap
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
        self.mindmap = storage.load()
        self.graph = self.mindmap.get_current_graph()

    def start_new_conversation(self, user_message: str) -> str:
        """
        Start a completely new conversation.
        
        Args:
            user_message: First user message
            
        Returns:
            Assistant response
        """
        # Create new graph + root block
        self.graph = ConversationGraph()
        root_block = create_root_block(self.llm, user_message)
        self.graph.add_block(root_block)
        self.graph.current_block_id = root_block.block_id
        self.mindmap.add_graph(self.graph)
        
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
        self.storage.save(self.mindmap)
        
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
        if not self.graph:
            return self.start_new_conversation(user_message)

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
            # Create new block(s)
            new_blocks = classification.new_blocks or []
            if not new_blocks and (classification.new_block_title or classification.new_block_intent):
                new_blocks = [{
                    "title": classification.new_block_title or "Untitled",
                    "intent": classification.new_block_intent or "New discussion",
                }]
            if not new_blocks:
                new_blocks = [{"title": "Untitled", "intent": "New discussion"}]

            created_blocks = []
            for block_seed in new_blocks:
                new_block = create_child_block(
                    self.llm,
                    current_block,
                    block_seed.get("title", "Untitled"),
                    block_seed.get("intent", "New discussion"),
                )
                self.graph.add_block(new_block)
                created_blocks.append(new_block)
                print(f"  [NEW] Created new block: '{new_block.title}'")

            target_block = created_blocks[0]
            self.graph.current_block_id = target_block.block_id
        
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
        self.storage.save(self.mindmap)
        
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
        if not self.graph or block_id not in self.graph.blocks:
            return "Block not found"
        
        self.graph.current_block_id = block_id
        block = self.graph.blocks[block_id]
        self.storage.save(self.mindmap)
        
        summary = f"\n[BLOCK] Switched to: {block.title}\n"
        summary += f"Intent: {block.intent}\n"
        summary += f"Summary: {block.summary or '(not yet summarized)'}\n"
        summary += f"Messages: {len(block.conversation_refs)}"
        
        return summary

    def print_mindmap(self) -> None:
        """Print the block tree."""
        print("\n[MINDMAP] CONVERSATION GRAPH:")
        if not self.graph:
            print("(no active graph)")
            return
        print_block_tree(self.graph)

    def export_graph(self) -> dict:
        """Export graph as dict (for visualization, etc)."""
        if not self.graph:
            return {}
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

    def list_graphs(self) -> list[tuple[str, str]]:
        summaries = []
        for graph_id, graph in self.mindmap.graphs.items():
            title = "Untitled graph"
            if graph.root_block_id and graph.root_block_id in graph.blocks:
                title = graph.blocks[graph.root_block_id].title
            summaries.append((graph_id, title))
        return summaries

    def switch_graph(self, graph_id: str) -> str:
        if graph_id not in self.mindmap.graphs:
            return "Graph not found"
        self.mindmap.current_graph_id = graph_id
        self.graph = self.mindmap.graphs[graph_id]
        self.storage.save(self.mindmap)
        title = "Untitled graph"
        if self.graph.root_block_id in self.graph.blocks:
            title = self.graph.blocks[self.graph.root_block_id].title
        return f"\n[GRAPH] Switched to: {title}\nGraph ID: {graph_id}"