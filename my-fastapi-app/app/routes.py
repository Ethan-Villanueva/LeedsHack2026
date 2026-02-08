from fastapi import Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import sys
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add mindmap_chat to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../mindmap_chat")))

from app import app, templates
from models import ConversationMessage, Block, Mindmap
from storage import JSONStorage
from conversation import ConversationManager
from llm.gemini import GeminiClient
from config import validate_config

# Initialize backends (lazy - only validate when actually needed)
storage = None
llm_client = None
conversation_mgr = None

def get_storage():
    """Lazy initialize storage."""
    global storage
    if storage is None:
        # Use absolute path relative to the repo root
        import os
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        data_file = os.path.join(repo_root, "mindmap_chat", "data", "conversation.json")
        storage = JSONStorage(data_file)
    return storage

def get_llm_client():
    """Lazy initialize LLM client."""
    global llm_client
    if llm_client is None:
        validate_config()  # Only validate when needed
        llm_client = GeminiClient()
    return llm_client

def get_conversation_manager():
    """Lazy initialize conversation manager."""
    global conversation_mgr
    if conversation_mgr is None:
        conversation_mgr = ConversationManager(get_llm_client(), get_storage())
    return conversation_mgr


# ============= Request/Response Models =============

class MessageRequest(BaseModel):
    """Request to add a message to a block."""
    content: str


class MessageResponse(BaseModel):
    """Response containing block messages."""
    messages: List[Dict[str, Any]]
    current_block_id: str


# ============= Frontend Pages =============

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


# ============= REST API Endpoints =============

@app.get("/api/mindmaps")
async def list_mindmaps():
    """
    List all mindmaps (graphs).
    
    Returns:
        List of mindmap summaries with id, title, root_block_id
    """
    mindmap = get_storage().load()
    
    mindmaps_list = []
    for graph_id, graph in mindmap.graphs.items():
        root_block = graph.blocks.get(graph.root_block_id)
        mindmaps_list.append({
            "graph_id": graph_id,
            "title": root_block.title if root_block else "Untitled",
            "root_block_id": graph.root_block_id,
            "block_count": len(graph.blocks),
            "message_count": len(graph.messages),
            "is_current": graph_id == mindmap.current_graph_id,
        })
    
    return {"mindmaps": mindmaps_list}


@app.post("/api/mindmaps/new")
async def create_new_mindmap():
    """
    Create a new empty mindmap with a root block.
    
    Returns:
        New mindmap with root block ready for chat
    """
    import uuid
    from models import ConversationGraph
    
    mindmap = get_storage().load()
    
    # Create new graph with root block
    graph = ConversationGraph()
    root_block = Block(
        title="New Mindmap",
        intent="",
        summary="",
        key_points=[],
        open_questions=[],
    )
    graph.add_block(root_block)
    
    # Add graph to mindmap
    mindmap.add_graph(graph)
    mindmap.current_graph_id = graph.graph_id
    
    # Save
    get_storage().save(mindmap)
    
    return {
        "graph_id": graph.graph_id,
        "title": root_block.title,
        "root_block_id": root_block.block_id,
        "block_count": 1,
        "message_count": 0,
        "is_current": True,
    }


@app.get("/api/mindmaps/{graph_id}/graph")
async def get_graph(graph_id: str):
    """
    Get full graph data for D3 visualization.
    
    Args:
        graph_id: ID of the graph
        
    Returns:
        D3-formatted graph with nodes and links
    """
    mindmap = get_storage().load()
    graph = mindmap.graphs.get(graph_id)
    
    if not graph:
        raise HTTPException(status_code=404, detail=f"Graph {graph_id} not found")
    
    return graph.to_d3_graph()


