# ConversationManager Integration Flow

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (main.js)                          │
│                                                                   │
│  User Interactions:                                              │
│  ├─ Click "Add New" -> showTopicModal() -> user enters topic    │
│  ├─ Click graph node -> switchBlock() + loadBlockMessages()      │
│  └─ Type message -> sendMessage() -> sendMessageToBlock()        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ REST API (JSON)
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      FASTAPI BACKEND (routes.py)                │
│                                                                   │
│  Endpoints (Lazy initialized with ConversationManager):         │
│                                                                   │
│  POST /api/mindmaps/new ──────┐                                 │
│                               │ Calls manager methods            │
│  POST /api/blocks/{id}/messages ┤                               │
│                               │                                  │
│  GET /api/blocks/{id}/messages┘                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Uses ConversationManager
                             │
┌────────────────────────────▼────────────────────────────────────┐
│         CONVERSATION MANAGER & CORE LOGIC (conversation.py)     │
│                                                                   │
│  manager.start_new_conversation(topic)                          │
│  └─ Creates new graph                                            │
│  └─ Creates root block from topic                               │
│  └─ Gets LLM response                                            │
│  └─ Saves to storage                                             │
│  └─ Returns initial response                                     │
│                                                                   │
│  manager.continue_conversation(content)                         │
│  └─ Adds user message to current block                          │
│  └─ Gets LLM response in context                                │
│  └─ Saves messages to graph                                     │
│  └─ Returns LLM response                                         │
│                                                                   │
│  graph.get_block_messages(block_id)                             │
│  └─ Returns list of messages for block                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Reads/Writes
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              STORAGE LAYER (json_storage.py)                     │
│                                                                   │
│  JSONStorage with atomic file writes (thread-safe)              │
│  └─ conversation.json (single source of truth)                  │
└────────────────────────────────────────────────────────────────┘
```

## Detailed Flow: Creating a New Mindmap

```
User (GUI)
    │
    ├─ Types "/new" in chat input
    │
    ▼
Frontend (main.js)
    │
    ├─ Check message === '/new'
    ├─ showTopicModal() -> "What would you like to discuss?"
    ├─ User enters: "Machine Learning Basics"
    │
    ▼
POST /api/mindmaps/new
{
    "topic": "Machine Learning Basics"
}
    │
    ▼
Backend (routes.py) - create_new_mindmap()
    │
    ├─ Get ConversationManager instance
    │
    ▼
ConversationManager.start_new_conversation("Machine Learning Basics")
    │
    ├─ Create new ConversationGraph()
    ├─ Call create_root_block() (uses LLM to set intent)
    ├─ Add root block to graph
    ├─ Add graph to mindmap
    ├─ Get LLM response for topic
    ├─ Add user message to block
    ├─ Add assistant message to block
    ├─ Save mindmap to storage
    └─ Return response text
    │
    ▼
Backend Response
{
    "graph_id": "uuid",
    "title": "Machine Learning Fundamentals",
    "root_block_id": "uuid",
    "initial_response": "Long LLM response...",
    ...
}
    │
    ▼
Frontend (main.js)
    │
    ├─ Refresh mindmap list (GET /api/mindmaps)
    ├─ Create new mindmap item in left panel
    ├─ Select new mindmap (GET /api/mindmaps/{graph_id}/graph)
    ├─ Draw D3 graph visualization
    ├─ Load initial block messages (GET /api/blocks/{root_id}/messages)
    ├─ Display messages in right panel
    ├─ Show success message + initial response
    │
    ▼
Display
    ├─ Left panel: New mindmap in list
    ├─ Middle panel: D3 graph with root node
    ├─ Right panel: Initial messages (topic + assistant response)
    └─ Ready for user to continue conversation
```

## Detailed Flow: Clicking a Graph Node

```
User clicks node in D3 graph
    │
    ▼
Frontend (main.js) - node.append('circle').on('click')
    │
    ├─ POST /api/blocks/{block_id}/switch (set context)
    ├─ Call loadBlockMessages(block_id)
    │
    ▼
GET /api/blocks/{block_id}/messages
    │
    ▼
Backend (routes.py) - get_block_messages()
    │
    ├─ Load mindmap from storage
    ├─ Find graph containing block
    ├─ Get block from graph
    └─ Call graph.get_block_messages(block_id)
    │
    ▼
ConversationGraph.get_block_messages(block_id)
    │
    ├─ Filter messages where message.block_id == block_id
    └─ Return list of ConversationMessages
    │
    ▼
