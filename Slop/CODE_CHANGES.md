# Code Changes Summary

## Files Modified
1. **routes.py** - Backend API endpoints
2. **main.js** - Frontend user interface

---

## Routes.py Changes

### 1. Added StartConversationRequest Model

**Location**: After MessageRequest class definition

```python
class StartConversationRequest(BaseModel):
    """Request to start a new conversation."""
    topic: str


class MessageRequest(BaseModel):
    """Request to add a message to a block."""
    content: str


class MessageResponse(BaseModel):
    """Response containing block messages."""
    messages: List[Dict[str, Any]]
    current_block_id: str
```

**Purpose**: Validates incoming request for starting a new conversation with a topic parameter.

---

### 2. Updated POST /api/mindmaps/new Endpoint

**Before**:
```python
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
```

**After**:
```python
@app.post("/api/mindmaps/new")
async def create_new_mindmap(payload: StartConversationRequest):
    """
    Start a new conversation using ConversationManager.
    Calls manager.start_new_conversation(topic).
    
    Args:
        payload: StartConversationRequest with topic
        
    Returns:
        New mindmap with root block and initial response
    """
    mgr = get_conversation_manager()
    
    # Use manager to start conversation (this creates the graph structure)
    response_text = mgr.start_new_conversation(payload.topic)
    
    # Get the current graph (just created)
    mindmap = get_storage().load()
    graph = mindmap.graphs.get(mindmap.current_graph_id)
    root_block = graph.blocks.get(graph.root_block_id)
    
    return {
        "graph_id": graph.graph_id,
        "title": root_block.title,
        "root_block_id": root_block.block_id,
        "block_count": len(graph.blocks),
        "message_count": len(graph.messages),
        "is_current": True,
        "initial_response": response_text,
    }
```

**Key Changes**:
- ✅ Accept `topic` parameter via `StartConversationRequest`
- ✅ Call `manager.start_new_conversation(payload.topic)` instead of creating empty graph
- ✅ Return `initial_response` from LLM
- ✅ No more hardcoded "New Mindmap" title - uses user's topic

**Why**: Uses ConversationManager for consistent behavior with CLI, respects user's topic input, includes LLM response.

---

### 3. Updated POST /api/blocks/{block_id}/messages Endpoint

**Before**:
```python
@app.post("/api/blocks/{block_id}/messages")
async def add_message_to_block(block_id: str, payload: MessageRequest, background_tasks: BackgroundTasks):
    """
    Add a user message to a block and get LLM response.
    ...
    """
    mindmap = get_storage().load()
    
    # Find the graph containing this block
    graph = None
    for gid, g in mindmap.graphs.items():
        if block_id in g.blocks:
            graph = g
            mindmap.current_graph_id = gid
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
```

**After**:
```python
@app.post("/api/blocks/{block_id}/messages")
async def add_message_to_block(block_id: str, payload: MessageRequest, background_tasks: BackgroundTasks):
    """
    Add a user message to a block and get LLM response using ConversationManager.
    Calls manager.continue_conversation(content).
    
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
    
    # Update conversation manager context and use it to continue conversation
    mgr = get_conversation_manager()
    mgr.mindmap = mindmap
    mgr.graph = graph
    mgr.graph.current_block_id = block_id
    
    # Use manager to continue conversation
    try:
        response_text = mgr.continue_conversation(payload.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")
    
    # Save updated graph
    get_storage().save(mindmap)
    
    # Get updated messages for this block
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
```

**Key Changes**:
- ✅ Call `manager.continue_conversation(payload.content)` instead of manual message creation
- ✅ Manager handles message creation, LLM call, and all logic
- ✅ Simplified code by delegating to manager
- ✅ Same behavior as CLI's `continue_conversation` method

**Why**: Uses ConversationManager for all conversation logic, consistent with CLI, cleaner code, manager handles all edge cases.

---

## Main.js Changes

### 1. Updated /new Command Handler

