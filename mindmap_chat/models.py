"""
Core data structures for the mindmap chat system.
These are JSON-serializable and represent the conversation graph.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import uuid
import json
from datetime import datetime


@dataclass
class ConversationMessage:
    """A single message in the conversation."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    block_id: str = ""
    role: str = "user"  # "user" or "assistant"
    content: str = ""
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    embedding: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        return cls(**data)


@dataclass
class Block:
    """A node in the conversation graph (mindmap block)."""
    block_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_block_id: Optional[str] = None
    title: str = ""
    intent: str = ""
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    embedding: List[float] = field(default_factory=list)  # Intent embedding
    children: List[str] = field(default_factory=list)
    conversation_refs: List[str] = field(default_factory=list)  # message_ids

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Block":
        return cls(**data)

    def add_message_ref(self, message_id: str):
        """Add a message ID reference to this block."""
        if message_id not in self.conversation_refs:
            self.conversation_refs.append(message_id)

    def add_child(self, block_id: str):
        """Add a child block."""
        if block_id not in self.children:
            self.children.append(block_id)


@dataclass
class ConversationGraph:
    """The entire conversation state."""
    root_block_id: str = ""
    blocks: Dict[str, Block] = field(default_factory=dict)
    messages: Dict[str, ConversationMessage] = field(default_factory=dict)
    current_block_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "root_block_id": self.root_block_id,
            "blocks": {bid: block.to_dict() for bid, block in self.blocks.items()},
            "messages": {mid: msg.to_dict() for mid, msg in self.messages.items()},
            "current_block_id": self.current_block_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationGraph":
        blocks = {
            bid: Block.from_dict(block_data)
            for bid, block_data in data.get("blocks", {}).items()
        }
        messages = {
            mid: ConversationMessage.from_dict(msg_data)
            for mid, msg_data in data.get("messages", {}).items()
        }
        return cls(
            root_block_id=data.get("root_block_id", ""),
            blocks=blocks,
            messages=messages,
            current_block_id=data.get("current_block_id", ""),
            metadata=data.get("metadata", {}),
        )

    def add_block(self, block: Block):
        """Add a block to the graph."""
        self.blocks[block.block_id] = block

    def add_message(self, message: ConversationMessage):
        """Add a message to the graph."""
        self.messages[message.message_id] = message

    def get_block_messages(self, block_id: str) -> List[ConversationMessage]:
        """Get all messages for a block."""
        block = self.blocks.get(block_id)
        if not block:
            return []
        return [self.messages[mid] for mid in block.conversation_refs if mid in self.messages]


@dataclass
class BlockClassification:
    """Output from intent classifier."""
    action: str  # "continue" | "deepen" | "new_sibling" | "new_child" | "tangent"
    confidence: float
    reasoning: str
    new_block_title: Optional[str] = None
    new_block_intent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
