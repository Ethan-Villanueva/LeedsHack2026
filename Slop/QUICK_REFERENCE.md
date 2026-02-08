# Quick Reference Guide

## Using the Web GUI

### Starting a New Mindmap

**Method 1: Click "Add New" Button**
1. Click the "Add New" button (top of left panel)
2. Enter topic: "e.g., Python async programming"
3. System calls `manager.start_new_conversation(topic)`
4. Displays initial LLM response + D3 graph

**Method 2: Type /new Command**
1. Type `/new` in chat input
2. Prompted: "What would you like to discuss?"
3. Enter topic
4. Same flow as Method 1

### Viewing Block Messages

1. Click any node in the D3 graph
2. Node highlights in red
3. Right panel shows all messages for that block
4. Uses `graph.get_block_messages(block_id)`

### Sending a Message

1. Type your question/statement in chat input
2. Press Enter (or Ctrl+Enter for newline)
3. Message appears immediately (optimistic update)
4. Backend calls `manager.continue_conversation(message)`
5. LLM response appears in chat
6. Graph updates if new relationships detected

### Switching Between Mindmaps

1. Click mindmap name in left sidebarpanel
2. Mindmap becomes active (highlighted)
3. D3 graph refreshes
4. Messages panel updates

### Deleting a Mindmap

- **GUI**: Not yet implemented (use CLI)
- **CLI**: Use `/delete` command

---

## API Endpoints Reference

### Create New Mindmap
```
POST /api/mindmaps/new
Content-Type: application/json

{
    "topic": "User's discussion topic"
}

Returns:
{
    "graph_id": "uuid",
    "title": "Auto-generated from topic",
    "root_block_id": "uuid",
    "initial_response": "LLM response",
    ...
}
```

**Calls**: `manager.start_new_conversation(topic)`

---

### List All Mindmaps
```
GET /api/mindmaps

Returns:
{
    "mindmaps": [
        {
            "graph_id": "uuid",
            "title": "Mindmap Title",
            "root_block_id": "uuid",
            "block_count": 5,
            "message_count": 42,
            "is_current": true
        }
    ]
}
```

---

### Get Graph Data (for D3 visualization)
```
GET /api/mindmaps/{graph_id}/graph

Returns:
{
    "nodes": [
        {
            "id": "block_id",
            "label": "Block Title",
            "intent": "...",
            "message_count": 3,
            "is_current": true
        }
    ],
    "links": [
        {
            "source": "block_id_1",
            "target": "block_id_2",
            "relation": "related_to",
            "confidence": 0.95,
            "color": "#FF6B6B",
            "strokeWidth": 2
        }
    ],
    "root_block_id": "uuid"
}
```

---

### Get Block Messages
```
GET /api/blocks/{block_id}/messages

Returns:
{
    "block_id": "uuid",
    "title": "Block Title",
    "intent": "Block intent",
    "messages": [
        {
            "message_id": "uuid",
            "role": "user",
            "content": "User message",
            "timestamp": 1234567890
        },
        {
            "message_id": "uuid",
            "role": "assistant",
            "content": "Assistant response",
            "timestamp": 1234567891
        }
    ]
}
```

**Calls**: `graph.get_block_messages(block_id)`

---

### Send Message to Block
```
POST /api/blocks/{block_id}/messages
Content-Type: application/json

{
    "content": "User's message/question"
}

Returns:
{
    "block_id": "uuid",
    "messages": [
        /* Updated message list with new user and assistant messages */
    ],
    "current_block_id": "uuid"
}
```

**Calls**: `manager.continue_conversation(content)`

---

### Switch to Block
```
POST /api/blocks/{block_id}/switch

Returns:
{
    "block_id": "uuid",
    "graph_id": "uuid",
    "success": true
}
```

---

### Switch Mindmap (Graph)
```
POST /api/mindmaps/{graph_id}/switch

Returns:
{
    "graph_id": "uuid",
    "success": true
}
```

---

## Data Model

### Block
```python
class Block:
    id: str  # UUID
    title: str
    intent: str  # What user wants to explore
    summary: str
    key_points: List[str]
    open_questions: List[str]
    message_ids: List[str]  # References to messages
```

### ConversationMessage
```python
class ConversationMessage:
    message_id: str  # UUID
    block_id: str  # Which block this message belongs to
    role: str  # "user" or "assistant"
    content: str  # Message text
    timestamp: int  # Unix timestamp
```