**Before**:
```javascript
// Check for /new command
if (message === '/new') {
    input.value = '';
    autoResizeTextarea();
    
    // Create new mindmap
    try {
        const response = await fetch('/api/mindmaps/new', { method: 'POST' });
        if (!response.ok) throw new Error('Failed to create mindmap');
        
        const newMindmap = await response.json();
        
        // Refresh mindmap list
        const mindmaps = await fetchMindmaps();
        allMindmaps = mindmaps;
        
        const mindmapList = document.querySelector('.mindmap-list');
        mindmapList.innerHTML = '';
        
        mindmaps.forEach((mindmap, index) => {
            const li = document.createElement('li');
            li.className = 'mindmap-item' + (mindmap.is_current ? ' active' : '');
            li.innerHTML = `
                <span class="mindmap-title">${mindmap.title}</span>
                <button class="mindmap-delete-btn" onclick="deleteMindmap(event, '${mindmap.graph_id}')">x</button>
            `;
            li.onclick = function() { selectMindmap(this, mindmap.graph_id); };
            mindmapList.appendChild(li);
        });
        
        // Select the new mindmap
        const firstItem = mindmapList.querySelector('.mindmap-item');
        if (firstItem) {
            await selectMindmap(firstItem, newMindmap.graph_id);
        }
        
        // Show success message
        const chatMessages = document.getElementById('chatMessages');
        const sysWrapper = document.createElement('div');
        sysWrapper.className = 'chat-message-wrapper system';
        sysWrapper.innerHTML = `<div class="chat-message"><div class="chat-bubble" style="background-color: #e8f5e9; color: #2e7d32;">✓ New mindmap created: "${newMindmap.title}"</div></div>`;
        chatMessages.appendChild(sysWrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        console.error('Error creating mindmap:', error);
        const chatMessages = document.getElementById('chatMessages');
        const errWrapper = document.createElement('div');
        errWrapper.className = 'chat-message-wrapper system';
        errWrapper.innerHTML = `<div class="chat-message"><div class="chat-bubble" style="background-color: #ffebee; color: #c62828;">✗ Error creating mindmap</div></div>`;
        chatMessages.appendChild(errWrapper);
    }
    return;
}
```

**After**:
```javascript
// Check for /new command - prompt for topic and use ConversationManager
if (message === '/new') {
    input.value = '';
    autoResizeTextarea();
    
    // Prompt user for topic using ConversationManager.start_new_conversation flow
    const topic = prompt('What would you like to discuss?');
    if (!topic) return;  // User cancelled
    
    try {
        const response = await fetch('/api/mindmaps/new', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic })
        });
        if (!response.ok) throw new Error('Failed to create mindmap');
        
        const newMindmap = await response.json();
        
        // Refresh mindmap list
        const mindmaps = await fetchMindmaps();
        allMindmaps = mindmaps;
        
        const mindmapList = document.querySelector('.mindmap-list');
        mindmapList.innerHTML = '';
        
        mindmaps.forEach((mindmap, index) => {
            const li = document.createElement('li');
            li.className = 'mindmap-item' + (mindmap.is_current ? ' active' : '');
            li.innerHTML = `
                <span class="mindmap-title">${mindmap.title}</span>
                <button class="mindmap-delete-btn" onclick="deleteMindmap(event, '${mindmap.graph_id}')">x</button>
            `;
            li.onclick = function() { selectMindmap(this, mindmap.graph_id); };
            mindmapList.appendChild(li);
        });
        
        // Select the new mindmap
        const firstItem = mindmapList.querySelector('.mindmap-item');
        if (firstItem) {
            await selectMindmap(firstItem, newMindmap.graph_id);
        }
        
        // Show success and initial response from manager.start_new_conversation
        const chatMessages = document.getElementById('chatMessages');
        const sysWrapper = document.createElement('div');
        sysWrapper.className = 'chat-message-wrapper system';
        sysWrapper.innerHTML = `<div class="chat-message"><div class="chat-bubble" style="background-color: #e8f5e9; color: #2e7d32;">✓ Mindmap created!</div></div>`;
        chatMessages.appendChild(sysWrapper);
        
        if (newMindmap.initial_response) {
            const assistantWrapper = document.createElement('div');
            assistantWrapper.className = 'chat-message-wrapper assistant';
            const timestamp = new Date().toLocaleTimeString();
            assistantWrapper.innerHTML = `
                <div class="chat-message">
                    <div class="chat-bubble">${newMindmap.initial_response}</div>
                    <div class="chat-timestamp">${timestamp}</div>
                </div>
            `;
            chatMessages.appendChild(assistantWrapper);
        }
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } catch (error) {
        console.error('Error creating mindmap:', error);
        const chatMessages = document.getElementById('chatMessages');
        const errWrapper = document.createElement('div');
        errWrapper.className = 'chat-message-wrapper system';
        errWrapper.innerHTML = `<div class="chat-message"><div class="chat-bubble" style="background-color: #ffebee; color: #c62828;">✗ Error creating mindmap</div></div>`;
        chatMessages.appendChild(errWrapper);
    }
    return;
}
```