@app.get("/api/blocks/{block_id}/messages")
async def get_block_messages(block_id: str):
    """
    Get all messages for a specific block.
    
    Args:
        block_id: ID of the block
        
    Returns:
        List of messages in the block
    """
    mindmap = get_storage().load()
    
    # Find the graph containing this block
    graph = None
    for g in mindmap.graphs.values():
        if block_id in g.blocks:
            graph = g
            break
    
    if not graph:
        raise HTTPException(status_code=404, detail=f"Block {block_id} not found")
    
    block = graph.blocks[block_id]
    messages = graph.get_block_messages(block_id)
    
    # Convert to JSON-serializable format
    messages_list = [
        {
            "message_id": msg.message_id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp,
        }
        for msg in messages
    ]
    
    return {
        "block_id": block_id,
        "title": block.title,
        "intent": block.intent,
        "summary": block.summary,
        "messages": messages_list,
    }


@app.post("/api/blocks/{block_id}/messages")
async def add_message_to_block(block_id: str, payload: MessageRequest, background_tasks: BackgroundTasks):
    """
    Add a user message to a block and get LLM response.
    
    Args:
        block_id: ID of the block
        payload: MessageRequest with message content
        
    Returns:
        Updated messages and assistant response
    """
    mindmap = get_storage().load()
    
    # Find the graph containing this block
    graph = None
    for gid, g in mindmap.graphs.items():
        if block_id in g.blocks:
            graph = g
            mindmap.current_graph_id = gid  # Switch to this graph
            break
    
    if not graph:
        raise HTTPException(status_code=404, detail=f"Block {block_id} not found")
    
    # Update conversation manager context
    mgr = get_conversation_manager()
    mgr.mindmap = mindmap
    mgr.graph = graph
    mgr.graph.current_block_id = block_id
    
    # Get block metadata
    block = graph.blocks[block_id]
    
    # Create user message
    user_msg = ConversationMessage(
        block_id=block_id,
        role="user",
        content=payload.content,
    )
    graph.add_message(user_msg)
    block.add_message_ref(user_msg.message_id)
    
    # Get LLM response (for now, synchronous; can be made async with WebSocket)
    try:
        # Build context from block
        context = f"Block: {block.title}\nIntent: {block.intent}\n\nUser: {payload.content}"
        response_text = mgr.llm.call(context)
        
        # Create assistant message
        assistant_msg = ConversationMessage(
            block_id=block_id,
            role="assistant",
            content=response_text,
        )
        graph.add_message(assistant_msg)
        block.add_message_ref(assistant_msg.message_id)
        
        # Save updated graph
        get_storage().save(mindmap)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
    
    # Get updated messages
    messages = graph.get_block_messages(block_id)
    messages_list = [
        {
            "message_id": msg.message_id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp,
        }
        for msg in messages
    ]
    
    return {
        "block_id": block_id,
        "messages": messages_list,
        "current_block_id": block_id,
    }


@app.post("/api/blocks/{block_id}/switch")
async def switch_to_block(block_id: str):
    """
    Switch the active block (for UI context).
    
    Args:
        block_id: ID of the block to switch to
        
    Returns:
        Updated current block info
    """
    mindmap = get_storage().load()
    
    # Find the graph containing this block
    for gid, g in mindmap.graphs.items():
        if block_id in g.blocks:
            mindmap.current_graph_id = gid
            g.current_block_id = block_id
            get_storage().save(mindmap)
            return {
                "block_id": block_id,
                "graph_id": gid,
                "success": True,
            }
    
    raise HTTPException(status_code=404, detail=f"Block {block_id} not found")


@app.post("/api/mindmaps/{graph_id}/switch")
async def switch_mindmap(graph_id: str):
    """
    Switch the active mindmap (graph).
    
    Args:
        graph_id: ID of the graph to switch to
        
    Returns:
        Updated current mindmap info
    """
    mindmap = get_storage().load()
    
    if graph_id not in mindmap.graphs:
        raise HTTPException(status_code=404, detail=f"Graph {graph_id} not found")
    
    mindmap.current_graph_id = graph_id
    get_storage().save(mindmap)
    
    return {
        "graph_id": graph_id,
        "success": True,
    }