### ConversationGraph (Mindmap)
```python
class ConversationGraph:
    graph_id: str  # UUID
    root_block_id: str  # Root of the conversation
    blocks: Dict[str, Block]  # block_id -> Block
    messages: List[ConversationMessage]  # All messages in graph
    current_block_id: str  # Currently active block
```

### Mindmap (Container)
```python
class Mindmap:
    graphs: Dict[str, ConversationGraph]  # graph_id -> Graph
    current_graph_id: str  # Currently active graph
```

---

## Frontend JavaScript Functions

### API Wrappers
- `fetchMindmaps()` - GET /api/mindmaps
- `fetchGraphData(graphId)` - GET /api/mindmaps/{graphId}/graph
- `fetchBlockMessages(blockId)` - GET /api/blocks/{blockId}/messages
- `sendMessageToBlock(blockId, content)` - POST /api/blocks/{blockId}/messages
- `switchBlock(blockId)` - POST /api/blocks/{blockId}/switch
- `addMindmap()` - Prompts and creates new mindmap

### UI Functions
- `selectMindmap(element, graphId)` - Switch active mindmap
- `drawMindmap(graphData)` - Render D3 force-directed graph
- `loadBlockMessages(blockId)` - Display messages in right panel
- `sendMessage()` - Handle chat input submission
- `autoResizeTextarea()` - Auto-expand message input

---

## Storage

### File Location
```
mindmap_chat/data/conversation.json
```

### Format
```json
{
    "current_graph_id": "uuid",
    "graphs": {
        "uuid": {
            "graph_id": "uuid",
            "root_block_id": "uuid",
            "current_block_id": "uuid",
            "blocks": {
                "block_uuid": {
                    "block_id": "block_uuid",
                    "title": "...",
                    "intent": "...",
                    "message_ids": ["msg_uuid1", "msg_uuid2"]
                }
            },
            "messages": [
                {
                    "message_id": "msg_uuid",
                    "block_id": "block_uuid",
                    "role": "user",
                    "content": "...",
                    "timestamp": 1234567890
                }
            ]
        }
    }
}
```

### Atomicity
- All writes use `tempfile` + `os.replace`
- Thread-safe with lock in JSONStorage
- No partial writes or corruption

---

## Troubleshooting

### Mindmap not appearing
- Check: Does `/api/mindmaps` return data?
- Check: Is conversation.json created?
- Check: Is backend running?

### Messages not loading
- Check: Does `/api/blocks/{id}/messages` return data?
- Check: Is block_id correct?
- Check: Are messages in storage?

### Chat not responding
- Check: Is Gemini API key set in .env?
- Check: Is backend returning 500 error?
- Check: Check browser console for JavaScript errors

### Graph not rendering
- Check: Does `/api/mindmaps/{id}/graph` return nodes?
- Check: Is D3 library loaded?
- Check: Is SVG element present in HTML?

---

## CLI Reference (for comparison)

### Create Conversation
```
> /new
What do you want to discuss? > Machine Learning
[Creates graph + gets initial response]
```

### View Messages
```
> /view <block_id>
[Lists all messages in block]
```

### Switch Block
```
> /switch <block_id>
[Switches context]
```

### List Mindmaps
```
> /graphs
[Lists all graphs]
```

### Continue Conversation
```
> [Just type a message]
[Calls manager.continue_conversation]
```

---

## Performance Notes

- First mindmap creation: ~2-3 seconds (LLM latency)
- Message sending: ~1-2 seconds (LLM + storage)
- Graph rendering: <100ms
- File I/O: <10ms (atomic writes)
- API calls: <100ms (excluding LLM)

---

## Architecture Comparison

### CLI (main.py)
```python
manager = ConversationManager(llm, storage)
response = manager.start_new_conversation(topic)
response = manager.continue_conversation(msg)
messages = manager.graph.get_block_messages(id)
```

### Web GUI (main.js + routes.py)
```javascript
// Frontend
await fetch('/api/mindmaps/new', { topic })
await fetch('/api/blocks/{id}/messages', { content })
await fetch('/api/blocks/{id}/messages')

// Backend (routes.py)
manager.start_new_conversation(topic)
manager.continue_conversation(content)
graph.get_block_messages(block_id)
```

**Same ConversationManager, different interface** ✅