**Key Changes**:
- ✅ Added `prompt('What would you like to discuss?')` to get topic from user
- ✅ Changed POST request to include JSON body with topic
- ✅ Display `newMindmap.initial_response` from manager
- ✅ Check for topic input cancellation

**Why**: Mirrors CLI flow where user is prompted for topic, sends topic to manager via API, displays initial response from LLM.

---

### 2. Updated addMindmap Function

**Before**:
```javascript
// Add mindmap function - creates new mindmap
async function addMindmap() {
    try {
        const response = await fetch('/api/mindmaps/new', { method: 'POST' });
        if (!response.ok) throw new Error('Failed to create mindmap');
        
        const newMindmap = await response.json();
        
        // Refresh mindmap list
        const mindmaps = await fetchMindmaps();
        allMindmaps = mindmaps;
        
        const mindmapList = document.querySelector('.mindmap-list');
        mindmapList.innerHTML = '';
        
        mindmaps.forEach((mindmap) => {
            const li = document.createElement('li');
            li.className = 'mindmap-item' + (mindmap.is_current ? ' active' : '');
            li.innerHTML = `
                <span class="mindmap-title">${mindmap.title}</span>
                <button class="mindmap-delete-btn" onclick="deleteMindmap(event, '${mindmap.graph_id}')">x</button>
            `;
            li.onclick = function() { selectMindmap(this, mindmap.graph_id); };
            mindmapList.appendChild(li);
        });
        
        // Select the new mindmap
        const firstItem = mindmapList.querySelector('.mindmap-item');
        if (firstItem) {
            await selectMindmap(firstItem, newMindmap.graph_id);
        }
    } catch (error) {
        console.error('Error creating mindmap:', error);
        alert('Failed to create new mindmap');
    }
}
```

**After**:
```javascript
// Add mindmap function - creates new mindmap via ConversationManager
async function addMindmap() {
    // Prompt user for topic using ConversationManager.start_new_conversation flow
    const topic = prompt('What would you like to discuss?');
    if (!topic) return;  // User cancelled
    
    try {
        const response = await fetch('/api/mindmaps/new', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic })
        });
        if (!response.ok) throw new Error('Failed to create mindmap');
        
        const newMindmap = await response.json();
        
        // Refresh mindmap list
        const mindmaps = await fetchMindmaps();
        allMindmaps = mindmaps;
        
        const mindmapList = document.querySelector('.mindmap-list');
        mindmapList.innerHTML = '';
        
        mindmaps.forEach((mindmap) => {
            const li = document.createElement('li');
            li.className = 'mindmap-item' + (mindmap.is_current ? ' active' : '');
            li.innerHTML = `
                <span class="mindmap-title">${mindmap.title}</span>
                <button class="mindmap-delete-btn" onclick="deleteMindmap(event, '${mindmap.graph_id}')">x</button>
            `;
            li.onclick = function() { selectMindmap(this, mindmap.graph_id); };
            mindmapList.appendChild(li);
        });
        
        // Select the new mindmap
        const firstItem = mindmapList.querySelector('.mindmap-item');
        if (firstItem) {
            await selectMindmap(firstItem, newMindmap.graph_id);
        }
    } catch (error) {
        console.error('Error creating mindmap:', error);
        alert('Failed to create new mindmap');
    }
}
```

**Key Changes**:
- ✅ Added prompt for topic input
- ✅ Changed to POST with JSON body including topic
- ✅ Same topic-based flow as /new command

**Why**: Consistent UX - both paths (button and /new command) follow same flow.

---

## Summary of Changes

### Routes.py
| Change | Purpose |
|--------|---------|
| Added `StartConversationRequest` | Validate topic parameter from frontend |
| Rewrote `/api/mindmaps/new` | Call `manager.start_new_conversation(topic)` |
| Simplified `/api/blocks/{id}/messages` POST | Call `manager.continue_conversation(content)` |

### Main.js
| Change | Purpose |
|--------|---------|
| Added topic prompt in `/new` handler | Mirror CLI: ask user what to discuss |
| Updated /new to use StartConversationRequest | Send topic to backend |
| Display `initial_response` from manager | Show LLM response from conversation start |
| Updated `addMindmap()` function | Same topic-based flow |

### Net Result
- ✅ All conversation logic uses ConversationManager
- ✅ Frontend prompts mimic CLI prompts
- ✅ API requests use proper request models
- ✅ No duplication of conversation logic
- ✅ GUI workflow mirrors CLI workflow