Backend Response
{
    "block_id": "uuid",
    "title": "Block Title",
    "intent": "Block intent...",
    "messages": [
        {
            "message_id": "uuid",
            "role": "user",
            "content": "...",
            "timestamp": 1234567890
        },
        {
            "message_id": "uuid",
            "role": "assistant",
            "content": "...",
            "timestamp": 1234567890
        }
    ]
}
    │
    ▼
Frontend (main.js) - loadBlockMessages()
    │
    ├─ Update right panel header (block title + intent)
    ├─ Clear existing messages
    ├─ For each message:
    │  └─ Create chat bubble (user/assistant styled differently)
    ├─ Scroll to bottom
    │
    ▼
Display
    ├─ Right panel: Updated with block's messages
    ├─ Node highlighted in D3 graph (red circle)
    └─ Ready for user to send message in this block
```

## Detailed Flow: Sending a Message

```
User types message and sends (or Ctrl+Enter)
    │
    ▼
Frontend (main.js) - sendMessage()
    │
    ├─ Check if currentBlockId exists
    ├─ Display user message optimistically
    │
    ▼
POST /api/blocks/{currentBlockId}/messages
{
    "content": "User's question or statement"
}
    │
    ▼
Backend (routes.py) - add_message_to_block()
    │
    ├─ Load mindmap from storage
    ├─ Find containing graph
    ├─ Set conversation manager context:
    │  ├─ mgr.mindmap = mindmap
    │  ├─ mgr.graph = graph
    │  └─ mgr.graph.current_block_id = block_id
    │
    ▼
ConversationManager.continue_conversation(user_message)
    │
    ├─ Add user message to current block
    ├─ Get block context (title, intent, previous messages)
    ├─ Call LLM with full context via llm.call()
    ├─ Add assistant response to block
    ├─ Return response text
    │
    ▼
Backend saves to storage
    │
    └─ Uses atomic file writes (tempfile + os.replace)
    │
    ▼
Backend Response
{
    "block_id": "uuid",
    "messages": [ /* updated list */ ],
    "current_block_id": "uuid"
}
    │
    ▼
Frontend (main.js) - Update UI
    │
    ├─ Remove "thinking..." loading indicator
    ├─ Reload block messages (GET /api/blocks/{id}/messages)
    ├─ Display all messages with timestamps
    ├─ Refresh D3 graph to show new relationships
    ├─ Auto-scroll to bottom
    │
    ▼
Display
    ├─ User's message appears in chat
    ├─ Assistant's response appears in chat
    ├─ D3 graph may show new nodes/links
    └─ Ready for next message
```

## Equivalence: CLI vs GUI

### Creating Conversation

**CLI (main.py):**
```python
user_input = "/new"
first_msg = input("What do you want to discuss? > ")  # User input
response = manager.start_new_conversation(first_msg)
print(f"Assistant: {response}")
```

**GUI (main.js):**
```javascript
message = "/new"
const topic = prompt('What would you like to discuss?');  // User input
const response = await fetch('/api/mindmaps/new', {
    method: 'POST',
    body: JSON.stringify({ topic })
});
const data = await response.json();
// Display data.initial_response
```

### Continuing Conversation

**CLI (main.py):**
```python
user_input = "User's question"
response = manager.continue_conversation(user_input)
print(f"Assistant: {response}")
```

**GUI (main.js):**
```javascript
message = "User's question"
const result = await sendMessageToBlock(currentBlockId, message);
// Display result.messages (all messages including new ones)
```

### Viewing Block Messages

**CLI (main.py):**
```python
cmd = "/view"
block_id = "block_id"
messages = manager.graph.get_block_messages(block_id)
for m in messages:
    print(f"- [{m.role}] {m.content}")
```

**GUI (main.js):**
```javascript
const blockData = await fetch(`/api/blocks/${block_id}/messages`);
// Display blockData.messages in chat panel
```

## Key Design Principles

1. **No Duplication**: ConversationManager logic not duplicated between CLI and Web
2. **Stateless Backend**: Each request loads fresh mindmap from storage
3. **Atomic Updates**: All writes use atomic file operations
4. **Context Isolation**: Each API call sets manager context before executing
5. **Error Handling**: Both CLI and Web handle errors from manager
6. **Type Safety**: Pydantic models validate all API calls
7. **Lazy Loading**: Manager only created when first API call made
