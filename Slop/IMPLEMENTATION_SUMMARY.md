# ConversationManager Integration Summary

## Overview
All frontend and backend operations now properly use `ConversationManager` from `main.py` via REST API endpoints. The GUI implementation mirrors the CLI workflow while maintaining separation of concerns.

## Key Changes

### 1. Backend (routes.py) - Now uses ConversationManager

#### Added StartConversationRequest Model
```python
class StartConversationRequest(BaseModel):
    """Request to start a new conversation."""
    topic: str
```

#### Updated API Endpoints

**POST /api/mindmaps/new** - Now uses `manager.start_new_conversation(topic)`
- Accepts topic as parameter
- Calls `mgr.start_new_conversation(payload.topic)` 
- Returns: graph_id, title, root_block_id, initial_response
- Equivalent to CLI: `/new` command followed by user input

**POST /api/blocks/{block_id}/messages** - Now uses `manager.continue_conversation(content)`
- Sends user message to block
- Calls `mgr.continue_conversation(payload.content)` 
- Returns: updated messages list with assistant response
- Equivalent to CLI: typing a message in the conversation

**GET /api/blocks/{block_id}/messages** - Uses `graph.get_block_messages(block_id)`
- Fetches all messages for a block
- Returns: block metadata + message list
- Equivalent to CLI: `/view <block_id>` command

**GET /api/mindmaps** - Lists all mindmaps
- Returns: mindmap summaries with current status
- Equivalent to CLI: `/graphs` command

### 2. Frontend (main.js) - Now mirrors CLI workflow

#### New Flow for Creating Mindmap

**Before:**
```javascript
// /new command -> create empty mindmap
await fetch('/api/mindmaps/new', { method: 'POST' })
```

**After:**
```javascript
// /new command -> PROMPT USER FOR TOPIC -> call manager.start_new_conversation
const topic = prompt('What would you like to discuss?');
const response = await fetch('/api/mindmaps/new', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic: topic })
});
const newMindmap = await response.json();
// Display initial_response from manager.start_new_conversation
```

#### Block Selection Flow

When user clicks a node in D3 graph:
1. `switchBlock(blockId)` - updates active block context
2. `loadBlockMessages(blockId)` - calls `GET /api/blocks/{blockId}/messages`
3. Displays messages in right chat panel using `manager.get_block_messages`

#### Message Sending Flow

When user types a message and sends:
1. Add message to UI (optimistic)
2. Call `sendMessageToBlock(blockId, message)` -> POST to `/api/blocks/{blockId}/messages`
3. Backend calls `manager.continue_conversation(content)`
4. Receive assistant response
5. Update UI with all messages

## ConversationManager Methods Used

| Method | Used By | Purpose |
|--------|---------|---------|
| `manager.start_new_conversation(topic)` | POST /api/mindmaps/new | Create new graph with root block + initial response |
| `manager.continue_conversation(content)` | POST /api/blocks/{id}/messages | Get LLM response for user message in current context |
| `manager.switch_block(block_id)` | (Available but not needed - context set via API) | Switch active block |
| `graph.get_block_messages(block_id)` | GET /api/blocks/{id}/messages | Fetch messages for a block |

## User Workflow (GUI)

1. **Create Mindmap:**
   - Click "Add New" or type `/new` in chat
   - Prompted: "What would you like to discuss?"
   - Calls `manager.start_new_conversation(topic)`
   - Shows: Initial response + mindmap in graph

2. **View Block Messages:**
   - Click a node in D3 graph
   - Right panel shows all messages for that block
   - Uses `manager.get_block_messages(block_id)`

3. **Continue Conversation:**
   - Type message in input
   - Click send (or Ctrl+Enter)
   - Calls `manager.continue_conversation(message)`
   - Shows assistant response
   - Graph updates with new connections

4. **Switch Blocks:**
   - Click different nodes
   - Active block context changes
   - Messages reload for new block

## Equivalence with CLI

| GUI Action | CLI Equivalent |
|-----------|-----------------|
| Click "Add New" + topic prompt | `/new` + user input |
| Click graph node | `/switch <block_id>` |
| View block messages on right | `/view <block_id>` |
| Type message + send | Type message in CLI |
| Graph visualization | `/map` command |

## Testing Results

✅ All endpoints tested and working:
- POST /api/mindmaps/new with topic -> creates conversation via manager
- GET /api/blocks/{id}/messages -> returns messages from manager
- POST /api/blocks/{id}/messages -> continues conversation via manager
- Manager methods properly called with correct context

✅ Frontend changes:
- /new command now prompts for topic via GUI modal
- addMindmap function also prompts for topic
- Block click handlers properly load messages from backend
- All API calls use JSON payloads as required

## Architecture Benefits

1. **Single Source of Truth**: ConversationManager logic used everywhere (CLI + Web)
2. **Uniform Behavior**: GUI and CLI have identical conversation flows
3. **Separation of Concerns**: Frontend just calls APIs, backend uses manager
4. **Lazy Initialization**: Manager only instantiated when needed
5. **Atomic Operations**: All data changes are atomic via storage
6. **Type Safety**: Request/response models validated with Pydantic
